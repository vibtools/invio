# Invio v1.0.0.1.7 Delta Patch Manifest

**Baseline:** exact `Invio v1.0.0.1.6` full artifact  
**Target:** `Invio v1.0.0.1.7`  
**Approved scope:** verify/fix only the previously approved P01 implementation/release state  
**Patch format:** project-root replace-ready ZIP, no wrapper directory

## Runtime/release corrections

- `providers/registry/refrens.json`
  - synchronize the stale shipped installed manifest to the existing bundled Refrens production manifest;
  - remove the shipped `1.0.3-ui` / deferred-backend presentation inconsistency.
- `src/core/provider_runtime/runtime.py`
  - release User-Agent marker only; P01 API-test/send semantics unchanged.
- `src/ui/main_window.py`
  - release startup/status marker only; P01 task/API-test behavior unchanged.

## Test corrections

- `tests/test_ui_contracts.py`
  - production-marker source corpus now covers source and bundled provider manifests, not mutable ignored provider registry state.
- `tests/test_repository_contracts.py`
  - current release metadata test naming/assertions synchronized to v1.0.0.1.7.

## Release metadata

- `pyproject.toml`
- `vibproject.ygit`
- `docs/docs.manifest.ygit`

## Documentation/log updates

README, CHANGELOG, ROADMAP, VERSIONING, project structure/current indexes, P01 implementation/verifier errata, phase ledger, architecture records, release notes, production-readiness report, final verification report, and new baseline freeze record are synchronized.

## Explicitly unchanged

- P01 Stripe/Refrens API-test request semantics;
- provider package manifests, IDs, credentials and account modes;
- `ProviderManager` implementation;
- `WorkerManager` implementation;
- Account/Customer List/Invoice Template/Task models;
- invoice send workflow semantics;
- Settings/Reports/Logs/Dashboard/other UI design;
- dependencies.

## Verification

- Final Python compilation: PASS.
- Final unit/contract suite: 63/63 PASS.
- Repository/provider audit: PASS.
- Existing source classes/functions removed: 0.
- Deleted baseline files: 0.
- The exact results and scope-diff audit are recorded in `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.7.md`.
