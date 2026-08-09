# Actual Implementation Status

**Baseline:** `Invio v1.0.0.1.25`  
**Completed production phases:** P01, P02, P03, P04, P05, P06, P07, P08  
**Purpose:** Record only behavior that exists in the current frozen source and explicit remaining production gaps.  
**Status values:** WORKING, PARTIAL, NOT IMPLEMENTED, BLOCKED.

## Current Summary

| Area | Status | Current reality |
|---|---|---|
| Vib Tools desktop shell/pages | WORKING | Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, Settings |
| Provider manifest install/load/uninstall | WORKING | Validated manifest registry workflow |
| Executable external provider plugin loading | NOT IMPLEMENTED | P13; ProviderManager still does not import/execute arbitrary provider code; v1.0.0.1.21 adds only an internal packaged-provider adapter registry |
| Stripe built-in invoice sending | WORKING locally by contract | Real HTTP path exists; live certification remains P14 |
| Refrens normal Task sending | BLOCKED | P04 can store explicit name/country, but the production Refrens Task runner remains P11 |
| Real Add Account API Test | WORKING/PARTIAL by provider | Stripe/Refrens verification is real on a dedicated dialog `QThread`; Agiled intentionally fails closed pending contract revalidation |
| Durable Accounts metadata | WORKING | Current SQLite schema v4 restores IDs/provider/name/mode/status/verification health/credential reference; account-health columns originated in schema v2 |
| Protected provider credentials | WORKING by local contract | `keyring` only; no plaintext fallback; native OS integration certification remains P14 |
| Durable Customer Lists | WORKING | Ordered customer records restore after restart; email mandatory, optional explicit name/country |
| Durable Invoice Templates | WORKING | Template fields/items/terms restore; Decimal values stored as text |
| Durable Tasks/reservations | WORKING | Task metadata, ordered accounts, counters/message, reservations and P05 immutable execution snapshots restore |
| Active-task restart recovery | WORKING | Running/Paused/Stopping recover as existing `Stopped`; no auto-resume/send |
| Immutable Task execution inputs | WORKING | P05 freezes ordered recipients, copied template, provider ID and account-assignment basis at Task creation; Start/Retry reuse it |
| Dedicated worker thread per active Task | WORKING | Existing one-`QThread`-per-Task WorkerManager unchanged |
| Worker/network reliability | WORKING | P08 structured retry classification, bounded retry/backoff/jitter, Retry-After, explicit timeout policy and safe asynchronous shutdown; v1.0.0.1.24 corrects truncated-body/TLS-close transient classification |
| Retry Failed / Resume Remaining in current session | WORKING | P07 uses exact ProviderRuntime failed/pending sets and immutable P05 ordering |
| Retry Failed / Resume Remaining after app restart | NOT IMPLEMENTED | Exact recipient identities are deliberately not guessed; P10 durable ledger/recovery |
| Recipient delivery ledger/provider IDs | NOT IMPLEMENTED | P10 |
| Settings persistence | WORKING | Existing non-sensitive JSON remains separate from P02 storage |

## P02 Durable Storage

### v1.0.0.1.9 P02 verification corrections

- Persistence-failure handling now records the task fault before requesting Stop, so a synchronous `Stopping` status signal cannot recursively re-enter the same failing persistence path.
- Startup validation now requires every persisted Task account selection to have exactly one matching reservation and rejects conflicting/missing reservation state as unsafe operational storage.
- P02 scope remains otherwise unchanged; production progress stays 2/14 and P03 remains next.


**Files:** `src/core/storage/schema.py`, `domain_store.py`, `credential_store.py`, `src/core/state/app_state.py`, `src/ui/main_window.py`, `src/app.py`

### WORKING

- Per-user `domain.sqlite3` is created beside the existing per-user `settings.json`.
- SQLite schema version is tracked with `PRAGMA user_version`.
- `foreign_keys=ON`, `journal_mode=WAL`, and `synchronous=FULL` are part of the storage contract.
- Account metadata stores only an opaque `credential_ref`; credential values are not columns in the database.
- Customer email order, template item/term order, and Task account order are persisted explicitly.
- Account reservation creation is transactional with Task creation. Task close transactionally deletes the Task and releases reservations.
- Template parent/items/terms and customer email replacement are committed transactionally.
- Startup integrity/schema validation rejects corrupt, unknown unversioned, and newer unsupported schemas without silently replacing them.
- Existing empty schema-v0 databases are backed up before migration through schema v1/v2/v3 to current schema v4; existing supported databases receive dedicated WAL-aware pre-migration backups before upgrade.
- Missing/unreadable protected credentials leave Account metadata visible but force runtime status `Not Verified`, preserving P01 Task gates.
- Previously active Tasks are not automatically resumed after process restart.
- Persistence failures are translated into existing `StateError`/user-facing handling; active task persistence failure requests WorkerManager stop.

### DELIBERATELY NOT P02

- No per-recipient delivery ledger, remote provider reconciliation, persisted provider customer/invoice IDs or persistent Retry Failed recipient set. These remain P10.
- Account Edit/Delete/Re-test and durable verification-health lifecycle are **WORKING in P03**. No age-based expiry/background polling is implemented.
- Customer record name/country expansion is **WORKING in P04**; no billing/shipping/payment expansion was added.
- Immutable Task execution snapshots are **WORKING in P05**; pre-P05 Tasks migrate as fail-closed `LegacyUnavailable` records.
- Provider capability/preflight is **WORKING in P06**; P07 Task state/resend semantics are now **WORKING for exact current-session built-in continuation sets**.
- No task-state-machine redesign, retry/backoff/rate-limit engine, multi-account concurrency/failover, report/privacy redesign, or external executable adapter system.


### v1.0.0.1.10 P03

**WORKING:** reservation-safe Account Edit/Delete, non-blocking Re-test, schema-v2 verification health, protected-credential rollback/restore handling, uninstalled-provider account visibility, active-Task uninstall block, and Task Start/Retry provider-installed gate.

**NOT CLAIMED:** automatic verification expiry, continuous health monitoring, send-time auth-health mutation, customer data upgrade, immutable Task inputs, retry/rate-limit engine, recipient delivery ledger, or live provider/native keyring certification.

## Provider / Accounts

### WORKING

- Provider manifest discovery/install/uninstall behavior is unchanged.
- Stripe/Refrens P01 API Test remains real and non-blocking.
- Successful Add Account persists its verified Account metadata and credentials only after protected credential storage succeeds.
- Database failure after credential write triggers compensating protected-credential deletion; cleanup failure is surfaced.
- Unverified/restored-without-secret Accounts cannot create/start/retry a Task.

### REMAINING

- Account edit/delete/re-test, verification time/error metadata, and provider-uninstall Task consistency are **WORKING in P03**.
- External executable provider adapters are P13.

## Customer Lists / Invoice Templates / Tasks

### WORKING

- Existing create/import/save/delete workflows now write durable state before mutating the authoritative in-memory collection.
- Restart reconstructs the same non-sensitive IDs, labels, ordering and Task relationships.
- Task status/progress/message updates are persisted.

### REMAINING

- Customer Lists remain editable/importable, but P05 freezes each new Task's creation-time customer records so later changes do not affect that Task.
- Bound Invoice Templates remain editable, but P05 Start/Retry use the Task's frozen template copy rather than the current template.
- Completed full resend and Failed normal Start are blocked by P07; Stopped uses Resume Remaining only when an exact safe current-session continuation set exists.
- Retry Failed / Resume Remaining recipient identities remain process-memory only; durable restart recovery remains P10.

## Threading / Worker

The existing WorkerManager remains one active Task per `QThread`; provider work stays out of the GUI thread. P08 adds bounded recipient retry, transport failure classification and safe asynchronous shutdown inside that same boundary. P09 still owns account scheduling/health/failover policy and P10 owns durable recipient-attempt/recovery state.

## Current Certification Boundary

P01-P08 unit/contract/source audits verify the implemented local contracts. Native Qt launch, native OS keyring behavior and live provider/restart failure certification are not represented as complete until P14.


### v1.0.0.1.11 P03 verification correction

**WORKING:** migration backups now include committed WAL state; startup credential-loss recovery durably keeps the Account `Not Verified` even if the protected secret later becomes readable again; Account Edit stages a durable fail-closed state before changing protected credentials and keeps runtime/durable state non-executable when compensation cannot restore the prior secret/metadata.

**UNCHANGED by the v1.0.0.1.11 corrective release:** P03 remained 3/14 at that historical point.


## v1.0.0.1.12 P04 Customer Data Contract

**WORKING:** `CustomerRecord` stores mandatory normalized email plus optional explicit name and uppercase two-letter ASCII country. Existing `CustomerList.emails`, `AppState.add_emails()` and `import_emails()` remain backward-compatible. Structured CSV/TSV/XLSX/XLSM imports recognize `email`, `name`, `country`; legacy files without an `email` header and TXT retain email extraction. Invalid structured rows, malformed import files, same-file conflicts, and existing-list metadata conflicts are reported; existing blank metadata can be enriched without silently overwriting nonblank values. SQLite schema v3 persists ordered records and migrates schema-v2 email rows with blank metadata. Task runtime snapshots carry customer records while Stripe execution continues to use email exactly as before.

**BLOCKED/REMAINING:** Refrens production Task execution remains P11. Customer Lists remain mutable after Task creation until P05. Manual per-record edit/delete UI, billing/shipping/payment fields, recipient delivery ledger, retry/rate-limit work and live certification are not part of P04.

**Production progress:** 4/14 phases complete. Next separately approved phase: P05.

## v1.0.0.1.13 P04 Verification Correction

**WORKING:** mutable `CustomerList.emails` compatibility is restored; import records retain source-row metadata through existing-list conflict reporting; country rejects non-ASCII two-letter lookalikes; malformed workbook/parser failures are contained in the import error boundary; the unrelated Dashboard label is restored to its pre-P04 wording.

**Production progress:** unchanged at 4/14 phases complete. P05 remains next and is not implemented here.
## v1.0.0.1.14 Operational Storage Runtime Hotfix

**WORKING:** the supported SQLite migration path still creates a WAL-aware pre-migration backup, and the temporary destination database is now explicitly closed before its atomic rename. This corrects the Windows `WinError 32` startup failure reproduced from the supplied screenshot.

**UNCHANGED:** schema v3, protected credentials, startup recovery semantics, ProviderRuntime send/API-test logic, WorkerManager, Customer/Invoice/Task/Account contracts and the 4/14 production-phase status. P05 is not implemented by this hotfix.


## v1.0.0.1.15 P05 Immutable Task Execution Snapshot

**WORKING:** every new Task captures a frozen provider ID, ordered Account basis, `recipient_ordinal_round_robin_v1` assignment strategy, ordered customer records and complete invoice-template copy at Task creation. `Task.total` is derived from the frozen recipient count. SQLite schema v4 persists snapshot metadata/customers/template/items/terms in the same transaction as Task/account reservations, and restart validates snapshot completeness/provider/account/total invariants before restoring operational state.

**WORKING:** ProviderRuntime Start/Retry converts only the Task's frozen snapshot into the existing runtime `TaskSnapshot`; it no longer reads live Customer List or Invoice Template content for an existing Task. `Task.id` is the canonical logical run identity; a different execution requires a new Task.

**MIGRATION:** pre-P05 schema-v3 Tasks remain present with status/counters/references/reservations but are marked `LegacyUnavailable`; original creation-time data is not fabricated from current list/template state. Their Start/Retry paths are disabled/gated while Close remains available.

**STILL NOT IMPLEMENTED:** P08/P09 network/scheduling hardening, P10 durable recipient delivery ledger/retry recovery, P11 Refrens Task enablement, P12 observability/privacy completion, P13 executable external adapters, and P14 native/live production certification.

**Production progress:** 5/14 phases complete. Next separately approved phase: P06.
## v1.0.0.1.16 P05 Verification Correction

**WORKING / VERIFIED:** New post-P05 Tasks cannot be persisted without a real captured immutable execution snapshot; `LegacyUnavailable` is migration-only. Captured progress is checked against the frozen recipient set during state updates and startup load, and routine Task status/progress writes no longer mutate the persisted immutable total. P05 remains complete; P06 is not implemented.

## P06 actual implementation - v1.0.0.1.17

**WORKING:** packaged Stripe/Refrens manifest declarations are reconciled with current built-in runtime capability before execution. Providers UI shows declared and runtime capability separately. External loaded manifests cannot use packaged IDs. Existing mismatched packaged-ID registry state fails closed without silent replacement.

**WORKING:** New Task, Start, and Retry perform local no-side-effect preflight. Account provider/status/verification timestamp/error/mode/required-credential state is checked; P05 frozen provider/account/template/customer data is used for existing Tasks. Stripe is preflighted as `INVOICE` only, Automatic Tax and non-zero template line tax are blocked under the current runtime/data contract, and Refrens Task execution remains P11.

**WORKING SECURITY BOUNDARY:** Refrens authentication accepts only the canonical `https://api.refrens.com` origin and rejects untrusted URL variants before the App ID/App Secret authentication payload is constructed.

**NOT IMPLEMENTED BY P07:** P08 retry/backoff/network reliability, P09 account scheduling/failover, P10 durable recipient delivery ledger/restart continuation, P11 Refrens normal Task execution, P12 observability/privacy completion, P13 executable external adapter architecture, and P14 live/native production certification.


## v1.0.0.1.18 P06 verification correction

P06 is COMPLETE and verification-corrected. Built-in packaged manifests must match hard-coded executable contracts; Task preflight validates frozen Account ordering; Refrens uses the safe currency catalogue and exact canonical endpoint; Providers displays installed declarations with effective runtime capability.

## v1.0.0.1.19 P07 status

**WORKING:** formal Task transition/action policy; pristine Ready-only First Run; same-worker Pause/Resume; exact current-session built-in Stripe Resume Remaining and Retry Failed; successful-recipient exclusion; repeated retry shrinkage; stop counter/runtime-set reconciliation; Completed resend blocking; Failed normal-Start blocking; injected-runner continuation fail-close; P06 preflight before every permitted new worker attempt; Account reservation retention until Close.

**INTENTIONALLY NOT DURABLE YET:** failed/pending recipient identity sets. After process restart Invio preserves aggregate status/counters but disables identity-based continuation rather than guessing. Durable recipient attempts, provider IDs, idempotency/recovery evidence remain P10.

**UNCHANGED:** SQLite schema v4, P05 immutable snapshots, P06 provider capability/preflight, WorkerManager one-QThread-per-active-Task architecture, packaged provider send semantics, Refrens P11 gate, dependencies and unrelated UI.

## v1.0.0.1.20 P07 verification correction

**WORKING:** P07 now reconciles the late-worker terminal race at the controller boundary: a queued `Completed` received after a valid late Pause/Stop state resolves to existing `Stopped`, so the approved transition table is not bypassed. Pause/Resume/Stop also require the existing WorkerManager thread to still be active.

**WORKING:** a current-session continuation can be proven safe but empty. That condition now reports that no recipients remain instead of using the separate restart/uncertain-state message. No send action is enabled for an empty set.

**HISTORICAL P07 NOTE:** exact continuation identities remain process-local and P10 still owns durable recipient recovery. SQLite remains schema v4. P08 network reliability is now implemented in v1.0.0.1.23 without changing the one-task-one-QThread architecture.

## v1.0.0.1.21 Current Provider Execution Status

| Provider | Manifest/package | API Test | Task invoice/send | Current status |
|---|---|---|---|---|
| Stripe | Working | Working | Working | Existing behavior preserved |
| Refrens | Working | Working | Blocked | P11 gate preserved |
| Agiled | Working | Fail-closed | Fail-closed | Authoritative API contract required |

The internal packaged-provider adapter registry is **WORKING**. Dynamic arbitrary external provider adapter discovery/loading is **NOT IMPLEMENTED** and remains P13. The v1.0.0.1.21 provider exception did not advance production progress; v1.0.0.1.23 subsequently completes P08 and advances progress to 8/14.

## v1.0.0.1.22 Verification Status

**VERIFIED:** the `v1.0.0.1.21` internal packaged-provider adapter registry, Stripe binding, Refrens P11 gate, Agiled package/manifest, declared-vs-executable capability separation, and Agiled no-transport fail-close behavior remain correct. Additional tests now cover Agiled package install/uninstall, runtime handler binding resolution, and the generic UI/API-test gate. No new executable Agiled capability is claimed.

## P08 status - v1.0.0.1.23; verification-corrected in v1.0.0.1.24

**WORKING:** structured network/provider retry classification, maximum three total recipient attempts, exponential backoff/jitter, Retry-After parsing, explicit 30-second shared urllib socket timeout, cooperative Pause/Stop-aware retry waits, per-recipient unexpected-exception isolation, and non-blocking application shutdown coordination that waits for task QThread completion.

**UNCHANGED / OUT OF SCOPE:** account failover and per-account rate scheduling (P09), persistent attempt/delivery ledger (P10), Refrens Task sending (P11), Agiled execution, external executable plugin loading (P13), SQLite schema v4 and dependencies.


### v1.0.0.1.24 P08 verification correction

**WORKING / CORRECTED:** truncated HTTP response bodies (`IncompleteRead`) and TLS EOF/clean-close interruptions now enter the same bounded transient retry path as other approved disconnects. HTTP error status/Retry-After metadata remains available even when its body is incomplete. Certificate-verification failures remain permanent.

**UNCHANGED:** three-total-attempt limit, backoff/jitter, one-task-one-QThread, account assignment, Stripe idempotency keys/business sequence, safe shutdown, P05-P07, schema v4, dependencies, Refrens P11 gate, Agiled fail-close and P09+ scope.

**Production progress:** 9/14; P10 is next only after separate approval.


## P09 status - v1.0.0.1.25

**WORKING.** The primary recipient/account mapping remains `recipient_ordinal_round_robin_v1`. Stripe Task requests use the internal 20 requests/second/account, burst-1 policy. Runtime-only account/provider health tracks bounded cooldowns; only unattempted recipients can use deterministic circular fallback for recognized account-scoped rate-limit cooldown. Attempted recipients never cross accounts, provider/network failures never account-hop, deterministic validation/customer/template failures never fail over, and HTTP 401/403 suppresses further network use until successful account re-verification. Intra-Task concurrency remains 1 and P10 persistence is not implemented.

**Production progress:** 9/14; P10 is next.
