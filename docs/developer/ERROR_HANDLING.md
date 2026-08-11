## v1.0.0.1.48.5 Error-Handling Note

No error-handling semantics changed. Row menu actions delegate to the existing MainWindow account handlers, so provider-not-installed, task-assignment, verification, protected-storage and delete-confirmation errors continue through the same existing dialogs and exceptions.

## v1.0.0.1.48.4 Error-Handling Note

No error classification, validation message, exception path or failure-handling behavior is changed. The New Task modal still uses the existing `_validate_and_accept()` validation gates and `compact_message_box()` warnings.

## v1.0.0.1.48.3 CI repository-contract regression boundary

GitHub Actions run `31516505105` failed after Linux Qt/PySide6 initialization had already succeeded. The failure was not a runtime exception: the v1.48.02 `.gitignore` workaround partially materialized the otherwise private `project/` directory in public CI. Historical tests use directory existence as the signal that a complete private baseline is available, so the partial tree caused them to read planning/specification/research files that were intentionally absent from GitHub.

The correction restores `/project/` as fully ignored and makes the four newer private v1.47/v1.48 reads conditional, matching the earlier v1.0.0.1.26 contract. Do not handle this class of CI failure by publishing selected private records; public CI assertions must be supported by tracked public evidence, with private evidence checked only in a full private baseline.

# Error Handling - Current Baseline and Production Plan

**Baseline:** `v1.0.0.1.33`  
**Status:** Current error-handling inventory including P12 export/privacy behavior.

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
| EH-005 | **RESOLVED in P04; corrected in v1.0.0.1.13:** structured customer import reports row-numbered missing/invalid email, invalid country, same-file conflicts, and existing-list metadata conflicts; malformed workbook/parser failures stay inside the caught import-error boundary | False/ambiguous customer rows/files are surfaced without silently creating data | COMPLETE v1.0.0.1.12; CORRECTED v1.0.0.1.13 |
| EH-006 | Stale/mutable Task inputs are not treated as an error | Wrong recipient/template run | P05 |
| EH-007 | **RESOLVED in v1.0.0.1.17:** provider/template/customer compatibility was not validated before side effects | Unsupported invoice type/currency/tax/customer requirements could reach provider execution | COMPLETE P06: no-side-effect capability preflight |
| EH-008 | Completed/Failed full Start resend semantics were ambiguous | RESOLVED in P07: Completed full resend and Failed normal Start are blocked; new full execution requires a new Task | P07 COMPLETE |
| EH-009 | **RESOLVED in P08; verification-corrected in v1.0.0.1.24:** provider/network failures carry retryability/category/HTTP metadata; truncated response bodies and TLS EOF/clean-close are correctly classified as transient where applicable | Structured bounded retry now receives the intended transport failures | COMPLETE P08 |
| EH-010 | **RESOLVED in P08:** maximum three total recipient attempts with exponential backoff and bounded jitter | Transient provider/network failures receive bounded automatic retry | COMPLETE P08 |
| EH-011 | **RESOLVED for reactive provider handling in P08:** 429/Retry-After is honored inside bounded retry; proactive per-account/provider scheduling limits remain P09 | Rate-limit responses no longer immediately amplify retry; proactive throttling still pending | P08 COMPLETE / P09 scheduling pending |
| EH-012 | **RESOLVED for safe cancellation in P08:** Stop prevents later retry/recipient work and waits cooperatively for the current bounded urllib request to return/timeout; no unsafe force-kill is attempted | Stop may wait for the bounded in-flight request by design, but shutdown remains safe | COMPLETE P08 |
| EH-013 | **RESOLVED in P08:** fixed 1500 ms blocking wait removed; MainWindow closes only after all task-owned QThreads actually finish | Application no longer accepts close while a task worker is still running | COMPLETE P08 |
| EH-014 | **RESOLVED for current-session aggregate reconciliation in P08:** unexpected per-recipient exceptions are isolated and counted once; durable attempt/provider-side evidence remains P10 | Aggregate progress stays consistent; crash/restart reconciliation remains pending | P08 COMPLETE / P10 durability pending |
| EH-015 | No account-health/failover error rules | Repeated failures on unhealthy account | P09 |
| EH-016 | Retry/idempotency/delivery state is not durable | Duplicate/unknown results after restart | P10 |
| EH-017 | Refrens Task runner remains disabled even though P04 can now store explicit required customer data | Provider unavailable for normal bulk task | P11 |
| EH-018 | **RESOLVED in P12:** Task/recipient/log exports use atomic writes and user-facing failure handling | Export failures no longer escape the Qt event handler or partially replace an existing target | COMPLETE P12 |
| EH-019 | **RESOLVED in P12:** recipient email is masked in Live Logs while full email is reserved for explicit support reports/exports | Diagnostic logs no longer expose full recipient email | COMPLETE P12 |
| EH-020 | **RESOLVED in P12; verification-corrected in v1.0.0.1.31:** centralized provider-neutral redaction covers known credential values plus named/auth token patterns, including quoted JSON-style fields | Provider diagnostic text is redacted before display/new durable error persistence | COMPLETE P12 / corrected v1.0.0.1.31 |
| EH-021 | External provider manifest may exist without executable adapter | Capability/runtime mismatch | P13 |
| EH-022 | No live integration/recovery certification | Unknown real-environment failure modes | P14 |
| EH-023 | **RESOLVED for packaged runtime IDs in v1.0.0.1.17:** external/installed manifest could collide with built-in runtime identity/credential/capability contract | Manifest declarations could disagree with executable Stripe/Refrens adapter | COMPLETE P06 packaged-ID reservation + manifest/runtime reconciliation; full external executable adapter architecture remains P13 |
| EH-024 | **RESOLVED in v1.0.0.1.17:** Refrens auth accepted any HTTPS base URL | App ID/App Secret could be sent to an owner-entered untrusted HTTPS host | COMPLETE P06: canonical `https://api.refrens.com` trust validation before auth payload construction |
| EH-025 | Stop could leave runtime retry/remaining recipients inconsistent with aggregate counters | RESOLVED for current-session P07 continuation: counters are derived from exact failed/pending sets. Durable identity recovery after restart remains P10 | P07 COMPLETE / P10 durability pending |
| EH-026 | **RESOLVED in P12:** CSV text cells are formula-neutralized before atomic export | Spreadsheet formula injection is prevented for user/provider-controlled text | COMPLETE P12 |
| EH-027 | **RESOLVED for P12 support reporting; verification-corrected in v1.0.0.1.31:** provider send acceptance is separate from independent email delivery and now requires durable send-stage success evidence | Inbox delivery remains unconfirmed without an independent provider delivery event; live certification remains P14 | COMPLETE P12 / P14 live evidence pending |
| EH-028 | File import boundary still does not classify every malformed workbook/parser exception | Some malformed files may escape the intended user warning taxonomy | P12 |
| EH-029 | **RESOLVED in v1.0.0.1.14:** migration-backup destination connection remained open across atomic rename on Windows | `WinError 32` could block application startup during supported schema migration | COMPLETE v1.0.0.1.14 |
| EH-030 | **RESOLVED in v1.0.0.1.15:** existing Task execution re-read live Customer List/Invoice Template at Start/Retry | Recipient/template drift could silently change an approved run and disagree with `Task.total` | COMPLETE P05 |
| EH-031 | **RESOLVED in v1.0.0.1.15:** pre-P05 Tasks have no trustworthy historical execution snapshot | Migration could fabricate false historical inputs if current list/template were copied | COMPLETE P05: preserve as `LegacyUnavailable`, block Start/Retry |
| EH-032 | **RESOLVED in v1.0.0.1.15:** persisted Task/snapshot provider/account/recipient/template invariants could be inconsistent | Unsafe execution or incorrect progress basis | COMPLETE P05: schema-v4 validation fails closed |
| EH-033 | **RESOLVED in v1.0.0.1.16:** normal post-P05 persistence could silently convert a new Task with no captured snapshot into `LegacyUnavailable` | A newly created Task could be misclassified as historical legacy state instead of failing creation | P05 correction: new Task persistence requires `Captured`; legacy state is migration-only |
| EH-034 | **RESOLVED in v1.0.0.1.16:** captured Task success/failed counters were not validated against processed recipients on update/load | Progress data could disagree with the immutable recipient snapshot while still loading | P05 correction: progress invariants fail closed |
| EH-035 | **RESOLVED in v1.0.0.1.16:** routine Task updates rewrote the persisted `total` column | Accidental in-memory total drift could be persisted even though P05 defines total as immutable | P05 correction: total is creation-only; update path validates but does not rewrite it |

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


## v1.0.0.1.11 P03 verification corrections

- **Migration backup fidelity:** pre-migration backups are created with SQLite backup semantics instead of copying only the main database file, so committed WAL pages are included.
- **Credential-loss restart safety:** missing/unreadable protected credentials are not only restored as `Not Verified` in memory; that downgrade/error summary is persisted before startup completes. If the recovery write fails, startup fails rather than silently retaining a stale durable `Verified` row.
- **Account Edit cross-store safety:** Account Edit persists a `Not Verified` safety state before replacing protected credentials. If protected-store/SQLite compensation fails, both runtime and durable state remain non-executable instead of reporting/retaining a stale `Verified` state.


## P04 customer import handling

Implemented in `v1.0.0.1.12`:

- structured CSV/TSV/XLSX/XLSM rows require a valid email cell and report row-numbered validation failures;
- optional country is accepted only as an explicit two-letter ASCII alphabetic code and is never guessed;
- name is never derived from email;
- duplicate identity is normalized lowercase email; same-file conflicting metadata is reported while the first accepted row remains authoritative;
- existing blank customer metadata can be enriched, but existing nonblank metadata is never silently overwritten;
- customer record persistence is transactional, so failed durable writes leave the previous in-memory/durable list unchanged;
- legacy `import_emails()` and email-only file behavior remain available for Stripe-compatible lists;
- Refrens production Task execution remains fail-closed pending P11 rather than being implicitly enabled by P04 data availability.

Malformed file/parser taxonomy beyond row validation remains a P12 hardening item (EH-028).

### v1.0.0.1.13 P04 correction

The P04 verification pass found that conflicts against already-stored customer metadata had lost their import row number, malformed workbook exceptions could escape the UI catch boundary, and the country test accepted non-ASCII alphabetic lookalikes. The correction preserves source-row metadata through merge diagnostics, wraps parser failures into the existing `ValueError` import contract, and restricts country to two ASCII alphabetic characters.
## v1.0.0.1.14 runtime/storage correction

The Windows migration-backup failure was traced to SQLite connection lifecycle rather than database corruption. `with sqlite3.connect(temp_backup)` did not close the destination connection before `Path.replace()`; Windows therefore rejected the rename because Invio itself still held the file. The destination is now explicitly closed in a `finally` block before replacement. A regression test enforces the close-before-replace ordering. No schema, provider, worker, task-state or future-roadmap behavior is added.


## P05 immutable execution-input handling

Implemented in `v1.0.0.1.15`:

- Task creation captures ordered recipients, copied invoice-template data, provider ID and ordered Account basis before the Task is committed. Task/reservations/snapshot rows share one transaction; a snapshot write failure rolls the whole Task creation back.
- `Task.total` is derived from the immutable recipient count. Runtime refuses execution when the stored total, provider, account order, assignment strategy or captured template/recipient state is inconsistent.
- Start/Retry use the stored Task snapshot and do not read current Customer List/Invoice Template content for that Task.
- Schema-v3 Tasks are migrated as `LegacyUnavailable` with no fabricated customer/template rows. Their Start/Retry actions are disabled and backend-gated; Close remains available so reservations can be released intentionally.
- Snapshot state contains no provider credential values. Existing protected Account credentials are resolved only through the normal P03-gated execution path.
- P05 does not claim P07 resend-state safety or P10 per-recipient delivery/restart reconciliation.
## v1.0.0.1.16 P05 verification correction

P05 creation/progress persistence is now fail-closed at both runtime-state and durable-storage boundaries. New Tasks must carry a captured snapshot; captured `processed/success/failed` values must agree; and the persisted Task total is not updated after creation. SQLite remains schema v4.

## P06 provider preflight handling

Implemented in `v1.0.0.1.17`:

- New Task candidate validation runs before Task persistence/account reservation; failed preflight has no provider network side effect.
- Start/Retry validation runs before injected/built-in runner creation and uses the existing P05 immutable snapshot rather than current mutable list/template data.
- Packaged provider-ID manifest/runtime mismatches fail closed and instruct explicit uninstall/reinstall instead of silently rewriting registry state.
- Unverified/incomplete/error-marked Account verification health, unsupported Account mode, missing required credentials, and Stripe key/mode mismatch fail locally.
- Stripe `BOS`, Automatic Tax under the current customer-location contract, and non-zero template percentage line tax under the current Stripe sender are rejected before invoice creation.
- Refrens normal Task capability remains unavailable until P11. Refrens endpoint trust is validated before App ID/App Secret payload construction.
- P06 does not classify network errors/retries or persist recipient attempt state; those remain P08/P10.
- P07 now protects deterministic current-session resend/continuation semantics, but does not persist failed/pending recipient identities; restart continuation remains fail-closed until P10.


## v1.0.0.1.18 P06 fail-closed corrections

P06 now also fail-closes packaged-manifest self-drift, preflight Account-input mismatch, Refrens unsupported currency, and any explicit Refrens port including `:443`. These failures occur before provider invoice/customer mutation.

## v1.0.0.1.19 P07 state/resend handling

P07 treats ambiguous resend actions as validation errors before a new worker is started. Completed Tasks cannot resend; Failed Tasks cannot normal-Start; Stopped Tasks can only Resume Remaining from an exact safe current-session continuation set; Retry Failed can only use an exact safe current-session failure set.

Controlled Stop reconciliation uses the same failed/pending sets to calculate persisted/UI counts. If recipient-level continuation becomes uncertain because of an unexpected runtime exception, or if the process restarts and the in-memory sets are lost, continuation is marked unavailable rather than reconstructed from aggregate counters. This avoids an accidental successful-recipient resend while leaving durable recovery to P10.

P07 does not add automatic network retry, backoff, HTTP cancellation, rate-limit behavior or provider-side reconciliation; those remain P08/P10.

## v1.0.0.1.20 P07 race/message corrections

- A late worker `Completed` signal can race with queued GUI Pause/Stop state. P07 now resolves that terminal event to existing `Stopped` when current state is `Paused`, `Stopping` or `Stopped`, preserving the approved transition matrix instead of raising an invalid-transition persistence error.
- Pause/Resume/Stop now fail before WorkerManager mutation when no active Task thread exists; the same active-worker fact disables those UI controls.
- A safe empty continuation is not an error and is no longer described as missing identity state. It simply has no Resume/Retry action because there are no unresolved recipients.
- This correction adds no network retry/error taxonomy, cancellation, durable recipient ledger or provider-side recovery; P08/P10 remain unchanged.

## v1.0.0.1.21 Provider Contract Fail-Closed Handling

- Unknown providers without an injected runner continue to fail with the existing runtime-unavailable path.
- Packaged manifest/runtime execution-contract drift fails preflight rather than trusting mutable metadata.
- Refrens Task execution continues to fail before provider-side mutation until P11.
- Agiled API Test and Task execution fail before network transport because its current authoritative API endpoint/authentication/send contract is unresolved. The configured Agiled API key is therefore not sent to a guessed endpoint.
- No retry/backoff/rate-limit/cancellation changes are introduced; those remain P08.

## v1.0.0.1.22 Verification Result

No new provider/API error-handling defect was found in the `v1.0.0.1.21` delta. Agiled still rejects API Test and Task execution before transport, and registry handler integrity is now explicitly regression-tested. P08 remains responsible for retry/backoff/rate-limit/timeout/cancellation/shutdown behavior.

## P08 Network and Worker Error Handling - v1.0.0.1.23

`ProviderRuntimeError` now carries `category`, `retryable`, optional `http_status`, and optional `retry_after_seconds` while remaining backward-compatible with existing message-only raises. Retryable transport failures are timeout/transient disconnect plus HTTP 408/429/500/502/503/504. Deterministic 4xx, invalid response shape/JSON and TLS certificate verification failures are permanent.

Automatic retry is recipient-scoped and bounded to three total attempts. Exponential delays are 0.5s then 1.0s before 0-25% jitter; Retry-After can extend the delay. Stop/Pause use cooperative Events rather than forced thread interruption. Unexpected recipient exceptions are recorded as one failed recipient and execution continues to the next recipient, preserving `processed = success + failed` for resolved recipients.


## 5. v1.0.0.1.24 P08 Verification Correction

The P08 re-audit reproduced two transport-classification gaps. `http.client.IncompleteRead` from a successful-status response body previously escaped `_stdlib_transport()` and bypassed automatic retry, and TLS EOF/clean-close exceptions were grouped with permanent TLS failures. The correction classifies those disconnect forms as retryable transient network failures while keeping certificate verification permanent. If an HTTP error body is truncated, the already-known HTTP status and Retry-After header remain authoritative.

No retry count, backoff, provider payload, Task state, WorkerManager, schema, dependency or P09+ handling is changed.


## 6. v1.0.0.1.25 P09 Scheduling/Health Error Policy

- Recognized Stripe `429` limiter reasons are account-scoped health incidents after P08 retry exhaustion; the account receives bounded runtime cooldown and only future unattempted recipients may use deterministic fallback.
- Timeout/disconnect/HTTP 408/5xx are provider/network incidents; the provider receives bounded runtime cooldown and account hopping is prohibited.
- HTTP 401/403 blocks additional network use of that runtime account until a successful account re-verification clears the runtime health.
- Deterministic 400/404/409/422/customer/template/operation failures do not cool, fail over or change account health.
- Rate/cooldown waits use the existing Pause/Stop-aware cooperative worker wait; no GUI-thread blocking or forced worker termination is introduced.


## 7. v1.0.0.1.26 CI repository-contract failure boundary

GitHub Actions run `31336019074` failed before application execution because `test_p09_completion_records_are_synchronized` directly opened a private file under `/project/`. That directory is intentionally excluded from public Git checkouts by `.gitignore`, so `FileNotFoundError` was deterministic in CI even though the full private baseline ZIP passed locally.

The correction does not change runtime exception handling. Repository contracts now require tracked public P09 completion records and only inspect private `project/` records when that private tree exists.

## 8. P10 durable delivery/recovery error handling - v1.0.0.1.27

P10 resolves the process-memory-only continuation gap for supported Stripe Tasks. Every Task provider request requires a committed `Started` operation row before transport. If that write fails, no request is sent. If provider execution occurs but the corresponding durable result cannot be committed, execution stops before another recipient/request; the prior `Started` evidence remains so restart recovery can classify a mutating outcome as `Uncertain` rather than guessing.

At startup, unfinished `Running` ledger runs become `Interrupted`; unresolved mutating operations become `Uncertain`, while read-only lookup uncertainty remains unresolved `Pending`. Latest durable recipient outcomes drive Task counter repair and continuation. Aggregate counters that claim outcomes unsupported by ledger evidence fail closed as inconsistent storage. Durable error records contain sanitized class/code/message only and never persist API keys, Authorization headers or provider credential payloads. P12 still owns generalized log/export/retention privacy and P14 owns live provider reconciliation/certification.

## 9. P10 uncertainty reconciliation correction - v1.0.0.1.28

`Started`/`Uncertain` mutating operations are no longer treated as permanently ambiguous when later durable evidence proves successful execution of the exact same stage with the same non-empty idempotency key. Conversely, a later deterministic failure at a different stage/key cannot erase an earlier unresolved mutating ambiguity. Durable continuation therefore stays fail-closed until ambiguity is genuinely reconciled. This changes no P08 retry classification or Stripe request behavior.

## P11 Refrens error/recovery rules - v1.0.0.1.29

- Refrens credentials are never constructed/transmitted until the configured base URL validates exactly as `https://api.refrens.com`.
- Missing email/name/country and Indian recipients without the unavailable GST State field fail before invoice creation.
- Authentication uses existing P08 retry classification and maximum-three-attempt policy.
- The invoice-create/email mutation is not blindly retried after timeout, disconnect, HTTP 408 or ambiguous 5xx; write-ahead P10 evidence remains `Uncertain`.
- Refrens 429/network/timeout/408/5xx enter provider-wide P09 cooldown; no speculative account hopping is introduced.
- A successful create response without `_id` is treated as uncertain rather than falsely reported as delivered.
- Durable `Uncertain` Refrens recipients are excluded from automatic Resume/Retry.

## P12 Export/Privacy Error Handling - v1.0.0.1.30

Task/recipient/log exports catch file/encoding/CSV failures at the UI boundary, emit a structured `ERROR/EXPORT` event and show a user-facing failure dialog instead of allowing the Qt handler to fail. Atomic sibling-temp writes protect an existing target from partial replacement. New durable provider error messages use centralized secret redaction before persistence. Historical ledger rows are not rewritten.


## P12 forensic correction - v1.0.0.1.31

The v1.0.0.1.30 baseline passed its existing tests but two support/privacy edge cases were reproducible. Quoted JSON-style secret fields were not matched by the named-secret regex unless the value was already known explicitly, and recipient reporting could infer provider acceptance from a recipient `Succeeded` result even with no durable send-stage success evidence. v1.0.0.1.31 corrects both paths and adds fail-closed historical account-evidence validation. No historical ledger rows are rewritten.

## P13 external adapter failure boundaries - v1.0.0.1.32

P13 contains adapter discovery/import/entrypoint/identity/version/profile/capability failures as non-executable runtime state instead of crashing application startup. API Test and Tasks fail closed when no validated executable adapter exists. Supported external non-idempotent mutations are never blindly retried after ambiguous network/408/5xx outcomes; P10 records `Uncertain`. Idempotent mutation retry requires a stable adapter-supplied provider idempotency reference. Adapter dependency/import failures do not trigger automatic installation.


## P13 external-adapter failure handling

| ID | Condition | Handling |
|---|---|---|
| EH-P13-01 | Staged/source adapter changes during install validation | Reject install; preserve prior registry state |
| EH-P13-02 | Adapter import/entrypoint raises, exits, or mutates `sys.path` | Contain failure, restore host path state, mark runtime Incompatible |
| EH-P13-03 | API Test returns without host-managed `SAFE_READ` | Verification fails closed |
| EH-P13-04 | Adapter reports recipient success without host-managed mutation/final-stage proof | Recipient execution fails closed |
| EH-P13-05 | Successful non-idempotent provider mutation followed by adapter/finalization interruption | Persist/recover recipient as `Uncertain`; never blind replay |

These rules introduce no schema migration and do not alter packaged Stripe/Refrens send behavior.

## P13 verification-correction failure boundaries - v1.0.0.1.33

- Adapter import and `create_adapter()` were already contained; v1.0.0.1.33 extends that boundary through adapter metadata/profile/scheduling/callable validation so `SystemExit`, `KeyboardInterrupt`-class `BaseException` or hostile conversion access cannot terminate startup. The provider becomes `Incompatible` with a diagnostic instead.
- External-provider uninstall now has an active-name rollback boundary. If the manifest move succeeds but the external adapter move fails, the manifest is restored before the error reaches the UI. Invio no longer reports an uninstall failure after silently losing the provider manifest.
- Temporary detached uninstall files are cleanup-only; cleanup failure does not convert a completed logical uninstall into a half-installed active provider.


## P14 candidate packaging/resource failures

`RuntimeResourceError` fails startup closed when an installed/source distribution is missing a required provider manifest or the checkmark asset. Wheel-content audit catches the same packaging defect before installation. This handling is deliberately narrow and does not convert unrelated application `RuntimeError` exceptions into resource failures. Native Windows/live-provider error certification remains pending evidence.

## v1.0.0.1.35 distribution error gates

| ID | Condition | Handling | Status |
|---|---|---|---|
| EH-036 | Nuitka OneDir lacks `main.exe` or a frozen provider/icon resource | preparation fails before portable/MSI publication | IMPLEMENTED |
| EH-037 | Git release tag does not exactly match `pyproject.toml` | release job fails before GitHub Release publication | IMPLEMENTED |
| EH-038 | WiX does not produce a non-empty MSI | Windows build fails; no release job runs | IMPLEMENTED |
| EH-039 | MSI silent install/run/uninstall smoke fails | Windows build fails; no tag release is published | IMPLEMENTED |
| EH-040 | portable/MSI/wheel/checksum inventory mismatches | distribution audit fails before artifact/release acceptance | IMPLEMENTED |

These build-time gates do not alter runtime provider/network error handling.


## v1.0.0.1.36 CI and SQLite handle correction

- GitHub source publication now fails regression if any approved `scripts/build` helper is missing; `.gitignore` explicitly re-includes that directory.
- `DomainStore._connect()` closes a SQLite connection if setup raises after `sqlite3.connect()` succeeds, then preserves the existing `DomainStoreError` / `DomainStoreCorruptionError` classification.
- The P14 subprocess crash-recovery test explicitly closes its post-crash SQLite verification query, avoiding Windows `WinError 32` during temporary-directory cleanup.
- No recovery classification, schema migration or delivery-ledger semantics change.


## v1.0.0.1.37 WiX version guard correction

GitHub Actions run `31374749523` showed a false-positive build guard rather than a WiX installation failure. The package manager installed pinned WiX `6.0.2`, while `wix --version` returned informational version `6.0.2+b3f3403`. The previous raw `-ne` string comparison treated the build metadata as a different tool version and aborted the pipeline. v1.37 trims the command output, removes only the optional `+build-metadata` portion for canonical comparison, and retains fail-closed behavior for a genuinely different core version. No runtime exception handling or application error path changes.

| EH-042 | WiX emits default `.wixpdb` beside the MSI, expanding the frozen release payload inventory | WiX build uses `-pdbtype none`; checksum/audit contracts remain fail-closed | IMPLEMENTED v1.0.0.1.38 |

## v1.0.0.1.40 live-provider correction

The owner-observed Refrens `terms` HTTP 400 is treated as a provider payload validation failure. The correction removes only the unsupported string-list request field; existing provider exception classification, Retry Failed safety and P10 ledger recording remain unchanged. Email-only missing name/country is prevented earlier by import-time default materialization rather than by guessing inside provider execution.

## v1.0.0.1.40.1 explicit Refrens email/build correction

Refrens create success is no longer treated as send acceptance. Invoice creation and the explicit `/invoices/:invoiceID/email` request are separate write-ahead mutations. A definitive email-trigger failure is reported as Failed and can reuse the durable invoice reference on Retry Failed; an ambiguous mutation remains Uncertain and is not blindly replayed. GitHub/Nuitka packaging no longer passes the duplicate custom keyring package configuration.

## v1.0.0.1.40.2 provider error-handling correction

Agiled API Test now performs one exact side-effect-free Bearer request to `GET https://api.agiled.ai/public/v1/me`. Provider HTTP failures continue through `ProviderRuntimeError`; no API key is logged or persisted outside the existing protected credential store. Agiled Task execution remains fail-closed before invoice transport because the supplied current OpenAPI does not define a field-level invoice mutation contract or invoice email/send operation.

For Refrens, the existing documented `/businesses/:urlKey/invoices/:invoiceID/email` operation is preserved. When a `ProviderRuntimeError` contains `http_status`, the provider log now emits a separate `CODE <status>` line. The live `HTTP 400: Not allowed to send mail` response is treated as a deterministic provider-side permission/capability rejection; it is not retried automatically, bypassed, or converted into provider acceptance.
