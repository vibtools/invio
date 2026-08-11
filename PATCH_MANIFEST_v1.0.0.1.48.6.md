# Invio v1.0.0.1.48.6 Replace-Ready Delta Patch Manifest

## Parent Official Baseline

`Invio_v1.0.0.1.48.5_Baseline.zip`

SHA-256: `a6db782f61e01d9be3fe8ffc26732745d4f60b843c4f57aa1b1b103bff3cf263`

## Locked correction

Accounts Page only: balanced compact table geometry, visible/contained Action column and 30x24 row control, window+screen-safe context-menu placement, and Accounts-scoped semantic styling using success `#22C55E`, warning `#FCD34D`, danger `#F87171`, primary `#2563EB`. Existing callbacks/business behavior are frozen.

## Verification

- Baseline: **457 / 447 PASS / 10 SKIPPED / 0 failures**
- Targeted corrected contracts: **89/89 PASS**
- Final full local audit: **462 / 451 PASS / 11 SKIPPED / 0 failures**
- Syntax / repository privacy / provider visibility: **PASS**
- Native PySide6 in this container: **unavailable; no false PASS claimed**

## Version mapping

- Application: `1.0.0.1.48.6`
- Tag: `v1.0.0.1.48.6`
- PE: `1.0.1.4806`
- MSI: `1.1.4806`
- Wheel: `1.0.0.1.48.6`

## Added

- `PATCH_MANIFEST_v1.0.0.1.48.6.md`
- `docs/release-notes/1.0.0.1.48.6.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.6.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.6.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.6.md`

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
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/accounts_page.py`
- `src/ui/styles.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

## Removed

None.

## Delta policy

No wrapper directory. Only changed/new files are packaged. `__pycache__`, `.pyc`, `.pytest_cache` and unrelated baseline files are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.
