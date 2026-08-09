# Error Handling - Current Baseline and Production Plan

**Baseline:** `v1.0.0.1.10`  
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
- duplicate account reservation;
- unverified account selection during Task creation.

Relevant MainWindow actions catch `StateError` and display a warning.

### Account API verification errors

**Files:** `src/ui/dialogs.py`, `src/core/provider_runtime/runtime.py`, `src/core/state/app_state.py`, `src/ui/main_window.py`

P01 now handles:

- missing required account/credential fields before network access;
- Stripe key-format and selected Test/Live mode mismatch before provider requests;
- Stripe/Refrens provider/network/permission failures without marking the account verified;
- providers without an executable API-test adapter as unavailable;
- credential-value scrubbing from provider error text before API-test display/logging;
- safe Add Account verification-thread lifetime by preventing dialog close while its `QThread` is active;
- unverified account rejection in New Task, backend Task creation, Start, and Retry.

### Settings load/save errors

**File:** `src/core/settings/manager.py`  
**Exception:** `SettingsError`

Currently handled:

- invalid/corrupt settings JSON falls back to defaults with a load warning;
- invalid start page, booleans, log limit and folder path;
- settings write failure;
- atomic temporary-file write + `os.replace`;
- best-effort runtime convenience state does not interrupt normal app work if saving fails.


### P02 durable-storage and credential errors

**Files:** `src/core/storage/`, `src/core/state/app_state.py`, `src/ui/main_window.py`, `src/app.py`

P02 now handles:

- SQLite open/integrity/schema failures with fail-closed startup; corrupt/unsupported storage is not silently replaced;
- schema version 0 -> 1 migration with pre-migration backup for an existing empty v0 database;
- unsupported future schema and unknown unversioned schema rejection;
- explicit SQLite transactions for customer-email replacement, template+children saves, Task+reservation creation, Task close/release and Task metadata updates;
- prior valid transaction preservation when a write fails;
- protected credential dependency/backend/read/write/delete failures without a plaintext-file fallback;
- compensation if Account metadata commit fails after protected credential write; a cleanup failure is surfaced rather than silently swallowed;
- missing/unreadable protected credential recovery by loading Account metadata as `Not Verified`;
- active Task restart recovery to the existing `Stopped` state without auto-resume;
- active-worker persistence failure by requesting Task stop and showing/logging a storage warning.

P02 does **not** claim provider-side crash reconciliation. A provider request may succeed immediately before a process/disk failure prevents the corresponding local progress update; persistent recipient attempts/provider IDs/idempotency reconciliation remain P10.

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
| EH-001 | **RESOLVED in P01:** Add Account executes real provider API verification on a dedicated `QThread` and fails closed | Invalid/revoked/unavailable credentials cannot become Task-ready | COMPLETE v1.0.0.1.6; re-verified v1.0.0.1.7 |
| EH-002 | **RESOLVED in P02:** transactional SQLite domain storage, schema checks, migration backup, corruption/future-schema fail-closed startup | Operational state now restart-durable by local contract | COMPLETE v1.0.0.1.8 |
| EH-003 | **RESOLVED in P02:** provider credentials use approved protected keyring storage with no plaintext fallback; missing secret restores Account as `Not Verified` | Native OS backend certification remains P14 | COMPLETE v1.0.0.1.8 |
| EH-004 | **RESOLVED in P03:** manual Re-test plus persisted verification state/time/safe error; failed Re-test becomes Not Verified | Known failed credentials cannot execute; no age-based/continuous health policy is claimed | COMPLETE v1.0.0.1.10 |
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


## P01 verification handling

Implemented in `v1.0.0.1.6`:

- missing required credential fields fail locally before network access;
- Stripe Test/Live mode mismatch fails before provider requests;
- Stripe/Refrens provider/network failures are returned to the user without marking the account verified;
- provider credential values are not included in Invio API-test log messages, and any returned error text is scrubbed against the submitted credential values before display/logging;
- providers without an executable API-test adapter fail closed as unavailable;
- Add Account cannot be closed while its verification thread is running, avoiding destruction of an active dialog-owned `QThread`;
- Task selection, creation, Start, and Retry reject accounts whose current-session status is not `Verified`.

Automatic retry/backoff, durable verification health, and persistent secret storage remain later phases and are not introduced by P01.


## P02 verification handling

Implemented in `v1.0.0.1.8`:

- operational state commits are transaction-bounded and schema-versioned;
- provider credentials are outside normal SQLite/settings/log storage;
- unavailable protected credentials fail closed to `Not Verified`;
- corrupt/future/unknown storage does not trigger silent database recreation;
- startup-active Tasks are recovered without sending;
- task persistence failure requests stop rather than allowing an unbounded unsaved run;
- exact recipient-level remote reconciliation remains intentionally deferred to P10.

## v1.0.0.1.9 P02 corrective handling

- **Persistence-stop re-entrancy:** the faulted-task guard is now set before `WorkerManager.stop()` is called, preventing recursive storage-failure handling if Stop emits `Stopping` while the database remains unavailable.
- **Reservation recovery consistency:** startup now fails closed when persisted `task_accounts` and `account_reservations` are not an exact one-to-one match. This prevents restored Tasks from losing account exclusivity silently.
- These are corrections to P02 failure/recovery handling only; no P03 lifecycle behavior is introduced.


## P03 account lifecycle handling

Implemented in `v1.0.0.1.10`:

- Account Edit is rejected while any open Task references the account and requires a new successful real API Test before commit.
- Failed candidate Edit verification never overwrites the saved account or protected credential.
- Re-test runs on a dialog-owned `QThread`; success/failure is durably recorded with UTC timestamp and credential-scrubbed error summary.
- Re-test is blocked while the referenced Task worker is active. Failed Re-test makes the account `Not Verified`, activating existing P01 execution gates.
- If the durable verification-health write fails after a real failed Re-test, the current process still marks the Account `Not Verified` before surfacing the persistence error. A successful Re-test never elevates an Account when its durable write fails.
- Account Delete is rejected while reserved/Task-referenced. Protected-secret deletion and SQLite deletion use compensation so a database failure attempts to restore the prior protected credential.
- Provider Uninstall is rejected while a matching Task worker is active. Otherwise provider installation state alone is removed; Accounts/Tasks/reservations/credentials remain.
- Task Start/Retry fail closed while the Task provider is not installed.
- Provider uninstall/reinstall does not invent verification expiry and does not silently delete/recreate accounts.
