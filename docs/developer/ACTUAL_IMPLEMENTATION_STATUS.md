# Actual Implementation Status

**Baseline:** `Invio v1.0.0.1.11`  
**Completed production phases:** P01, P02, P03  
**Purpose:** Record only behavior that exists in the current frozen source and explicit remaining production gaps.  
**Status values:** WORKING, PARTIAL, NOT IMPLEMENTED, BLOCKED.

## Current Summary

| Area | Status | Current reality |
|---|---|---|
| Vib Tools desktop shell/pages | WORKING | Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, Settings |
| Provider manifest install/load/uninstall | WORKING | Validated manifest registry workflow |
| Executable external provider plugin loading | NOT IMPLEMENTED | P13; ProviderManager still does not import/execute provider code |
| Stripe built-in invoice sending | WORKING locally by contract | Real HTTP path exists; live certification remains P14 |
| Refrens normal Task sending | BLOCKED | Current email-only customer contract cannot supply required country |
| Real Add Account API Test | WORKING | P01 real Stripe/Refrens verification on a dedicated dialog `QThread` |
| Durable Accounts metadata | WORKING | SQLite schema v2 restores IDs/provider/name/mode/status/verification health/credential reference |
| Protected provider credentials | WORKING by local contract | `keyring` only; no plaintext fallback; native OS integration certification remains P14 |
| Durable Customer Lists | WORKING | Lists and ordered email addresses restore after restart |
| Durable Invoice Templates | WORKING | Template fields/items/terms restore; Decimal values stored as text |
| Durable Tasks/reservations | WORKING | Task metadata, ordered accounts, counters/message and reservations restore |
| Active-task restart recovery | WORKING | Running/Paused/Stopping recover as existing `Stopped`; no auto-resume/send |
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
- Existing empty schema-v0 databases are backed up before migration through schema v1 to current schema v2; existing schema-v1 databases receive a dedicated pre-migration backup before v2 upgrade.
- Missing/unreadable protected credentials leave Account metadata visible but force runtime status `Not Verified`, preserving P01 Task gates.
- Previously active Tasks are not automatically resumed after process restart.
- Persistence failures are translated into existing `StateError`/user-facing handling; active task persistence failure requests WorkerManager stop.

### DELIBERATELY NOT P02

- No per-recipient delivery ledger, remote provider reconciliation, persisted provider customer/invoice IDs or persistent Retry Failed recipient set. These remain P10.
- Account Edit/Delete/Re-test and durable verification-health lifecycle are **WORKING in P03**. No age-based expiry/background polling is implemented.
- No Customer model name/country expansion. P04.
- No immutable Task execution snapshot. P05.
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

- Customer Lists remain email-only and live-mutable after Task creation. P04/P05.
- Bound Invoice Templates remain editable and runtime uses current template at Start/Retry. P05.
- Completed/Failed full-Start resend semantics remain unchanged. P07.
- Retry Failed remains process-memory only. P10.

## Threading / Worker

The existing WorkerManager is unchanged: one active Task owns one `QThread`; provider work stays out of the GUI thread. P02 adds local persistence calls around existing UI/state events but does not introduce a new sending worker model.

Remaining worker reliability work is P08/P09/P10.

## Current Certification Boundary

P01/P02/P03 unit/contract/source audits verify the implemented local contracts. Native Qt launch, native OS keyring behavior and live provider/restart failure certification are not represented as complete until P14.


### v1.0.0.1.11 P03 verification correction

**WORKING:** migration backups now include committed WAL state; startup credential-loss recovery durably keeps the Account `Not Verified` even if the protected secret later becomes readable again; Account Edit stages a durable fail-closed state before changing protected credentials and keeps runtime/durable state non-executable when compensation cannot restore the prior secret/metadata.

**UNCHANGED:** P03 remains 3/14 production phases complete; P04-P14 remain pending.
