# Invio v1.0.0.1.33 P13 Verification-Correction Delta Patch Manifest

Parent baseline: `Invio v1.0.0.1.32`
Target: `Invio v1.0.0.1.33`
Scope: P13 - Executable External Provider Adapter Contract forensic verification correction

- Added: 6
- Modified: 28
- Removed: 0
- Total delta files: 34
- SQLite schema: v5 unchanged
- P10 delivery-ledger tables: exactly 3 unchanged
- P11 live acceptance: pending
- P13: COMPLETE / verification-corrected
- P14: not implemented

## Corrected P13 defects

1. Post-entrypoint adapter metadata/profile/scheduling/callable `BaseException` is normalized to fail-closed `ExternalAdapterError`/`Incompatible` state rather than being able to terminate startup discovery.
2. External-provider uninstall uses staged active registry moves and restores the manifest if the adapter move fails, preventing half-uninstalled manifest/adapter state.

## Delta paths

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.33.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.33.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.33.md`
- `project/research/P13_VERIFICATION_CORRECTION_v1.0.0.1.33.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.33.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.33.md`
- `pyproject.toml`
- `src/core/provider_manager/manager.py`
- `src/core/provider_runtime/external.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `tests/test_p13_external_adapters.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`
