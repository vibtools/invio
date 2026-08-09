# Actual Implementation Status

**Baseline:** `Invio v1.0.0.1.16`  
**Completed production phases:** P01, P02, P03, P04, P05  
**Purpose:** Record only behavior that exists in the current frozen source and explicit remaining production gaps.  
**Status values:** WORKING, PARTIAL, NOT IMPLEMENTED, BLOCKED.

## Current Summary

| Area | Status | Current reality |
|---|---|---|
| Vib Tools desktop shell/pages | WORKING | Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, Settings |
| Provider manifest install/load/uninstall | WORKING | Validated manifest registry workflow |
| Executable external provider plugin loading | NOT IMPLEMENTED | P13; ProviderManager still does not import/execute provider code |
| Stripe built-in invoice sending | WORKING locally by contract | Real HTTP path exists; live certification remains P14 |
| Refrens normal Task sending | BLOCKED | P04 can store explicit name/country, but the production Refrens Task runner remains P11 |
| Real Add Account API Test | WORKING | P01 real Stripe/Refrens verification on a dedicated dialog `QThread` |
| Durable Accounts metadata | WORKING | Current SQLite schema v4 restores IDs/provider/name/mode/status/verification health/credential reference; account-health columns originated in schema v2 |
| Protected provider credentials | WORKING by local contract | `keyring` only; no plaintext fallback; native OS integration certification remains P14 |
| Durable Customer Lists | WORKING | Ordered customer records restore after restart; email mandatory, optional explicit name/country |
| Durable Invoice Templates | WORKING | Template fields/items/terms restore; Decimal values stored as text |
| Durable Tasks/reservations | WORKING | Task metadata, ordered accounts, counters/message, reservations and P05 immutable execution snapshots restore |
| Active-task restart recovery | WORKING | Running/Paused/Stopping recover as existing `Stopped`; no auto-resume/send |
| Immutable Task execution inputs | WORKING | P05 freezes ordered recipients, copied template, provider ID and account-assignment basis at Task creation; Start/Retry reuse it |
| Dedicated worker thread per active Task | WORKING | Existing one-`QThread`-per-Task WorkerManager unchanged |
| Retry Failed after app restart | NOT IMPLEMENTED | ProviderRuntime failed-recipient set is still process memory; P10 |
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
- No provider capability preflight. P06.
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
- Completed/Failed full-Start resend semantics remain unchanged. P07.
- Retry Failed remains process-memory only. P10.

## Threading / Worker

The existing WorkerManager is unchanged: one active Task owns one `QThread`; provider work stays out of the GUI thread. P02 adds local persistence calls around existing UI/state events but does not introduce a new sending worker model.

Remaining worker reliability work is P08/P09/P10.

## Current Certification Boundary

P01-P05 unit/contract/source audits verify the implemented local contracts. Native Qt launch, native OS keyring behavior and live provider/restart failure certification are not represented as complete until P14.


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

**STILL NOT IMPLEMENTED:** P06 provider preflight, P07 state-machine/resend hardening, P08/P09 network/scheduling hardening, P10 durable recipient delivery ledger/retry recovery, P11 Refrens Task enablement, P12 observability/privacy completion, P13 executable external adapters, P14 native/live production certification.

**Production progress:** 5/14 phases complete. Next separately approved phase: P06.
## v1.0.0.1.16 P05 Verification Correction

**WORKING / VERIFIED:** New post-P05 Tasks cannot be persisted without a real captured immutable execution snapshot; `LegacyUnavailable` is migration-only. Captured progress is checked against the frozen recipient set during state updates and startup load, and routine Task status/progress writes no longer mutate the persisted immutable total. P05 remains complete; P06 is not implemented.

