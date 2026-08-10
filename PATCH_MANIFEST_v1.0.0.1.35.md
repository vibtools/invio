# Invio v1.0.0.1.35 P14 Distribution Verification Delta Patch Manifest

Parent baseline: `Invio v1.0.0.1.34`
Target source/build baseline: `Invio v1.0.0.1.35`
Scope: P14 certification-candidate forensic verification plus owner-approved Nuitka OneDir / WiX MSI / GitHub distribution-release pipeline.

- Added: 18
- Modified: 28
- Removed: 0
- Total delta files: 46
- SQLite schema: v5 unchanged
- P10 delivery-ledger tables: exactly 3 unchanged
- P11: IMPLEMENTED / LIVE ACCEPTANCE PENDING
- P14: CERTIFICATION PENDING
- Production-ready: NO
- Runtime dependencies: unchanged

## Delta paths

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.35.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/getting-started/installation.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.35.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.35.md`
- `project/research/P14_DISTRIBUTION_VERIFICATION_CORRECTION_v1.0.0.1.35.md`
- `project/research/P14_IMPLEMENTATION_AND_CERTIFICATION_LOG_v1.0.0.1.35.md`
- `project/research/P14_LIVE_INTEGRATION_MATRIX_v1.0.0.1.35.md`
- `project/research/P14_PACKAGING_CERTIFICATION_v1.0.0.1.35.md`
- `project/research/P14_WINDOWS_DISTRIBUTION_PIPELINE_v1.0.0.1.35.md`
- `project/research/P14_WINDOWS_NATIVE_CERTIFICATION_v1.0.0.1.35.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.35.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.35.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.35.md`
- `pyproject.toml`
- `scripts/build/finalize_release_checksums.py`
- `scripts/build/generate_wix_source.py`
- `scripts/build/prepare_windows_distribution.py`
- `scripts/build/version_info.py`
- `scripts/test/p14_distribution_audit.py`
- `scripts/test/p14_wheel_audit.py`
- `src/core/paths.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Distribution contract

- Normal push/PR: Ubuntu regression/wheel + Windows regression/wheel/native smoke + Nuitka OneDir + portable ZIP + WiX MSI + distribution artifact.
- Matching release tag: publish portable ZIP, MSI, wheel and `SHA256SUMS.txt` after gated jobs pass.
- Nuitka/WiX are build-only and are not application runtime dependencies.
- MSI is per-user LocalAppData to preserve the existing writable P13 provider registry.

The tag/live/native certification gates are not fabricated as PASS in this delta.
