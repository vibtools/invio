# Invio v1.0.0.1.48.4 Replace-Ready Delta Patch Manifest

## Parent Official Baseline

`Invio_v1.0.0.1.48.3_Baseline.zip`

## Target

`Invio v1.0.0.1.48.4`

## Locked scope

Tasks-page **Compact Add Task Modal UI Redesign** only, plus directly required regression coverage, release/version identity and synchronized documentation.

## Runtime/UI correction

- Recompose only `NewTaskDialog` into one Provider/filter/search toolbar row, existing account table/pager, and one selector/action row.
- Keep the account grid at the existing 250px design cap with vertical scrolling instead of dynamic shrink-to-row-count behavior.
- Preserve all existing field data, callbacks, validation, payload and Task creation semantics.
- Reuse existing dialog title bar, border/shadow, color and typography system; no shared style redesign.

## Frozen boundaries

No provider adapter/manifest/plugin behavior, AppState/domain model, Task state machine, WorkerManager, storage/schema, retry/scheduling/delivery ledger, Settings, other page/dialog, dependency or project structure change is included.

## Verification summary

- Baseline audit: 444 discovered / 440 PASS / 4 PySide6-environment SKIPPED.
- Targeted affected suite: 162 discovered / 154 PASS / 8 PySide6-environment SKIPPED / 0 failures.
- Final audit: 451 discovered / 443 PASS / 8 PySide6-environment SKIPPED / 0 failures.
- Syntax audit: PASS.
- Repository privacy: PASS.
- Provider visibility: PASS.
- New real PySide6 New Task interaction tests are included for dependency-installed CI.
- Native Qt execution in this forensic container is blocked by unavailable PySide6 and unavailable external package network access; no false runtime PASS is claimed.
- Removed baseline files: 0.

## Version mapping

- Application: `1.0.0.1.48.4`
- PE: `1.0.1.4804`
- MSI: `1.1.4804`
- Tag: `v1.0.0.1.48.4`
- Wheel: `1.0.0.1.48.4`

## Delta policy

The delivered ZIP contains only changed/new files from the exact uploaded v1.48.3 baseline, has no wrapper folder, and excludes `__pycache__`, `.pyc`, build outputs and unrelated files. `SHA256SUMS.txt` hashes every other delta payload file and intentionally excludes itself.

## Exact delta inventory

- Added: **5**
- Modified: **33**
- Removed: **0**
- Total delta paths: **38**

### Added

- `PATCH_MANIFEST_v1.0.0.1.48.4.md`
- `docs/release-notes/1.0.0.1.48.4.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.4.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.4.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.4.md`

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
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/getting-started/installation.md`
- `docs/guides/tasks.md`
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
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

### Removed

None.
