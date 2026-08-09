# Invio v1.0.0.1.19 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.19`  
**Official parent baseline:** reconstructed exact `Invio v1.0.0.1.18` from uploaded `Invio v1.0.0.1.17.zip` + verified v1.0.0.1.18 delta  
**Parent v1.0.0.1.18 non-cache tree SHA-256:** `858b477f98f4d4191a01cb5787d088cf8aa667320c628f47705d275f9954071c`  
**Scope:** P07 - Task State Machine and Resend Safety  
**Production phase count:** 7 / 14  
**Delta file count:** 42  
**Added files:** 8  
**Deleted parent files:** 0

## Functional implementation

- Adds a central Task state/action policy for `Ready`, `Running`, `Paused`, `Stopping`, `Stopped`, `Failed`, and `Completed`.
- First Run is available only for a pristine Ready Task.
- Stopped built-in Stripe continuation is **Resume Remaining** using only exact current-session failed + never-attempted recipients in the P05 immutable order.
- Failed built-in Stripe continuation is **Retry Failed** using only the exact current-session failed set; repeated retry shrinks to unresolved failures.
- Completed resend and Failed normal Start are blocked in UI/backend execution boundaries.
- Stop/final counters are reconciled from the same runtime failed/pending sets used to decide the next recipient subset.
- Application restart never fabricates recipient continuation identities from aggregate counters; Resume/Retry fails closed when the exact current-session set is unavailable.
- Existing injected runner first-run behavior remains; Retry/Resume continuation fails closed because the callback API exposes no exact recipient subset.
- P06 preflight remains mandatory before every permitted new worker attempt.
- Account reservations remain until existing Close Task release.

## Runtime/source files changed

- `src/tasks/state_machine.py` (new)
- `src/tasks/__init__.py`
- `src/core/state/app_state.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/provider_runtime/__init__.py`
- `src/core/storage/domain_store.py`
- `src/ui/main_window.py`
- `src/ui/pages/tasks_page.py`

## Test files changed

- `tests/test_task_state_machine.py` (new)
- `tests/test_provider_runtime.py`
- `tests/test_storage.py`
- `tests/test_ui_contracts.py`
- `tests/test_repository_contracts.py`

## Release/documentation records changed

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.19.md` (new)
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/P07_IMPLEMENTATION_LOG_v1.0.0.1.19.md` (new)
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.19.md` (new)
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.19.md` (new)
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.19.md` (new)
- `PATCH_MANIFEST_v1.0.0.1.19.md` (new)
- `pyproject.toml`
- `vibproject.ygit`

## Explicitly unchanged

- SQLite schema v4 and `src/core/storage/schema.py`
- WorkerManager and one-QThread-per-active-Task architecture
- ProviderManager and packaged `providers/packages/*` manifests
- CredentialStore/keyring mechanism
- Account/Customer/Invoice model trees
- P05 immutable Task snapshot format and Task.id logical run identity
- P06 provider capability/preflight contracts
- existing external `register_task_runner(provider_id, runner)` API
- Stripe/Refrens provider-send API semantics; Refrens normal Task execution remains P11
- `requirements.txt` and dependency versions
- unrelated UI pages, shared styles/tokens/widgets
- P08-P14 behavior

## Verification gate before packaging

- exact reconstructed parent v1.0.0.1.18 suite: **200/200 PASS**
- final v1.0.0.1.19 suite: **224/224 PASS**
- Python compile: **PASS**
- repository syntax/privacy/provider-visibility audit: **PASS**
- JSON/YGIT/TOML validation: **PASS**
- SQLite schema remains v4: **PASS**
- existing top-level Python symbol removal/rename count: **0**
- parent non-cache file deletion count: **0**
- protected out-of-scope source changes: **0**
- delta wrapper folder: **none**
- delta cache artifacts: **none**
- final parent + delta non-cache byte comparison: **PASS**
- fresh-overlay unit/contract suite: **224/224 PASS**
- fresh-overlay repository audit: **PASS**

Native PySide6 rendering, native OS keyring integration and owner-account live provider certification are not claimed by this environment.
