# Invio v1.0.0.1.5 Delta Patch Manifest

**Baseline:** `v1.0.0.1.4`  
**Target:** `v1.0.0.1.5`  
**Patch type:** replace-ready project-root delta  
**Scope:** Invoice Template UI geometry repair only, plus required version/test/documentation/audit records.

## Runtime/source files

- `src/ui/dialogs.py` - Invoice Template-only geometry/root-cause correction.
- `src/ui/main_window.py` - release version markers only.
- `src/core/provider_runtime/runtime.py` - release User-Agent marker only; provider behavior unchanged.
- `pyproject.toml` - version metadata only.
- `vibproject.ygit` - version metadata only.

## Tests

- `tests/test_ui_contracts.py` - replaces the faulty maximum-height source expectation with minimum-content/height-for-width regression contracts.
- `tests/test_repository_contracts.py` - target release metadata expectation updated without renaming/removing the existing test function.

## Public documentation

- `README.md`
- `CHANGELOG.md`
- `VERSIONING.md`
- `docs/docs.manifest.ygit`
- `docs/index.md`
- `docs/developer/architecture.md`
- `docs/features/ui-milestone.md`
- `docs/guides/invoice-templates.md`
- `docs/release-notes/1.0.0.1.5.md`

## Private project records

- `project/architecture/ARCHITECTURE.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.4.md`
- `project/research/UPDATE_IMPLEMENTATION_LOG_v1.0.0.1.5.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.5.md`

## Package rules

- No wrapper directory.
- Extract directly over the `v1.0.0.1.4` project root and replace matching files.
- No baseline file is deleted by this patch.
- No `__pycache__` or `.pyc` file is included.
