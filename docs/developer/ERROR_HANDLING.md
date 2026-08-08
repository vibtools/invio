# Error Handling - Current Baseline and Production Plan

**Baseline:** `v1.0.0.1.5`  
**Status:** Forensic inventory. No runtime code is changed by this document.

## 1. Current Error-Handling Layers

### Provider manifest/install errors

**File:** `src/core/provider_manager/manager.py`  
**Exception:** `ProviderManifestError`

Currently handled:

- unreadable/invalid JSON manifest;
- invalid provider ID;
- missing provider name/version;
- invalid credential-field definition;
- bundled provider package not found;
- uninstall of a provider that is not installed;
- filesystem error while removing installed registry manifest.

UI install/load/uninstall handlers catch `ProviderManifestError` and show a warning dialog.

### Application-state validation errors

**File:** `src/core/state/app_state.py`  
**Exception:** `StateError`

Currently handled:

- missing account name;
- missing customer-list name;
- missing/unsupported invoice currency;
- invalid due-day range;
- unsupported invoice type;
- invalid invoice item structure/numbers/ranges;
- missing invoice item;
- deleting customer list/template while referenced by a Task;
- missing task account/list/template;
- mixed-provider account selection;
- duplicate account reservation.

Relevant MainWindow actions catch `StateError` and display a warning.

### Settings load/save errors

**File:** `src/core/settings/manager.py`  
**Exception:** `SettingsError`

Currently handled:

- invalid/corrupt settings JSON falls back to defaults with a load warning;
- invalid start page, booleans, log limit and folder path;
- settings write failure;
- atomic temporary-file write + `os.replace`;
- best-effort runtime convenience state does not interrupt normal app work if saving fails.

### Provider HTTP/response errors

**File:** `src/core/provider_runtime/runtime.py`  
**Exception:** `ProviderRuntimeError`

Currently handled/translated:

- HTTP provider errors with provider message extraction where possible;
- URL/network/timeout/OS errors;
- invalid JSON response;
- unexpected top-level response format;
- invalid Stripe key prefix;
- Stripe Test/Live mode mismatch;
- missing Stripe customer/invoice IDs;
- invalid Refrens HTTPS base URL;
- missing Refrens URL Key/App ID/App Secret;
- missing Refrens access token;
- invalid/missing Refrens customer email/country in helper contract;
- missing Refrens invoice `_id`;
- unsupported built-in provider task runner;
- deliberate Refrens task data gate.

### Stripe per-recipient handling

**File:** `src/core/provider_runtime/runtime.py::_run_stripe_batch`

- `ProviderRuntimeError` for one recipient is caught.
- Recipient is added to the in-memory failed set.
- Failure is logged and processing continues with later recipients.
- After batch completion, remaining failures cause the worker run to fail and allow Retry Failed.

### Worker exception isolation

**File:** `src/core/worker_manager/manager.py::_TaskWorker.run`

- Any uncaught `Exception` from a task runner is contained in the worker thread.
- Task finishes as `Failed` rather than propagating the exception into the GUI thread.
- A `Worker error: ...` log message is emitted.

### UI confirmation/error dialogs

**File:** `src/ui/main_window.py`

Existing confirmations cover:

- exit with active tasks;
- close task;
- delete invoice template;
- delete customer list;
- clear logs.

Known state/provider/import errors are normally converted to compact message boxes.

### Secret masking

**File:** `src/ui/main_window.py::log`

- Regex masking exists for values shaped like Stripe `sk_*` / `rk_*` test/live keys.
- This masking does not currently represent a general provider-secret redaction framework.

## 2. Current Handling Gaps

| EH ID | Missing/incomplete handling | Risk | Planned phase |
|---|---|---|---|
| EH-001 | Add Account API Test does not execute network verification | Invalid account reaches Task setup | P01 |
| EH-002 | No persistent storage/migration error model for operational data | Restart/data-loss/corruption risk | P02 |
| EH-003 | No protected credential-store error/recovery handling | Secret availability/security risk | P02 |
| EH-004 | No verified-account health/retest lifecycle | Stale/revoked credentials fail during send | P03 |
| EH-005 | Customer import does not provide complete row-level diagnostics | Partial/ambiguous bulk import | P04 |
| EH-006 | Stale/mutable Task inputs are not treated as an error | Wrong recipient/template run | P05 |
| EH-007 | Provider capability/customer/template mismatch lacks preflight error | Side effects can start before incompatibility is clear | P06 |
| EH-008 | Completed/Failed full Start resend semantics are not protected | Duplicate invoice/email risk | P07 |
| EH-009 | No retryable/permanent provider error taxonomy | Incorrect retry behavior | P08 |
| EH-010 | No automatic bounded retry/backoff/jitter | Transient failures become manual failures | P08 |
| EH-011 | No explicit 429/Retry-After handling | Rate-limit amplification | P08/P09 |
| EH-012 | Stop cannot interrupt in-flight blocking request | Slow stop/close | P08 |
| EH-013 | `stop_all(1500)` can finish waiting before 30 s HTTP timeout | Unsafe shutdown possibility | P08 |
| EH-014 | Unexpected exception inside a recipient stage is not reconciled at recipient level | Partial/uncertain run | P08/P10 |
| EH-015 | No account-health/failover error rules | Repeated failures on unhealthy account | P09 |
| EH-016 | Retry/idempotency/delivery state is not durable | Duplicate/unknown results after restart | P10 |
| EH-017 | Refrens task currently stops at required-country gate | Provider unavailable for normal bulk task | P11 |
| EH-018 | Export report/log writes lack user-facing `OSError` handling | Event-handler error on disk/path failure | P12 |
| EH-019 | Emails/PII are logged in clear | Privacy/support risk | P12 |
| EH-020 | Secret masking is Stripe-pattern-specific | Other provider secrets may appear in error text | P12 |
| EH-021 | External provider manifest may exist without executable adapter | Capability/runtime mismatch | P13 |
| EH-022 | No live integration/recovery certification | Unknown real-environment failure modes | P14 |
| EH-023 | External provider manifest can collide with a built-in runtime ID/credential contract | Wrong credential/runtime mapping | P06/P13 |
| EH-024 | Refrens auth accepts any HTTPS base URL | Credentials can be sent to an unintended host | P06/P11 |
| EH-025 | Stop can leave internal retry recipients not reflected in `task.failed` | Retry button/state inconsistency | P07/P10 |
| EH-026 | CSV export is not spreadsheet-formula-safe | Spreadsheet execution risk on opened export | P12 |
| EH-027 | Provider API acceptance is treated as Task success without inbox-delivery confirmation | Misinterpreted delivery state | P10/P12/P14 |
| EH-028 | File import catches only a limited exception set at the MainWindow boundary | Some malformed workbook/parser failures may escape the intended user warning path | P04/P12 |

## 3. Required Production Error Taxonomy

Future phases should converge on a stable error classification without changing provider/business semantics silently:

- **ValidationError**: local input/configuration error, never auto-retry.
- **AuthenticationError**: credential rejected/expired, require re-verification.
- **PermissionError**: credential valid but operation not authorized, do not blindly retry.
- **RateLimitError**: retry only according to bounded provider-safe delay.
- **TransientNetworkError**: timeout/disconnect/eligible 5xx; bounded retry.
- **ProviderRequestError**: deterministic provider rejection (4xx/business rule); no automatic replay unless explicitly safe.
- **DataRequirementError**: required customer/template/provider data missing before side effects.
- **PersistenceError**: storage/transaction/migration/secret-store issue; fail closed.
- **CancellationError/Stopped**: user-requested termination, reconciled separately from failure.
- **UnknownExecutionError**: unexpected exception; preserve run as uncertain/failed and retain reconciliation evidence.

The exact class structure must be approved within the relevant phase before implementation; this document does not authorize a refactor by itself.

## 4. Error-Handling Acceptance Rule

A production phase is not complete until every new external operation defines:

1. what can fail;
2. whether the failure is retryable;
3. how many retries are allowed;
4. what user sees;
5. what is logged/redacted;
6. what persistent state is written;
7. whether any provider-side side effect may already have occurred;
8. how restart/retry reconciles the uncertain state.
