# Invio v1.0.0.1.15 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.15`  
**Official parent baseline:** exact reconstructed `Invio v1.0.0.1.14` non-cache tree  
**Parent tree SHA-256:** `a44a794a96fffeaaeccd5c63ed5eeddbafbbd0d1a62a2568e043c2d83592bb58`  
**Scope:** P05 - Immutable Task Execution Snapshot and Input Consistency  
**Production phase count:** 5 / 14

## Functional implementation

- Adds durable immutable Task recipient/template/provider/account-order snapshots.
- Uses `Task.id` as the canonical logical run identity.
- Derives `Task.total` from the frozen recipient count.
- Makes ProviderRuntime Start/Retry consume the same frozen Task snapshot rather than live Customer List/Invoice Template data.
- Migrates pre-P05 Tasks to fail-closed `LegacyUnavailable` metadata without fabricating historical inputs.
- Keeps P06+, WorkerManager architecture, Stripe send semantics and Refrens P11 execution boundary unchanged.

## Runtime/source files changed

- `src/tasks/models/task.py`
- `src/tasks/models/__init__.py`
- `src/core/state/app_state.py`
- `src/core/storage/schema.py`
- `src/core/storage/domain_store.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/tasks_page.py`

## Test files changed

- `tests/test_state.py`
- `tests/test_storage.py`
- `tests/test_provider_runtime.py`
- `tests/test_ui_contracts.py`
- `tests/test_repository_contracts.py`

## Release/documentation records

README/CHANGELOG/ROADMAP/versioning/structure/compatibility plus relevant user, Task, Invoice Template, architecture, configuration, troubleshooting, developer and private production records are synchronized with P05.

New records include:

- `docs/release-notes/1.0.0.1.15.md`
- `project/research/P05_IMPLEMENTATION_LOG_v1.0.0.1.15.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.15.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.15.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.15.md`
- `PATCH_MANIFEST_v1.0.0.1.15.md`

## Explicitly unchanged

- ProviderManager
- WorkerManager and one-QThread-per-active-Task architecture
- CredentialStore/keyring mechanism and dependency versions
- Account model/lifecycle and P03 provider-install/verification gates
- CustomerRecord/import/storage behavior from P04
- Invoice Template source model/editor behavior
- provider manifests
- Stripe invoice/customer/send semantics except release User-Agent version text
- Refrens production Task runner remains disabled
- shared UI styles/tokens/widgets and unrelated pages
- `requirements.txt`
- P06-P14 features

## Final verification gate

- exact v1.0.0.1.14 baseline suite: **139/139 PASS**
- final v1.0.0.1.15 suite: **162/162 PASS**
- Python compile: PASS
- repository audit: PASS
- JSON/YGIT/TOML parse: PASS
- baseline Python symbol preservation: PASS
- protected out-of-scope hash comparison: PASS
- parent non-cache file deletion count: 0
- delta file count: **45**
- fresh parent + delta non-cache byte comparison: PASS
- delta wrapper folder: none
- delta cache artifacts: none

Native PySide6 rendering, native OS keyring integration and live Stripe/Refrens provider certification are not claimed by this environment.
