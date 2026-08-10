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
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ...accounts.models import Account
from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceTemplate, STRIPE_ZERO_DECIMAL_CURRENCIES
from ...tasks.delivery_ledger import (
    DELIVERY_OPERATION_FAILED,
    DELIVERY_OPERATION_SUCCEEDED,
    DELIVERY_OPERATION_UNCERTAIN,
    DELIVERY_RESULT_FAILED,
    DELIVERY_RESULT_SUCCEEDED,
    DELIVERY_RESULT_UNCERTAIN,
    DELIVERY_RUN_COMPLETED,
    DELIVERY_RUN_FAILED,
    DELIVERY_RUN_STOPPED,
)
from ...tasks.models import LEGACY_SNAPSHOT_MESSAGE, TASK_ASSIGNMENT_STRATEGY, TASK_SNAPSHOT_CAPTURED, Task
from ...tasks.state_machine import TaskExecutionMode, is_pristine_first_run
from ..observability import redact_sensitive_text
from ..state import AppState
from ..storage import DomainStore, DomainStoreError
from .adapters import ProviderCapabilityProfile, ProviderSchedulingPolicy, provider_adapter_contract
from .external import (
    ADAPTER_STATUS_EXECUTABLE,
    EXTERNAL_OPERATION_KINDS,
    IDEMPOTENT_MUTATION,
    NON_IDEMPOTENT_MUTATION,
    SAFE_READ,
    ExternalAccountTestContext,
    ExternalAdapterError,
    ExternalAdapterRegistry,
    ExternalRecipientExecutionContext,
    ExternalRecipientResult,
    ExternalTaskValidationContext,
)
from .preflight import canonical_refrens_base_url, preflight_runtime_inputs


RETRYABLE_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
PERMANENT_HTTP_STATUSES = frozenset({400, 401, 403, 404, 409, 422})
DEFAULT_CONNECT_TIMEOUT_SECONDS = 30.0
DEFAULT_READ_TIMEOUT_SECONDS = 30.0
MAX_TOTAL_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 0.5
RETRY_BACKOFF_CAP_SECONDS = 8.0
RETRY_JITTER_RATIO = 0.25


def _context_log(context: Any, message: str, *, severity: str = "INFO", category: str = "PROVIDER") -> None:
    normalized = str(message).casefold()
    effective_severity = severity
    if severity == "INFO":
        if "failed" in normalized or "worker error" in normalized:
            effective_severity = "ERROR"
        elif any(token in normalized for token in ("retry", "cooldown", "stopped", "uncertain", "blocked")):
            effective_severity = "WARNING"
    structured = getattr(context, "structured_log", None)
    if callable(structured):
        structured(effective_severity, category, message)
    else:
        context.log(message)


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
        rate_limit_reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = bool(retryable)
        self.http_status = http_status
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit_reason = str(rate_limit_reason or "").strip().lower() or None


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
    uncertain_recipients: tuple[str, ...] = ()
    assigned_account_ids: tuple[tuple[str, str], ...] = ()

    @property
    def retry_failed_available(self) -> bool:
        return (
            self.continuation_safe
            and bool(self.failed_recipients)
            and not self.pending_recipients
            and not self.uncertain_recipients
        )

    @property
    def resume_remaining_available(self) -> bool:
        return self.continuation_safe and bool(
            self.failed_recipients or self.pending_recipients or self.uncertain_recipients
        )


@dataclass(slots=True)
class _DeliveryState:
    failed_recipients: set[str] = field(default_factory=set)
    pending_recipients: set[str] = field(default_factory=set)
    uncertain_recipients: set[str] = field(default_factory=set)
    attempted_recipients: set[str] = field(default_factory=set)
    attempted_account_ids: dict[str, str] = field(default_factory=dict)
    continuation_safe: bool = False
    execution_mode: str = ""


@dataclass(slots=True)
class _SchedulerHealthState:
    consecutive_incidents: int = 0
    cooldown_until: float = 0.0
    blocked_reason: str = ""
    last_reason: str = ""


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
            rate_limit_reason=response_headers.get("Stripe-Rate-Limited-Reason") if status == 429 else None,
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
        domain_store: DomainStore | None = None,
        project_root: Path | None = None,
    ) -> None:
        self._transport = transport or _stdlib_transport
        self._domain_store = domain_store
        # urllib has one socket timeout; keep connect/read policy equal and explicit.
        self.connect_timeout = max(1.0, float(timeout))
        self.read_timeout = max(1.0, float(timeout))
        self.timeout = max(self.connect_timeout, self.read_timeout)
        self._retry_jitter_source = retry_jitter_source or random.random
        self._state_lock = threading.Lock()
        self._delivery_state: dict[str, _DeliveryState] = {}
        self._scheduler_lock = threading.Lock()
        self._account_health: dict[tuple[str, str], _SchedulerHealthState] = {}
        self._provider_health: dict[str, _SchedulerHealthState] = {}
        self._account_next_request_at: dict[tuple[str, str], float] = {}
        self._external_registry = ExternalAdapterRegistry(project_root) if project_root is not None else None

    def clear_task(self, task_id: str) -> None:
        with self._state_lock:
            self._delivery_state.pop(task_id, None)

    def reset_account_health(self, account_id: str, *, provider_id: str | None = None) -> None:
        """Clear P09 runtime-only health after a successful account re-verification."""
        wanted_provider = provider_id.strip().lower() if provider_id else None
        with self._scheduler_lock:
            known_keys = set(self._account_health) | set(self._account_next_request_at)
            keys = [
                key
                for key in known_keys
                if key[1] == account_id and (wanted_provider is None or key[0] == wanted_provider)
            ]
            for key in keys:
                self._account_health.pop(key, None)
                self._account_next_request_at.pop(key, None)

    def reload_external_adapters(self) -> None:
        if self._external_registry is not None:
            self._external_registry.reload_installed()

    def validate_external_adapter(self, manifest, adapter_path: Path) -> None:
        ExternalAdapterRegistry.validate_adapter(manifest, adapter_path)

    def external_adapter_status(self, provider_id: str) -> tuple[str, str]:
        if self._external_registry is None:
            return "Manifest only", "External adapter discovery is unavailable in this runtime."
        status = self._external_registry.status(provider_id)
        return status.status, status.message

    def external_adapter(self, provider_id: str):
        return self._external_registry.adapter(provider_id) if self._external_registry is not None else None

    def capability_profile(self, provider_id: str) -> ProviderCapabilityProfile | None:
        built_in = provider_adapter_contract(provider_id)
        if built_in is not None:
            return built_in.profile
        external = self.external_adapter(provider_id)
        return external.profile if external is not None else None

    def runtime_capabilities(self, provider_id: str) -> tuple[str, ...]:
        profile = self.capability_profile(provider_id)
        if profile is None:
            return ()
        order = ("invoice", "send_invoice", "api_test")
        known = [value for value in order if value in profile.executable_capabilities]
        known.extend(sorted(value for value in profile.executable_capabilities if value not in order))
        return tuple(known)

    def external_task_validation_issues(
        self,
        provider_id: str,
        template: InvoiceTemplate,
        customers: tuple[CustomerRecord, ...] | list[CustomerRecord],
    ) -> tuple[object, ...]:
        adapter = self.external_adapter(provider_id)
        if adapter is None or not adapter.profile.task_execution_enabled:
            return ()
        context = ExternalTaskValidationContext(
            provider_id=provider_id.strip().lower(),
            template=copy.deepcopy(template),
            customers=tuple(customers),
        )
        try:
            return tuple(adapter.validate_task(context) or ())
        except BaseException as exc:
            return (
                type("ExternalValidationFailure", (), {
                    "code": "external-validation-error",
                    "message": f"External provider Task validation failed: {type(exc).__name__}: {exc}",
                    "correction": "Fix or replace the external adapter before executing this Task.",
                })(),
            )

    def supports_api_test(self, provider_id: str) -> bool:
        """Return whether a built-in or validated external adapter exposes API Test."""
        adapter = provider_adapter_contract(provider_id)
        if adapter is not None:
            return bool(adapter.supports_api_test)
        external = self.external_adapter(provider_id)
        return bool(external is not None and "api_test" in external.profile.executable_capabilities)

    def _external_api_test_request(
        self,
        *,
        provider_id: str,
        stage: str,
        operation_kind: str,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        json_data: dict[str, Any] | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        del provider_id, stage
        if operation_kind != SAFE_READ:
            raise ProviderRuntimeError(
                "External API Test may perform only SAFE_READ operations; side-effecting verification is blocked.",
                category="preflight",
                retryable=False,
            )
        if idempotency_key:
            raise ProviderRuntimeError("SAFE_READ API Test operation cannot declare an idempotency key.")
        if body is not None and json_data is not None:
            raise ProviderRuntimeError("External request cannot provide both body and json_data.")
        effective_headers = dict(headers or {})
        effective_body = body
        if json_data is not None:
            effective_headers.setdefault("Content-Type", "application/json")
            effective_body = _json_body(json_data)
        attempt = 1
        while True:
            try:
                return self._transport(method.upper(), url, effective_headers, effective_body, self.timeout)
            except ProviderRuntimeError as exc:
                if not exc.retryable or attempt >= MAX_TOTAL_ATTEMPTS:
                    raise
                time.sleep(self._retry_delay_seconds(attempt, exc))
                attempt += 1

    def test_account(self, provider_id: str, credentials: dict[str, str], *, mode: str = "") -> str:
        adapter = provider_adapter_contract(provider_id)
        if adapter is not None:
            if not adapter.supports_api_test or adapter.api_test_handler is None:
                if adapter.api_test_unavailable_message:
                    raise ProviderRuntimeError(adapter.api_test_unavailable_message)
                raise ProviderRuntimeError("No built-in API-test adapter is available for this provider.")
            handler = getattr(self, adapter.api_test_handler, None)
            if not callable(handler):
                raise ProviderRuntimeError(
                    f"The registered API-test handler for provider '{adapter.provider_id}' is unavailable."
                )
            return handler(credentials, mode=mode)

        external = self.external_adapter(provider_id)
        if external is None or "api_test" not in external.profile.executable_capabilities:
            raise ProviderRuntimeError("No built-in API-test adapter is available for this provider, and no validated external adapter is installed.")
        successful_safe_reads = [0]

        def api_test_request(**kwargs):
            result = self._external_api_test_request(provider_id=provider_id, **kwargs)
            successful_safe_reads[0] += 1
            return result

        context = ExternalAccountTestContext(
            provider_id=provider_id.strip().lower(),
            credentials=dict(credentials),
            mode=mode,
            request=api_test_request,
        )
        try:
            result = external.test_account(context)
        except ProviderRuntimeError:
            raise
        except BaseException as exc:
            raise ProviderRuntimeError(
                f"External provider API Test failed: {type(exc).__name__}: {exc}",
                category="provider",
                retryable=False,
            ) from exc
        if successful_safe_reads[0] < 1:
            raise ProviderRuntimeError(
                "External provider API Test did not complete a host-managed SAFE_READ request; "
                "account verification cannot be accepted.",
                category="preflight",
                retryable=False,
            )
        message = str(result).strip()
        return message or f"{provider_id} API connection verified."

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
        if self._domain_store is not None:
            try:
                durable = self._domain_store.delivery_summary(task)
            except DomainStoreError as exc:
                raise ProviderRuntimeError(
                    f"Durable delivery ledger could not be read: {exc}",
                    category="storage",
                    retryable=False,
                ) from exc
            if durable is not None:
                return TaskDeliverySummary(
                    continuation_safe=durable.continuation_safe,
                    failed_recipients=durable.failed_recipients,
                    pending_recipients=durable.pending_recipients,
                    uncertain_recipients=durable.uncertain_recipients,
                    assigned_account_ids=durable.assigned_account_ids,
                    processed=durable.processed,
                    success=durable.success,
                    failed=durable.failed,
                    remaining=durable.remaining,
                )

        order = tuple(customer.email for customer in execution.customers)
        known = set(order)
        with self._state_lock:
            state = self._delivery_state.get(task.id)
            if state is None:
                return None
            failed_set = set(state.failed_recipients)
            pending_set = set(state.pending_recipients)
            uncertain_set = set(state.uncertain_recipients)
            bindings = dict(state.attempted_account_ids)
            safe = bool(state.continuation_safe)

        safe = safe and failed_set.isdisjoint(pending_set | uncertain_set)
        safe = safe and pending_set.isdisjoint(uncertain_set)
        safe = safe and failed_set.issubset(known) and pending_set.issubset(known) and uncertain_set.issubset(known)
        ordered_failed = tuple(email for email in order if email in failed_set)
        ordered_pending = tuple(email for email in order if email in pending_set)
        ordered_uncertain = tuple(email for email in order if email in uncertain_set)
        ordered_bindings = tuple((email, bindings[email]) for email in order if email in bindings)
        if not safe:
            return TaskDeliverySummary(
                continuation_safe=False,
                failed_recipients=ordered_failed,
                pending_recipients=ordered_pending,
                uncertain_recipients=ordered_uncertain,
                assigned_account_ids=ordered_bindings,
                processed=task.processed,
                success=task.success,
                failed=task.failed,
                remaining=task.remaining,
            )

        processed = task.total - len(ordered_pending) - len(ordered_uncertain)
        failed = len(ordered_failed)
        success = processed - failed
        if processed < 0 or success < 0 or processed > task.total:
            return TaskDeliverySummary(
                continuation_safe=False,
                failed_recipients=ordered_failed,
                pending_recipients=ordered_pending,
                uncertain_recipients=ordered_uncertain,
                assigned_account_ids=ordered_bindings,
                processed=task.processed,
                success=task.success,
                failed=task.failed,
                remaining=task.remaining,
            )
        return TaskDeliverySummary(
            continuation_safe=True,
            failed_recipients=ordered_failed,
            pending_recipients=ordered_pending,
            uncertain_recipients=ordered_uncertain,
            assigned_account_ids=ordered_bindings,
            processed=processed,
            success=success,
            failed=failed,
            remaining=len(ordered_pending) + len(ordered_uncertain),
        )

    def _hydrate_delivery_state_from_summary(
        self,
        task: Task,
        summary: TaskDeliverySummary,
        *,
        execution_mode: TaskExecutionMode,
    ) -> _DeliveryState:
        state = _DeliveryState(
            failed_recipients=set(summary.failed_recipients),
            pending_recipients=set(summary.pending_recipients),
            uncertain_recipients=set(summary.uncertain_recipients),
            attempted_recipients={email for email, _account_id in summary.assigned_account_ids},
            attempted_account_ids=dict(summary.assigned_account_ids),
            continuation_safe=summary.continuation_safe,
            execution_mode=execution_mode.value,
        )
        with self._state_lock:
            self._delivery_state[task.id] = state
        return state


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
        external_adapter = None
        if adapter is not None:
            if not adapter.supports_task_execution or adapter.task_batch_handler is None:
                message = adapter.task_unavailable_message or adapter.profile.task_unavailable_message
                raise ProviderRuntimeError(message or "No built-in task runner is available for this provider.")
            batch_handler = getattr(self, adapter.task_batch_handler, None)
            if not callable(batch_handler):
                raise ProviderRuntimeError(
                    f"The registered Task handler for provider '{adapter.provider_id}' is unavailable."
                )
            runtime_profile = adapter.profile
        else:
            external_adapter = self.external_adapter(snapshot.provider_id)
            if external_adapter is None or not external_adapter.profile.task_execution_enabled:
                raise ProviderRuntimeError("No executable Task adapter is available for this external provider.")
            if self._domain_store is None:
                raise ProviderRuntimeError(
                    "Executable external Tasks require the durable P10 delivery ledger; operational storage is unavailable.",
                    category="storage",
                )
            batch_handler = self._run_external_batch
            runtime_profile = external_adapter.profile

        runtime_preflight = preflight_runtime_inputs(
            provider_id=snapshot.provider_id,
            template=snapshot.template,
            customers=(CustomerRecord(customer.email, customer.name, customer.country) for customer in snapshot.customers),
            runtime_profile=runtime_profile,
        )
        if not runtime_preflight.passed:
            raise ProviderRuntimeError(runtime_preflight.message)
        if external_adapter is not None:
            extra_issues = self.external_task_validation_issues(
                snapshot.provider_id,
                snapshot.template,
                [CustomerRecord(c.email, c.name, c.country) for c in snapshot.customers],
            )
            if extra_issues:
                first = extra_issues[0]
                message = str(getattr(first, "message", first)).strip()
                correction = str(getattr(first, "correction", "")).strip()
                raise ProviderRuntimeError(f"{message} {correction}".strip(), category="preflight")

        existing_summary = self.delivery_summary(task)
        if retry_failed:
            if task.status != "Failed":
                raise ProviderRuntimeError("Retry Failed is only available for a Failed Task.")
            if existing_summary is None or not existing_summary.continuation_safe:
                message = (
                    "The exact failed recipient set is not available in the durable delivery ledger."
                    if self._domain_store is not None
                    else "The exact failed recipient set is not available in this application session."
                )
                raise ProviderRuntimeError(message)
            if existing_summary.pending_recipients or existing_summary.uncertain_recipients:
                raise ProviderRuntimeError(
                    "Retry Failed is unavailable while pending or uncertain recipients remain. Use Resume Remaining."
                )
            recipients = tuple(
                email for email in snapshot.customer_emails if email in existing_summary.failed_recipients
            )
            if not recipients:
                raise ProviderRuntimeError("This task has no failed recipients to retry.")
            if self._domain_store is not None:
                self._hydrate_delivery_state_from_summary(
                    task,
                    existing_summary,
                    execution_mode=TaskExecutionMode.RETRY_FAILED,
                )
            else:
                with self._state_lock:
                    delivery = self._delivery_state.get(task.id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The exact failed recipient set is not available in this application session."
                        )
                    delivery.execution_mode = TaskExecutionMode.RETRY_FAILED.value
            mode = TaskExecutionMode.RETRY_FAILED
        elif resume_remaining:
            if task.status != "Stopped":
                raise ProviderRuntimeError("Resume Remaining is only available for a Stopped Task.")
            if existing_summary is None or not existing_summary.continuation_safe:
                message = (
                    "The exact continuation recipient set is not available in the durable delivery ledger."
                    if self._domain_store is not None
                    else "The exact continuation recipient set is not available in this application session."
                )
                raise ProviderRuntimeError(message)
            if snapshot.provider_id == "refrens" or external_adapter is not None:
                # Refrens and generic external providers cannot blindly replay
                # unresolved non-idempotent mutations. Only known failed/pending
                # recipients are safe automatic continuation candidates.
                eligible = set(existing_summary.failed_recipients) | set(existing_summary.pending_recipients)
                if not eligible and existing_summary.uncertain_recipients:
                    if external_adapter is not None:
                        raise ProviderRuntimeError(
                            "External Resume Remaining is unavailable because only uncertain provider outcomes remain. "
                            "Automatic replay is disabled to prevent duplicate provider mutations."
                        )
                    raise ProviderRuntimeError(
                        "Refrens Resume Remaining is unavailable because only uncertain provider outcomes remain. "
                        "Automatic replay is disabled to prevent duplicate invoice/email delivery."
                    )
            else:
                eligible = (
                    set(existing_summary.failed_recipients)
                    | set(existing_summary.pending_recipients)
                    | set(existing_summary.uncertain_recipients)
                )
            recipients = tuple(email for email in snapshot.customer_emails if email in eligible)
            if not recipients:
                raise ProviderRuntimeError("This task has no remaining recipients to resume.")
            if self._domain_store is not None:
                self._hydrate_delivery_state_from_summary(
                    task,
                    existing_summary,
                    execution_mode=TaskExecutionMode.RESUME_REMAINING,
                )
            else:
                with self._state_lock:
                    delivery = self._delivery_state.get(task.id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The exact continuation recipient set is not available in this application session."
                        )
                    delivery.execution_mode = TaskExecutionMode.RESUME_REMAINING.value
            mode = TaskExecutionMode.RESUME_REMAINING
        else:
            if task.status != "Ready" or not is_pristine_first_run(task):
                raise ProviderRuntimeError(
                    "A full Start is only available for a pristine Ready Task. Create a new Task for another full execution."
                )
            if existing_summary is not None:
                raise ProviderRuntimeError(
                    "This Task already has durable delivery history; a duplicate full Start is not allowed."
                )
            with self._state_lock:
                existing = self._delivery_state.get(task.id)
                if existing is not None and existing.execution_mode:
                    raise ProviderRuntimeError(
                        "This Task already has a current-session execution state; a duplicate full Start is not allowed."
                    )
                recipients = snapshot.customer_emails
                self._delivery_state[task.id] = _DeliveryState(
                    failed_recipients=set(),
                    pending_recipients=set(recipients),
                    uncertain_recipients=set(),
                    continuation_safe=True,
                    execution_mode=TaskExecutionMode.FIRST_RUN.value,
                )
            mode = TaskExecutionMode.FIRST_RUN

        def runner(context: Any) -> None:
            run_id = ""
            if self._domain_store is not None:
                try:
                    run = self._domain_store.begin_delivery_run(
                        context.task,
                        execution_mode=mode.value,
                        recipients=recipients,
                    )
                except DomainStoreError as exc:
                    raise ProviderRuntimeError(
                        f"Durable delivery run could not be started before provider execution: {exc}",
                        category="storage",
                        retryable=False,
                    ) from exc
                run_id = run.run_id
                _context_log(context, f"Durable delivery run {run.run_id} started (run {run.run_number}).", category="TASK")
            try:
                if external_adapter is not None:
                    batch_handler(
                        context,
                        snapshot,
                        recipients,
                        execution_mode=mode,
                        run_id=run_id,
                        external_adapter=external_adapter,
                    )
                else:
                    batch_handler(
                        context,
                        snapshot,
                        recipients,
                        execution_mode=mode,
                        run_id=run_id,
                    )
            except Exception as exc:
                if self._domain_store is not None and run_id:
                    # A storage fault can leave a write-ahead Started operation
                    # whose provider outcome is unknown. Keep the run Running so
                    # startup recovery classifies it as Interrupted/Uncertain.
                    if not isinstance(exc, ProviderRuntimeError) or exc.category != "storage":
                        try:
                            self._domain_store.finish_delivery_run(run_id, status=DELIVERY_RUN_FAILED)
                        except DomainStoreError as finish_exc:
                            raise ProviderRuntimeError(
                                f"Delivery run terminal state could not be saved: {finish_exc}",
                                category="storage",
                                retryable=False,
                            ) from exc
                raise
            else:
                if self._domain_store is not None and run_id:
                    terminal = DELIVERY_RUN_STOPPED if context.stop_flag.is_set() else DELIVERY_RUN_COMPLETED
                    try:
                        self._domain_store.finish_delivery_run(run_id, status=terminal)
                    except DomainStoreError as exc:
                        raise ProviderRuntimeError(
                            f"Delivery run terminal state could not be saved: {exc}",
                            category="storage",
                            retryable=False,
                        ) from exc

        return runner


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

    def _provider_scheduling_policy(self, provider_id: str) -> ProviderSchedulingPolicy | None:
        adapter = provider_adapter_contract(provider_id)
        if adapter is not None:
            return adapter.scheduling_policy
        external = self.external_adapter(provider_id)
        return external.scheduling_policy if external is not None else None

    @staticmethod
    def _cooldown_delay(
        *,
        incident_count: int,
        base_seconds: float,
        cap_seconds: float,
        retry_after_seconds: float | None = None,
    ) -> float:
        exponent = max(0, int(incident_count) - 1)
        delay = min(float(cap_seconds), float(base_seconds) * (2**exponent))
        if retry_after_seconds is not None:
            delay = max(delay, max(0.0, float(retry_after_seconds)))
        return delay

    def _account_health_status(self, provider_id: str, account_id: str) -> tuple[str, float]:
        key = (provider_id.strip().lower(), account_id)
        now = time.monotonic()
        with self._scheduler_lock:
            state = self._account_health.get(key)
            if state is None:
                return "", 0.0
            remaining = max(0.0, state.cooldown_until - now)
            if remaining <= 0:
                state.cooldown_until = 0.0
            return state.blocked_reason, remaining

    def _provider_cooldown_remaining(self, provider_id: str) -> float:
        normalized = provider_id.strip().lower()
        now = time.monotonic()
        with self._scheduler_lock:
            state = self._provider_health.get(normalized)
            if state is None:
                return 0.0
            remaining = max(0.0, state.cooldown_until - now)
            if remaining <= 0:
                state.cooldown_until = 0.0
            return remaining

    def _wait_for_provider_health(self, context: Any, provider_id: str, *, email: str = "") -> bool:
        while True:
            remaining = self._provider_cooldown_remaining(provider_id)
            if remaining <= 0:
                return not context.stop_flag.is_set() and _wait_for_resume(context)
            suffix = f" before {email}" if email else ""
            _context_log(context, 
                f"{provider_id.title()} provider cooldown active; waiting {remaining:.2f}s{suffix}."
            )
            if not _cooperative_retry_wait(context, remaining):
                return False

    def _wait_for_account_health(
        self,
        context: Any,
        provider_id: str,
        account: AccountSnapshot,
        *,
        email: str,
    ) -> bool:
        while True:
            blocked_reason, remaining = self._account_health_status(provider_id, account.id)
            if blocked_reason:
                raise ProviderRuntimeError(
                    f"{provider_id.title()} account '{account.name}' is blocked for this runtime after an "
                    f"authentication/permission failure: {blocked_reason} Re-test the account before retrying.",
                    category="account-blocked",
                    retryable=False,
                )
            if remaining <= 0:
                return not context.stop_flag.is_set() and _wait_for_resume(context)
            _context_log(context, 
                f"{provider_id.title()} account '{account.name}' is cooling down; "
                f"waiting {remaining:.2f}s before {email}."
            )
            if not _cooperative_retry_wait(context, remaining):
                return False

    def _select_stripe_account(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        email: str,
        primary_index: int,
        *,
        allow_failover: bool,
    ) -> AccountSnapshot:
        if not self._wait_for_provider_health(context, snapshot.provider_id, email=email):
            raise ProviderRuntimeError(
                "Stripe recipient scheduling stopped by user request.",
                category="stopped",
                retryable=False,
            )

        accounts = snapshot.accounts
        primary = accounts[primary_index]
        while True:
            blocked_reason, primary_remaining = self._account_health_status(snapshot.provider_id, primary.id)
            if blocked_reason:
                raise ProviderRuntimeError(
                    f"Stripe account '{primary.name}' is blocked for this runtime after an authentication/permission "
                    f"failure: {blocked_reason} Re-test the account before retrying.",
                    category="account-blocked",
                    retryable=False,
                )
            if primary_remaining <= 0:
                return primary

            if not allow_failover:
                if not self._wait_for_account_health(
                    context, snapshot.provider_id, primary, email=email
                ):
                    raise ProviderRuntimeError(
                        "Stripe recipient scheduling stopped by user request.",
                        category="stopped",
                        retryable=False,
                    )
                return primary

            cooling_waits = [primary_remaining]
            for offset in range(1, len(accounts)):
                candidate = accounts[(primary_index + offset) % len(accounts)]
                candidate_blocked, candidate_remaining = self._account_health_status(
                    snapshot.provider_id, candidate.id
                )
                if candidate_blocked:
                    continue
                if candidate_remaining <= 0:
                    _context_log(context, 
                        f"Stripe primary account '{primary.name}' is temporarily unavailable; "
                        f"routing unattempted recipient {email} to account '{candidate.name}'."
                    )
                    return candidate
                cooling_waits.append(candidate_remaining)

            wait_seconds = min(cooling_waits)
            _context_log(context, 
                f"All eligible Stripe accounts are cooling down; waiting {wait_seconds:.2f}s before {email}."
            )
            if not _cooperative_retry_wait(context, wait_seconds):
                raise ProviderRuntimeError(
                    "Stripe recipient scheduling stopped by user request.",
                    category="stopped",
                    retryable=False,
                )

    def _await_account_rate_slot(
        self,
        context: Any,
        provider_id: str,
        account: AccountSnapshot,
    ) -> bool:
        policy = self._provider_scheduling_policy(provider_id)
        if policy is None or policy.requests_per_second_per_account <= 0:
            return not context.stop_flag.is_set() and _wait_for_resume(context)
        if policy.burst_capacity != 1:
            raise ProviderRuntimeError(
                f"Unsupported {provider_id.title()} scheduling burst capacity; expected 1.",
                category="scheduler",
                retryable=False,
            )
        interval = 1.0 / float(policy.requests_per_second_per_account)
        key = (provider_id.strip().lower(), account.id)
        while True:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                return False
            with self._scheduler_lock:
                now = time.monotonic()
                next_allowed = self._account_next_request_at.get(key, 0.0)
                if now >= next_allowed:
                    self._account_next_request_at[key] = now + interval
                    return True
                delay = next_allowed - now
            if not _cooperative_retry_wait(context, delay):
                return False

    def _mark_recipient_attempted(self, task_id: str, email: str, account_id: str) -> None:
        with self._state_lock:
            delivery = self._delivery_state.get(task_id)
            if delivery is None or not delivery.continuation_safe:
                raise ProviderRuntimeError(
                    "The Task continuation state became unavailable before provider execution."
                )
            existing_account_id = delivery.attempted_account_ids.get(email)
            if existing_account_id is not None and existing_account_id != account_id:
                delivery.continuation_safe = False
                raise ProviderRuntimeError(
                    "The current-session recipient/account binding changed after provider execution began; "
                    "continuation is blocked to prevent cross-account replay."
                )
            delivery.attempted_recipients.add(email)
            delivery.attempted_account_ids[email] = account_id

    @staticmethod
    def _safe_delivery_error(account: AccountSnapshot, exc: BaseException) -> tuple[str, str, str]:
        message = redact_sensitive_text(
            str(exc).strip(),
            secret_values=account.credentials.values(),
            mask_emails=False,
        )[:2000]
        if isinstance(exc, ProviderRuntimeError):
            code = f"HTTP_{exc.http_status}" if exc.http_status is not None else (exc.category or "provider")
        else:
            code = type(exc).__name__
        return type(exc).__name__, code, message

    def _finish_ledger_recipient(
        self,
        *,
        run_id: str,
        recipient_ordinal: int,
        result: str,
        stage: str,
        attempt_number: int,
        account: AccountSnapshot,
        error: BaseException | None = None,
    ) -> None:
        if self._domain_store is None or not run_id:
            return
        error_class = error_code = error_message = ""
        if error is not None:
            error_class, error_code, error_message = self._safe_delivery_error(account, error)
        try:
            self._domain_store.finish_delivery_recipient(
                run_id=run_id,
                recipient_ordinal=recipient_ordinal,
                final_result=result,
                stage=stage,
                attempt_number=attempt_number,
                error_class=error_class,
                error_code=error_code,
                error_message=error_message,
            )
        except DomainStoreError as exc:
            raise ProviderRuntimeError(
                f"Durable recipient result could not be saved: {exc}",
                category="storage",
                retryable=False,
            ) from exc

    def _record_scheduler_failure(
        self,
        provider_id: str,
        account: AccountSnapshot,
        exc: ProviderRuntimeError,
    ) -> tuple[str, ...]:
        policy = self._provider_scheduling_policy(provider_id)
        if policy is None:
            return ()
        normalized = provider_id.strip().lower()
        account_key = (normalized, account.id)
        now = time.monotonic()
        messages: list[str] = []

        if exc.http_status in {401, 403}:
            with self._scheduler_lock:
                state = self._account_health.setdefault(account_key, _SchedulerHealthState())
                state.blocked_reason = str(exc)
                state.cooldown_until = 0.0
                state.last_reason = f"HTTP {exc.http_status}"
            messages.append(
                f"{provider_id.title()} account '{account.name}' is blocked for this runtime after HTTP "
                f"{exc.http_status}; re-test the account before retrying."
            )
            return tuple(messages)

        if (
            exc.http_status == 429
            and exc.rate_limit_reason is not None
            and exc.rate_limit_reason in policy.account_rate_limit_reasons
        ):
            with self._scheduler_lock:
                state = self._account_health.setdefault(account_key, _SchedulerHealthState())
                state.consecutive_incidents += 1
                delay = self._cooldown_delay(
                    incident_count=state.consecutive_incidents,
                    base_seconds=policy.account_cooldown_base_seconds,
                    cap_seconds=policy.account_cooldown_cap_seconds,
                    retry_after_seconds=exc.retry_after_seconds,
                )
                state.cooldown_until = max(state.cooldown_until, now + delay)
                state.last_reason = exc.rate_limit_reason
            messages.append(
                f"{provider_id.title()} account '{account.name}' entered a {delay:.2f}s cooldown after "
                f"rate-limit reason '{exc.rate_limit_reason}'."
            )
            return tuple(messages)

        provider_transient = (
            exc.category in {"timeout", "network"}
            or exc.http_status in {408, 500, 502, 503, 504}
            or (normalized == "refrens" and exc.http_status == 429)
            or (provider_adapter_contract(normalized) is None and exc.http_status == 429)
        )
        if provider_transient:
            with self._scheduler_lock:
                state = self._provider_health.setdefault(normalized, _SchedulerHealthState())
                state.consecutive_incidents += 1
                delay = self._cooldown_delay(
                    incident_count=state.consecutive_incidents,
                    base_seconds=policy.provider_cooldown_base_seconds,
                    cap_seconds=policy.provider_cooldown_cap_seconds,
                    retry_after_seconds=exc.retry_after_seconds,
                )
                state.cooldown_until = max(state.cooldown_until, now + delay)
                state.last_reason = exc.category if exc.http_status is None else f"HTTP {exc.http_status}"
            messages.append(
                f"{provider_id.title()} provider entered a {delay:.2f}s cooldown after "
                f"{state.last_reason}; account hopping is disabled for provider/network failures."
            )
        return tuple(messages)

    def _record_scheduler_success(self, provider_id: str, account: AccountSnapshot) -> None:
        normalized = provider_id.strip().lower()
        account_key = (normalized, account.id)
        with self._scheduler_lock:
            account_state = self._account_health.get(account_key)
            if account_state is not None and not account_state.blocked_reason:
                account_state.consecutive_incidents = 0
                account_state.cooldown_until = 0.0
                account_state.last_reason = ""
            provider_state = self._provider_health.get(normalized)
            if provider_state is not None:
                provider_state.consecutive_incidents = 0
                provider_state.cooldown_until = 0.0
                provider_state.last_reason = ""

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
        *,
        run_id: str = "",
        recipient_ordinal: int = -1,
    ) -> tuple[dict[str, Any], int]:
        if not run_id:
            run_id = str(getattr(context, "_invio_delivery_run_id", ""))
        if recipient_ordinal < 0:
            recipient_ordinal = int(getattr(context, "_invio_recipient_ordinal", -1))
        attempt = 1
        while True:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                raise ProviderRuntimeError("Stripe recipient execution stopped before the next attempt.", category="stopped")
            try:
                result = self._send_stripe_invoice(
                    snapshot,
                    account,
                    email,
                    context=context,
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                    attempt_number=attempt,
                )
                return result, attempt
            except ProviderRuntimeError as exc:
                if not exc.retryable or attempt >= MAX_TOTAL_ATTEMPTS:
                    setattr(exc, "attempt_number", attempt)
                    raise
                retry_number = attempt
                delay = self._retry_delay_seconds(retry_number, exc)
                _context_log(context, 
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
            except Exception as exc:
                setattr(exc, "attempt_number", attempt)
                raise


    @staticmethod
    def _external_mutation_is_ambiguous(exc: ProviderRuntimeError) -> bool:
        return (
            exc.category in {"timeout", "network"}
            or exc.http_status in {408, 500, 502, 503, 504}
        )

    def _external_task_request(
        self,
        context: Any,
        *,
        snapshot: TaskSnapshot,
        account: AccountSnapshot,
        run_id: str,
        recipient_ordinal: int,
        attempt_state: list[int],
        operation_state: dict[str, Any],
        stage: str,
        operation_kind: str,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        json_data: dict[str, Any] | None = None,
        idempotency_key: str = "",
        provider_reference_key: str = "",
    ) -> dict[str, Any]:
        clean_stage = str(stage).strip()
        if not clean_stage or len(clean_stage) > 96 or any(ch.isspace() for ch in clean_stage):
            raise ProviderRuntimeError("External provider operation stage is invalid.", category="preflight")
        if operation_kind not in EXTERNAL_OPERATION_KINDS:
            raise ProviderRuntimeError("External provider operation kind is unsupported.", category="preflight")
        if operation_kind == IDEMPOTENT_MUTATION and not str(idempotency_key).strip():
            raise ProviderRuntimeError(
                "IDEMPOTENT_MUTATION requires a real stable provider-supported idempotency reference.",
                category="preflight",
            )
        if operation_kind != IDEMPOTENT_MUTATION and idempotency_key:
            raise ProviderRuntimeError(
                "Only IDEMPOTENT_MUTATION may declare an idempotency reference.",
                category="preflight",
            )
        ledger_stage = (
            f"external_mutation:{clean_stage}"
            if operation_kind in {IDEMPOTENT_MUTATION, NON_IDEMPOTENT_MUTATION}
            else f"external_read:{clean_stage}"
        )
        if body is not None and json_data is not None:
            raise ProviderRuntimeError("External request cannot provide both body and json_data.")

        effective_headers = dict(headers or {})
        effective_body = body
        if json_data is not None:
            effective_headers.setdefault("Content-Type", "application/json")
            effective_body = _json_body(json_data)

        while True:
            attempt_number = attempt_state[0]
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                raise ProviderRuntimeError("External provider execution stopped before the next operation.", category="stopped")
            if not self._wait_for_provider_health(context, snapshot.provider_id, email=snapshot.customers[recipient_ordinal].email):
                raise ProviderRuntimeError("External provider execution stopped during provider cooldown.", category="stopped")
            if not self._wait_for_account_health(
                context, snapshot.provider_id, account, email=snapshot.customers[recipient_ordinal].email
            ):
                raise ProviderRuntimeError("External provider execution stopped during account cooldown.", category="stopped")
            if not self._await_account_rate_slot(context, snapshot.provider_id, account):
                raise ProviderRuntimeError("External provider execution stopped during account rate wait.", category="stopped")
            self._mark_recipient_attempted(
                snapshot.task_id, snapshot.customers[recipient_ordinal].email, account.id
            )
            if self._domain_store is not None and run_id:
                try:
                    self._domain_store.begin_delivery_operation(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        attempt_number=attempt_number,
                        stage=ledger_stage,
                        account_id=account.id,
                        account_name=account.name,
                        idempotency_key=str(idempotency_key).strip(),
                    )
                except DomainStoreError as exc:
                    raise ProviderRuntimeError(
                        f"Durable Started operation could not be committed before external provider request: {exc}",
                        category="storage",
                    ) from exc
            try:
                result = self._transport(method.upper(), url, effective_headers, effective_body, self.timeout)
            except ProviderRuntimeError as exc:
                uncertain = operation_kind == NON_IDEMPOTENT_MUTATION and self._external_mutation_is_ambiguous(exc)
                status = DELIVERY_OPERATION_UNCERTAIN if uncertain else DELIVERY_OPERATION_FAILED
                if self._domain_store is not None and run_id:
                    error_class, error_code, error_message = self._safe_delivery_error(account, exc)
                    try:
                        self._domain_store.finish_delivery_operation(
                            run_id=run_id, recipient_ordinal=recipient_ordinal, attempt_number=attempt_number,
                            stage=ledger_stage, status=status, error_class=error_class, error_code=error_code,
                            error_message=error_message,
                        )
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"External provider request ended but its durable result could not be saved: {ledger_exc}",
                            category="storage",
                        ) from exc
                for message in self._record_scheduler_failure(snapshot.provider_id, account, exc):
                    _context_log(context, message)
                if uncertain:
                    wrapped = ProviderRuntimeError(
                        f"External non-idempotent operation '{clean_stage}' has an uncertain provider outcome: {exc}",
                        category="uncertain", retryable=False, http_status=exc.http_status,
                    )
                    setattr(wrapped, "attempt_number", attempt_number)
                    raise wrapped from exc
                retry_allowed = operation_kind in {SAFE_READ, IDEMPOTENT_MUTATION} and exc.retryable
                if not retry_allowed or attempt_number >= MAX_TOTAL_ATTEMPTS:
                    setattr(exc, "attempt_number", attempt_number)
                    raise
                delay = self._retry_delay_seconds(attempt_number, exc)
                _context_log(
                    context,
                    f"External provider transient failure during {clean_stage} "
                    f"(attempt {attempt_number}/{MAX_TOTAL_ATTEMPTS}): {exc}. Retrying in {delay:.2f}s.",
                )
                if not _cooperative_retry_wait(context, delay):
                    raise ProviderRuntimeError("External provider retry stopped by user request.", category="stopped") from exc
                attempt_state[0] += 1
                continue

            provider_reference = ""
            if provider_reference_key:
                provider_reference = str(result.get(provider_reference_key, "")).strip()
                if not provider_reference:
                    error = ProviderRuntimeError(
                        f"External provider response did not contain required reference '{provider_reference_key}'.",
                        category="response", retryable=False,
                    )
                    status = DELIVERY_OPERATION_UNCERTAIN if operation_kind != SAFE_READ else DELIVERY_OPERATION_FAILED
                    if self._domain_store is not None and run_id:
                        error_class, error_code, error_message = self._safe_delivery_error(account, error)
                        try:
                            self._domain_store.finish_delivery_operation(
                                run_id=run_id, recipient_ordinal=recipient_ordinal, attempt_number=attempt_number,
                                stage=ledger_stage, status=status, error_class=error_class, error_code=error_code,
                                error_message=error_message,
                            )
                        except DomainStoreError as ledger_exc:
                            raise ProviderRuntimeError(
                                f"External provider response could not be reconciled durably: {ledger_exc}",
                                category="storage",
                            ) from error
                    setattr(error, "attempt_number", attempt_number)
                    raise error
            if self._domain_store is not None and run_id:
                try:
                    self._domain_store.finish_delivery_operation(
                        run_id=run_id, recipient_ordinal=recipient_ordinal, attempt_number=attempt_number,
                        stage=ledger_stage, status=DELIVERY_OPERATION_SUCCEEDED, provider_reference=provider_reference,
                    )
                except DomainStoreError as exc:
                    raise ProviderRuntimeError(
                        f"External provider request succeeded but its durable result could not be saved: {exc}",
                        category="storage",
                    ) from exc
            self._record_scheduler_success(snapshot.provider_id, account)
            if operation_kind in {IDEMPOTENT_MUTATION, NON_IDEMPOTENT_MUTATION}:
                successful_stages = operation_state.setdefault("mutating_succeeded_stages", [])
                successful_stages.append(ledger_stage)
                if operation_kind == NON_IDEMPOTENT_MUTATION:
                    operation_state["non_idempotent_succeeded"] = True
            return result

    def _run_external_batch(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        recipients: tuple[str, ...],
        *,
        execution_mode: TaskExecutionMode,
        run_id: str = "",
        external_adapter=None,
    ) -> None:
        if external_adapter is None:
            raise ProviderRuntimeError("Validated external provider adapter is unavailable.")
        full_index = {email: index for index, email in enumerate(snapshot.customer_emails)}
        with self._state_lock:
            delivery = self._delivery_state.get(snapshot.task_id)
            if delivery is None or not delivery.continuation_safe:
                raise ProviderRuntimeError("The Task continuation state is unavailable before external execution.")
            attempted_before_execution = set(delivery.attempted_recipients)
            attempted_account_ids = dict(delivery.attempted_account_ids)

        validation_context = ExternalTaskValidationContext(
            provider_id=snapshot.provider_id,
            template=copy.deepcopy(snapshot.template),
            customers=tuple(CustomerRecord(c.email, c.name, c.country) for c in snapshot.customers),
        )
        try:
            validation_issues = tuple(external_adapter.validate_task(validation_context) or ())
        except BaseException as exc:
            raise ProviderRuntimeError(
                f"External provider Task validation failed: {type(exc).__name__}: {exc}", category="preflight"
            ) from exc
        if validation_issues:
            first = validation_issues[0]
            message = str(getattr(first, "message", first)).strip() or "External provider Task validation failed."
            correction = str(getattr(first, "correction", "")).strip()
            raise ProviderRuntimeError(f"{message} {correction}".strip(), category="preflight")

        _context_log(context, f"External {snapshot.provider_id} batch started with {len(recipients)} recipient(s).", category="TASK")
        attempted = 0
        for email in recipients:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                break
            recipient_ordinal = full_index[email]
            primary_index = recipient_ordinal % len(snapshot.accounts)
            bound_account_id = attempted_account_ids.get(email)
            if email in attempted_before_execution and not bound_account_id:
                raise ProviderRuntimeError(
                    "The attempted external recipient has no exact account binding; continuation is blocked."
                )
            if bound_account_id:
                account = next((a for a in snapshot.accounts if a.id == bound_account_id), None)
                if account is None:
                    raise ProviderRuntimeError(
                        "The attempted external recipient account is outside the frozen Task account set."
                    )
            else:
                account = snapshot.accounts[primary_index]

            attempt_state = [1]
            operation_state: dict[str, Any] = {
                "mutating_succeeded_stages": [],
                "non_idempotent_succeeded": False,
            }
            result_stage = ""
            try:
                customer = snapshot.customers[recipient_ordinal]
                external_context = ExternalRecipientExecutionContext(
                    provider_id=snapshot.provider_id,
                    task_id=snapshot.task_id,
                    account_id=account.id,
                    account_name=account.name,
                    account_mode=account.mode,
                    credentials=dict(account.credentials),
                    customer=CustomerRecord(customer.email, customer.name, customer.country),
                    template=copy.deepcopy(snapshot.template),
                    request=lambda **kwargs: self._external_task_request(
                        context, snapshot=snapshot, account=account, run_id=run_id,
                        recipient_ordinal=recipient_ordinal, attempt_state=attempt_state,
                        operation_state=operation_state, **kwargs
                    ),
                    log=lambda message: _context_log(context, str(message)),
                )
                result = external_adapter.execute_recipient(external_context)
                if not isinstance(result, ExternalRecipientResult):
                    raise ProviderRuntimeError(
                        "External adapter execute_recipient must return ExternalRecipientResult.", category="provider"
                    )
                result_stage = result.final_stage.strip()
                successful_mutating_stages = tuple(operation_state.get("mutating_succeeded_stages", ()))
                if not successful_mutating_stages:
                    raise ProviderRuntimeError(
                        "External adapter returned recipient success without a successful host-managed mutating "
                        "provider operation; recipient success cannot be recorded.",
                        category="provider",
                        retryable=False,
                    )
                if not result_stage or result_stage != successful_mutating_stages[-1]:
                    raise ProviderRuntimeError(
                        "External adapter final_stage must match its last successful host-managed mutating operation.",
                        category="provider",
                        retryable=False,
                    )
                if self._domain_store is not None and run_id:
                    if result.provider_customer_id or result.provider_invoice_id:
                        try:
                            self._domain_store.update_delivery_provider_ids(
                                run_id=run_id, recipient_ordinal=recipient_ordinal,
                                provider_customer_id=result.provider_customer_id or None,
                                provider_invoice_id=result.provider_invoice_id or None,
                            )
                        except DomainStoreError as exc:
                            raise ProviderRuntimeError(
                                f"External provider references could not be saved: {exc}", category="storage"
                            ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id, recipient_ordinal=recipient_ordinal, result=DELIVERY_RESULT_SUCCEEDED,
                        stage=result_stage, attempt_number=attempt_state[0], account=account,
                    )
            except BaseException as exc:
                attempt_number = int(getattr(exc, "attempt_number", attempt_state[0]))
                final_result = (
                    DELIVERY_RESULT_UNCERTAIN
                    if operation_state.get("non_idempotent_succeeded")
                    else DELIVERY_RESULT_FAILED
                )
                if self._domain_store is not None and run_id:
                    try:
                        if self._domain_store.recipient_has_uncertain_mutation(
                            run_id=run_id, recipient_ordinal=recipient_ordinal
                        ):
                            final_result = DELIVERY_RESULT_UNCERTAIN
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"External delivery uncertainty could not be reconciled: {ledger_exc}", category="storage"
                        ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id, recipient_ordinal=recipient_ordinal, result=final_result, stage=result_stage,
                        attempt_number=attempt_number, account=account, error=exc,
                    )
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError("The external Task continuation state became unavailable.") from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                    if final_result == DELIVERY_RESULT_UNCERTAIN:
                        delivery.uncertain_recipients.add(email)
                    else:
                        delivery.failed_recipients.add(email)
                _context_log(context, f"External {snapshot.provider_id} execution failed for {email}: {exc}")
            else:
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError("The external Task continuation state became unavailable.")
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                _context_log(context, f"External {snapshot.provider_id} recipient accepted for {email}.")

            attempted += 1
            summary = self.delivery_summary(context.task)
            if summary is None or not summary.continuation_safe:
                raise ProviderRuntimeError("The external Task continuation state could not be reconciled safely.")
            context.progress(
                summary.processed, summary.success, summary.failed,
                f"Processed {attempted}/{len(recipients)} external recipient(s).",
            )

        summary = self.delivery_summary(context.task)
        if summary is None or not summary.continuation_safe:
            raise ProviderRuntimeError("The external Task continuation state could not be reconciled safely.")
        if context.stop_flag.is_set():
            _context_log(context, "External provider batch stopped by user request.", category="TASK")
            return
        if summary.pending_recipients:
            raise ProviderRuntimeError("External Task ended before all selected recipients were resolved safely.")
        if summary.uncertain_recipients:
            raise ProviderRuntimeError(
                f"{len(summary.uncertain_recipients)} external recipient(s) have uncertain provider outcomes. "
                "Automatic replay is disabled for uncertain external mutations."
            )
        if summary.failed_recipients:
            raise ProviderRuntimeError(
                f"{summary.failed} external recipient(s) failed. Use Retry Failed after reviewing Live Logs."
            )
        _context_log(context, "External provider batch completed successfully.", category="TASK")

    def _run_stripe_batch(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        recipients: tuple[str, ...],
        *,
        execution_mode: TaskExecutionMode,
        run_id: str = "",
    ) -> None:
        full_index = {email: index for index, email in enumerate(snapshot.customer_emails)}
        with self._state_lock:
            delivery = self._delivery_state.get(snapshot.task_id)
            if delivery is None or not delivery.continuation_safe:
                raise ProviderRuntimeError("The Task continuation state is unavailable before Stripe execution.")
            attempted_before_execution = set(delivery.attempted_recipients)
            attempted_account_ids = dict(delivery.attempted_account_ids)

        attempted = 0
        label = {
            TaskExecutionMode.FIRST_RUN: "Stripe batch",
            TaskExecutionMode.RESUME_REMAINING: "Stripe continuation",
            TaskExecutionMode.RETRY_FAILED: "Stripe failed-recipient retry",
        }[execution_mode]
        _context_log(context, 
            f"{label} started with {len(recipients)} recipient(s) using template '{snapshot.template.name}'."
        )

        for email in recipients:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                break
            recipient_ordinal = full_index[email]
            primary_index = recipient_ordinal % len(snapshot.accounts)
            bound_account_id = attempted_account_ids.get(email)
            if email in attempted_before_execution and not bound_account_id:
                raise ProviderRuntimeError(
                    "The attempted recipient has no exact account binding in durable/current-session state; "
                    "continuation is blocked to prevent cross-account replay."
                )
            if bound_account_id:
                bound_index = next(
                    (index for index, item in enumerate(snapshot.accounts) if item.id == bound_account_id),
                    None,
                )
                if bound_index is None:
                    raise ProviderRuntimeError(
                        "The attempted recipient account is no longer present in the frozen Task account set."
                    )
                scheduling_index = bound_index
                allow_failover = False
            else:
                scheduling_index = primary_index
                allow_failover = True
            account = snapshot.accounts[scheduling_index]
            attempt_number = 1
            try:
                account = self._select_stripe_account(
                    context,
                    snapshot,
                    email,
                    scheduling_index,
                    allow_failover=allow_failover,
                )
                setattr(context, "_invio_delivery_run_id", run_id)
                setattr(context, "_invio_recipient_ordinal", recipient_ordinal)
                send_result = self._send_stripe_invoice_with_retry(
                    context,
                    snapshot,
                    account,
                    email,
                )
                if (
                    isinstance(send_result, tuple)
                    and len(send_result) == 2
                    and isinstance(send_result[1], int)
                ):
                    _sent, attempt_number = send_result
            except ProviderRuntimeError as exc:
                attempt_number = int(getattr(exc, "attempt_number", attempt_number))
                if exc.category == "stopped" and context.stop_flag.is_set():
                    break
                if exc.category == "storage":
                    raise
                for message in self._record_scheduler_failure(snapshot.provider_id, account, exc):
                    _context_log(context, message)
                final_result = DELIVERY_RESULT_FAILED
                if self._domain_store is not None and run_id:
                    try:
                        if self._domain_store.recipient_has_uncertain_mutation(
                            run_id=run_id,
                            recipient_ordinal=recipient_ordinal,
                        ):
                            final_result = DELIVERY_RESULT_UNCERTAIN
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"Durable delivery uncertainty could not be reconciled: {ledger_exc}",
                            category="storage",
                            retryable=False,
                        ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=final_result,
                        stage="",
                        attempt_number=attempt_number,
                        account=account,
                        error=exc,
                    )
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                    if final_result == DELIVERY_RESULT_UNCERTAIN:
                        delivery.uncertain_recipients.add(email)
                    else:
                        delivery.failed_recipients.add(email)
                _context_log(context, f"Stripe send failed for {email} via account '{account.name}': {exc}")
            except Exception as exc:
                attempt_number = int(getattr(exc, "attempt_number", attempt_number))
                final_result = DELIVERY_RESULT_FAILED
                if self._domain_store is not None and run_id:
                    try:
                        if self._domain_store.recipient_has_uncertain_mutation(
                            run_id=run_id,
                            recipient_ordinal=recipient_ordinal,
                        ):
                            final_result = DELIVERY_RESULT_UNCERTAIN
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"Durable delivery uncertainty could not be reconciled: {ledger_exc}",
                            category="storage",
                            retryable=False,
                        ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=final_result,
                        stage="",
                        attempt_number=attempt_number,
                        account=account,
                        error=exc,
                    )
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                    if final_result == DELIVERY_RESULT_UNCERTAIN:
                        delivery.uncertain_recipients.add(email)
                    else:
                        delivery.failed_recipients.add(email)
                _context_log(context, 
                    f"Stripe send failed unexpectedly for {email} via account '{account.name}': "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                if self._domain_store is not None and run_id:
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=DELIVERY_RESULT_SUCCEEDED,
                        stage="invoice_send",
                        attempt_number=attempt_number,
                        account=account,
                    )
                self._record_scheduler_success(snapshot.provider_id, account)
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError("The Task continuation state became unavailable during execution.")
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                _context_log(context, f"Stripe invoice sent to {email} via account '{account.name}'.")

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
            _context_log(context, "Stripe batch stopped by user request.", category="TASK")
            return
        if summary.pending_recipients:
            raise ProviderRuntimeError("Task execution ended before all selected recipients were resolved safely.")
        if summary.uncertain_recipients:
            raise ProviderRuntimeError(
                f"{len(summary.uncertain_recipients)} recipient(s) have an uncertain provider outcome. "
                "Use Resume Remaining to reconcile only unresolved recipients."
            )
        if summary.failed_recipients:
            raise ProviderRuntimeError(
                f"{summary.failed} recipient(s) failed. Use Retry Failed after reviewing Live Logs."
            )
        _context_log(context, "Stripe batch completed successfully.", category="TASK")

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

    def _send_stripe_invoice(
        self,
        snapshot: TaskSnapshot,
        account: AccountSnapshot,
        email: str,
        *,
        context: Any | None = None,
        run_id: str = "",
        recipient_ordinal: int = -1,
        attempt_number: int = 1,
    ) -> dict[str, Any]:
        key = account.credentials.get("secret_key", "").strip()
        self._validate_stripe_key(key)
        self._validate_stripe_mode(account, key)
        template = snapshot.template
        currency = template.currency.upper()
        scheduling_kwargs = {
            "context": context,
            "account": account,
            "task_id": snapshot.task_id,
            "recipient_email": email,
            "run_id": run_id,
            "recipient_ordinal": recipient_ordinal,
            "attempt_number": attempt_number,
        }

        customer_id = ""
        if template.reuse_customer:
            found = self._stripe_request(
                "GET",
                "/customers",
                key,
                query={"email": email, "limit": 1},
                operation_stage="customer_lookup",
                **scheduling_kwargs,
            )
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
                operation_stage="customer_create",
                **scheduling_kwargs,
            )
            customer_id = str(created_customer.get("id", "")).strip()
        if not customer_id:
            raise ProviderRuntimeError("Stripe customer response did not contain an id.", category="response")

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
            operation_stage="invoice_create",
            **scheduling_kwargs,
        )
        invoice_id = str(invoice.get("id", "")).strip()
        if not invoice_id:
            raise ProviderRuntimeError("Stripe invoice response did not contain an id.", category="response")

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
                item_form["quantity_decimal"] = _decimal_text(quantity)
            if template.automatic_tax:
                item_form["tax_behavior"] = "exclusive"
            self._stripe_request(
                "POST",
                "/invoiceitems",
                key,
                form=item_form,
                idempotency=_idempotency_key(snapshot.task_id, email, f"item-{index}"),
                operation_stage=f"invoice_item:{index}",
                **scheduling_kwargs,
            )

        finalized = self._stripe_request(
            "POST",
            f"/invoices/{invoice_id}/finalize",
            key,
            form={"auto_advance": False},
            idempotency=_idempotency_key(snapshot.task_id, email, "finalize"),
            operation_stage="invoice_finalize",
            **scheduling_kwargs,
        )
        finalized_id = str(finalized.get("id", invoice_id)).strip() or invoice_id
        sent = self._stripe_request(
            "POST",
            f"/invoices/{finalized_id}/send",
            key,
            form={},
            idempotency=_idempotency_key(snapshot.task_id, email, "send"),
            operation_stage="invoice_send",
            **scheduling_kwargs,
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
        context: Any | None = None,
        account: AccountSnapshot | None = None,
        task_id: str = "",
        recipient_email: str = "",
        run_id: str = "",
        recipient_ordinal: int = -1,
        attempt_number: int = 1,
        operation_stage: str = "",
    ) -> dict[str, Any]:
        url = f"{self.STRIPE_BASE_URL}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("ascii")
        headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "Invio/1.0.0.1.36 Vib-Tools",
        }
        body = None
        if method.upper() != "GET":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = _form_body(form or {})
        if idempotency:
            headers["Idempotency-Key"] = idempotency

        ledger_started = False
        if context is not None and account is not None:
            if not self._wait_for_provider_health(context, "stripe", email=recipient_email):
                raise ProviderRuntimeError(
                    "Stripe recipient execution stopped during provider cooldown.",
                    category="stopped",
                    retryable=False,
                )
            if not self._await_account_rate_slot(context, "stripe", account):
                raise ProviderRuntimeError(
                    "Stripe recipient execution stopped during account rate wait.",
                    category="stopped",
                    retryable=False,
                )
            if task_id and recipient_email:
                self._mark_recipient_attempted(task_id, recipient_email, account.id)
            if self._domain_store is not None and run_id:
                if recipient_ordinal < 0 or not operation_stage:
                    raise ProviderRuntimeError(
                        "Durable delivery operation identity is incomplete before provider execution.",
                        category="storage",
                        retryable=False,
                    )
                try:
                    self._domain_store.begin_delivery_operation(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        attempt_number=attempt_number,
                        stage=operation_stage,
                        account_id=account.id,
                        account_name=account.name,
                        idempotency_key=idempotency or "",
                    )
                except DomainStoreError as exc:
                    raise ProviderRuntimeError(
                        f"Durable Started operation could not be committed before provider request: {exc}",
                        category="storage",
                        retryable=False,
                    ) from exc
                ledger_started = True

        try:
            result = self._transport(method.upper(), url, headers, body, self.timeout)
        except Exception as exc:
            if ledger_started and self._domain_store is not None and account is not None:
                if isinstance(exc, ProviderRuntimeError):
                    ambiguous = exc.category in {"timeout", "network"} and method.upper() != "GET"
                else:
                    ambiguous = method.upper() != "GET"
                op_status = DELIVERY_OPERATION_UNCERTAIN if ambiguous else DELIVERY_OPERATION_FAILED
                error_class, error_code, error_message = self._safe_delivery_error(account, exc)
                try:
                    self._domain_store.finish_delivery_operation(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        attempt_number=attempt_number,
                        stage=operation_stage,
                        status=op_status,
                        error_class=error_class,
                        error_code=error_code,
                        error_message=error_message,
                    )
                except DomainStoreError as ledger_exc:
                    raise ProviderRuntimeError(
                        f"Provider request ended but its durable operation result could not be saved: {ledger_exc}",
                        category="storage",
                        retryable=False,
                    ) from exc
            raise

        if ledger_started and self._domain_store is not None:
            provider_reference = ""
            if operation_stage == "customer_lookup":
                data = result.get("data") if isinstance(result, dict) else None
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    provider_reference = str(data[0].get("id", "")).strip()
            elif isinstance(result, dict):
                provider_reference = str(result.get("id", "")).strip()
            try:
                self._domain_store.finish_delivery_operation(
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                    attempt_number=attempt_number,
                    stage=operation_stage,
                    status=DELIVERY_OPERATION_SUCCEEDED,
                    provider_reference=provider_reference,
                )
            except DomainStoreError as exc:
                raise ProviderRuntimeError(
                    f"Provider request succeeded but its durable operation result could not be saved: {exc}",
                    category="storage",
                    retryable=False,
                ) from exc
        return result


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

    def _refrens_auth_with_retry(
        self,
        context: Any,
        account: AccountSnapshot,
        email: str,
        *,
        task_id: str,
        run_id: str,
        recipient_ordinal: int,
    ) -> tuple[str, str, str, int]:
        raw_base_url = account.credentials.get("base_url", "").strip()
        url_key = account.credentials.get("url_key", "").strip()
        app_id = account.credentials.get("app_id", "").strip()
        app_secret = account.credentials.get("app_secret", "").strip()
        try:
            base_url = canonical_refrens_base_url(raw_base_url)
        except ValueError as exc:
            raise ProviderRuntimeError(str(exc)) from exc
        if not all((url_key, app_id, app_secret)):
            raise ProviderRuntimeError("Refrens URL Key, App ID and App Secret are required.")

        # Construct the secret-bearing payload only after the destination has
        # passed the exact canonical-host trust policy.
        payload = {"strategy": "app-secret", "appId": app_id, "appSecret": app_secret}
        attempt = 1
        while True:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                raise ProviderRuntimeError(
                    "Refrens authentication stopped before the next attempt.",
                    category="stopped",
                    retryable=False,
                )
            try:
                response = self._refrens_request(
                    "POST",
                    base_url,
                    "/authentication",
                    token=None,
                    json_data=payload,
                    context=context,
                    account=account,
                    task_id=task_id,
                    recipient_email=email,
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                    attempt_number=attempt,
                    operation_stage="refrens_authentication",
                    mutating=False,
                )
                token = str(response.get("accessToken", "")).strip()
                if not token:
                    raise ProviderRuntimeError("Refrens authentication response did not contain accessToken.")
                return token, base_url, url_key, attempt
            except ProviderRuntimeError as exc:
                if not exc.retryable or attempt >= MAX_TOTAL_ATTEMPTS:
                    setattr(exc, "attempt_number", attempt)
                    raise
                delay = self._retry_delay_seconds(attempt, exc)
                _context_log(context, 
                    f"Refrens authentication transient failure for {email} via account '{account.name}' "
                    f"(attempt {attempt}/{MAX_TOTAL_ATTEMPTS}): {exc}. Retrying in {delay:.2f}s."
                )
                if not _cooperative_retry_wait(context, delay):
                    raise ProviderRuntimeError(
                        "Refrens authentication retry stopped by user request.",
                        category="stopped",
                        retryable=False,
                    ) from exc
                attempt += 1
            except Exception as exc:
                setattr(exc, "attempt_number", attempt)
                raise

    @staticmethod
    def _refrens_mutation_is_ambiguous(exc: BaseException) -> bool:
        if not isinstance(exc, ProviderRuntimeError):
            return True
        return exc.category in {"timeout", "network"} or exc.http_status in {408, 500, 502, 503, 504}

    def _refrens_request(
        self,
        method: str,
        base_url: str,
        path: str,
        *,
        token: str | None,
        json_data: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        context: Any | None = None,
        account: AccountSnapshot | None = None,
        task_id: str = "",
        recipient_email: str = "",
        run_id: str = "",
        recipient_ordinal: int = -1,
        attempt_number: int = 1,
        operation_stage: str = "",
        mutating: bool = False,
        required_reference_key: str = "",
    ) -> dict[str, Any]:
        try:
            trusted_base_url = canonical_refrens_base_url(base_url)
        except ValueError as exc:
            raise ProviderRuntimeError(str(exc)) from exc
        url = f"{trusted_base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        headers = {"Accept": "application/json", "User-Agent": "Invio/1.0.0.1.36 Vib-Tools"}
        body = None
        if json_data is not None:
            headers["Content-Type"] = "application/json"
            body = _json_body(json_data)
        if token:
            headers["Authorization"] = f"Bearer {token}"

        ledger_started = False
        if context is not None and account is not None:
            if not self._wait_for_provider_health(context, "refrens", email=recipient_email):
                raise ProviderRuntimeError(
                    "Refrens recipient execution stopped during provider cooldown.",
                    category="stopped",
                    retryable=False,
                )
            if not self._wait_for_account_health(context, "refrens", account, email=recipient_email):
                raise ProviderRuntimeError(
                    "Refrens recipient execution stopped during account cooldown.",
                    category="stopped",
                    retryable=False,
                )
            if not self._await_account_rate_slot(context, "refrens", account):
                raise ProviderRuntimeError(
                    "Refrens recipient execution stopped during account rate wait.",
                    category="stopped",
                    retryable=False,
                )
            if task_id and recipient_email:
                self._mark_recipient_attempted(task_id, recipient_email, account.id)
            if self._domain_store is not None and run_id:
                if recipient_ordinal < 0 or not operation_stage:
                    raise ProviderRuntimeError(
                        "Durable Refrens operation identity is incomplete before provider execution.",
                        category="storage",
                        retryable=False,
                    )
                try:
                    self._domain_store.begin_delivery_operation(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        attempt_number=attempt_number,
                        stage=operation_stage,
                        account_id=account.id,
                        account_name=account.name,
                        idempotency_key="",
                    )
                except DomainStoreError as exc:
                    raise ProviderRuntimeError(
                        f"Durable Started operation could not be committed before Refrens request: {exc}",
                        category="storage",
                        retryable=False,
                    ) from exc
                ledger_started = True

        try:
            result = self._transport(method.upper(), url, headers, body, self.timeout)
        except Exception as exc:
            if ledger_started and self._domain_store is not None and account is not None:
                operation_status = DELIVERY_OPERATION_FAILED
                if mutating and self._refrens_mutation_is_ambiguous(exc):
                    operation_status = DELIVERY_OPERATION_UNCERTAIN
                error_class, error_code, error_message = self._safe_delivery_error(account, exc)
                try:
                    self._domain_store.finish_delivery_operation(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        attempt_number=attempt_number,
                        stage=operation_stage,
                        status=operation_status,
                        error_class=error_class,
                        error_code=error_code,
                        error_message=error_message,
                    )
                except DomainStoreError as ledger_exc:
                    raise ProviderRuntimeError(
                        f"Refrens request ended but its durable operation result could not be saved: {ledger_exc}",
                        category="storage",
                        retryable=False,
                    ) from exc
            raise

        provider_reference = ""
        if isinstance(result, dict) and required_reference_key:
            provider_reference = str(result.get(required_reference_key, "")).strip()
            if not provider_reference:
                error = ProviderRuntimeError(
                    f"Refrens response did not contain required provider reference '{required_reference_key}'; "
                    "the provider-side outcome cannot be reconciled safely.",
                    category="response",
                    retryable=False,
                )
                if ledger_started and self._domain_store is not None and account is not None:
                    error_class, error_code, error_message = self._safe_delivery_error(account, error)
                    try:
                        self._domain_store.finish_delivery_operation(
                            run_id=run_id,
                            recipient_ordinal=recipient_ordinal,
                            attempt_number=attempt_number,
                            stage=operation_stage,
                            status=DELIVERY_OPERATION_UNCERTAIN if mutating else DELIVERY_OPERATION_FAILED,
                            error_class=error_class,
                            error_code=error_code,
                            error_message=error_message,
                        )
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"Refrens response was received but its durable operation result could not be saved: {ledger_exc}",
                            category="storage",
                            retryable=False,
                        ) from error
                raise error
        elif isinstance(result, dict):
            provider_reference = str(result.get("_id", "")).strip()

        if ledger_started and self._domain_store is not None:
            try:
                self._domain_store.finish_delivery_operation(
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                    attempt_number=attempt_number,
                    stage=operation_stage,
                    status=DELIVERY_OPERATION_SUCCEEDED,
                    provider_reference=provider_reference,
                )
            except DomainStoreError as exc:
                raise ProviderRuntimeError(
                    f"Refrens request succeeded but its durable operation result could not be saved: {exc}",
                    category="storage",
                    retryable=False,
                ) from exc
        return result

    def _run_refrens_batch(
        self,
        context: Any,
        snapshot: TaskSnapshot,
        recipients: tuple[str, ...],
        *,
        execution_mode: TaskExecutionMode,
        run_id: str = "",
    ) -> None:
        full_index = {email: index for index, email in enumerate(snapshot.customer_emails)}
        with self._state_lock:
            delivery = self._delivery_state.get(snapshot.task_id)
            if delivery is None or not delivery.continuation_safe:
                raise ProviderRuntimeError("The Task continuation state is unavailable before Refrens execution.")
            attempted_before_execution = set(delivery.attempted_recipients)
            attempted_account_ids = dict(delivery.attempted_account_ids)

        attempted = 0
        label = {
            TaskExecutionMode.FIRST_RUN: "Refrens batch",
            TaskExecutionMode.RESUME_REMAINING: "Refrens continuation",
            TaskExecutionMode.RETRY_FAILED: "Refrens failed-recipient retry",
        }[execution_mode]
        _context_log(context, 
            f"{label} started with {len(recipients)} recipient(s) using template '{snapshot.template.name}'."
        )

        for email in recipients:
            if context.stop_flag.is_set() or not _wait_for_resume(context):
                break
            recipient_ordinal = full_index[email]
            customer = snapshot.customers[recipient_ordinal]
            primary_index = recipient_ordinal % len(snapshot.accounts)
            bound_account_id = attempted_account_ids.get(email)
            if email in attempted_before_execution and not bound_account_id:
                raise ProviderRuntimeError(
                    "The attempted Refrens recipient has no exact account binding in durable/current-session state; "
                    "continuation is blocked to prevent cross-account replay."
                )
            if bound_account_id:
                bound_index = next(
                    (index for index, item in enumerate(snapshot.accounts) if item.id == bound_account_id),
                    None,
                )
                if bound_index is None:
                    raise ProviderRuntimeError(
                        "The attempted Refrens recipient account is no longer present in the frozen Task account set."
                    )
                account = snapshot.accounts[bound_index]
            else:
                # P11 deliberately does not speculate across Refrens accounts.
                # The frozen round-robin primary remains authoritative.
                account = snapshot.accounts[primary_index]

            attempt_number = 1
            stage = ""
            try:
                payload = self.build_refrens_invoice_payload(
                    snapshot.template,
                    customer_email=customer.email,
                    customer_country=customer.country,
                    customer_name=customer.name,
                )
                token, base_url, url_key, attempt_number = self._refrens_auth_with_retry(
                    context,
                    account,
                    email,
                    task_id=snapshot.task_id,
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                )
                stage = "refrens_invoice_create_email"
                request_payload = copy.deepcopy(payload)
                request_payload["email"] = {
                    "to": {
                        "email": customer.email,
                        "name": customer.name,
                    }
                }
                created = self._refrens_request(
                    "POST",
                    base_url,
                    f"/businesses/{url_key}/invoices",
                    token=token,
                    json_data=request_payload,
                    context=context,
                    account=account,
                    task_id=snapshot.task_id,
                    recipient_email=email,
                    run_id=run_id,
                    recipient_ordinal=recipient_ordinal,
                    attempt_number=attempt_number,
                    operation_stage=stage,
                    mutating=True,
                    required_reference_key="_id",
                )
                invoice_id = str(created.get("_id", "")).strip()
                if not invoice_id:
                    raise ProviderRuntimeError(
                        "Refrens invoice response did not contain _id; delivery cannot be confirmed safely.",
                        category="response",
                        retryable=False,
                    )
            except ProviderRuntimeError as exc:
                attempt_number = int(getattr(exc, "attempt_number", attempt_number))
                if exc.category == "stopped" and context.stop_flag.is_set():
                    break
                if exc.category == "storage":
                    raise
                for message in self._record_scheduler_failure(snapshot.provider_id, account, exc):
                    _context_log(context, message)
                final_result = DELIVERY_RESULT_FAILED
                if self._domain_store is not None and run_id:
                    try:
                        if self._domain_store.recipient_has_uncertain_mutation(
                            run_id=run_id,
                            recipient_ordinal=recipient_ordinal,
                        ):
                            final_result = DELIVERY_RESULT_UNCERTAIN
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"Durable Refrens uncertainty could not be reconciled: {ledger_exc}",
                            category="storage",
                            retryable=False,
                        ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=final_result,
                        stage=stage,
                        attempt_number=attempt_number,
                        account=account,
                        error=exc,
                    )
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during Refrens execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                    if final_result == DELIVERY_RESULT_UNCERTAIN:
                        delivery.uncertain_recipients.add(email)
                    else:
                        delivery.failed_recipients.add(email)
                _context_log(context, f"Refrens send failed for {email} via account '{account.name}': {exc}")
            except Exception as exc:
                attempt_number = int(getattr(exc, "attempt_number", attempt_number))
                final_result = DELIVERY_RESULT_FAILED
                if self._domain_store is not None and run_id:
                    try:
                        if self._domain_store.recipient_has_uncertain_mutation(
                            run_id=run_id,
                            recipient_ordinal=recipient_ordinal,
                        ):
                            final_result = DELIVERY_RESULT_UNCERTAIN
                    except DomainStoreError as ledger_exc:
                        raise ProviderRuntimeError(
                            f"Durable Refrens uncertainty could not be reconciled: {ledger_exc}",
                            category="storage",
                            retryable=False,
                        ) from exc
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=final_result,
                        stage=stage,
                        attempt_number=attempt_number,
                        account=account,
                        error=exc,
                    )
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError(
                            "The Task continuation state became unavailable during Refrens execution."
                        ) from exc
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                    if final_result == DELIVERY_RESULT_UNCERTAIN:
                        delivery.uncertain_recipients.add(email)
                    else:
                        delivery.failed_recipients.add(email)
                _context_log(context, 
                    f"Refrens send failed unexpectedly for {email} via account '{account.name}': "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                if self._domain_store is not None and run_id:
                    self._finish_ledger_recipient(
                        run_id=run_id,
                        recipient_ordinal=recipient_ordinal,
                        result=DELIVERY_RESULT_SUCCEEDED,
                        stage="refrens_invoice_create_email",
                        attempt_number=attempt_number,
                        account=account,
                    )
                self._record_scheduler_success(snapshot.provider_id, account)
                with self._state_lock:
                    delivery = self._delivery_state.get(snapshot.task_id)
                    if delivery is None or not delivery.continuation_safe:
                        raise ProviderRuntimeError("The Task continuation state became unavailable during Refrens execution.")
                    delivery.pending_recipients.discard(email)
                    delivery.failed_recipients.discard(email)
                    delivery.uncertain_recipients.discard(email)
                _context_log(context, f"Refrens invoice created and email requested for {email} via account '{account.name}'.")

            attempted += 1
            summary = self.delivery_summary(context.task)
            if summary is None or not summary.continuation_safe:
                raise ProviderRuntimeError("The Refrens Task continuation state could not be reconciled safely.")
            if execution_mode is TaskExecutionMode.RETRY_FAILED:
                message = f"Retry processed {attempted}/{len(recipients)} failed Refrens recipient(s)."
            elif execution_mode is TaskExecutionMode.RESUME_REMAINING:
                message = f"Resume processed {attempted}/{len(recipients)} safe Refrens recipient(s)."
            else:
                message = f"Processed {summary.processed}/{context.task.total} Refrens recipient(s)."
            context.progress(summary.processed, summary.success, summary.failed, message)

        if not context.stop_flag.is_set() and not context.pause_gate.is_set():
            _wait_for_resume(context)

        summary = self.delivery_summary(context.task)
        if summary is None or not summary.continuation_safe:
            raise ProviderRuntimeError("The Refrens Task continuation state could not be reconciled safely.")
        if context.stop_flag.is_set():
            _context_log(context, "Refrens batch stopped by user request.", category="TASK")
            return
        if summary.pending_recipients:
            raise ProviderRuntimeError("Refrens execution ended before all selected safe recipients were resolved.")
        if summary.uncertain_recipients:
            raise ProviderRuntimeError(
                f"{len(summary.uncertain_recipients)} Refrens recipient(s) have an uncertain provider outcome. "
                "Automatic replay is disabled because Refrens does not expose an approved idempotency contract."
            )
        if summary.failed_recipients:
            raise ProviderRuntimeError(
                f"{summary.failed} Refrens recipient(s) failed. Use Retry Failed after reviewing Live Logs."
            )
        _context_log(context, "Refrens batch completed successfully.", category="TASK")

    def build_refrens_invoice_payload(
        self,
        template: InvoiceTemplate,
        *,
        customer_email: str,
        customer_country: str,
        customer_name: str = "",
    ) -> dict[str, Any]:
        """Build a Refrens invoice payload from explicit approved customer data."""
        country = customer_country.strip().upper()
        if len(country) != 2 or not country.isascii() or not country.isalpha():
            raise ProviderRuntimeError("Refrens customer country must be an ISO 3166-1 alpha-2 code.")
        if country == "IN":
            raise ProviderRuntimeError(
                "Refrens requires billedTo.gstState for Indian customers, but the current approved Invio customer "
                "model does not contain GST State. No invoice was created."
            )
        email = customer_email.strip().lower()
        if not email:
            raise ProviderRuntimeError("Refrens customer email is required.")
        name = customer_name.strip()
        if not name:
            raise ProviderRuntimeError("Refrens customer name is required; Invio will not substitute the email address.")
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
                "name": name,
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
        email = customer_email.strip().lower()
        name = customer_name.strip()
        if not email:
            raise ProviderRuntimeError("Refrens customer email is required.")
        if not name:
            raise ProviderRuntimeError("Refrens customer name is required; Invio will not substitute the email address.")
        token, base_url, url_key = self._refrens_auth(credentials)
        request_payload = copy.deepcopy(payload)
        request_payload["email"] = {
            "to": {
                "email": email,
                "name": name,
            }
        }
        created = self._refrens_request(
            "POST", base_url, f"/businesses/{url_key}/invoices", token=token, json_data=request_payload
        )
        invoice_id = str(created.get("_id", "")).strip()
        if not invoice_id:
            raise ProviderRuntimeError("Refrens invoice response did not contain _id; delivery cannot be confirmed.")
        return created
