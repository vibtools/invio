# Invio v1.0.0.1.45.0 Replace-Ready Delta Patch Manifest

This overlay is based strictly on the owner-frozen `Invio v1.0.0.1.44.0` baseline and contains only the approved Providers Page transient-window/card-layout fix, direct verification/version synchronization, and required documentation records.

## Version

- Application: `1.0.0.1.45.0`
- PE: `1.0.1.4500`
- MSI: `1.1.4500`
- Reserved future tag: `v1.0.0.1.45.0`

## Approved implementation

- Prevent provider cards from being shown before `QGridLayout` re-parents them into the Providers Page host.
- Move Available/Verified from below logo to below Provider Name.
- Compact status mark to 18px and Provider card height to 194px.
- Preserve provider search, responsive grid, logo size, description ellipsis, footer version, install/uninstall callbacks and all backend/runtime behavior.

## Final inventory

- Added: **6**
- Modified: **30**
- Removed: **0**
- Total delta paths: **36**

### Added

- `PATCH_MANIFEST_v1.0.0.1.45.0.md`
- `docs/release-notes/1.0.0.1.45.0.md`
- `examples/providers_transient_window_fix.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.45.0.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.45.0.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.45.0.md`

### Modified

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
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
- `src/ui/pages/providers_page.py`
- `src/ui/styles.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None.

## Verification

- Targeted UI/repository/P14 suite: 129/129 PASS.
- Exact post-documentation truthfulness rerun: 1/1 PASS after a test-only wording synchronization.
- Final full audit: 419/419 PASS; syntax/privacy/provider-visibility PASS.
- No product code change after the final full audit.
- Final ZIP/overlay byte verification is recorded at delivery time.
