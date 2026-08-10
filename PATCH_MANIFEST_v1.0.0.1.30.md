# Invio v1.0.0.1.30 P12 Delta Patch Manifest

Parent baseline: `Invio v1.0.0.1.29`
Target: `Invio v1.0.0.1.30` P12 Reports, Logs, Privacy and Operational Observability

Scope: owner-approved P12 only. P11 remains IMPLEMENTED / LIVE ACCEPTANCE PENDING. SQLite remains schema v5 with exactly three P10 delivery-ledger tables.

## Replace-ready file inventory

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.30.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.30.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.30.md`
- `project/research/P12_IMPLEMENTATION_LOG_v1.0.0.1.30.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.30.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.30.md`
- `pyproject.toml`
- `src/core/observability.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/core/worker_manager/manager.py`
- `src/tasks/delivery_ledger.py`
- `src/ui/main_window.py`
- `src/ui/pages/logs_page.py`
- `src/ui/pages/reports_page.py`
- `tests/test_p12_observability.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Inventory summary

- Added relative to parent: **8** (including this manifest)
- Modified relative to parent: **28**
- Removed: **0**
- Total delta paths: **36**

The ZIP must be extracted at the project root with no wrapper directory. No cache/bytecode artifacts are part of the delta.
