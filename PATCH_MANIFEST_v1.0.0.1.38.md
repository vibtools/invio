# Invio v1.0.0.1.38 P14 WiX Debug-Symbol Release Inventory Correction Delta Patch Manifest

Parent Official source/build baseline: `Invio v1.0.0.1.37`

Target Official source/build baseline candidate: `Invio v1.0.0.1.38`

Scope: correction of the confirmed GitHub Actions release-inventory failure in run `31386258538` / Windows job `93447256779`, plus v1.38 release identity and directly related regression/documentation synchronization only.

## Status

- P11: **IMPLEMENTED / LIVE ACCEPTANCE PENDING**
- P14: **CERTIFICATION PENDING**
- Completed acceptance phases: **12/14**
- Production-ready: **NO**
- SQLite schema: **v5 unchanged**
- P10 delivery-ledger tables: **exactly 3 unchanged**
- Runtime dependencies: **unchanged**
- Provider business/send behavior: **unchanged**
- WorkerManager / Task thread architecture: **unchanged**
- P13 external adapter interface: **v1 unchanged**
- UI/UX and page inventory: **unchanged**
- WiX package pin: **6.0.2 unchanged**
- Nuitka pin: **4.1.3 unchanged**

## Audited failure evidence

- GitHub Actions run: `31386258538`
- Windows job: `93447256779`
- Tested commit: `fca2da3e4bb6d19687f2c85f48911d7ade7501ba`
- Full v1.37 regression: **383/383 PASS**
- Wheel/native PySide6/keyring/resource smoke: **PASS**
- Nuitka OneDir + portable preparation + compiled startup smoke: **PASS**
- WiX `6.0.2` installation: **PASS**
- MSI build: **PASS**
- MSI clean install/run/uninstall smoke: **PASS**
- Failure stage: **Assemble release payloads and checksums**
- Unexpected file: `Invio_v1.0.0.1.37_windows_x64_setup.wixpdb`

## Exact correction

The existing WiX build command adds only `-pdbtype none`. The approved release directory remains portable ZIP + MSI + wheel + `SHA256SUMS.txt`. The checksum writer and distribution auditor are intentionally unchanged so unexpected files still fail closed.

## Verification before seal

- Targeted verification cycle 1: Primary P14 workflow/distribution correction tests **PASS**; one historical current-workflow version assertion required synchronization.
- Targeted verification cycle 2: **57/57 PASS**.
- Additional targeted fix/retry cycles: **0**.
- Final `python scripts/test/audit.py`: **PASS**
- Final regression: **385/385 PASS**
- Syntax audit: **PASS**
- Repository privacy contract: **PASS**
- Provider visibility contract: **PASS**
- Removed/renamed baseline files: **0**
- Frozen checksum/auditor/runtime/dependency/provider/schema/thread contracts: **verified unchanged except required release markers**
- Wrapper directory: **none**
- Fresh parent + delta overlay: **0 missing / 0 extra / 0 byte mismatch PASS**
- Cache/generated files: **excluded**

## v1.37 -> v1.38 delta

### Added
- `PATCH_MANIFEST_v1.0.0.1.38.md`
- `docs/release-notes/1.0.0.1.38.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.38.md`
- `project/research/P14_WIXPDB_RELEASE_INVENTORY_CORRECTION_v1.0.0.1.38.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.38.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.38.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.38.md`

### Modified
- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
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
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Delivery archive inventory

- Added paths: **7**
- Modified paths: **27**
- Removed paths: **0**
- Total replace-ready ZIP paths: **34**
- Wrapper directory: **none**
- Cache/generated files: **excluded**

`SHA256SUMS.txt` contains SHA-256 values for the other **33** delta payload paths and excludes itself by design.

## Certification truthfulness

The v1.38 source correction is locally verified, but P14 is not marked complete. The exact pushed v1.38 Windows workflow must complete final checksum audit and Windows artifact upload successfully. Owner-controlled live provider acceptance gates also remain outstanding.
