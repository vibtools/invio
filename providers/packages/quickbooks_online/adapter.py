from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from src.core.provider_runtime import (
    BrowserOAuthProfile,
    ExternalOAuthConnectionResult,
    ExternalOnboardingResult,
    ExternalRecipientResult,
    ExternalValidationIssue,
    IDEMPOTENT_MUTATION,
    SAFE_READ,
    ProviderCapabilityProfile,
    ProviderOnboardingProfile,
    ProviderRuntimeError,
)
from src.core.storage import CredentialStore, CredentialStoreError


PROVIDER_ID = "quickbooks_online"
ADAPTER_VERSION = "1.2.0"
USER_AGENT = "Invio-QuickBooks-Online-Provider/1.2.0 Vib-Tools"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API_BASES = {
    "Sandbox": "https://sandbox-quickbooks.api.intuit.com",
    "Production": "https://quickbooks.api.intuit.com",
}
MINOR_VERSION = "75"


class Adapter:
    interface_version = 1
    provider_id = PROVIDER_ID
    adapter_version = ADAPTER_VERSION
    scheduling_policy = None
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
        supports_terms=False,
        required_customer_fields=("email", "name"),
    )

    browser_oauth_profile = BrowserOAuthProfile(
        button_label="Connect QuickBooks Online",
        redirect_uri_credential_key="redirect_uri",
        pkce_required=False,
        connect_required_credential_keys=("client_id", "client_secret", "redirect_uri"),
        timeout_seconds=300,
    )

    onboarding_profile = ProviderOnboardingProfile(
        button_label="Quick Connect",
        auto_verify=True,
    )

    @staticmethod
    def _validate_browser_redirect(redirect_uri: str, mode: str) -> None:
        parsed = urlsplit(str(redirect_uri).strip())
        host = (parsed.hostname or "").strip().lower()
        if mode == "Production":
            if parsed.scheme.lower() != "https":
                raise ProviderRuntimeError(
                    "QuickBooks Production OAuth Redirect URI must use HTTPS. Intuit does not permit localhost HTTP redirects for production apps.",
                    category="preflight", retryable=False,
                )
            if host in {"localhost", "127.0.0.1", "::1"}:
                raise ProviderRuntimeError(
                    "QuickBooks Production OAuth Redirect URI cannot use localhost/loopback. Configure the exact registered HTTPS callback URI and paste the final callback URL into Invio after consent.",
                    category="preflight", retryable=False,
                )
            # Intuit production redirect registration does not accept IP-address hosts.
            try:
                import ipaddress
                ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                raise ProviderRuntimeError(
                    "QuickBooks Production OAuth Redirect URI must use a DNS hostname, not an IP address.",
                    category="preflight", retryable=False,
                )

    def build_oauth_authorization_url(self, context) -> str:
        client_id = str(context.credentials.get("client_id", "")).strip()
        mode = str(context.mode).strip()
        if mode not in API_BASES:
            raise ProviderRuntimeError("QuickBooks account mode must be Sandbox or Production.", category="preflight")
        if not client_id:
            raise ProviderRuntimeError("OAuth Client ID is required before connecting QuickBooks Online.", category="preflight")
        self._validate_browser_redirect(context.redirect_uri, mode)
        params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": context.redirect_uri,
            "state": context.state,
        }
        return "https://appcenter.intuit.com/connect/oauth2?" + urlencode(params)

    def complete_oauth_authorization(self, context) -> ExternalOAuthConnectionResult:
        client_id = str(context.credentials.get("client_id", "")).strip()
        client_secret = str(context.credentials.get("client_secret", "")).strip()
        if not client_id or not client_secret:
            raise ProviderRuntimeError("OAuth Client ID and Client Secret are required to complete QuickBooks authorization.", category="preflight")
        mode = str(context.mode).strip()
        if mode not in API_BASES:
            raise ProviderRuntimeError("QuickBooks account mode must be Sandbox or Production.", category="preflight")
        self._validate_browser_redirect(context.redirect_uri, mode)
        realm_id = str(context.callback_params.get("realmId", "")).strip()
        if not realm_id:
            raise ProviderRuntimeError("QuickBooks OAuth callback did not include realmId.", category="authentication", retryable=False)
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        body = urlencode({
            "grant_type": "authorization_code",
            "code": context.authorization_code,
            "redirect_uri": context.redirect_uri,
        }).encode("utf-8")
        token = context.request(
            stage="oauth_code_exchange",
            method="POST",
            url=TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            body=body,
        )
        if not isinstance(token, dict):
            raise ProviderRuntimeError("QuickBooks OAuth token response was not a JSON object.", category="response")
        error = str(token.get("error", "")).strip()
        if error:
            detail = str(token.get("error_description") or error).strip()
            raise ProviderRuntimeError(f"QuickBooks OAuth authorization failed: {detail}", category="authentication", retryable=False)
        refresh_token = str(token.get("refresh_token", "")).strip()
        access_token = str(token.get("access_token", "")).strip()
        if not refresh_token or not access_token:
            raise ProviderRuntimeError("QuickBooks OAuth authorization did not return both access_token and refresh_token.", category="authentication", retryable=False)
        return ExternalOAuthConnectionResult(
            credential_updates={"refresh_token": refresh_token, "realm_id": realm_id},
            message="QuickBooks Online authorization completed. Invio will persist the latest rotated refresh token automatically.",
        )

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._access_cache: dict[str, tuple[str, float]] = {}

    def prepare_account(self, context) -> ExternalOnboardingResult:
        client_id = str(context.credentials.get("client_id", "")).strip()
        client_secret = str(context.credentials.get("client_secret", "")).strip()
        refresh_token = str(context.credentials.get("refresh_token", "")).strip()
        mode = str(context.mode).strip()
        realm_id = str(context.credentials.get("realm_id", "")).strip()
        if mode not in API_BASES or not client_id or not client_secret or not refresh_token or not realm_id:
            raise ProviderRuntimeError(
                "QuickBooks Quick Connect requires completed browser authorization and valid app credentials before account preparation.",
                category="preflight", retryable=False,
            )
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_result = context.request(
            stage="onboarding_oauth_refresh", operation_kind=SAFE_READ, method="POST", url=TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth}", "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT,
            },
            body=urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode(),
        )
        access_token = str(token_result.get("access_token", "")).strip() if isinstance(token_result, dict) else ""
        latest_refresh = str(token_result.get("refresh_token", "")).strip() if isinstance(token_result, dict) else ""
        if not access_token or not latest_refresh:
            raise ProviderRuntimeError("QuickBooks onboarding OAuth refresh did not return both access_token and refresh_token.", category="response")

        company = self._qbo_request(
            context, token=access_token, mode=mode, realm_id=realm_id, stage="onboarding_company_read",
            operation_kind=SAFE_READ, method="GET", resource=f"companyinfo/{quote(realm_id, safe='')}"
        ).get("CompanyInfo")
        if not isinstance(company, dict) or str(company.get("Id", "")).strip() != realm_id:
            raise ProviderRuntimeError("QuickBooks CompanyInfo could not verify the connected company during Easy Onboarding.", category="response")
        account_label = str(company.get("CompanyName", "")).strip() or str(company.get("LegalName", "")).strip() or "QuickBooks Online"

        configured_item_id = str(context.credentials.get("default_item_id", "")).strip()
        if configured_item_id:
            item = self._qbo_request(
                context, token=access_token, mode=mode, realm_id=realm_id, stage="onboarding_default_item_read",
                operation_kind=SAFE_READ, method="GET", resource=f"item/{quote(configured_item_id, safe='')}"
            ).get("Item")
            if not isinstance(item, dict) or str(item.get("Id", "")).strip() != configured_item_id or item.get("Active") is False:
                raise ProviderRuntimeError("Configured QuickBooks Default Item ID is missing or inactive.", category="preflight")
            managed_item_id = configured_item_id
            created = False
        else:
            item_result = self._query(
                context, token=access_token, mode=mode, realm_id=realm_id, stage="onboarding_managed_item_lookup",
                statement="SELECT * FROM Item WHERE Name = 'Invio Service' AND Active = true STARTPOSITION 1 MAXRESULTS 1000",
            )
            response = item_result.get("QueryResponse")
            items = response.get("Item", []) if isinstance(response, dict) else []
            if isinstance(items, dict):
                items = [items]
            matches = [
                row for row in items
                if isinstance(row, dict) and str(row.get("Name", "")).strip() == "Invio Service" and row.get("Active", True)
            ] if isinstance(items, list) else []
            if len(matches) > 1:
                raise ProviderRuntimeError("Multiple active QuickBooks Items are named 'Invio Service'; managed resource selection is ambiguous.", category="preflight")
            if matches:
                managed_item_id = str(matches[0].get("Id", "")).strip()
                if not managed_item_id:
                    raise ProviderRuntimeError("QuickBooks Invio Service item is missing Id.", category="response")
                created = False
            else:
                accounts_result = self._query(
                    context, token=access_token, mode=mode, realm_id=realm_id, stage="onboarding_income_accounts_read",
                    statement="SELECT * FROM Account WHERE Active = true STARTPOSITION 1 MAXRESULTS 1000",
                )
                account_response = accounts_result.get("QueryResponse")
                account_rows = account_response.get("Account", []) if isinstance(account_response, dict) else []
                if isinstance(account_rows, dict):
                    account_rows = [account_rows]
                candidates = []
                for row in account_rows if isinstance(account_rows, list) else []:
                    if not isinstance(row, dict):
                        continue
                    account_type = str(row.get("AccountType", "")).strip().casefold()
                    if account_type != "income" or row.get("Active") is False:
                        continue
                    account_id = str(row.get("Id", "")).strip()
                    name = str(row.get("Name", "")).strip()
                    subtype = str(row.get("AccountSubType", "")).strip()
                    if account_id:
                        candidates.append((account_id, name, subtype))
                preferred = [row for row in candidates if row[1].casefold() == "sales of product income" or row[2].casefold() == "salesofproductincome"]
                usable = preferred if len(preferred) == 1 else candidates if len(candidates) == 1 else []
                if len(usable) != 1:
                    raise ProviderRuntimeError(
                        "QuickBooks needs one unambiguous active Income account to create the managed Invio Service item. "
                        "Create an 'Invio Service' Service item manually or configure Default Item ID in Advanced Setup.",
                        category="preflight", retryable=False,
                    )
                income_id, income_name, _subtype = usable[0]
                request_id = "invio-onboarding-" + hashlib.sha256(f"{realm_id}\0Invio Service".encode()).hexdigest()[:32]
                created_result = self._qbo_request(
                    context, token=access_token, mode=mode, realm_id=realm_id, stage="onboarding_managed_item_create",
                    operation_kind=IDEMPOTENT_MUTATION, method="POST", resource="item",
                    query={"requestid": request_id},
                    json_data={
                        "Name": "Invio Service",
                        "Type": "Service",
                        "IncomeAccountRef": {"value": income_id, "name": income_name},
                    },
                    idempotency_key=request_id,
                )
                item = created_result.get("Item")
                managed_item_id = str(item.get("Id", "")).strip() if isinstance(item, dict) else ""
                if not managed_item_id or not isinstance(item, dict) or str(item.get("Name", "")).strip() != "Invio Service":
                    raise ProviderRuntimeError("QuickBooks managed item creation did not return the expected Invio Service item.", category="response")
                created = True

        action = "created" if created else "reused"
        return ExternalOnboardingResult(
            credential_updates={"refresh_token": latest_refresh, "default_item_id": managed_item_id},
            message=f"QuickBooks account prepared. Invio Service {action} and provider-managed credentials are ready.",
            account_label=account_label,
        )

    def test_account(self, context):
        account = self._account_values(context.credentials, context.mode)
        token = self._access_token(account)
        mode, realm_id, default_item_id = account[3], account[4], account[5]
        # A host-managed SAFE_READ is mandatory for executable external API Test.
        company = self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage="company_info_read",
            operation_kind=SAFE_READ,
            method="GET",
            resource=f"companyinfo/{quote(realm_id, safe='')}",
        )
        info = company.get("CompanyInfo")
        if not isinstance(info, dict) or not str(info.get("Id", "")).strip():
            raise ProviderRuntimeError("QuickBooks CompanyInfo response did not identify the configured company.", category="response")
        if str(info.get("Id", "")).strip() != realm_id:
            raise ProviderRuntimeError("QuickBooks Realm ID does not match the connected CompanyInfo response.", category="preflight")

        self._query(context, token=token, mode=mode, realm_id=realm_id, stage="invoice_read", statement="SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS 1")
        if default_item_id:
            item = self._qbo_request(
                context,
                token=token,
                mode=mode,
                realm_id=realm_id,
                stage="default_item_read",
                operation_kind=SAFE_READ,
                method="GET",
                resource=f"item/{quote(default_item_id, safe='')}",
            ).get("Item")
            if not isinstance(item, dict) or str(item.get("Id", "")).strip() != default_item_id:
                raise ProviderRuntimeError("Configured QuickBooks Default Item ID could not be verified.", category="preflight")
            if item.get("Active") is False:
                raise ProviderRuntimeError("Configured QuickBooks Default Item ID is inactive.", category="preflight")
        return f"QuickBooks Online {mode} API connection verified."

    def validate_task(self, context):
        t = context.template
        issues: list[ExternalValidationIssue] = []
        if str(t.invoice_type).strip().upper() != "INVOICE":
            issues.append(ExternalValidationIssue("qbo_invoice_type", "QuickBooks Online provider supports Invoice tasks only.", "Use Invoice Type INVOICE."))
        if str(t.invoice_title).strip() not in {"", "Invoice"}:
            issues.append(ExternalValidationIssue("qbo_invoice_title", "QuickBooks Online adapter does not map a custom Invio invoice title.", "Use the default Invoice title."))
        if str(t.invoice_subtitle).strip():
            issues.append(ExternalValidationIssue("qbo_invoice_subtitle", "QuickBooks Online adapter does not map Invoice Subtitle.", "Leave Invoice Subtitle blank."))
        if bool(t.automatic_tax):
            issues.append(ExternalValidationIssue("qbo_automatic_tax", "QuickBooks Online tax behavior varies by company/region and cannot be inferred from Invio Automatic Tax.", "Disable Automatic Tax for this provider."))
        if str(t.footer).strip():
            issues.append(ExternalValidationIssue("qbo_footer", "QuickBooks Online adapter does not map Invio Footer.", "Leave Footer blank."))
        if str(t.customer_note).strip():
            issues.append(ExternalValidationIssue("qbo_customer_note", "QuickBooks Online adapter does not map Invio Customer Note separately.", "Leave Customer Note blank."))
        if t.terms:
            issues.append(ExternalValidationIssue("qbo_terms", "QuickBooks SalesTermRef requires an explicit provider term ID; Invio Terms are not guessed.", "Remove Terms for this QuickBooks Task."))
        if not t.items:
            issues.append(ExternalValidationIssue("qbo_items", "QuickBooks Online invoice requires at least one line item.", "Add an invoice item."))
        for index, item in enumerate(t.items, 1):
            if not str(item.description).strip():
                issues.append(ExternalValidationIssue("qbo_description", f"QuickBooks item {index} requires a description.", "Set a line-item description."))
            if Decimal(item.quantity) <= 0:
                issues.append(ExternalValidationIssue("qbo_quantity", f"QuickBooks item {index} quantity must be positive.", "Use quantity greater than zero."))
            if Decimal(item.unit_amount) < 0:
                issues.append(ExternalValidationIssue("qbo_unit_amount", f"QuickBooks item {index} unit amount cannot be negative.", "Use zero or positive unit amount."))
            if Decimal(item.tax_rate) != 0:
                issues.append(ExternalValidationIssue("qbo_line_tax", f"QuickBooks item {index} has an Invio line tax without an explicit QuickBooks TaxCodeRef.", "Set line tax to 0."))
        return tuple(issues)

    def execute_recipient(self, context):
        account = self._account_values(context.credentials, context.account_mode)
        token = self._access_token(account)
        mode, realm_id, default_item_id = account[3], account[4], account[5]

        customer_id = self._resolve_customer(context, token=token, mode=mode, realm_id=realm_id)
        item_ids = self._resolve_items(
            context, token=token, mode=mode, realm_id=realm_id, default_item_id=default_item_id
        )
        include_currency = self._validate_currency(context, token=token, mode=mode, realm_id=realm_id)

        today = date.today()
        due = today + timedelta(days=int(context.template.days_until_due))
        lines: list[dict[str, Any]] = []
        for invoice_item, item_id in zip(context.template.items, item_ids, strict=True):
            quantity = Decimal(invoice_item.quantity)
            unit_amount = Decimal(invoice_item.unit_amount)
            lines.append(
                {
                    "DetailType": "SalesItemLineDetail",
                    "Description": str(invoice_item.description).strip(),
                    "Amount": float(quantity * unit_amount),
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": item_id},
                        "Qty": float(quantity),
                        "UnitPrice": float(unit_amount),
                    },
                }
            )
        invoice: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "TxnDate": today.isoformat(),
            "DueDate": due.isoformat(),
            "BillEmail": {"Address": str(context.customer.email).strip()},
            "Line": lines,
        }
        if include_currency:
            invoice["CurrencyRef"] = {"value": str(context.template.currency).strip().upper()}
        memo = str(context.template.memo).strip()
        if memo:
            invoice["CustomerMemo"] = {"value": memo}

        invoice_key = self._request_id(context, "invoice-create")
        result = self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage="invoice_create",
            operation_kind=IDEMPOTENT_MUTATION,
            method="POST",
            resource="invoice",
            query={"requestid": invoice_key},
            json_data=invoice,
            idempotency_key=invoice_key,
        )
        created = result.get("Invoice")
        invoice_id = str(created.get("Id", "")).strip() if isinstance(created, dict) else ""
        if not invoice_id:
            raise ProviderRuntimeError("QuickBooks invoice creation succeeded without Invoice.Id.", category="response")
        context.log(f"QuickBooks Online invoice created (provider invoice {invoice_id}).")

        send_key = self._request_id(context, "invoice-send")
        sent = self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage="invoice_email_send",
            operation_kind=IDEMPOTENT_MUTATION,
            method="POST",
            resource=f"invoice/{quote(invoice_id, safe='')}/send",
            query={"sendTo": str(context.customer.email).strip(), "requestid": send_key},
            idempotency_key=send_key,
        )
        if not isinstance(sent.get("Invoice"), dict):
            raise ProviderRuntimeError("QuickBooks invoice send response did not contain the Invoice object.", category="response")
        context.log("QuickBooks Online accepted the invoice email send request.")
        return ExternalRecipientResult(
            provider_customer_id=customer_id,
            provider_invoice_id=invoice_id,
            final_stage="external_mutation:invoice_email_send",
        )

    @staticmethod
    def _account_values(credentials: dict[str, str], mode: str) -> tuple[str, str, str, str, str, str]:
        client_id = str(credentials.get("client_id", "")).strip()
        client_secret = str(credentials.get("client_secret", "")).strip()
        refresh_token = str(credentials.get("refresh_token", "")).strip()
        clean_mode = str(mode).strip()
        realm_id = str(credentials.get("realm_id", "")).strip()
        default_item_id = str(credentials.get("default_item_id", "")).strip()
        if clean_mode not in API_BASES:
            raise ProviderRuntimeError("QuickBooks account mode must be Sandbox or Production.", category="preflight")
        missing = [label for label, value in (
            ("OAuth Client ID", client_id),
            ("OAuth Client Secret", client_secret),
            ("OAuth Refresh Token", refresh_token),
            ("QuickBooks Realm ID", realm_id),
        ) if not value]
        if missing:
            raise ProviderRuntimeError("QuickBooks account is missing required field(s): " + ", ".join(missing) + ".", category="preflight")
        return client_id, client_secret, refresh_token, clean_mode, realm_id, default_item_id

    def _access_token(self, account: tuple[str, str, str, str, str, str]) -> str:
        client_id, client_secret, configured_refresh, mode, realm_id, _ = account
        source_hash = hashlib.sha256(configured_refresh.encode()).hexdigest()
        cache_id = hashlib.sha256(f"{PROVIDER_ID}\0{client_id}\0{mode}\0{realm_id}".encode()).hexdigest()[:40]
        now = time.monotonic()
        with self._lock:
            cached = self._access_cache.get(cache_id)
            if cached and cached[1] > now:
                return cached[0]

        refresh_token = configured_refresh
        store = CredentialStore()
        reference = store.credential_ref(f"oauth-cache-{PROVIDER_ID}-{cache_id}")
        try:
            persisted = store.get_credentials(reference)
        except CredentialStoreError as exc:
            raise ProviderRuntimeError("QuickBooks rotating OAuth refresh token cannot be read from protected OS storage.", category="storage") from exc
        if persisted and persisted.get("source_hash") == source_hash and persisted.get("refresh_token"):
            refresh_token = persisted["refresh_token"]

        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        response = self._direct_oauth_json(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            body=urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode(),
        )
        access_token = str(response.get("access_token", "")).strip()
        new_refresh = str(response.get("refresh_token", "")).strip()
        if not access_token or not new_refresh:
            raise ProviderRuntimeError("QuickBooks OAuth refresh response did not contain both access_token and refresh_token.", category="response")
        try:
            store.set_credentials(
                f"oauth-cache-{PROVIDER_ID}-{cache_id}",
                {"source_hash": source_hash, "refresh_token": new_refresh},
            )
        except CredentialStoreError as exc:
            raise ProviderRuntimeError("QuickBooks returned a refreshed token but it could not be saved to protected OS storage.", category="storage") from exc
        try:
            expires = int(response.get("expires_in", 3600))
        except (TypeError, ValueError):
            expires = 3600
        with self._lock:
            self._access_cache[cache_id] = (access_token, time.monotonic() + max(60, min(expires, 3600) - 120))
        return access_token

    @staticmethod
    def _direct_oauth_json(url: str, *, headers: dict[str, str], body: bytes) -> dict[str, Any]:
        req = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=30) as response:  # noqa: S310 - fixed official Intuit OAuth endpoint
                raw = response.read()
        except HTTPError as exc:
            raw = exc.read()
            try:
                data = json.loads(raw.decode()) if raw else {}
            except Exception:
                data = {}
            message = str(data.get("error_description") or data.get("error") or f"HTTP {exc.code}")
            raise ProviderRuntimeError(f"QuickBooks OAuth refresh failed: {message}", category="authentication", http_status=int(exc.code)) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderRuntimeError("QuickBooks OAuth refresh network request failed.", category="network", retryable=False) from exc
        try:
            data = json.loads(raw.decode())
        except Exception as exc:
            raise ProviderRuntimeError("QuickBooks OAuth refresh returned invalid JSON.", category="response") from exc
        if not isinstance(data, dict):
            raise ProviderRuntimeError("QuickBooks OAuth refresh returned an unexpected response.", category="response")
        return data

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": USER_AGENT}

    def _qbo_request(
        self,
        context,
        *,
        token: str,
        mode: str,
        realm_id: str,
        stage: str,
        operation_kind: str,
        method: str,
        resource: str,
        query: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        params: dict[str, Any] = dict(query or {})
        params.setdefault("minorversion", MINOR_VERSION)
        url = f"{API_BASES[mode]}/v3/company/{quote(realm_id, safe='')}/{resource.lstrip('/')}"
        if params:
            url += "?" + urlencode(params)
        result = context.request(
            stage=stage,
            operation_kind=operation_kind,
            method=method,
            url=url,
            headers=self._headers(token),
            json_data=json_data,
            idempotency_key=idempotency_key,
        )
        if not isinstance(result, dict):
            raise ProviderRuntimeError("QuickBooks Online API returned an unexpected response.", category="response")
        fault = result.get("Fault")
        if isinstance(fault, dict):
            errors = fault.get("Error")
            parts: list[str] = []
            if isinstance(errors, list):
                for item in errors:
                    if isinstance(item, dict):
                        parts.append(str(item.get("Detail") or item.get("Message") or item.get("code") or "").strip())
            raise ProviderRuntimeError("QuickBooks API error: " + ("; ".join(x for x in parts if x) or "unknown fault"), category="provider")
        return result

    def _query(self, context, *, token: str, mode: str, realm_id: str, stage: str, statement: str) -> dict[str, Any]:
        return self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage=stage,
            operation_kind=SAFE_READ,
            method="GET",
            resource="query",
            query={"query": statement},
        )

    def _resolve_customer(self, context, *, token: str, mode: str, realm_id: str) -> str:
        email = str(context.customer.email).strip().casefold()
        if bool(context.template.reuse_customer):
            start = 1
            matches: list[dict[str, Any]] = []
            while True:
                result = self._query(
                    context,
                    token=token,
                    mode=mode,
                    realm_id=realm_id,
                    stage=f"customer_lookup_{start}",
                    statement=f"SELECT * FROM Customer WHERE Active IN (true,false) STARTPOSITION {start} MAXRESULTS 1000",
                )
                response = result.get("QueryResponse")
                customers = response.get("Customer", []) if isinstance(response, dict) else []
                if isinstance(customers, dict):
                    customers = [customers]
                if not isinstance(customers, list):
                    customers = []
                for customer in customers:
                    if not isinstance(customer, dict):
                        continue
                    address = customer.get("PrimaryEmailAddr")
                    candidate = str(address.get("Address", "")).strip().casefold() if isinstance(address, dict) else ""
                    if candidate == email:
                        matches.append(customer)
                if len(customers) < 1000:
                    break
                start += 1000
            if len(matches) > 1:
                raise ProviderRuntimeError(f"Multiple QuickBooks customers use {email}; customer reuse is ambiguous.", category="preflight")
            if matches:
                customer_id = str(matches[0].get("Id", "")).strip()
                if not customer_id:
                    raise ProviderRuntimeError("QuickBooks reused customer is missing Id.", category="response")
                context.log(f"QuickBooks customer found for {email} (customer {customer_id}).")
                return customer_id

        key = self._request_id(context, "customer-create")
        result = self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage="customer_create",
            operation_kind=IDEMPOTENT_MUTATION,
            method="POST",
            resource="customer",
            query={"requestid": key},
            json_data={
                "DisplayName": str(context.customer.name).strip(),
                "PrimaryEmailAddr": {"Address": str(context.customer.email).strip()},
            },
            idempotency_key=key,
        )
        customer = result.get("Customer")
        customer_id = str(customer.get("Id", "")).strip() if isinstance(customer, dict) else ""
        if not customer_id:
            raise ProviderRuntimeError("QuickBooks customer creation succeeded without Customer.Id.", category="response")
        context.log(f"QuickBooks customer created for {email} (customer {customer_id}).")
        return customer_id

    def _resolve_items(self, context, *, token: str, mode: str, realm_id: str, default_item_id: str) -> list[str]:
        if default_item_id:
            item = self._qbo_request(
                context,
                token=token,
                mode=mode,
                realm_id=realm_id,
                stage="default_item_read",
                operation_kind=SAFE_READ,
                method="GET",
                resource=f"item/{quote(default_item_id, safe='')}",
            ).get("Item")
            if not isinstance(item, dict) or str(item.get("Id", "")).strip() != default_item_id or item.get("Active") is False:
                raise ProviderRuntimeError("Configured QuickBooks Default Item ID is missing or inactive.", category="preflight")
            return [default_item_id] * len(context.template.items)

        resolved: dict[str, str] = {}
        output: list[str] = []
        for invoice_item in context.template.items:
            name = str(invoice_item.description).strip()
            if name not in resolved:
                literal = self._qbo_literal(name)
                result = self._query(
                    context,
                    token=token,
                    mode=mode,
                    realm_id=realm_id,
                    stage=f"item_lookup_{hashlib.sha256(name.encode()).hexdigest()[:10]}",
                    statement=f"SELECT * FROM Item WHERE Name = '{literal}' AND Active = true STARTPOSITION 1 MAXRESULTS 1000",
                )
                response = result.get("QueryResponse")
                items = response.get("Item", []) if isinstance(response, dict) else []
                if isinstance(items, dict):
                    items = [items]
                exact = [item for item in items if isinstance(item, dict) and str(item.get("Name", "")).strip() == name and item.get("Active", True)] if isinstance(items, list) else []
                if len(exact) != 1:
                    raise ProviderRuntimeError(
                        f"QuickBooks Item mapping for '{name}' must resolve to exactly one active Item. Configure Default Item ID or create an exact matching Item.",
                        category="preflight",
                    )
                item_id = str(exact[0].get("Id", "")).strip()
                if not item_id:
                    raise ProviderRuntimeError("QuickBooks Item lookup returned an item without Id.", category="response")
                resolved[name] = item_id
            output.append(resolved[name])
        return output

    def _validate_currency(self, context, *, token: str, mode: str, realm_id: str) -> bool:
        result = self._qbo_request(
            context,
            token=token,
            mode=mode,
            realm_id=realm_id,
            stage="preferences_read",
            operation_kind=SAFE_READ,
            method="GET",
            resource="preferences",
        )
        prefs = result.get("Preferences")
        currency_prefs = prefs.get("CurrencyPrefs") if isinstance(prefs, dict) else None
        if not isinstance(currency_prefs, dict):
            raise ProviderRuntimeError("QuickBooks Preferences did not expose CurrencyPrefs; currency mapping cannot be verified.", category="preflight")
        home = currency_prefs.get("HomeCurrency")
        home_code = str(home.get("value", "")).strip().upper() if isinstance(home, dict) else ""
        if not home_code:
            raise ProviderRuntimeError("QuickBooks home currency could not be determined.", category="preflight")
        wanted = str(context.template.currency).strip().upper()
        if wanted == home_code:
            return False
        if not bool(currency_prefs.get("MultiCurrencyEnabled")):
            raise ProviderRuntimeError(
                f"QuickBooks company home currency is {home_code}, but template currency is {wanted} and MultiCurrency is disabled.",
                category="preflight",
            )
        return True

    @staticmethod
    def _qbo_literal(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def _request_id(context, stage: str) -> str:
        seed = f"{context.task_id}\0{str(context.customer.email).strip().casefold()}\0{stage}"
        return "invio-" + hashlib.sha256(seed.encode()).hexdigest()[:40]


def create_adapter():
    return Adapter()
