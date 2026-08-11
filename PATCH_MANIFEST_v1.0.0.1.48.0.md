# Invio v1.0.0.1.48.0 Replace-Ready Delta Patch Manifest

## Parent baseline
`Invio v1.0.0.1.47.0_Baseline.zip`

## Target
`Invio v1.0.0.1.48.0`

## Locked scope
Custom Main/Dialog chrome presentation only:
- compact Close-side right inset;
- subtle app-owned dialog border/shadow separation;
- removal of duplicate body dialog titles.

No business/runtime/provider/storage/task/customer/invoice/settings/Data Grid/navigation behavior change is included.

## Final delta inventory
- Added: **6**
- Modified: **26**
- Removed: **0**
- Total paths: **32**
- `SHA256SUMS.txt`: **31** payload hashes (every delta payload path except the checksum manifest itself).

## Product implementation paths
- `src/ui/title_bars.py`
- `src/ui/dialogs.py`
- `src/ui/styles.py`

## Version identity-only paths
- `.github/workflows/ci.yml`
- `pyproject.toml`
- `vibproject.ygit`
- `docs/docs.manifest.ygit`
- `src/ui/main_window.py`
- `src/core/provider_runtime/runtime.py`

## Verification contracts
- `tests/test_ui_contracts.py`
- `tests/test_repository_contracts.py`
- `tests/test_p14_distribution_pipeline.py`

## Documentation / forensic records
README, CHANGELOG, compatibility/version/roadmap/project-structure records, user/developer docs, private project architecture/planning records, release notes, scope/root-cause/final-verification records and the desktop visual canary.

No file is renamed or removed. The ZIP is project-root relative with no wrapper directory.
