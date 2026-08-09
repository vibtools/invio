# Invio v1.0.0.1.20 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.20`  
**Official parent baseline:** exact uploaded `Invio v1.0.0.1.19.zip`  
**Parent ZIP SHA-256:** `3dccf28aa27672af720d6dd9981aeb5b4b10b564f16522ba760f33040fdbe828`  
**Parent non-cache tree SHA-256:** `563538088716f67f92bfd8d75c92b82d5efaf62f0929be64c14d2886fd4da9d3`  
**Scope:** P07 forensic verification/correction  
**Production phase count:** 7 / 14
**Delta file count:** 37  
**Added files:** 6  
**Deleted parent files:** 0  

## Functional correction

- Resolves the P07 late worker-terminal versus accepted Pause/Stop state race without expanding the approved transition table.
- Disables and backend-blocks Pause/Resume/Stop when the Task's existing WorkerManager thread is no longer active.
- Distinguishes safe exact empty continuation from unavailable recipient identity state.
- Preserves existing First Run, Resume Remaining and Retry Failed recipient-selection behavior.

## Runtime/source change boundary

- `src/tasks/state_machine.py`
- `src/tasks/__init__.py`
- `src/ui/main_window.py`
- `src/core/provider_runtime/runtime.py` (release User-Agent marker only)

WorkerManager, AppState, DomainStore, storage schema, ProviderManager and P06 preflight are unchanged.

## Regression coverage

P07 tests add coverage for:

- late Completed signal reconciliation while retaining the original transition table;
- active-worker-dependent Running/Paused control policy;
- safe-empty stopped continuation;
- stop-after-last-success ProviderRuntime summary;
- MainWindow controller/source contracts for active-worker guards and accurate safe-empty messages.

## Documentation/release records

Public README/changelog/roadmap/versioning/compatibility, user/developer/task/provider/troubleshooting documentation and release metadata are synchronized. Private architecture, roadmap, phase log, forensic correction, final verification, readiness and baseline freeze records are synchronized.

## Explicitly unchanged

- SQLite schema v4 and all schema migrations.
- WorkerManager implementation/thread architecture.
- P05 immutable Task snapshot contract.
- P06 provider preflight/capability contract.
- Account/Customer/Invoice behavior.
- provider manifests and send semantics.
- external runner registration API.
- dependencies and P08-P14 behavior.

## Verification before final packaging

- exact parent suite: **224/224 PASS**;
- corrected suite: **230/230 PASS**;
- Python compile: PASS;
- repository audit: PASS;
- JSON/YGIT/TOML parsing: PASS;
- existing top-level Python symbol removals/renames: 0;
- final fresh-overlay test/audit and cache-free delta checks: **PASS** (revalidated after final manifest content).
