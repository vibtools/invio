from __future__ import annotations

import base64
import copy
import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ...accounts.models import Account
from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceTemplate, STRIPE_ZERO_DECIMAL_CURRENCIES
from ...tasks.models import Task
from ..state import AppState


class ProviderRuntimeError(RuntimeError):
    """Raised when a packaged provider cannot execute a requested operation."""


Transport = Callable[[str, str, dict[str, str], bytes | None, float], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    id: str
    name: str
    mode: str
    credentials: dict[str, str]


@dataclass(frozen=True, slots=True)
class CustomerSnapshot:
    email: str
    name: str = ""
    country: str = ""

    @classmethod
    def from_record(cls, record: CustomerRecord) -> "CustomerSnapshot":
        return cls(record.email, record.name, record.country)


@dataclass(frozen=True, slots=True, init=False)
class TaskSnapshot:
    task_id: str
    task_name: str
    provider_id: str
    accounts: tuple[AccountSnapshot, ...]
    customers: tuple[CustomerSnapshot, ...]
    template: InvoiceTemplate

    def __init__(
        self,
        task_id: str,
        task_name: str,
        provider_id: str,
        accounts: tuple[AccountSnapshot, ...],
        customer_emails: tuple[str, ...] | None,
        template: InvoiceTemplate,
        *,
        customers: tuple[CustomerSnapshot, ...] | None = None,
    ) -> None:
        if customers is not None and customer_emails is not None:
            raise ValueError("Provide customers or customer_emails, not both.")
        resolved = customers
        if resolved is None:
            resolved = tuple(CustomerSnapshot(email=email) for email in (customer_emails or ()))
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "task_name", task_name)
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "accounts", accounts)
        object.__setattr__(self, "customers", tuple(resolved))
        object.__setattr__(self, "template", template)

    @property
    def customer_emails(self) -> tuple[str, ...]:
        """Backward-compatible email view used by the unchanged Stripe engine."""
        return tuple(customer.email for customer in self.customers)


@dataclass(slots=True)
class _DeliveryState:
    failed_recipients: set[str] = field(default_factory=set)


def _extract_api_error(data: Any) -> str:
    if isinstance(data, dict):
        stripe_error = data.get("error")
        if isinstance(stripe_error, dict):
            message = stripe_error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        for key in ("message", "error", "name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested = data.get("data")
        if isinstance(nested, dict):
            message = nested.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
    return ""


def _stdlib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> dict[str, Any]:
    request = Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS provider endpoints / user-declared Refrens base URL
            raw = response.read()
    except HTTPError as exc:
        raw = exc.read()
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            data = {"raw": raw.decode("utf-8", errors="replace")[:1000]}
        message = _extract_api_error(data) or f"Provider API returned HTTP {exc.code}."
        raise ProviderRuntimeError(message) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ProviderRuntimeError(f"Provider network request failed: {exc}") from exc

    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderRuntimeError("Provider API returned an invalid JSON response.") from exc
    if not isinstance(data, dict):
        raise ProviderRuntimeError("Provider API returned an unexpected response format.")
    return data


def _form_body(values: dict[str, Any]) -> bytes:
    clean: list[tuple[str, str]] = []
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool):
            clean.append((key, "true" if value else "false"))
        else:
            clean.append((key, str(value)))
    return urlencode(clean).encode("utf-8")


def _json_body(values: dict[str, Any]) -> bytes:
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _idempotency_key(task_id: str, email: str, stage: str) -> str:
    digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:20]
    return f"invio:{task_id}:{digest}:{stage}"[:255]


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _stripe_minor_decimal(major: Decimal, currency: str) -> Decimal:
    code = currency.upper()
    if code in STRIPE_ZERO_DECIMAL_CURRENCIES:
        return major
    # ISK and UGX intentionally stay in the two-decimal branch because Stripe
    # requires backward-compatible x100 API values for those currencies.
    return major * Decimal("100")


def _wait_for_resume(context: Any) -> bool:
    while not context.pause_gate.wait(timeout=0.2):
        if context.stop_flag.is_set():
            return False
    return not context.stop_flag.is_set()


class ProviderRuntime:
    """Built-in execution adapters for packaged invoice providers.

    Each call to ``make_task_runner`` snapshots the selected accounts, template,
    and provider-neutral customer records on the GUI thread. The returned runner performs network
    work only inside the task-owned worker thread created by ``WorkerManager``.
    """

    STRIPE_BASE_URL = "https://api.stripe.com/v1"

    def __init__(self, *, transport: Transport | None = None, timeout: float = 30.0) -> None:
        self._transport = transport or _stdlib_transport
        self.timeout = max(1.0, float(timeout))
        self._state_lock = threading.Lock()
        self._delivery_state: dict[str, _DeliveryState] = {}

    def clear_task(self, task_id: str) -> None:
        with self._state_lock:
            self._delivery_state.pop(task_id, None)

    @staticmethod
    def supports_api_test(provider_id: str) -> bool:
        """Return whether Invio has an executable built-in API-test adapter."""
        return provider_id.strip().lower() in {"stripe", "refrens"}

    def test_account(self, provider_id: str, credentials: dict[str, str], *, mode: str = "") -> str:
        provider_id = provider_id.strip().lower()
        if provider_id == "stripe":
            key = credentials.get("secret_key", "").strip()
            self._validate_stripe_key(key)
            if mode.strip():
                self._validate_stripe_mode_value(mode, key)
            self._stripe_request("GET", "/customers", key, query={"limit": 1})
            self._stripe_request("GET", "/invoices", key, query={"limit": 1})
            return "Stripe API connection verified."
        if provider_id == "refrens":
            token, base_url, url_key = self._refrens_auth(credentials)
            self._refrens_request(
                "GET",
                base_url,
                f"/businesses/{url_key}/invoices",
                token=token,
                query={"$limit": 1, "$skip": 0, "$sort[createdAt]": -1},
            )
            return "Refrens API connection verified."
        raise ProviderRuntimeError("No built-in API-test adapter is available for this provider.")

    def make_task_runner(self, task: Task, state: AppState, *, retry_failed: bool = False) -> Callable[[Any], None]:
        snapshot = self._snapshot(task, state)
        if snapshot.provider_id == "refrens":
            # P04 stores explicit provider-neutral customer name/country data, but
            # the approved Refrens production Task runner remains a later P11
            # phase. Keep this fail-closed gate until that pipeline is approved.
            raise ProviderRuntimeError(
                "Refrens customer name/country data can be stored explicitly, but the Refrens production Task runner "
                "is not enabled until the approved P11 pipeline is implemented. No Refrens invoice was created or sent."
            )
        if snapshot.provider_id != "stripe":
            raise ProviderRuntimeError("No built-in task runner is available for this provider.")

        with self._state_lock:
            delivery = self._delivery_state.setdefault(task.id, _DeliveryState())
            if retry_failed:
                recipients = tuple(email for email in snapshot.customer_emails if email in delivery.failed_recipients)
                if not recipients:
                    raise ProviderRuntimeError("This task has no failed recipients to retry.")
            else:
                delivery.failed_recipients.clear()
                recipients = snapshot.customer_emails

        return lambda context: self._run_stripe_batch(context, snapshot, recipients, retry_failed=retry_failed)

    @staticmethod
    def _snapshot(task: Task, state: AppState) -> TaskSnapshot:
        template = state.invoice_templates.get(task.invoice_template_id)
        if template is None:
            raise ProviderRuntimeError("The invoice template assigned to this task no longer exists.")
        customer_list = state.customer_lists.get(task.customer_list_id)
        if customer_list is None or not customer_list.customers:
            raise ProviderRuntimeError("The customer list assigned to this task has no customers.")

        accounts: list[AccountSnapshot] = []
        for account_id in task.account_ids:
            account: Account | None = state.accounts.get(account_id)
            if account is None:
                raise ProviderRuntimeError("A provider account assigned to this task no longer exists.")
            if account.provider_id != task.provider_id:
                raise ProviderRuntimeError("A task account no longer matches the task provider.")
            accounts.append(AccountSnapshot(account.id, account.name, account.mode, dict(account.credentials)))
        if not accounts:
            raise ProviderRuntimeError("The task has no provider account assigned.")

        return TaskSnapshot(
            task_id=task.id,
            task_name=task.name,
            provider_id=task.provider_id,
            accounts=tuple(accounts),
            customer_emails=None,
            template=copy.deepcopy(template),
            customers=tuple(CustomerSnapshot.from_record(customer) for customer in customer_list.customers),
        )

    def _run_stripe_batch(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        recipients: tuple[str, ...],
        *,
        retry_failed: bool,
    ) -> None:
        full_index = {email: index for index, email in enumerate(snapshot.customer_emails)}
        base_success = context.task.success if retry_failed else 0
        original_retry_set = set(recipients) if retry_failed else set()
        attempted: set[str] = set()
        new_failed: set[str] = set()
        new_success = 0

        context.log(
            f"Stripe batch started with {len(recipients)} recipient(s) using template '{snapshot.template.name}'."
        )
        for email in recipients:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                break
            account = snapshot.accounts[full_index[email] % len(snapshot.accounts)]
            attempted.add(email)
            try:
                self._send_stripe_invoice(snapshot, account, email)
                new_success += 1
                context.log(f"Stripe invoice sent to {email} via account '{account.name}'.")
            except ProviderRuntimeError as exc:
                new_failed.add(email)
                context.log(f"Stripe send failed for {email} via account '{account.name}': {exc}")

            if retry_failed:
                unresolved = original_retry_set - attempted
                success_count = base_success + new_success
                failed_count = len(unresolved) + len(new_failed)
                processed = context.task.total
                message = f"Retry processed {len(attempted)}/{len(recipients)} failed recipient(s)."
            else:
                success_count = new_success
                failed_count = len(new_failed)
                processed = len(attempted)
                message = f"Processed {processed}/{context.task.total} recipient(s)."
            context.progress(processed, success_count, failed_count, message)

        if retry_failed:
            remaining_failed = (original_retry_set - attempted) | new_failed
        else:
            remaining_failed = new_failed | (set(recipients) - attempted if context.stop_flag.is_set() else set())
        with self._state_lock:
            self._delivery_state.setdefault(snapshot.task_id, _DeliveryState()).failed_recipients = set(remaining_failed)

        if context.stop_flag.is_set():
            context.log("Stripe batch stopped by user request.")
            return
        if remaining_failed:
            raise ProviderRuntimeError(
                f"{len(remaining_failed)} recipient(s) failed. Use Retry Failed after reviewing Live Logs."
            )
        context.log("Stripe batch completed successfully.")

    @staticmethod
    def _validate_stripe_key(secret_key: str) -> None:
        key = secret_key.strip()
        if not key.startswith(("sk_test_", "sk_live_", "rk_test_", "rk_live_")):
            raise ProviderRuntimeError("Stripe secret/restricted key format is invalid.")

    @staticmethod
    def _validate_stripe_mode_value(mode: str, secret_key: str) -> None:
        normalized = mode.strip().lower()
        if normalized == "test" and "_test_" not in secret_key:
            raise ProviderRuntimeError("Stripe account mode is Test but the configured key is not a test key.")
        if normalized == "live" and "_live_" not in secret_key:
            raise ProviderRuntimeError("Stripe account mode is Live but the configured key is not a live key.")

    @staticmethod
    def _validate_stripe_mode(account: AccountSnapshot, secret_key: str) -> None:
        ProviderRuntime._validate_stripe_mode_value(account.mode, secret_key)

    def _send_stripe_invoice(self, snapshot: TaskSnapshot, account: AccountSnapshot, email: str) -> dict[str, Any]:
        key = account.credentials.get("secret_key", "").strip()
        self._validate_stripe_key(key)
        self._validate_stripe_mode(account, key)
        template = snapshot.template
        currency = template.currency.upper()

        customer_id = ""
        if template.reuse_customer:
            found = self._stripe_request("GET", "/customers", key, query={"email": email, "limit": 1})
            data = found.get("data")
            if isinstance(data, list) and data and isinstance(data[0], dict):
                customer_id = str(data[0].get("id", "")).strip()
        if not customer_id:
            created_customer = self._stripe_request(
                "POST",
                "/customers",
                key,
                form={"email": email},
                idempotency=_idempotency_key(snapshot.task_id, email, "customer"),
            )
            customer_id = str(created_customer.get("id", "")).strip()
        if not customer_id:
            raise ProviderRuntimeError("Stripe customer response did not contain an id.")

        memo_parts = []
        if template.invoice_title.strip() and template.invoice_title.strip().casefold() != "invoice":
            memo_parts.append(template.invoice_title.strip())
        if template.invoice_subtitle.strip():
            memo_parts.append(template.invoice_subtitle.strip())
        if template.memo.strip():
            memo_parts.append(template.memo.strip())
        footer_parts = [part for part in (template.footer.strip(), template.customer_note.strip()) if part]
        if template.terms:
            footer_parts.append("Terms: " + " | ".join(template.terms))

        invoice_form: dict[str, Any] = {
            "customer": customer_id,
            "collection_method": "send_invoice",
            "days_until_due": template.days_until_due,
            "auto_advance": False,
            "currency": currency.lower(),
            "pending_invoice_items_behavior": "exclude",
        }
        if memo_parts:
            invoice_form["description"] = "\n".join(memo_parts)
        if footer_parts:
            invoice_form["footer"] = "\n".join(footer_parts)
        if template.automatic_tax:
            invoice_form["automatic_tax[enabled]"] = True

        invoice = self._stripe_request(
            "POST",
            "/invoices",
            key,
            form=invoice_form,
            idempotency=_idempotency_key(snapshot.task_id, email, "invoice"),
        )
        invoice_id = str(invoice.get("id", "")).strip()
        if not invoice_id:
            raise ProviderRuntimeError("Stripe invoice response did not contain an id.")

        for index, item in enumerate(template.items):
            quantity = item.quantity
            description = item.description
            unit_minor = _stripe_minor_decimal(item.unit_amount, currency)
            item_form: dict[str, Any] = {
                "customer": customer_id,
                "invoice": invoice_id,
                "currency": currency.lower(),
                "description": description,
                "unit_amount_decimal": _decimal_text(unit_minor),
            }
            if quantity == quantity.to_integral_value():
                item_form["quantity"] = int(quantity)
            else:
                # Stripe supports decimal invoice-item quantities directly.
                item_form["quantity_decimal"] = _decimal_text(quantity)
            if template.automatic_tax:
                item_form["tax_behavior"] = "exclusive"
            self._stripe_request(
                "POST",
                "/invoiceitems",
                key,
                form=item_form,
                idempotency=_idempotency_key(snapshot.task_id, email, f"item-{index}"),
            )

        finalized = self._stripe_request(
            "POST",
            f"/invoices/{invoice_id}/finalize",
            key,
            form={"auto_advance": False},
            idempotency=_idempotency_key(snapshot.task_id, email, "finalize"),
        )
        finalized_id = str(finalized.get("id", invoice_id)).strip() or invoice_id
        sent = self._stripe_request(
            "POST",
            f"/invoices/{finalized_id}/send",
            key,
            form={},
            idempotency=_idempotency_key(snapshot.task_id, email, "send"),
        )
        return sent

    def _stripe_request(
        self,
        method: str,
        path: str,
        secret_key: str,
        *,
        form: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        idempotency: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.STRIPE_BASE_URL}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("ascii")
        headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "Invio/1.0.0.1.14 Vib-Tools",
        }
        body = None
        if method.upper() != "GET":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = _form_body(form or {})
        if idempotency:
            headers["Idempotency-Key"] = idempotency
        return self._transport(method.upper(), url, headers, body, self.timeout)

    def _refrens_auth(self, credentials: dict[str, str]) -> tuple[str, str, str]:
        base_url = credentials.get("base_url", "").strip().rstrip("/")
        url_key = credentials.get("url_key", "").strip()
        app_id = credentials.get("app_id", "").strip()
        app_secret = credentials.get("app_secret", "").strip()
        if not base_url.startswith("https://"):
            raise ProviderRuntimeError("Refrens API Base URL must use HTTPS.")
        if not all((url_key, app_id, app_secret)):
            raise ProviderRuntimeError("Refrens URL Key, App ID and App Secret are required.")
        payload = {"strategy": "app-secret", "appId": app_id, "appSecret": app_secret}
        response = self._refrens_request("POST", base_url, "/authentication", json_data=payload, token=None)
        token = str(response.get("accessToken", "")).strip()
        if not token:
            raise ProviderRuntimeError("Refrens authentication response did not contain accessToken.")
        return token, base_url, url_key

    def _refrens_request(
        self,
        method: str,
        base_url: str,
        path: str,
        *,
        token: str | None,
        json_data: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        headers = {"Accept": "application/json", "User-Agent": "Invio/1.0.0.1.14 Vib-Tools"}
        body = None
        if json_data is not None:
            headers["Content-Type"] = "application/json"
            body = _json_body(json_data)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._transport(method.upper(), url, headers, body, self.timeout)

    def build_refrens_invoice_payload(
        self,
        template: InvoiceTemplate,
        *,
        customer_email: str,
        customer_country: str,
        customer_name: str = "",
    ) -> dict[str, Any]:
        """Build a documented Refrens payload when required customer data exists.

        P04 Customer Lists can provide explicit ``customer_country`` and optional
        name data. This helper remains contract-testable while the production
        Refrens Task runner itself stays disabled until P11.
        """
        country = customer_country.strip().upper()
        if len(country) != 2 or not country.isascii() or not country.isalpha():
            raise ProviderRuntimeError("Refrens customer country must be an ISO 3166-1 alpha-2 code.")
        email = customer_email.strip().lower()
        if not email:
            raise ProviderRuntimeError("Refrens customer email is required.")
        due_date = datetime.now(timezone.utc) + timedelta(days=template.days_until_due)
        terms = list(template.terms)
        if template.customer_note.strip():
            terms.append(template.customer_note.strip())
        if template.footer.strip():
            terms.append(template.footer.strip())
        payload: dict[str, Any] = {
            "invoiceTitle": template.invoice_title.strip() or "Invoice",
            "invoiceSubTitle": template.invoice_subtitle.strip(),
            "invoiceType": template.invoice_type if template.invoice_type in {"INVOICE", "BOS"} else "INVOICE",
            "currency": template.currency.upper(),
            "dueDate": due_date.isoformat(),
            "billedTo": {
                "name": customer_name.strip() or email,
                "country": country,
                "email": email,
            },
            "items": [
                {
                    "name": item.description,
                    "rate": float(item.unit_amount),
                    "quantity": float(item.quantity),
                    "taxRate": float(item.tax_rate),
                }
                for item in template.items
            ],
        }
        if template.memo.strip():
            payload["notes"] = template.memo.strip()
        if terms:
            payload["terms"] = terms
        return payload

    def create_and_send_refrens_invoice(
        self,
        credentials: dict[str, str],
        payload: dict[str, Any],
        *,
        customer_email: str,
        customer_name: str = "",
    ) -> dict[str, Any]:
        token, base_url, url_key = self._refrens_auth(credentials)
        request_payload = copy.deepcopy(payload)
        request_payload["email"] = {
            "to": {
                "email": customer_email.strip().lower(),
                "name": customer_name.strip() or customer_email.strip().lower(),
            }
        }
        created = self._refrens_request(
            "POST", base_url, f"/businesses/{url_key}/invoices", token=token, json_data=request_payload
        )
        invoice_id = str(created.get("_id", "")).strip()
        if not invoice_id:
            raise ProviderRuntimeError("Refrens invoice response did not contain _id; delivery cannot be confirmed.")
        return created
