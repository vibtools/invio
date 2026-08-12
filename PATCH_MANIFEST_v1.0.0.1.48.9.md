# Invio v1.0.0.1.48.9 Replace-Ready Delta Patch Manifest

## Parent Baseline Freeze

`Invio_v1.0.0.1.48.8_Baseline.zip`.

The parent baseline is owner-verified on real Windows/PySide6: the previously failing Accounts status-width test, the New Task canonical status-badge test, and the complete 470-test audit all PASS before this update.

## Locked scope

UI only: Customer Lists final compact design, rollout of the already-frozen compact Page Header / Section Toolbar pattern to applicable pages, and directly required tests/version/docs/verification records. No backend/provider/storage/business behavior change is approved.

## Confirmed root cause

The v1.48.8 Customer Lists page still used a two-column `QTableWidget` plus a separate list pager, a separate customer action row, and a second customer toolbar. Invoice Templates and Reports rendered section titles above their search/filter toolbars; Providers used a standalone search row; Settings combined page title, search and page actions in one custom header. These were presentation-composition inconsistencies. No backend defect was found.

## Implementation

- Customer Lists: compact scrollable navigation list; inline muted customer-count badge; row-scoped `⋯` Delete List menu; preserved list search/state filter and selection behavior.
- Customer Lists Customers panel: `Customers + Search + Country + Upload` on one compact row; unchanged `# / EMAIL / NAME / COUNTRY` data table and customer pagination.
- Shared UI: `DataGridToolbar` gains backward-compatible optional section title/actions; `section_toolbar()` provides the same hierarchy for non-table controls; shared bounded popup placement constrains app-owned row menus to the application/window and available screen intersection.
- Invoice Templates and Reports move existing section titles into their existing DataGridToolbar rows.
- Providers uses `Provider Catalog + Search` in one compact section row.
- Settings uses the shared page header for Reset/Save and a compact `Preferences + Search` section row.
- Accounts, Dashboard, Tasks and Live Logs were audited and retained because their established layouts already satisfy the frozen hierarchy or their page-specific compact layout contract.
- Existing design tokens and semantic status colors are unchanged.

## Backend freeze

No changes to data models, provider adapters, provider APIs, ProviderManager, WorkerManager, Task execution/state machine, database/storage schema, authentication, import parsing, validation or business rules. `src/core/provider_runtime/runtime.py` changes only the existing public User-Agent version marker from `1.0.0.1.48.8` to `1.0.0.1.48.9`; `src/ui/main_window.py` changes only existing visible/log version markers.

## Version mapping

- Application: `1.0.0.1.48.9`
- Tag identity: `v1.0.0.1.48.9` (no tag is created by this patch)
- PE: `1.0.1.4809`
- MSI: `1.1.4809`
- Wheel: `1.0.0.1.48.9`

## Verification completed in delivery workspace

- Parent baseline local audit: 470 discovered, 458 PASS, 12 PySide6-gated SKIPPED, 0 FAIL/ERROR; syntax/privacy/provider visibility PASS.
- v1.48.9 final audit: 477 discovered, 462 PASS, 15 PySide6-gated SKIPPED, 0 FAIL/ERROR; syntax/privacy/provider visibility PASS.
- UI/repository/distribution targeted contracts: PASS.
- Wheel build: PASS (`invio-1.0.0.1.48.9-py3-none-any.whl`).
- P14 wheel content audit: PASS (56 source modules, 11 exact runtime resources).
- Version mapping helper: application/PE/MSI/tag resolves exactly to the values above.
- Native v1.48.9 Customer Lists PySide6 interaction tests are present but cannot execute in the delivery container because PySide6 is not installed; this is an explicit remaining Windows runtime certification gate, not represented as PASS.

## Added

- `PATCH_MANIFEST_v1.0.0.1.48.9.md`
- `docs/release-notes/1.0.0.1.48.9.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.9.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.9.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.9.md`

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
- `src/ui/pages/customer_lists_page.py`
- `src/ui/pages/invoice_templates_page.py`
- `src/ui/pages/providers_page.py`
- `src/ui/pages/reports_page.py`
- `src/ui/pages/settings_page.py`
- `src/ui/styles.py`
- `src/ui/widgets.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

## Removed

None.

## Delta policy

The ZIP has no wrapper directory and contains only changed/new files. `__pycache__`, `.pyc`, `.pytest_cache`, build output and unrelated parent files are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.

## Final delta inventory count

- Added: 5
- Modified: 38 (including `SHA256SUMS.txt`)
- Removed: 0
- Total delta paths: 43
- `SHA256SUMS.txt` payload entries: 42
