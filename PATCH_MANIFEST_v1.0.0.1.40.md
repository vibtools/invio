# Invio v1.0.0.1.40 Live Refrens/UI/Customer Defaults/Icon Correction Delta Patch Manifest

Parent Official Baseline: `Invio v1.0.0.1.39`  
Target: `Invio v1.0.0.1.40` local source/live correction candidate  
Release authorization: **NO — owner local/live + non-tagged compiled-artifact acceptance required**

## Approved correction scope

1. New Task account-list dark visibility.
2. Right-click/context-menu dark visibility.
3. Email-only customer import defaults plus Settings Default Customer Name/Country.
4. Confirmed Refrens create-invoice `terms` HTTP 400 correction.
5. Customer Lists table/background dark visibility.
6. Owner-controlled `assets/icons/app.png` / `assets/icons/app.ico` runtime/build wiring.
7. Required v1.40 tests/version/docs only.

## Binary branding assets

The owner stated that `assets/icons/app.png` and `assets/icons/app.ico` will be added at those exact paths. They were not supplied to this patching environment, so the delta does **not** fabricate or replace those binary assets. The source/build contract now consumes them, and Windows CI will require `app.ico` once the owner adds the files.

## Delta inventory

- Added: **7**
- Modified: **42**
- Removed: **0**
- Total paths: **49**

### Added

- `PATCH_MANIFEST_v1.0.0.1.40.md`
- `docs/api/refrens-runtime.md`
- `docs/release-notes/1.0.0.1.40.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.40.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.40.md`

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
- `scripts/test/p14_distribution_audit.py`
- `src/app.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/settings/manager.py`
- `src/customers/importers/__init__.py`
- `src/customers/importers/email_importer.py`
- `src/ui/main_window.py`
- `src/ui/pages/customer_lists_page.py`
- `src/ui/pages/settings_page.py`
- `src/ui/styles.py`
- `tests/test_customer_importers.py`
- `tests/test_p11_refrens_task.py`
- `tests/test_p14_certification.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_provider_runtime.py`
- `tests/test_repository_contracts.py`
- `tests/test_settings.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

### Removed

- None

`SHA256SUMS.txt` hashes every other delta path and intentionally excludes itself.
