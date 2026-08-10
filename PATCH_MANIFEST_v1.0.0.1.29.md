# Invio v1.0.0.1.29 P11 Delta Patch Manifest

Parent Official Baseline: `Invio v1.0.0.1.28`
Target: `Invio v1.0.0.1.29` P11 implementation candidate
Phase status: **IMPLEMENTED / LIVE ACCEPTANCE PENDING**
Production progress: **10 / 14 complete**

This is a project-root replace-ready delta. No wrapper directory is required. No baseline file is deleted by this patch. P11 must not be marked COMPLETE until the owner live Refrens API Test, real invoice creation and recipient email-delivery gate passes.

## Inventory

- Added: **7**
- Modified: **33**
- Removed: **0**
- Total delta files: **40**

## Added

- `PATCH_MANIFEST_v1.0.0.1.29.md`
- `docs/release-notes/1.0.0.1.29.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.29.md`
- `project/research/P11_IMPLEMENTATION_LOG_v1.0.0.1.29.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.29.md`
- `project/specifications/P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.29.md`
- `tests/test_p11_refrens_task.py`

## Modified

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
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `pyproject.toml`
- `src/core/provider_runtime/adapters.py`
- `src/core/provider_runtime/preflight.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/tasks/delivery_ledger.py`
- `src/ui/main_window.py`
- `tests/test_p09_scheduling.py`
- `tests/test_provider_adapter_registry.py`
- `tests/test_provider_preflight.py`
- `tests/test_provider_runtime.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Removed

- None.

## Exact replace-ready paths

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.29.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.29.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.29.md`
- `project/research/P11_IMPLEMENTATION_LOG_v1.0.0.1.29.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.29.md`
- `project/specifications/P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.29.md`
- `pyproject.toml`
- `src/core/provider_runtime/adapters.py`
- `src/core/provider_runtime/preflight.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/tasks/delivery_ledger.py`
- `src/ui/main_window.py`
- `tests/test_p09_scheduling.py`
- `tests/test_p11_refrens_task.py`
- `tests/test_provider_adapter_registry.py`
- `tests/test_provider_preflight.py`
- `tests/test_provider_runtime.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`
