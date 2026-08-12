# Invio v1.0.0.1.49 Replace-Ready Delta Patch Manifest

## Parent Baseline Freeze

Official parent baseline: `Invio_v1.0.0.1.48.9_Baseline.zip`.

## Locked scope

UI only: Provider and Settings compact page/section headers plus Invoice Templates and Reports table layout/position/overflow correction, with directly required tests/version/documentation/verification records. No backend/provider/storage/business behavior change is approved.

## Content-preservation lock

Invoice Templates table body remains authoritative and preserves `TEMPLATE / CURRENCY / TYPE / DUE / ITEMS / TAX / ACTIONS`, all row values and Edit/Delete callbacks. Reports preserves every Task Summary and Recipient Delivery History column/value. No column hiding/removal/data rewrite is permitted; wide content uses horizontal scrolling.

## Confirmed root cause

- Provider/Settings page hierarchy was already correct, but page-local spacing remained larger than the frozen compact spacing and the dedicated search fields inherited the generic 32px form-control height instead of the compact 28px toolbar control geometry.
- Invoice Templates retained all content, but the fixed 80px Actions column left no containment margin for the existing 32px Edit + 44px Delete controls plus spacing; horizontal overflow behavior was implicit.
- Reports retained all content, but wide data columns used Stretch, compressing headers/cells into the viewport instead of preserving content-driven widths with horizontal scrolling.

## Implementation

- Providers: compact page-local spacing; Provider search constrained to the established compact search width and 28px control styling. Provider cards/data/actions unchanged.
- Settings: compact page-local spacing; Settings search constrained to the established compact search width and 28px control styling. All settings controls and persistence callbacks unchanged.
- Invoice Templates: all seven columns/values retained; Actions column widened to 96px, action host receives safe side margins, headers aligned, horizontal scrolling explicitly enabled.
- Reports: all 9 Task Summary and 11 Recipient Delivery History columns/values retained; both tables use content-driven `ResizeToContents`, `StretchLastSection(False)` and per-pixel horizontal scrolling.

## Backend freeze

No changes to provider APIs, ProviderManager, provider packages, WorkerManager, Task execution/state machine, authentication, data models, database/storage schema, report-generation logic, delivery ledger logic or dependencies. `src/core/provider_runtime/runtime.py` changes only public version/User-Agent markers.

## Version mapping

- Application: `1.0.0.1.49`
- Tag identity: `v1.0.0.1.49` (no tag created by this patch)
- PE: `1.0.1.49`
- MSI: `1.1.49`
- Wheel: `1.0.0.1.49`

## Verification status

Delivery-container baseline audit and updated audits are recorded in `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.md`. Native PySide6 interaction tests are included but remain environment-gated in this container because PySide6 is not installed.

## Removed

None.

## Delta policy

The delivery ZIP has no wrapper directory and contains only changed/new files. Runtime caches/build artifacts are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.

## Final delta inventory

### Added
- `PATCH_MANIFEST_v1.0.0.1.49.md`
- `docs/release-notes/1.0.0.1.49.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.md`

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
- `docs/guides/invoice-templates.md`
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py` (version/User-Agent markers only)
- `src/ui/main_window.py` (version markers only)
- `src/ui/pages/invoice_templates_page.py`
- `src/ui/pages/providers_page.py`
- `src/ui/pages/reports_page.py`
- `src/ui/pages/settings_page.py`
- `src/ui/styles.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

### Counts
- Added: 5
- Modified: 37 (including `SHA256SUMS.txt`)
- Removed: 0
- Total delta paths: 42
- `SHA256SUMS.txt` payload entries: 41
