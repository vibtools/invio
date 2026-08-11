# Invio v1.0.0.1.48.8 Replace-Ready Delta Patch Manifest

## Parent Baseline Freeze

Latest updated `v1.0.0.1.48.7` delta state, reconstructed over `Invio_v1.0.0.1.48.6_Baseline.zip`.

## Locked scope

Confirmed Accounts canonical-status column natural-width runtime correction only, plus directly required regression/version/documentation/release records.

## Confirmed failure evidence

The owner-provided real Windows PySide6 run failed only the Accounts scalable-pagination/status layout test because:

- `page.table.columnWidth(2) == 132`
- canonical `✕ Not Installed` badge required `badge.sizeHint().width() + 4 == 184`
- the New Task canonical single-badge runtime test passed
- the full 468-test run repeated that same single Accounts failure.

## Root cause

The v1.48.7 shared renderer was already canonical and provided a badge-derived table-item size hint. `AccountsPage` overrode that contract by forcing Status column 2 to `QHeaderView.Fixed` at 132px. The fixed pixel assumption is not portable across real Qt font/DPI metrics.

## Correction

- `src/ui/pages/accounts_page.py`: Status column 2 now uses `QHeaderView.ResizeToContents`.
- The fixed `header.resizeSection(2, 132)` override is removed.
- Existing `ACCOUNT` and `PROVIDER` stretch modes remain unchanged.
- Existing `ACTION` fixed 68px column and 30x24 row control remain unchanged.
- Existing v1.48.7 shared renderer, badge colors, raw-status metadata, callbacks, filters and pagination remain unchanged.
- The previously failing `tests/test_ui_runtime_interactions.py` file is byte-identical to the v1.48.7 parent state; the runtime assertion was not weakened or rewritten.

## Version mapping

- Application: `1.0.0.1.48.8`
- Tag: `v1.0.0.1.48.8`
- PE: `1.0.1.4808`
- MSI: `1.1.4808`
- Wheel: `1.0.0.1.48.8`

## Forensic audit

Parent v1.48.7 local audit:
- 468 tests discovered
- 456 PASS
- 12 PySide6-gated SKIPPED
- 0 failures/errors
- syntax PASS
- repository privacy PASS
- provider visibility PASS

Updated v1.48.8 local final audit:
- 470 tests discovered
- 458 PASS
- 12 PySide6-gated SKIPPED
- 0 failures/errors
- syntax PASS
- repository privacy PASS
- provider visibility PASS

A single attempt to install PySide6 in the forensic container failed because external package resolution/DNS is unavailable. No retry loop was performed and no native Qt PASS is fabricated.

## Added

- `PATCH_MANIFEST_v1.0.0.1.48.8.md`
- `docs/release-notes/1.0.0.1.48.8.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.8.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.8.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.8.md`

## Modified

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
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/getting-started/installation.md`
- `docs/guides/accounts.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `examples/accounts_flat_table_ui.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py` (version/User-Agent markers only)
- `src/ui/main_window.py` (version markers only)
- `src/ui/pages/accounts_page.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

## Removed

None.

## Delta policy

The ZIP has no wrapper directory and contains only changed/new files. `__pycache__`, `.pyc`, `.pytest_cache` and unrelated parent files are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.
