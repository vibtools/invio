# Invio v1.0.0.1.42.0 Global Forms + Settings UI/UX Patch Manifest

This replace-ready overlay is based on the owner-frozen `Invio v1.0.0.1.41.1` baseline. It contains only the approved Global Forms + Settings Page UI/UX refinement, directly required UI/version tests, version identity and synchronized documentation. The v1.41.1 Providers Page design and all provider/runtime/storage/business behavior remain frozen.

## Version

- Application: `1.0.0.1.42.0`
- PE: `1.0.1.4200`
- MSI: `1.1.4200`
- Reserved future tag: `v1.0.0.1.42.0`

## Approved UI scope

- Scoped 32px Global Forms/Settings controls and buttons with 6px radius.
- Softened form/settings title, body, muted and placeholder text colors with a 400/500 typography cap.
- Application-owned dialog padding normalized to 12px and section spacing to 8px.
- Verbose dialog subtitles and nonessential help captions removed without changing field/business semantics.
- Deterministic right-aligned secondary Cancel + primary Save/Create/Add dialog footer actions.
- Settings Search with Ctrl+F focus and live card filtering.
- Settings responsive 2-column/1-column reflow.
- Customer Defaults full-row span with compact inline fields.
- `Restore Defaults` presentation renamed to `Reset Settings`; reset/save persistence behavior unchanged.
- All five Settings card descriptions/subtitles removed.

## Explicitly frozen

- Providers Page v1.41.1 approved UI and provider card behavior.
- ProviderManager, ProviderRuntime/API semantics, Stripe/Refrens/Agiled/Odoo execution and P13 trust/execution architecture.
- SettingsManager/AppSettings schema, keys, defaults and persistence rules.
- SQLite schema v5, CredentialStore, WorkerManager/QThread, Task/customer/invoice business behavior and dependencies.

## Inventory

- Added: **6**
- Modified: **32**
- Removed: **0**
- Total overlay paths: **38**

### Added

- `PATCH_MANIFEST_v1.0.0.1.42.0.md`
- `docs/release-notes/1.0.0.1.42.0.md`
- `examples/forms_settings_ui.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.42.0.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.42.0.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.42.0.md`

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
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `src/ui/pages/settings_page.py`
- `src/ui/styles.py`
- `src/ui/tokens.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None

## Verification

- Targeted Global Forms + Settings contracts: **61/61 PASS**.
- Final repository audit: **413/413 PASS**, syntax PASS, repository privacy PASS, provider visibility PASS.
- Real v1.42.0 wheel build: PASS; P14 wheel content audit PASS (55 source modules, 10 exact runtime resources).
- Wheel SHA-256: `808406394abf8de93a184fda597e454224b8db1d0b3940eea23f7afe8d0900fb`.
- Removed existing files: **0**.
- Native Qt visual acceptance remains owner-controlled because PySide6 is unavailable in the Linux forensic environment.
- A green non-tag GitHub CI run is required before any tag/release decision.

