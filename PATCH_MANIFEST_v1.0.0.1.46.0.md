# Invio v1.0.0.1.46.0 Replace-Ready Delta Patch Manifest

- Official parent baseline: `Invio v1.0.0.1.45.0`
- Candidate: `Invio v1.0.0.1.46.0`
- Application: `1.0.0.1.46.0`
- PE: `1.0.1.4600`
- MSI: `1.1.4600`
- Scope: custom Main Window and application-owned QDialog/QMessageBox title bars only.

## Inventory

- Added: **7**
- Modified: **30**
- Removed: **0**
- Total paths: **37**

## Added

- `PATCH_MANIFEST_v1.0.0.1.46.0.md`
- `docs/release-notes/1.0.0.1.46.0.md`
- `examples/custom_title_bars_ui.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.46.0.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.46.0.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.46.0.md`
- `src/ui/title_bars.py`

## Modified

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `pyproject.toml`
- `src/app.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `src/ui/styles.py`
- `src/ui/tokens.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

## Removed

- None

## Verification

- Targeted suite: `133 / 133 PASS`.
- Final full audit: `422 / 422 PASS`.
- Syntax/privacy/provider-visibility audits: PASS.
- No wrapper directory, no path traversal, no Python cache artifact in the delta ZIP.
- Exact parent-baseline + delta overlay must match the candidate byte-for-byte.
