# Invio v1.0.0.1.37 P14 WiX Version Verification Correction Delta Patch Manifest

Parent Official source/build baseline: `Invio v1.0.0.1.36`

Target Official source/build baseline candidate: `Invio v1.0.0.1.37`

Scope: correction of the confirmed GitHub Actions WiX Toolset version-verification false failure in run `31374749523` / Windows job `93411358955`, plus the explicitly requested v1.37 release identity and directly related regression/documentation synchronization only.

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

- GitHub Actions run: `31374749523`
- Windows job: `93411358955`
- Tested commit: `3fb7017bb56c7f65328c58e1195df8927944bda5`
- Full v1.36 regression before WiX step: **381/381 PASS**
- Wheel/native PySide6/keyring/resource smoke: **PASS**
- Nuitka OneDir build: **PASS**
- Portable preparation: **PASS**
- Compiled OneDir startup smoke: **PASS**
- `dotnet tool install --global wix --version 6.0.2`: **SUCCESS**
- `wix --version`: `6.0.2+b3f3403`
- Failure source: raw exact-string version comparison in `.github/workflows/ci.yml`

## Exact correction

The workflow keeps the exact WiX `6.0.2` package pin and normalizes only an optional SemVer `+build-metadata` suffix before comparing the CLI informational version with `WIX_VERSION`.

A genuinely different canonical core version still fails through the existing stale-version guard.

## Verification before seal

- Targeted correction verification cycle 1: Primary WiX workflow regression **PASS**; one newly added documentation assertion exposed a Markdown text-form mismatch.
- Targeted correction verification cycle 2: exact documentation assertion correction **PASS**.
- Additional targeted fix/retry cycles: **0**
- Final `python scripts/test/audit.py`: **PASS**
- Final regression: **383/383 PASS**
- Syntax audit: **PASS**
- Repository privacy contract: **PASS**
- Provider visibility contract: **PASS**
- Removed/renamed baseline files: **0**
- Frozen runtime/dependency/provider/schema/thread contracts: **verified unchanged**
- Fresh parent + delta overlay: **0 missing / 0 extra / 0 byte mismatch PASS**
- Wrapper directory: **none**
- Cache/generated files: **excluded**

## v1.36 -> v1.37 delta

### Added
- `PATCH_MANIFEST_v1.0.0.1.37.md`
- `docs/release-notes/1.0.0.1.37.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.37.md`
- `project/research/P14_WIX_VERSION_VERIFICATION_CORRECTION_v1.0.0.1.37.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.37.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.37.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.37.md`

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

The v1.37 source correction is locally verified, but P14 is not marked complete. The exact pushed v1.37 Windows workflow must pass the corrected guard and the MSI/checksum/artifact stages that were skipped in the failed v1.36 job. Owner-controlled live provider gates also remain outstanding.
