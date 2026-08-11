# Invio v1.0.0.1.43.0 Global Data Tables + Lists + Fonts Patch Manifest

This project-root replace-ready overlay is based on the owner-frozen `Invio v1.0.0.1.42.0` baseline. It contains only the approved compact Data Grid UI/UX implementation, directly required UI/version/distribution tests, the `search.svg` runtime resource, synchronized documentation and forensic verification records.

## Version

- Application: `1.0.0.1.43.0`
- PE: `1.0.1.4300`
- MSI: `1.1.4300`
- Reserved future tag: `v1.0.0.1.43.0`

## Approved scope

- 28px Data Grid search/filter/pagination controls, 28px headers and 30px rows.
- UI-session case-insensitive search, derived filters and in-memory pagination (10/25/50), with no backend pagination or sorting.
- Segoe UI Variable/Segoe UI data-surface typography, 12px/400 body and 11px/600 headers.
- Subtle zebra/hover/selection states, no vertical grid lines, compact semantic status badges and full-value tooltips.
- Accounts QTreeWidget hierarchy/date presentation, Customer Lists/Records table consistency, Invoice Templates 80px Actions clip fix, unified Reports surfaces, Invoice Items view-only search/pagination, and the approved New Task Accounts QListWidget-to-QTableWidget conversion capped at 250px.
- `assets/icons/search.svg` included in wheel/portable resource audits.

## Explicitly frozen

- Providers Page v1.41.1 approved design and Global Forms/Settings v1.42.0 approved design outside the explicitly scoped data surfaces.
- ProviderManager, ProviderRuntime/API behavior, Stripe/Refrens/Agiled/Odoo execution and P13.
- SQLite schema v5, CredentialStore, WorkerManager/QThread, Task/customer/invoice/report business semantics, Settings persistence, dependencies and release topology.

## Verification

- Targeted Cycle 1: 54 tests, 52 PASS, 2 stale pre-v1.43 literal UI assertions.
- Targeted Cycle 2: exact two failures + new v1.43 contract, 3/3 PASS; loop closed.
- Final repository audit: **415/415 PASS**, syntax PASS, repository privacy PASS, provider visibility PASS.
- Real candidate wheel: `invio-1.0.0.1.43.0-py3-none-any.whl`.
- P14 wheel audit: PASS, 55 source modules, 11 exact runtime resources.
- Wheel SHA-256: `9ecf5defb6cd832c68e3bd2a03ce199c44ec6557b6333d592ff2d07ad5dc8004`.
- Native desktop visual acceptance remains owner-controlled; green non-tag GitHub CI is required before any tag/freeze decision.

## Delta inventory

- Added: **7**
- Modified: **39**
- Removed: **0**
- Total overlay paths: **46**

### Added

- `PATCH_MANIFEST_v1.0.0.1.43.0.md`
- `assets/icons/search.svg`
- `docs/release-notes/1.0.0.1.43.0.md`
- `examples/data_grid_ui.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.43.0.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.43.0.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.43.0.md`

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
- `scripts/build/prepare_windows_distribution.py`
- `scripts/test/p14_wheel_audit.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `src/ui/pages/accounts_page.py`
- `src/ui/pages/customer_lists_page.py`
- `src/ui/pages/invoice_templates_page.py`
- `src/ui/pages/reports_page.py`
- `src/ui/styles.py`
- `src/ui/tokens.py`
- `src/ui/widgets.py`
- `tests/test_p14_certification.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None

`SHA256SUMS.txt` hashes every delta payload path except itself.
