# Invio v1.0.0.1.34 P14 Certification Candidate Delta Patch Manifest

Parent baseline: `Invio v1.0.0.1.33`
Target candidate: `Invio v1.0.0.1.34`
Scope: P14 - Live Integration, Recovery, Packaging and Production Certification
Status: **CERTIFICATION PENDING / NOT PRODUCTION READY**

- Added: 15
- Modified: 28
- Removed: 0
- Total delta files: 43
- SQLite schema: v5 unchanged
- P10 delivery-ledger tables: exactly 3 unchanged
- P11: IMPLEMENTED / LIVE ACCEPTANCE PENDING
- P14: CERTIFICATION PENDING
- Completed acceptance phases: 12/14
- Production-ready: NO
- Packaging technology: setuptools/wheel only
- New runtime dependencies: 0

## Executed candidate evidence

- Private regression/audit: 368/368 PASS + repository audit PASS
- Clean public regression/audit: 368/368 PASS + repository audit PASS
- Focused P08/P12/P14 evidence: 35/35 PASS
- 10,000-recipient import: PASS
- 1,000-recipient injected execution soak: PASS
- subprocess crash/restart uncertainty recovery: PASS
- wheel content: 55 source modules + 4 exact runtime resources PASS
- isolated wheel resource/provider/settings resolution: PASS

## Mandatory certification evidence still pending

- owner-controlled Stripe Test integration
- owner-controlled Stripe Live integration
- Refrens live API Test
- real Refrens invoice creation
- actual owner-controlled Refrens email receipt
- executed clean Windows wheel install/native PySide6/keyring/three-QThread smoke

## Delta paths

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.33_project_records_sync.md`
- `PATCH_MANIFEST_v1.0.0.1.34.md`
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
- `docs/release-notes/1.0.0.1.34.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.34.md`
- `project/research/P14_IMPLEMENTATION_AND_CERTIFICATION_LOG_v1.0.0.1.34.md`
- `project/research/P14_LIVE_INTEGRATION_MATRIX_v1.0.0.1.34.md`
- `project/research/P14_PACKAGING_CERTIFICATION_v1.0.0.1.34.md`
- `project/research/P14_WINDOWS_NATIVE_CERTIFICATION_v1.0.0.1.34.md`
- `project/research/PRIVATE_DEVELOPMENT_RECORDS_SYNC_v1.0.0.1.33.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.34.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.34.md`
- `pyproject.toml`
- `scripts/test/p14_wheel_audit.py`
- `scripts/test/p14_windows_smoke.py`
- `src/app.py`
- `src/core/paths.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/styles.py`
- `tests/test_p14_certification.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`
