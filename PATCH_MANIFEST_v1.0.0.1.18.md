# Invio v1.0.0.1.18 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.18`  
**Official parent baseline:** exact uploaded `Invio v1.0.0.1.17.zip`  
**Parent ZIP SHA-256:** `6c9919f6ce7bd7030f4436b1b4707144f1d5db5be2e672fa1030ae71fce31936`  
**Scope:** P06 forensic verification/correction only  
**Production phase count:** 6 / 14  
**Delta file count:** 40  
**Added files:** 7  
**Deleted parent files:** 0

## Verified P06 corrections

- Independent hard-coded built-in manifest/runtime contract check prevents packaged Stripe/Refrens declarations from self-validating after execution-contract drift.
- Task preflight requires supplied Account IDs/order to equal the immutable P05 Account assignment basis.
- Refrens currency validation uses Invio's existing frozen invoice-currency catalogue; the catalogue is not broadened in this corrective release.
- Refrens endpoint trust accepts only canonical `https://api.refrens.com` (optional trailing slash), with no explicit port.
- Providers cards render the actual installed declaration and only report effective built-in runtime capability when installed, packaged and hard-coded runtime contracts agree.
- Provider-contract documentation no longer claims the 135-code Invio Stripe catalogue is a universal exact provider list.

## Runtime/release files changed

- `pyproject.toml`
- `src/core/provider_runtime/preflight.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/providers_page.py`
- `vibproject.ygit`

## Test files changed

- `tests/test_provider_preflight.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`

## Documentation/private release records changed

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.18.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/api/provider-manifest.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/guides/invoice-templates.md`
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.18.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.18.md`
- `project/research/P06_VERIFICATION_CORRECTION_v1.0.0.1.18.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.18.md`
- `project/research/PROVIDER_CONTRACT_REVALIDATION_v1.0.0.1.18.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.18.md`

## Explicitly unchanged

- SQLite schema v4 and `src/core/storage/*`
- WorkerManager and one-QThread-per-active-Task architecture
- Account/Customer/Invoice/Task model trees
- packaged `providers/packages/*` manifests
- `requirements.txt` and dependency versions
- P05 immutable Task snapshot architecture
- existing external `register_task_runner(provider_id, runner)` API
- Stripe/Refrens provider-send implementation semantics
- Refrens P11 normal Task gate
- P07-P14 feature state

## Verification gate

- exact parent v1.0.0.1.17 suite: **194/194 PASS**
- corrected v1.0.0.1.18 suite before packaging: **200/200 PASS**
- Python compilation: **PASS**
- repository syntax/privacy/provider-visibility audit: **PASS**
- JSON/YGIT/TOML validation: **PASS**
- SQLite schema remains v4: **PASS**
- existing top-level Python symbol removal/rename count: **0**
- parent non-cache file deletion count: **0**
- protected out-of-scope source changes: **0**
- delta wrapper folder: **none**
- delta cache artifacts: **none**
- final parent + delta byte comparison and fresh-overlay test/audit: required and performed before delivery

Native PySide6 rendering, native OS keyring integration and owner-account live provider certification are not claimed by this environment.
