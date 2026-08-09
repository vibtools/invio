from __future__ import annotations

import base64
import copy
import hashlib
import json
import random
import socket
import ssl
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from http.client import IncompleteRead
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ...accounts.models import Account
from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceTemplate, STRIPE_ZERO_DECIMAL_CURRENCIES
from ...tasks.models import LEGACY_SNAPSHOT_MESSAGE, TASK_ASSIGNMENT_STRATEGY, TASK_SNAPSHOT_CAPTURED, Task
from ...tasks.state_machine import TaskExecutionMode, is_pristine_first_run
from ..state import AppState
from .adapters import provider_adapter_contract
from .preflight import canonical_refrens_base_url, preflight_runtime_inputs


RETRYABLE_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
PERMANENT_HTTP_STATUSES = frozenset({400, 401, 403, 404, 409, 422})
DEFAULT_CONNECT_TIMEOUT_SECONDS = 30.0
DEFAULT_READ_TIMEOUT_SECONDS = 30.0
MAX_TOTAL_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 0.5
RETRY_BACKOFF_CAP_SECONDS = 8.0
RETRY_JITTER_RATIO = 0.25


class ProviderRuntimeError(RuntimeError):
    """Provider/runtime failure with machine-readable P08 retry metadata."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "provider",
        retryable: bool = False,
        http_status: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = bool(retryable)
        self.http_status = http_status
        self.retry_after_seconds = retry_after_seconds


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


@dataclass(frozen=True, slots=True)
class TaskDeliverySummary:
    continuation_safe: bool
    failed_recipients: tuple[str, ...]
    pending_recipients: tuple[str, ...]
    processed: int
    success: int
    failed: int
    remaining: int

    @property
    def retry_failed_available(self) -> bool:
        return self.continuation_safe and bool(self.failed_recipients) and not self.pending_recipients

    @property
    def resume_remaining_available(self) -> bool:
        return self.continuation_safe and bool(self.failed_recipients or self.pending_recipients)


@dataclass(slots=True)
class _DeliveryState:
    failed_recipients: set[str] = field(default_factory=set)
    pending_recipients: set[str] = field(default_factory=set)
    continuation_safe: bool = False
    execution_mode: str = ""


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


def _parse_retry_after(value: str | None) -> float | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


def _network_runtime_error(exc: BaseException) -> ProviderRuntimeError:
    reason = exc.reason if isinstance(exc, URLError) else exc
    if isinstance(reason, ssl.SSLCertVerificationError):
        return ProviderRuntimeError(
            f"Provider TLS certificate verification failed: {reason}",
            category="tls",
            retryable=False,
        )
    if isinstance(reason, (ssl.SSLEOFError, ssl.SSLZeroReturnError)):
        return ProviderRuntimeError(
            f"Provider TLS connection ended before the request completed: {reason}",
            category="network",
            retryable=True,
        )
    if isinstance(reason, ssl.SSLError):
        return ProviderRuntimeError(
            f"Provider TLS connection failed: {reason}",
            category="tls",
            retryable=False,
        )
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return ProviderRuntimeError(
            f"Provider network request timed out: {reason}",
            category="timeout",
            retryable=True,
        )
    if isinstance(reason, IncompleteRead):
        return ProviderRuntimeError(
            "Provider network response ended before the complete response body was received.",
            category="network",
            retryable=True,
        )
    retryable_disconnect = isinstance(
        reason,
        (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, ConnectionError),
    )
    return ProviderRuntimeError(
        f"Provider network request failed: {reason}",
        category="network",
        retryable=retryable_disconnect or isinstance(exc, URLError),
    )


def _stdlib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> dict[str, Any]:
    request = Request(url, data=body, headers=headers, method=method.upper())
    try:
        # urllib exposes one socket timeout value; P08 deliberately uses the
        # same explicit bound for connection establishment and response reads.
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS provider endpoints / trusted Refrens endpoint
            raw = response.read()
    except HTTPError as exc:
        try:
            raw = exc.read()
        except IncompleteRead as read_exc:
            raw = bytes(read_exc.partial or b"")
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            data = {"raw": raw.decode("utf-8", errors="replace")[:1000]}
        status = int(exc.code)
        message = _extract_api_error(data) or f"Provider API returned HTTP {status}."
        retryable = status in RETRYABLE_HTTP_STATUSES
        response_headers = exc.headers or {}
        raise ProviderRuntimeError(
            message,
            category="rate-limit" if status == 429 else "http",
            retryable=retryable,
            http_status=status,
            retry_after_seconds=_parse_retry_after(response_headers.get("Retry-After")) if retryable else None,
        ) from exc
    except (URLError, TimeoutError, OSError, IncompleteRead) as exc:
        raise _network_runtime_error(exc) from exc

    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderRuntimeError(
            "Provider API returned an invalid JSON response.",
            category="response",
            retryable=False,
        ) from exc
    if not isinstance(data, dict):
        raise ProviderRuntimeError(
            "Provider API returned an unexpected response format.",
            category="response",
            retryable=False,
        )
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


def _cooperative_retry_wait(context: Any, delay_seconds: float) -> bool:
    remaining = max(0.0, float(delay_seconds))
    while remaining > 0:
        if context.stop_flag.is_set():
            return False
        if not context.pause_gate.is_set() and not _wait_for_resume(context):
            return False
        step = min(0.1, remaining)
        started = time.monotonic()
        if context.stop_flag.wait(step):
            return False
        if context.pause_gate.is_set():
            remaining = max(0.0, remaining - (time.monotonic() - started))
    return not context.stop_flag.is_set()


class ProviderRuntime:
    """Built-in execution adapters for packaged invoice providers.

    Each call to ``make_task_runner`` snapshots the selected accounts, template,
    and provider-neutral customer records on the GUI thread. The returned runner performs network
    work only inside the task-owned worker thread created by ``WorkerManager``.
    """

    STRIPE_BASE_URL = "https://api.stripe.com/v1"

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        timeout: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        retry_jitter_source: Callable[[], float] | None = None,
    ) -> None:
        self._transport = transport or _stdlib_transport
        # urllib has one socket timeout; keep connect/read policy equal and explicit.
        self.connect_timeout = max(1.0, float(timeout))
        self.read_timeout = max(1.0, float(timeout))
        self.timeout = max(self.connect_timeout, self.read_timeout)
        self._retry_jitter_source = retry_jitter_source or random.random
        self._state_lock = threading.Lock()
        self._delivery_state: dict[str, _DeliveryState] = {}

    def clear_task(self, task_id: str) -> None:
        with self._state_lock:
            self._delivery_state.pop(task_id, None)

    @staticmethod
    def supports_api_test(provider_id: str) -> bool:
        """Return whether the registered provider adapter exposes a verified API-test handler."""
        adapter = provider_adapter_contract(provider_id)
        return bool(adapter is not None and adapter.supports_api_test)

    def test_account(self, provider_id: str, credentials: dict[str, str], *, mode: str = "") -> str:
        adapter = provider_adapter_contract(provider_id)
        if adapter is None or not adapter.supports_api_test or adapter.api_test_handler is None:
            if adapter is not None and adapter.api_test_unavailable_message:
                raise ProviderRuntimeError(adapter.api_test_unavailable_message)
            raise ProviderRuntimeError("No built-in API-test adapter is available for this provider.")
        handler = getattr(self, adapter.api_test_handler, None)
        if not callable(handler):
            raise ProviderRuntimeError(
                f"The registered API-test handler for provider '{adapter.provider_id}' is unavailable."
            )
        return handler(credentials, mode=mode)

    def _test_stripe_account(self, credentials: dict[str, str], *, mode: str = "") -> str:
        key = credentials.get("secret_key", "").strip()
        self._validate_stripe_key(key)
        if mode.strip():
            self._validate_stripe_mode_value(mode, key)
        self._stripe_request("GET", "/customers", key, query={"limit": 1})
        self._stripe_request("GET", "/invoices", key, query={"limit": 1})
        return "Stripe API connection verified."

    def _test_refrens_account(self, credentials: dict[str, str], *, mode: str = "") -> str:
        del mode
        token, base_url, url_key = self._refrens_auth(credentials)
        self._refrens_request(
            "GET",
            base_url,
            f"/businesses/{url_key}/invoices",
            token=token,
            query={"$limit": 1, "$skip": 0, "$sort[createdAt]": -1},
        )
        return "Refrens API connection verified."

    def delivery_summary(self, task: Task) -> TaskDeliverySummary | None:
        execution = task.execution_snapshot
        if execution is None or execution.state != TASK_SNAPSHOT_CAPTURED:
            return None
        order = tuple(customer.email for customer in execution.customers)
        known = set(order)
        with self._state_lock:
            state = self._delivery_state.get(task.id)
            if state is None:
                return None
            failed_set = set(state.failed_recipients)
            pending_set = set(state.pending_recipients)
            safe = bool(state.continuation_safe)

        safe = safe and failed_set.isdisjoint(pending_set)
        safe = safe and failed_set.issubset(known) and pending_set.issubset(known)
        ordered_failed = tuple(email for email in order if email in failed_set)
        ordered_pending = tuple(email for email in order if email in pending_set)
        if not safe:
            return TaskDeliverySummary(
                continuation_safe=False,
                failed_recipients=ordered_failed,
                pending_recipients=ordered_pending,
                processed=task.processed,
                success=task.success,
                failed=task.failed,
                remaining=task.remaining,
            )

        processed = task.total - len(ordered_pending)
        failed = len(ordered_failed)
        success = processed - failed
        if processed < 0 or success < 0 or processed > task.total:
            return TaskDeliverySummary(
                continuation_safe=False,
                failed_recipients=ordered_failed,
                pending_recipients=ordered_pending,
                processed=task.processed,
                success=task.success,
                failed=task.failed,
                remaining=task.remaining,
            )
        return TaskDeliverySummary(
            continuation_safe=True,
            failed_recipients=ordered_failed,
            pending_recipients=ordered_pending,
            processed=processed,
            success=success,
            failed=failed,
            remaining=len(ordered_pending),
        )

    def make_task_runner(
        self,
        task: Task,
        state: AppState,
        *,
        retry_failed: bool = False,
        resume_remaining: bool = False,
    ) -> Callable[[Any], None]:
        if retry_failed and resume_remaining:
            raise ProviderRuntimeError("Retry Failed and Resume Remaining cannot be requested together.")
        snapshot = self._snapshot(task, state)
        adapter = provider_adapter_contract(snapshot.provider_id)
        if adapter is None:
            raise ProviderRuntimeError("No built-in task runner is available for this provider.")
        if not adapter.supports_task_execution or adapter.task_batch_handler is None:
            message = adapter.task_unavailable_message or adapter.profile.task_unavailable_message
            raise ProviderRuntimeError(message or "No built-in task runner is available for this provider.")
        batch_handler = getattr(self, adapter.task_batch_handler, None)
        if not callable(batch_handler):
            raise ProviderRuntimeError(
                f"The registered Task handler for provider '{adapter.provider_id}' is unavailable."
            )

        runtime_preflight = preflight_runtime_inputs(
            provider_id=snapshot.provider_id,
            template=snapshot.template,
            customers=(CustomerRecord(customer.email, customer.name, customer.country) for customer in snapshot.customers),
        )
        if not runtime_preflight.passed:
            raise ProviderRuntimeError(runtime_preflight.message)

        with self._state_lock:
            if retry_failed:
                if task.status != "Failed":
                    raise ProviderRuntimeError("Retry Failed is only available for a Failed Task.")
                delivery = self._delivery_state.get(task.id)
                if delivery is None or not delivery.continuation_safe:
                    raise ProviderRuntimeError(
                        "The exact failed recipient set is not available in this application session."
                    )
                if delivery.pending_recipients:
                    raise ProviderRuntimeError(
                        "Retry Failed is unavailable while unattempted recipients remain. Use Resume Remaining."
                    )
                recipients = tuple(
                    email for email in snapshot.customer_emails if email in delivery.failed_recipients
                )
                if not recipients:
                    raise ProviderRuntimeError("This task has no failed recipients to retry.")
                delivery.execution_mode = TaskExecutionMode.RETRY_FAILED.value
                mode = TaskExecutionMode.RETRY_FAILED
            elif resume_remaining:
                if task.status != "Stopped":
                    raise ProviderRuntimeError("Resume Remaining is only available for a Stopped Task.")
                delivery = self._delivery_state.get(task.id)
                if delivery is None or not delivery.continuation_safe:
                    raise ProviderRuntimeError(
                        "The exact continuation recipient set is not available in this application session."
                    )
                eligible = delivery.failed_recipients | delivery.pending_recipients
                recipients = tuple(email for email in snapshot.customer_emails if email in eligible)
                if not recipients:
                    raise ProviderRuntimeError("This task has no remaining recipients to resume.")
                delivery.execution_mode = TaskExecutionMode.RESUME_REMAINING.value
                mode = TaskExecutionMode.RESUME_REMAINING
            else:
                if task.status != "Ready" or not is_pristine_first_run(task):
                    raise ProviderRuntimeError(
                        "A full Start is only available for a pristine Ready Task. Create a new Task for another full execution."
                    )
                existing = self._delivery_state.get(task.id)
                if existing is not None and existing.execution_mode:
                    raise ProviderRuntimeError(
                        "This Task already has a current-session execution state; a duplicate full Start is not allowed."
                    )
                recipients = snapshot.customer_emails
                self._delivery_state[task.id] = _DeliveryState(
                    failed_recipients=set(),
                    pending_recipients=set(recipients),
                    continuation_safe=True,
                    execution_mode=TaskExecutionMode.FIRST_RUN.value,
                )
                mode = TaskExecutionMode.FIRST_RUN

        return lambda context: batch_handler(context, snapshot, recipients, execution_mode=mode)

    @staticmethod
    def _snapshot(task: Task, state: AppState) -> TaskSnapshot:
        execution = task.execution_snapshot
        if execution is None or execution.state != TASK_SNAPSHOT_CAPTURED:
            raise ProviderRuntimeError(LEGACY_SNAPSHOT_MESSAGE)
        if execution.provider_id != task.provider_id:
            raise ProviderRuntimeError("The immutable task snapshot provider no longer matches the task provider.")
        if execution.assignment_strategy != TASK_ASSIGNMENT_STRATEGY:
            raise ProviderRuntimeError("The immutable task snapshot uses an unsupported account-assignment strategy.")
        if execution.account_ids != tuple(task.account_ids):
            raise ProviderRuntimeError("The immutable task snapshot account order no longer matches the task account binding.")
        if execution.template is None:
            raise ProviderRuntimeError("The immutable task snapshot has no invoice template.")
        if execution.template.id != task.invoice_template_id:
            raise ProviderRuntimeError("The immutable task snapshot template no longer matches the task template binding.")
        if task.total != len(execution.customers):
            raise ProviderRuntimeError("The task total no longer matches its immutable recipient snapshot.")
        if not execution.customers:
            raise ProviderRuntimeError("The immutable task snapshot has no recipients.")

        accounts: list[AccountSnapshot] = []
        for account_id in execution.account_ids:
            account: Account | None = state.accounts.get(account_id)
            if account is None:
                raise ProviderRuntimeError("A provider account assigned to this task no longer exists.")
            if account.provider_id != execution.provider_id:
                raise ProviderRuntimeError("A task account no longer matches the immutable task provider.")
            accounts.append(AccountSnapshot(account.id, account.name, account.mode, dict(account.credentials)))
        if not accounts:
            raise ProviderRuntimeError("The task has no provider account assigned.")

        return TaskSnapshot(
            task_id=task.id,
            task_name=task.name,
            provider_id=execution.provider_id,
            accounts=tuple(accounts),
            customer_emails=None,
            template=execution.template.to_template(),
            customers=tuple(CustomerSnapshot.from_record(customer) for customer in execution.customers),
        )

    def _retry_delay_seconds(self, retry_number: int, exc: ProviderRuntimeError) -> float:
        exponent = max(0, retry_number - 1)
        base = min(RETRY_BACKOFF_CAP_SECONDS, RETRY_BASE_DELAY_SECONDS * (2**exponent))
        jitter = base * RETRY_JITTER_RATIO * max(0.0, min(1.0, float(self._retry_jitter_source())))
        computed = base + jitter
        if exc.retry_after_seconds is not None:
            computed = max(computed, max(0.0, float(exc.retry_after_seconds)))
        return computed

    def _send_stripe_invoice_with_retry(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        account: AccountSnapshot,
        email: str,
    ) -> dict[str, Any]:
        attempt = 1
        while True:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                raise ProviderRuntimeError("Stripe recipient execution stopped before the next attempt.", category="stopped")
            try:
                return self._send_stripe_invoice(snapshot, account, email)
            except ProviderRuntimeError as exc:
                if not exc.retryable or attempt >= MAX_TOTAL_ATTEMPTS:
                    raise
                retry_number = attempt
                delay = self._retry_delay_seconds(retry_number, exc)
                context.log(
                    f"Stripe transient failure for {email} via account '{account.name}' "
                    f"(attempt {attempt}/{MAX_TOTAL_ATTEMPTS}): {exc}. "
                    f"Retrying in {delay:.2f}s."
                )
                if not _cooperative_retry_wait(context, delay):
                    raise ProviderRuntimeError(
                        "Stripe recipient retry stopped by user request.",
                        category="stopped",
                        retryable=False,
                    ) from exc
                attempt += 1

    def _run_stripe_batch(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        recipients: tuple[str, ...],
        *,
        execution_mode: TaskExecutionMode,
    ) -> None:
        full_index = {email: index for index, email in enumerate(snapshot.customer_emails)}
        attempted = 0
        label = {
            TaskExecutionMode.FIRST_RUN: "Stripe batch",
            TaskExecutionMode.RESUME_REMAINING: "Stripe continuation",
            TaskExecutionMode.RETRY_FAILED: "Stripe failed-recipient retry",
        }[execution_mode]
        context.log(
            f"{label} started with {len(recipients)} recipient(s) using template '{snapshot.template.name}'."
        )

        for email in recipients:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                break
            account = snapshot.accounts[full_index[email] % len(snapshot.accounts)]
            try:
                self._send_stripe_invoice_with_retry(context, snapshot, account, email)
            except ProviderRuntimeError as exc:
                if exc.category == "stopped" and context.stop_flag.is_set():
                    break
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.add(email)
                context.log(f"Stripe send failed for {email} via account '{account.name}': {exc}")
            except Exception as exc:
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.add(email)
                context.log(
                    f"Stripe send failed unexpectedly for {email} via account '{account.name}': "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError("The Task continuation state became unavailable during execution.")
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                context.log(f"Stripe invoice sent to {email} via account '{account.name}'.")

            attempted += 1
            summary = self.delivery_summary(context.task)
            if summary is None or not summary.continuation_safe:
                raise ProviderRuntimeError("The Task continuation state could not be reconciled safely.")
            if execution_mode is TaskExecutionMode.RETRY_FAILED:
                message = f"Retry processed {attempted}/{len(recipients)} failed recipient(s)."
            elif execution_mode is TaskExecutionMode.RESUME_REMAINING:
                message = f"Resume processed {attempted}/{len(recipients)} remaining recipient(s)."
            else:
                message = f"Processed {summary.processed}/{context.task.total} recipient(s)."
            context.progress(summary.processed, summary.success, summary.failed, message)

        if not context.stop_flag.is_set() and not context.pause_gate.is_set():
            _wait_for_resume(context)

        summary = self.delivery_summary(context.task)
        if summary is None or not summary.continuation_safe:
            raise ProviderRuntimeError("The Task continuation state could not be reconciled safely.")
        if context.stop_flag.is_set():
            context.log("Stripe batch stopped by user request.")
            return
        if summary.pending_recipients:
            with self._state_lock:
                delivery = self._delivery_state.get(snapshot.task_id)
                if delivery is not None:
                    delivery.continuation_safe = False
            raise ProviderRuntimeError("Task execution ended before all selected recipients were resolved safely.")
        if summary.failed_recipients:
            raise ProviderRuntimeError(
                f"{summary.failed} recipient(s) failed. Use Retry Failed after reviewing Live Logs."
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
            "User-Agent": "Invio/1.0.0.1.24 Vib-Tools",
        }
        body = None
        if method.upper() != "GET":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = _form_body(form or {})
        if idempotency:
            headers["Idempotency-Key"] = idempotency
        return self._transport(method.upper(), url, headers, body, self.timeout)

    def _refrens_auth(self, credentials: dict[str, str]) -> tuple[str, str, str]:
        raw_base_url = credentials.get("base_url", "").strip()
        url_key = credentials.get("url_key", "").strip()
        app_id = credentials.get("app_id", "").strip()
        app_secret = credentials.get("app_secret", "").strip()
        try:
            base_url = canonical_refrens_base_url(raw_base_url)
        except ValueError as exc:
            # Validate the destination before constructing the authentication
            # payload so App ID/App Secret are never sent to an untrusted host.
            raise ProviderRuntimeError(str(exc)) from exc
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
        headers = {"Accept": "application/json", "User-Agent": "Invio/1.0.0.1.24 Vib-Tools"}
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
