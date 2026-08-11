# Invio v1.0.0.1.48.5 Replace-Ready Delta Patch Manifest

## Parent Official Baseline

`Invio_v1.0.0.1.48.4_Baseline.zip`

Parent ZIP SHA-256:

`a35120f86282ff3c3067146e140e428900dd2bf4c9800d67e5c37988c6b3c791`

## Target

`Invio v1.0.0.1.48.5`

## Locked scope

Accounts-page **Compact Flat Account Table & Semantic Status UI** only, plus directly required affected regression coverage, release/version identity and synchronized documentation.

## Runtime/UI changes

- Replace Accounts provider-parent/account-child `QTreeWidget` hierarchy with a flat four-column `QTableWidget`.
- Keep only `Add Account` in the page header.
- Put `Added Accounts List`, Search, Provider filter and Status filter on one compact row.
- Preserve DataGrid pagination and rows-per-page.
- Move the existing Edit / Re-test / Delete callbacks to a compact per-row `⋯` menu.
- Reuse existing status badge colors semantically without modifying the shared palette.
- Preserve all backend/data/action contracts.

## Frozen boundaries

No provider adapter/manifest/plugin logic, AppState/domain contract, credential/storage/schema behavior, account API-test implementation, Task/WorkerManager behavior, retry/scheduling/delivery ledger, Settings, dependency, global style/token system, other page/dialog or folder architecture change is included.

## Verification summary

- Baseline audit: **451 discovered / 443 PASS / 8 environment-gated SKIPPED / 0 failures**.
- Final targeted affected suite: **168 executed / 158 PASS / 10 environment-gated SKIPPED / 0 failures**.
- Final full audit: **457 discovered / 447 PASS / 10 environment-gated SKIPPED / 0 failures**.
- Syntax audit: **PASS**.
- Repository privacy: **PASS**.
- Provider visibility: **PASS**.
- Removed baseline files: **0**.
- Local native PySide6 execution: **UNAVAILABLE** because PySide6 is not installed; real Accounts interaction tests are included for dependency-installed CI and no false PASS is claimed.

## Version mapping

- Application: `1.0.0.1.48.5`
- PE: `1.0.1.4805`
- MSI: `1.1.4805`
- Tag: `v1.0.0.1.48.5`
- Wheel: `1.0.0.1.48.5`

## Delta inventory

### Added

- `PATCH_MANIFEST_v1.0.0.1.48.5.md`
- `docs/guides/accounts.md`
- `docs/release-notes/1.0.0.1.48.5.md`
- `examples/accounts_flat_table_ui.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.5.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.5.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.5.md`

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
- `src/ui/pages/accounts_page.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

### Removed

None.

## Delta policy

The delivery ZIP has no wrapper directory and contains only these changed/new files. `__pycache__`, `.pyc`, `.pytest_cache`, build output and unrelated baseline files are excluded. `SHA256SUMS.txt` hashes every other delta payload file and intentionally excludes itself.
