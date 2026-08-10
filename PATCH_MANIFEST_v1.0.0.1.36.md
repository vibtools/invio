# Invio v1.0.0.1.36 P14 GitHub Actions CI Verification Correction Delta Patch Manifest

Parent Official source/build baseline: `Invio v1.0.0.1.35`
Target Official source/build baseline: `Invio v1.0.0.1.36`
Scope: confirmed P14 v1.35 GitHub Actions CI failure correction and exact version/documentation synchronization only.

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
- UI/UX and page inventory: **unchanged**

## Audited failing evidence

- GitHub Actions run: `31371279808`
- Tested commit: `12ef4800a75a993da3899399882f0e44daccd4df`
- Ubuntu job: `93400604928`
- Windows job: `93400604966`

Confirmed causes:
1. existing `.gitignore` `build/` pattern also ignored the intentional `scripts/build/` source helpers, so v1.35 Git staging omitted them;
2. P14 Windows crash-recovery test did not explicitly close its direct SQLite verification handle;
3. `DomainStore._connect()` could leave a partially initialized SQLite connection open when setup raised before return.

## Verification before seal

- Focused correction regression: **12/12 PASS**
- Full target regression: **381/381 PASS**
- `python scripts/test/audit.py`: **PASS**
- Wheel audit: **55 source modules / 4 exact runtime resources PASS**
- Isolated installed-wheel resource/provider probe: **PASS**
- Frozen contract comparison: **16/16 byte-identical**
- v1.35 `scripts/build` reconciliation bytes: **5/5 byte-identical**
- Git ignore simulation: `scripts/build/*` trackable; generated root `build/` still ignored
- Fresh parent-overlay comparison: **0 missing / 0 extra / 0 byte mismatch**
- Sealed private overlay: **381/381 PASS + audit PASS**
- Clean-public overlay: **381/381 PASS + audit PASS**

## Normal v1.35 -> v1.36 source delta

- Added: **7**
- Modified: **31**
- Removed: **0**
- Normal changed files: **38**

### Added
- `PATCH_MANIFEST_v1.0.0.1.36.md`
- `docs/release-notes/1.0.0.1.36.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.36.md`
- `project/research/P14_GITHUB_ACTIONS_CI_CORRECTION_v1.0.0.1.36.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.36.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.36.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.36.md`

### Modified
- `.github/workflows/ci.yml`
- `.gitignore`
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
- `src/core/storage/domain_store.py`
- `src/ui/main_window.py`
- `tests/test_p14_certification.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_storage.py`
- `vibproject.ygit`

## GitHub publication reconciliation — byte-identical to v1.35

These five paths are intentionally included in the delivery ZIP even though they are not source-byte changes from the Official v1.35 baseline. They existed in the v1.35 source baseline but were absent from GitHub commit `12ef4800...` because the prior `.gitignore` rule hid `scripts/build/`. Re-publishing them restores the approved v1.35 build-source state after the ignore rule is corrected.

- `scripts/build/.gitkeep`
- `scripts/build/finalize_release_checksums.py`
- `scripts/build/generate_wix_source.py`
- `scripts/build/prepare_windows_distribution.py`
- `scripts/build/version_info.py`

## Delivery archive inventory

- Normal changed paths: **38**
- Byte-identical GitHub reconciliation paths: **5**
- Total replace-ready ZIP paths: **43**
- Removed paths: **0**
- Wrapper directory: **none**
- Cache/generated files: **excluded**

`SHA256SUMS.txt` contains SHA-256 values for the other **42** payload paths and excludes itself by design.

## Certification truthfulness

This delta does not claim that v1.36 has already passed GitHub Windows/Nuitka/WiX/MSI execution. The exact v1.36 commit must run successfully after push before that external P14 evidence can be recorded. P14 therefore remains **CERTIFICATION PENDING**.
