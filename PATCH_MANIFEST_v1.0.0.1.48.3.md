# Invio v1.0.0.1.48.3 Replace-Ready Delta Patch Manifest

## Parent Official Baseline

`Invio_v1.0.0.1.48.02_CL_FIx_Baseline.zip`

## Target

`Invio v1.0.0.1.48.3`

## Locked scope

End-to-End GitHub CI/test/build/release pipeline forensic audit and stabilization only, plus required v1.0.0.1.48.3 identity and synchronized documentation.

## Root-cause correction

- Restores `/project/` as fully Git-ignored private material instead of partially exposing selected historical records.
- Makes only the four newer v1.47/v1.48 private repository-contract reads conditional on a complete private baseline, matching the already established historical test boundary.
- Retains the working Linux Qt/offscreen PySide6 CI environment from v1.48.02.
- Leaves wheel/Nuitka/WiX/MSI/checksum/artifact/exact-tag release behavior unchanged apart from the required target version mapping.

## Version mapping

- Application: `1.0.0.1.48.3`
- PE: `1.0.1.4803`
- MSI: `1.1.4803`
- Tag: `v1.0.0.1.48.3`
- Wheel: `1.0.0.1.48.3`

## Verification summary

- Targeted repository/P14/UI gate: PASS after the permitted second targeted cycle; local PySide6-only tests skip because the dependency is absent from the forensic container, while GitHub run `31516505105` proves those real tests pass on both Linux and Windows.
- Clean public-checkout simulation: **444 discovered / 440 PASS / 4 local-environment SKIPPED**, repository failures 0.
- Full private-baseline audit: **444 discovered / 440 PASS / 4 local-environment SKIPPED**, repository failures 0.
- Real wheel build + P14 wheel content audit: PASS.
- YAML/JSON/YGIT/TOML parse: PASS.
- Unexpected runtime/application source behavior diffs: 0.
- Removed baseline files: 0.

## Delta inventory

The exact changed/added file list and final counts are sealed together with `SHA256SUMS.txt` in the delivered ZIP. No build cache, wheel, `__pycache__`, `.pyc`, wrapper directory or unrelated runtime file is included.

## Exact delta file inventory

### Added (5)

- `PATCH_MANIFEST_v1.0.0.1.48.3.md`
- `docs/release-notes/1.0.0.1.48.3.md`
- `project/research/FINAL_CI_FORENSIC_VERIFICATION_v1.0.0.1.48.3.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.3.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.3.md`

### Modified (28)

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
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

### Removed

None.

Total delta paths: **33**. `SHA256SUMS.txt` contains hashes for the other **32** payload paths and intentionally excludes itself.
