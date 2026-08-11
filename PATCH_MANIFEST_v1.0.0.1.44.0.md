# Invio v1.0.0.1.44.0 Intro/Subtitle Cleanup Patch Manifest

Parent Official Baseline: `Invio v1.0.0.1.43.0`  
Candidate: `Invio v1.0.0.1.44.0`  
Scope: static Intro Description / Subtitle presentation removal only.

## Version

- Application: `1.0.0.1.44.0`
- PE: `1.0.1.4400`
- MSI: `1.1.4400`
- Reserved tag: `v1.0.0.1.44.0`

## Verification

- Scoped contracts: `117/117 PASS`.
- v1.44/version/distribution targeted contracts: `11/11 PASS`.
- Final repository audit: `417/417 PASS`.
- Syntax/privacy/provider-visibility audits: PASS.
- Removed existing files: `0`.

## Inventory

- Added: **6**
- Modified: **30**
- Removed: **0**
- Total overlay paths: **36**

### Added

- `PATCH_MANIFEST_v1.0.0.1.44.0.md`
- `docs/release-notes/1.0.0.1.44.0.md`
- `examples/intro_subtitle_cleanup_ui.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.44.0.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.44.0.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.44.0.md`

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
- `src/ui/pages/tasks_page.py`
- `src/ui/widgets.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None

## Scope preservation

No provider/runtime/storage/task/customer/invoice/report/settings/data-grid behavior is changed. Shared helper signatures are preserved; only static description rendering is hidden, plus the one static Task-card subtitle is removed.
