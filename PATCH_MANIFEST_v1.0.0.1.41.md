# Invio v1.0.0.1.41 Providers Page UI/UX Delta Patch Manifest

Parent Official Production Baseline: `v1.0.0.1.40.2`.

This replace-ready project-root overlay contains only the approved Providers Page compact UI/UX implementation, directly related tests/version markers, and mandatory synchronized documentation. No provider business/runtime/storage/threading behavior is changed.

## Inventory

- Added: **4**
- Modified: **33**
- Removed: **0**
- Total delta paths: **37**

### Added

- `PATCH_MANIFEST_v1.0.0.1.41.md`
- `docs/release-notes/1.0.0.1.41.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.41.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.41.md`

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
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `examples/odoo_provider_canary.md`
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
- `tests/test_p13_external_adapters.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None

## UI scope

- Provider cards: 220px fixed height, 280px minimum width, 16px padding.
- Provider grid: 16px gaps, responsive 2–4 columns.
- Header: neutral 32x32 initial + title/version + right status.
- Description: maximum three visible lines + ellipsis + full tooltip.
- Metadata: compact effective-runtime capability chips plus one runtime/credential line.
- Footer: existing Install/Uninstall action bottom-anchored by stretch.
- Hover: surface `#1A212E`; normal border retained.
- Load Provider: visual emphasis only; trusted-code workflow unchanged.

## Frozen behavior

- ProviderManager / ProviderRuntime provider handlers / P13 / Odoo / Refrens / Stripe / Agiled unchanged.
- Accounts, Tasks, Settings and every non-Providers page unchanged.
- SQLite schema remains v5; requirements/dependencies unchanged.
- WorkerManager/QThread architecture unchanged.

## Version

- Application `1.0.0.1.41`
- PE `1.0.1.41`
- MSI `1.1.41`
- Reserved tag `v1.0.0.1.41` (not authorized until owner visual acceptance and candidate CI).
