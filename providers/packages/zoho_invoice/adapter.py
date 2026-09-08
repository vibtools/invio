from __future__ import annotations

import hashlib
import threading
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode, urlsplit

from src.core.provider_runtime import (
    BrowserOAuthProfile,
    ExternalOAuthAccountChoice,
    ExternalOAuthConnectionResult,
    ExternalOnboardingResult,
    ExternalRecipientResult,
    ExternalValidationIssue,
    NON_IDEMPOTENT_MUTATION,
    SAFE_READ,
    ProviderCapabilityProfile,
    ProviderOnboardingProfile,
    ProviderRuntimeError,
    ProviderSchedulingPolicy,
)


PROVIDER_ID = "zoho_invoice"
ADAPTER_VERSION = "1.2.0"
USER_AGENT = "Invio-ZohoInvoice-Provider/1.2.0 Vib-Tools"

# Zoho Invoice v3 publishes these eight API data-center domains.  The Accounts
# host is supplied explicitly by the user so the adapter never guesses a DC.
_ACCOUNTS_TO_INVOICE_API = {
    "accounts.zoho.com": "https://www.zohoapis.com",
    "accounts.zoho.eu": "https://www.zohoapis.eu",
    "accounts.zoho.in": "https://www.zohoapis.in",
    "accounts.zoho.com.au": "https://www.zohoapis.com.au",
    "accounts.zoho.jp": "https://www.zohoapis.jp",
    "accounts.zohocloud.ca": "https://www.zohoapis.ca",
    "accounts.zoho.com.cn": "https://www.zohoapis.com.cn",
    "accounts.zoho.sa": "https://www.zohoapis.sa",
}


class Adapter:
    interface_version = 1
    provider_id = PROVIDER_ID
    adapter_version = ADAPTER_VERSION

    # Zoho Invoice documents 100 API calls/minute per organization.  Invio's
    # current scheduling contract is per account, not per organization, so this
    # is intentionally conservative for the common one-account-per-org setup.
    scheduling_policy = ProviderSchedulingPolicy(
        requests_per_second_per_account=0.75,
        burst_capacity=1,
        account_cooldown_base_seconds=5.0,
        account_cooldown_cap_seconds=60.0,
        provider_cooldown_base_seconds=5.0,
        provider_cooldown_cap_seconds=60.0,
        account_rate_limit_reasons=frozenset(),
    )

    profile = ProviderCapabilityProfile(
        provider_id=PROVIDER_ID,
        executable_capabilities=frozenset({"invoice", "send_invoice", "api_test"}),
        task_execution_enabled=True,
        task_unavailable_message="",
        invoice_types=frozenset({"INVOICE"}),
        currencies=None,
        supports_automatic_tax=False,
        supports_line_tax=False,
        supports_customer_reuse=True,
        supports_memo=True,
        supports_footer=False,
        supports_customer_note=False,
        supports_terms=True,
        required_customer_fields=("email", "name"),
    )

    browser_oauth_profile = BrowserOAuthProfile(
        button_label="Connect Zoho Invoice",
        redirect_uri="http://127.0.0.1:8766/oauth/callback/zoho-invoice",
        pkce_required=True,
        connect_required_credential_keys=("accounts_server_url", "client_id", "client_secret"),
        timeout_seconds=180,
    )

    onboarding_profile = ProviderOnboardingProfile(
        button_label="Quick Connect",
        auto_verify=True,
    )

    @staticmethod
    def _oauth_accounts_server(value: str) -> tuple[str, str]:
        accounts_server = str(value).strip().rstrip("/")
        parsed = urlsplit(accounts_server)
        host = (parsed.hostname or "").lower()
        if (
            parsed.scheme.lower() != "https"
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or host not in _ACCOUNTS_TO_INVOICE_API
        ):
            raise ProviderRuntimeError(
                "Zoho Accounts Server must be an official HTTPS Zoho Accounts data-center origin.",
                category="preflight",
                retryable=False,
            )
        return accounts_server, host

    def build_oauth_authorization_url(self, context) -> str:
        accounts_server, _host = self._oauth_accounts_server(context.credentials.get("accounts_server_url", ""))
        client_id = str(context.credentials.get("client_id", "")).strip()
        if not client_id:
            raise ProviderRuntimeError("OAuth Client ID is required before connecting Zoho Invoice.", category="preflight")
        params = {
            "scope": "ZohoInvoice.settings.READ,ZohoInvoice.settings.CREATE,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE",
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": context.redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
            "state": context.state,
            "code_challenge": context.code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{accounts_server}/oauth/v2/auth?{urlencode(params)}"

    def complete_oauth_authorization(self, context) -> ExternalOAuthConnectionResult:
        configured_server, _configured_host = self._oauth_accounts_server(context.credentials.get("accounts_server_url", ""))
        callback_server = str(context.callback_params.get("accounts-server", "")).strip()
        accounts_server, host = self._oauth_accounts_server(callback_server or configured_server)
        client_id = str(context.credentials.get("client_id", "")).strip()
        client_secret = str(context.credentials.get("client_secret", "")).strip()
        if not client_id or not client_secret:
            raise ProviderRuntimeError("OAuth Client ID and Client Secret are required to complete Zoho Invoice authorization.", category="preflight")
        token_body = urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": context.authorization_code,
            "redirect_uri": context.redirect_uri,
            "code_verifier": context.code_verifier,
        }).encode("utf-8")
        token = context.request(
            stage="oauth_code_exchange",
            method="POST",
            url=f"{accounts_server}/oauth/v2/token",
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT},
            body=token_body,
        )
        if not isinstance(token, dict):
            raise ProviderRuntimeError("Zoho OAuth token response was not a JSON object.", category="response")
        error = str(token.get("error", "")).strip()
        if error:
            detail = str(token.get("error_description") or error).strip()
            raise ProviderRuntimeError(f"Zoho OAuth authorization failed: {detail}", category="authentication", retryable=False)
        access_token = str(token.get("access_token", "")).strip()
        refresh_token = str(token.get("refresh_token", "")).strip()
        if not access_token or not refresh_token:
            raise ProviderRuntimeError(
                "Zoho OAuth authorization did not return both access_token and refresh_token. Reconnect with offline access and consent enabled.",
                category="authentication",
                retryable=False,
            )
        api_origin = _ACCOUNTS_TO_INVOICE_API[host]
        organizations = context.request(
            stage="oauth_account_discovery",
            method="GET",
            url=f"{api_origin}/invoice/v3/organizations",
            headers={"Authorization": f"Zoho-oauthtoken {access_token}", "Accept": "application/json", "User-Agent": USER_AGENT},
        )
        if not isinstance(organizations, dict):
            raise ProviderRuntimeError("Zoho Invoice organization discovery returned an unexpected response.", category="response")
        rows = organizations.get("organizations")
        if not isinstance(rows, list):
            raise ProviderRuntimeError("Zoho Invoice organization discovery did not return an organizations list.", category="response")
        choices = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            organization_id = str(row.get("organization_id", "")).strip()
            if not organization_id:
                continue
            label = str(row.get("name", "")).strip() or f"Zoho Invoice {organization_id}"
            choices.append(ExternalOAuthAccountChoice(organization_id, label))
        if not choices:
            raise ProviderRuntimeError("No Zoho Invoice organization is available to the authorized user.", category="preflight", retryable=False)
        return ExternalOAuthConnectionResult(
            credential_updates={"accounts_server_url": accounts_server, "refresh_token": refresh_token},
            message="Zoho Invoice authorization completed. Invio will refresh access tokens automatically.",
            choices=tuple(choices),
            choice_credential_key="organization_id",
        )

    def __init__(self) -> None:
        self._cache_lock = threading.RLock()
        self._token_cache: dict[str, tuple[str, str, float]] = {}
        self._currency_cache: dict[tuple[str, str], str] = {}
        self._item_cache: dict[tuple[str, str], str] = {}

    # ------------------------------------------------------------------
    # Public P13 adapter interface
    # ------------------------------------------------------------------

    def prepare_account(self, context) -> ExternalOnboardingResult:
        account = self._account_values(context.credentials)
        access_token, invoice_api = self._access_token(context, account)
        organization_id = account[4]
        organization = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            stage="onboarding_organization_read",
            operation_kind=SAFE_READ,
            method="GET",
            path=f"/organizations/{organization_id}",
        )
        org = organization.get("organization")
        if not isinstance(org, dict) or str(org.get("organization_id", "")).strip() != organization_id:
            raise ProviderRuntimeError("Zoho Invoice organization could not be verified during Easy Onboarding.", category="response")
        account_label = str(org.get("name", "")).strip() or "Zoho Invoice"

        default_item_id = account[5]
        if default_item_id:
            item = self._invoice_request(
                context, access_token=access_token, invoice_api=invoice_api, organization_id=organization_id,
                stage="onboarding_default_item_read", operation_kind=SAFE_READ, method="GET",
                path=f"/items/{default_item_id}",
            ).get("item")
            if not isinstance(item, dict) or self._positive_numeric_id(item.get("item_id")) != default_item_id:
                raise ProviderRuntimeError("Configured Zoho Invoice Default Item ID could not be verified.", category="preflight")
            if str(item.get("status", "active")).strip().lower() not in {"", "active"}:
                raise ProviderRuntimeError("Configured Zoho Invoice Default Item ID is inactive.", category="preflight")
            managed_item_id = default_item_id
            created = False
        else:
            result = self._invoice_request(
                context, access_token=access_token, invoice_api=invoice_api, organization_id=organization_id,
                stage="onboarding_managed_item_lookup", operation_kind=SAFE_READ, method="GET", path="/items",
                query={"name": "Invio Service", "per_page": 200},
            )
            items = result.get("items")
            if not isinstance(items, list):
                raise ProviderRuntimeError("Zoho Invoice items response is missing items list.", category="response")
            matches = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                if str(item.get("name", "")).strip().casefold() != "invio service":
                    continue
                if str(item.get("status", "active")).strip().lower() not in {"", "active"}:
                    continue
                item_id = self._positive_numeric_id(item.get("item_id"))
                if item_id:
                    matches.append(item_id)
            unique = sorted(set(matches))
            if len(unique) > 1:
                raise ProviderRuntimeError("Multiple active Zoho Invoice items are named 'Invio Service'; managed resource selection is ambiguous.", category="preflight")
            if unique:
                managed_item_id = unique[0]
                created = False
            else:
                created_result = self._invoice_request(
                    context, access_token=access_token, invoice_api=invoice_api, organization_id=organization_id,
                    stage="onboarding_managed_item_create", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST", path="/items",
                    json_data={
                        "name": "Invio Service",
                        "rate": 0,
                        "description": "Invio-managed default service item for automated invoice line mapping.",
                        "product_type": "service",
                    },
                )
                item = created_result.get("item")
                managed_item_id = self._positive_numeric_id(item.get("item_id") if isinstance(item, dict) else None)
                if not managed_item_id or not isinstance(item, dict) or str(item.get("name", "")).strip() != "Invio Service":
                    raise ProviderRuntimeError("Zoho Invoice managed item creation did not return the expected Invio Service item.", category="response")
                created = True

        action = "created" if created else "reused"
        return ExternalOnboardingResult(
            credential_updates={"default_item_id": managed_item_id},
            message=f"Zoho Invoice account prepared. Invio Service {action} and provider-managed credentials are ready.",
            account_label=account_label,
        )

    def test_account(self, context):
        account = self._account_values(context.credentials)
        access_token, invoice_api = self._access_token(context, account)

        organization = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=account[4],
            stage="organization_read",
            operation_kind=SAFE_READ,
            method="GET",
            path=f"/organizations/{account[4]}",
        )
        org = organization.get("organization")
        if not isinstance(org, dict) or str(org.get("organization_id", "")).strip() != account[4]:
            raise ProviderRuntimeError(
                "Zoho Invoice organization verification did not return the configured organization ID.",
                category="provider-contract",
                retryable=False,
            )

        self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=account[4],
            stage="contacts_read",
            operation_kind=SAFE_READ,
            method="GET",
            path="/contacts",
            query={"contact_type": "customer", "per_page": 1},
        )
        self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=account[4],
            stage="items_read",
            operation_kind=SAFE_READ,
            method="GET",
            path="/items",
            query={"per_page": 1},
        )
        self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=account[4],
            stage="invoices_read",
            operation_kind=SAFE_READ,
            method="GET",
            path="/invoices",
            query={"per_page": 1},
        )

        default_item_id = account[5]
        if default_item_id:
            item_result = self._invoice_request(
                context,
                access_token=access_token,
                invoice_api=invoice_api,
                organization_id=account[4],
                stage="default_item_read",
                operation_kind=SAFE_READ,
                method="GET",
                path=f"/items/{default_item_id}",
            )
            item = item_result.get("item")
            if not isinstance(item, dict) or str(item.get("item_id", "")).strip() != default_item_id:
                raise ProviderRuntimeError(
                    "Zoho Invoice Default Item ID did not resolve to the configured item.",
                    category="provider-contract",
                    retryable=False,
                )
            if str(item.get("status", "active")).strip().lower() not in {"", "active"}:
                raise ProviderRuntimeError(
                    "Zoho Invoice Default Item ID is not active.",
                    category="provider-state",
                    retryable=False,
                )

        return "Zoho Invoice API connection verified."

    def validate_task(self, context):
        issues: list[ExternalValidationIssue] = []
        template = context.template

        if str(template.invoice_type).strip().upper() != "INVOICE":
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_invoice_type",
                    "Zoho Invoice provider supports customer invoices only.",
                    "Use Invoice Type INVOICE.",
                )
            )
        if str(template.invoice_title).strip() not in {"", "Invoice"}:
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_invoice_title",
                    "Zoho Invoice provider does not map a custom Invio invoice title.",
                    "Use the default Invoice title.",
                )
            )
        if str(template.invoice_subtitle).strip():
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_invoice_subtitle",
                    "Zoho Invoice provider does not map the Invio invoice subtitle field.",
                    "Leave Invoice Subtitle blank.",
                )
            )
        if bool(template.automatic_tax):
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_automatic_tax",
                    "Zoho Invoice provider does not infer automatic tax configuration.",
                    "Disable Automatic Tax for this Task.",
                )
            )
        if str(template.footer).strip():
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_footer",
                    "Zoho Invoice provider does not map the Invio footer field.",
                    "Leave Footer blank for this Task.",
                )
            )
        if str(template.customer_note).strip():
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_customer_note",
                    "Zoho Invoice provider does not map the Invio customer-note field.",
                    "Leave Customer Note blank for this Task.",
                )
            )
        if not template.items:
            issues.append(
                ExternalValidationIssue(
                    "zoho_invoice_items",
                    "Zoho Invoice invoice requires at least one line item.",
                    "Add at least one invoice item.",
                )
            )
        for index, item in enumerate(template.items, start=1):
            description = str(item.description).strip()
            if not description:
                issues.append(
                    ExternalValidationIssue(
                        "zoho_invoice_item_name",
                        f"Zoho Invoice invoice item {index} requires a non-empty description/item name.",
                        "Set the Invio item description to an existing Zoho Invoice Item name or configure Default Item ID.",
                    )
                )
            if Decimal(item.quantity) <= 0:
                issues.append(
                    ExternalValidationIssue(
                        "zoho_invoice_quantity",
                        f"Zoho Invoice invoice item {index} must have a positive quantity.",
                        "Use a quantity greater than zero.",
                    )
                )
            if Decimal(item.unit_amount) < 0:
                issues.append(
                    ExternalValidationIssue(
                        "zoho_invoice_unit_amount",
                        f"Zoho Invoice invoice item {index} cannot use a negative unit amount in this adapter.",
                        "Use a zero or positive unit amount.",
                    )
                )
            if Decimal(item.tax_rate) != 0:
                issues.append(
                    ExternalValidationIssue(
                        "zoho_invoice_line_tax",
                        f"Zoho Invoice invoice item {index} has a non-zero Invio line-tax rate that cannot be mapped safely without a Zoho tax_id.",
                        "Set the Invio line tax to 0 for this provider.",
                    )
                )
        return tuple(issues)

    def execute_recipient(self, context):
        account = self._account_values(context.credentials)
        access_token, invoice_api = self._access_token(context, account)
        organization_id = account[4]
        default_item_id = account[5]

        currency_id = self._resolve_currency(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            currency_code=context.template.currency,
            cache_key=self._credential_cache_key(account),
        )

        # Resolve every item before the first business-data mutation so missing
        # or ambiguous catalog mappings fail closed without creating a contact.
        item_ids = [
            self._resolve_item(
                context,
                access_token=access_token,
                invoice_api=invoice_api,
                organization_id=organization_id,
                description=str(item.description).strip(),
                default_item_id=default_item_id,
                cache_key=self._credential_cache_key(account),
            )
            for item in context.template.items
        ]

        contact_id = self._resolve_contact(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            currency_id=currency_id,
            currency_code=str(context.template.currency).strip().upper(),
        )

        today = date.today()
        due = today + timedelta(days=int(context.template.days_until_due))
        line_items: list[dict[str, Any]] = []
        for item, item_id in zip(context.template.items, item_ids):
            line_items.append(
                {
                    "item_id": item_id,
                    "description": str(item.description).strip(),
                    "rate": float(Decimal(item.unit_amount)),
                    "quantity": float(Decimal(item.quantity)),
                }
            )

        invoice_payload: dict[str, Any] = {
            "customer_id": contact_id,
            "currency_id": currency_id,
            "date": today.isoformat(),
            "due_date": due.isoformat(),
            "payment_terms": int(context.template.days_until_due),
            "send": False,
            "line_items": line_items,
        }
        memo = str(context.template.memo).strip()
        if memo:
            invoice_payload["notes"] = memo
        if context.template.terms:
            invoice_payload["terms"] = "\n".join(str(term).strip() for term in context.template.terms if str(term).strip())

        invoice_result = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            stage="invoice_create",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            method="POST",
            path="/invoices",
            json_data=invoice_payload,
        )
        invoice = invoice_result.get("invoice")
        invoice_id = self._positive_numeric_id(invoice.get("invoice_id") if isinstance(invoice, dict) else None)
        if not invoice_id:
            raise ProviderRuntimeError(
                "Zoho Invoice invoice creation succeeded without a usable invoice_id in the response.",
                category="response",
                retryable=False,
            )
        context.log(f"Zoho Invoice invoice created (provider invoice {invoice_id}).")

        send_result = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            stage="invoice_email_send",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            method="POST",
            path=f"/invoices/{invoice_id}/email",
            query={"send_attachment": "true"},
            json_data={"to_mail_ids": [context.customer.email]},
        )
        message = str(send_result.get("message", "")).strip()
        if message:
            context.log(f"Zoho Invoice accepted invoice email request: {message}")
        else:
            context.log("Zoho Invoice accepted invoice email request.")

        return ExternalRecipientResult(
            provider_customer_id=contact_id,
            provider_invoice_id=invoice_id,
            final_stage="external_mutation:invoice_email_send",
        )

    # ------------------------------------------------------------------
    # Account/authentication helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _account_values(credentials: dict[str, str]) -> tuple[str, str, str, str, str, str]:
        accounts_server = str(credentials.get("accounts_server_url", "")).strip().rstrip("/")
        client_id = str(credentials.get("client_id", "")).strip()
        client_secret = str(credentials.get("client_secret", "")).strip()
        refresh_token = str(credentials.get("refresh_token", "")).strip()
        organization_id = str(credentials.get("organization_id", "")).strip()
        default_item_id = str(credentials.get("default_item_id", "")).strip()

        missing = [
            label
            for label, value in (
                ("Zoho Accounts Server", accounts_server),
                ("OAuth Client ID", client_id),
                ("OAuth Client Secret", client_secret),
                ("OAuth Refresh Token", refresh_token),
                ("Zoho Invoice Organization ID", organization_id),
            )
            if not value
        ]
        if missing:
            raise ProviderRuntimeError(
                "Zoho Invoice account is missing required credential field(s): " + ", ".join(missing) + ".",
                category="preflight",
                retryable=False,
            )

        parsed = urlsplit(accounts_server)
        host = (parsed.hostname or "").lower()
        if (
            parsed.scheme.lower() != "https"
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or host not in _ACCOUNTS_TO_INVOICE_API
        ):
            raise ProviderRuntimeError(
                "Zoho Accounts Server must be an official HTTPS Zoho Accounts data-center origin.",
                category="preflight",
                retryable=False,
            )
        if not organization_id.isdigit():
            raise ProviderRuntimeError(
                "Zoho Invoice Organization ID must contain numeric characters only.",
                category="preflight",
                retryable=False,
            )
        if default_item_id and not default_item_id.isdigit():
            raise ProviderRuntimeError(
                "Zoho Invoice Default Item ID must contain numeric characters only when provided.",
                category="preflight",
                retryable=False,
            )
        return accounts_server, client_id, client_secret, refresh_token, organization_id, default_item_id

    @staticmethod
    def _credential_cache_key(account: tuple[str, str, str, str, str, str]) -> str:
        material = "\x00".join(account[:5]).encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    def _access_token(self, context, account: tuple[str, str, str, str, str, str]) -> tuple[str, str]:
        accounts_server, client_id, client_secret, refresh_token, _organization_id, _default_item_id = account
        cache_key = self._credential_cache_key(account)
        now = time.monotonic()
        with self._cache_lock:
            cached = self._token_cache.get(cache_key)
            if cached is not None and cached[2] > now:
                return cached[0], cached[1]

        token_url = f"{accounts_server}/oauth/v2/token"
        token_body = urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            }
        ).encode("utf-8")
        response = context.request(
            stage="oauth_refresh",
            operation_kind=SAFE_READ,
            method="POST",
            url=token_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            body=token_body,
        )
        if not isinstance(response, dict):
            raise ProviderRuntimeError("Zoho OAuth refresh response was not a JSON object.", category="response")
        if str(response.get("error", "")).strip():
            description = str(response.get("error_description", response.get("error", "OAuth refresh failed"))).strip()
            raise ProviderRuntimeError(
                f"Zoho OAuth refresh failed: {description}",
                category="authentication",
                retryable=False,
            )
        access_token = str(response.get("access_token", "")).strip()
        if not access_token:
            raise ProviderRuntimeError("Zoho OAuth refresh response did not contain access_token.", category="response")

        accounts_host = (urlsplit(accounts_server).hostname or "").lower()
        invoice_api = _ACCOUNTS_TO_INVOICE_API[accounts_host]
        try:
            expires_in = int(response.get("expires_in", 3600))
        except (TypeError, ValueError):
            expires_in = 3600
        usable_for = max(60, min(expires_in, 3600) - 120)
        with self._cache_lock:
            self._token_cache[cache_key] = (access_token, invoice_api, time.monotonic() + usable_for)
        return access_token, invoice_api

    # ------------------------------------------------------------------
    # Zoho Invoice REST helpers
    # ------------------------------------------------------------------

    def _invoice_request(
        self,
        context,
        *,
        access_token: str,
        invoice_api: str,
        organization_id: str,
        stage: str,
        operation_kind: str,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_path = "/" + str(path).lstrip("/")
        query_data = dict(query or {})
        query_string = urlencode(query_data, doseq=True)
        url = f"{invoice_api}/invoice/v3{clean_path}"
        if query_string:
            url += "?" + query_string
        response = context.request(
            stage=stage,
            operation_kind=operation_kind,
            method=method,
            url=url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "X-com-zoho-invoice-organizationid": organization_id,
                "User-Agent": USER_AGENT,
            },
            json_data=json_data,
        )
        if not isinstance(response, dict):
            raise ProviderRuntimeError("Zoho Invoice response was not a JSON object.", category="response")
        if "code" in response:
            code = response.get("code")
            try:
                numeric_code = int(code)
            except (TypeError, ValueError):
                numeric_code = -1
            if numeric_code != 0:
                message = str(response.get("message", "Zoho Invoice API returned a non-success response.")).strip()
                raise ProviderRuntimeError(
                    f"Zoho Invoice API error code {code!s}: {message}",
                    category="provider",
                    retryable=False,
                )
        # Invio's host transport has already enforced HTTP 2xx here.  Some
        # Zoho mutation endpoints may return an empty 2xx response body, so an
        # absent business-level `code` is accepted while payload-bearing reads
        # are still validated by their callers.
        return response

    def _resolve_currency(
        self,
        context,
        *,
        access_token: str,
        invoice_api: str,
        organization_id: str,
        currency_code: str,
        cache_key: str,
    ) -> str:
        wanted = str(currency_code).strip().upper()
        key = (cache_key, wanted)
        with self._cache_lock:
            cached = self._currency_cache.get(key)
            if cached:
                return cached

        page = 1
        while page <= 20:
            result = self._invoice_request(
                context,
                access_token=access_token,
                invoice_api=invoice_api,
                organization_id=organization_id,
                stage="currency_lookup",
                operation_kind=SAFE_READ,
                method="GET",
                path="/settings/currencies",
                query={"page": page, "per_page": 200},
            )
            currencies = result.get("currencies")
            if not isinstance(currencies, list):
                raise ProviderRuntimeError("Zoho Invoice currencies response is missing currencies list.", category="response")
            for currency in currencies:
                if not isinstance(currency, dict):
                    continue
                if str(currency.get("currency_code", "")).strip().upper() == wanted:
                    currency_id = self._positive_numeric_id(currency.get("currency_id"))
                    if currency_id:
                        with self._cache_lock:
                            self._currency_cache[key] = currency_id
                        return currency_id
            page_context = result.get("page_context")
            if not isinstance(page_context, dict) or not bool(page_context.get("has_more_page")):
                break
            page += 1
        raise ProviderRuntimeError(
            f"Zoho Invoice organization does not expose configured currency {wanted}.",
            category="preflight",
            retryable=False,
        )

    def _resolve_item(
        self,
        context,
        *,
        access_token: str,
        invoice_api: str,
        organization_id: str,
        description: str,
        default_item_id: str,
        cache_key: str,
    ) -> str:
        if default_item_id:
            key = (cache_key, f"id:{default_item_id}")
            with self._cache_lock:
                cached = self._item_cache.get(key)
                if cached:
                    return cached
            result = self._invoice_request(
                context,
                access_token=access_token,
                invoice_api=invoice_api,
                organization_id=organization_id,
                stage="default_item_lookup",
                operation_kind=SAFE_READ,
                method="GET",
                path=f"/items/{default_item_id}",
            )
            item = result.get("item")
            item_id = self._positive_numeric_id(item.get("item_id") if isinstance(item, dict) else None)
            if not item_id:
                raise ProviderRuntimeError("Zoho Invoice Default Item ID could not be resolved.", category="preflight")
            if str(item.get("status", "active")).strip().lower() not in {"", "active"}:
                raise ProviderRuntimeError("Zoho Invoice Default Item ID is inactive.", category="preflight")
            with self._cache_lock:
                self._item_cache[key] = item_id
            return item_id

        wanted = description.strip()
        key = (cache_key, "name:" + wanted.casefold())
        with self._cache_lock:
            cached = self._item_cache.get(key)
            if cached:
                return cached
        result = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            stage="item_lookup",
            operation_kind=SAFE_READ,
            method="GET",
            path="/items",
            query={"name": wanted, "per_page": 200},
        )
        items = result.get("items")
        if not isinstance(items, list):
            raise ProviderRuntimeError("Zoho Invoice items response is missing items list.", category="response")
        matches: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("name", "")).strip().casefold() != wanted.casefold():
                continue
            if str(item.get("status", "active")).strip().lower() not in {"", "active"}:
                continue
            item_id = self._positive_numeric_id(item.get("item_id"))
            if item_id:
                matches.append(item_id)
        unique = sorted(set(matches))
        if len(unique) != 1:
            if not unique:
                raise ProviderRuntimeError(
                    f"No active Zoho Invoice Item exactly matches Invio line-item description '{wanted}'. "
                    "Create that Zoho Item or configure Default Item ID on the Invio account.",
                    category="preflight",
                    retryable=False,
                )
            raise ProviderRuntimeError(
                f"Multiple active Zoho Invoice Items exactly match '{wanted}'; item mapping is ambiguous.",
                category="preflight",
                retryable=False,
            )
        with self._cache_lock:
            self._item_cache[key] = unique[0]
        return unique[0]

    def _resolve_contact(
        self,
        context,
        *,
        access_token: str,
        invoice_api: str,
        organization_id: str,
        currency_id: str,
        currency_code: str,
    ) -> str:
        email = str(context.customer.email).strip()
        if bool(context.template.reuse_customer):
            result = self._invoice_request(
                context,
                access_token=access_token,
                invoice_api=invoice_api,
                organization_id=organization_id,
                stage="contact_lookup",
                operation_kind=SAFE_READ,
                method="GET",
                path="/contacts",
                query={"contact_type": "customer", "email": email, "per_page": 200},
            )
            contacts = result.get("contacts")
            if not isinstance(contacts, list):
                raise ProviderRuntimeError("Zoho Invoice contacts response is missing contacts list.", category="response")
            exact: list[dict[str, Any]] = []
            for contact in contacts:
                if not isinstance(contact, dict):
                    continue
                if str(contact.get("email", "")).strip().casefold() != email.casefold():
                    continue
                if str(contact.get("contact_type", "customer")).strip().lower() != "customer":
                    continue
                if str(contact.get("status", "active")).strip().lower() not in {"", "active"}:
                    continue
                exact.append(contact)
            if len(exact) > 1:
                raise ProviderRuntimeError(
                    f"Multiple active Zoho Invoice customer contacts use {email}; customer reuse is ambiguous.",
                    category="preflight",
                    retryable=False,
                )
            if exact:
                contact = exact[0]
                contact_id = self._positive_numeric_id(contact.get("contact_id"))
                if not contact_id:
                    raise ProviderRuntimeError("Zoho Invoice reused contact is missing contact_id.", category="response")
                existing_currency_id = str(contact.get("currency_id", "")).strip()
                existing_currency_code = str(contact.get("currency_code", "")).strip().upper()
                if existing_currency_id and existing_currency_id != currency_id:
                    raise ProviderRuntimeError(
                        f"Zoho Invoice customer {email} is assigned to currency {existing_currency_code or existing_currency_id}, "
                        f"but the Invio template uses {currency_code}.",
                        category="preflight",
                        retryable=False,
                    )
                if existing_currency_code and existing_currency_code != currency_code:
                    raise ProviderRuntimeError(
                        f"Zoho Invoice customer {email} uses {existing_currency_code}, but the Invio template uses {currency_code}.",
                        category="preflight",
                        retryable=False,
                    )
                context.log(f"Zoho Invoice customer found for {email} (contact {contact_id}).")
                return contact_id

        payload = {
            "contact_name": str(context.customer.name).strip(),
            "contact_type": "customer",
            "currency_id": currency_id,
            "contact_persons": [
                {
                    "email": email,
                    "is_primary_contact": True,
                }
            ],
        }
        created = self._invoice_request(
            context,
            access_token=access_token,
            invoice_api=invoice_api,
            organization_id=organization_id,
            stage="contact_create",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            method="POST",
            path="/contacts",
            json_data=payload,
        )
        contact = created.get("contact")
        contact_id = self._positive_numeric_id(contact.get("contact_id") if isinstance(contact, dict) else None)
        if not contact_id:
            raise ProviderRuntimeError(
                "Zoho Invoice contact creation succeeded without a usable contact_id in the response.",
                category="response",
                retryable=False,
            )
        context.log(f"Zoho Invoice customer created for {email} (contact {contact_id}).")
        return contact_id

    @staticmethod
    def _positive_numeric_id(value: Any) -> str:
        text = str(value or "").strip()
        if text.isdigit() and int(text) > 0:
            return text
        return ""


def create_adapter():
    return Adapter()
