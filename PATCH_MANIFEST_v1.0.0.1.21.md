# Invio v1.0.0.1.21 Delta Patch Manifest

**Parent baseline:** `Invio v1.0.0.1.20`  
**Target:** `Invio v1.0.0.1.21`  
**Scope:** approved PRE-P08 Provider Adapter Foundation + Agiled Provider  
**Roadmap progress:** 7/14 unchanged; P08 remains next

## Runtime / provider files

- `src/core/provider_runtime/adapters.py` - new internal packaged-provider adapter registry.
- `src/core/provider_runtime/__init__.py` - public registry exports.
- `src/core/provider_runtime/preflight.py` - registry-backed capability/manifest contract lookup.
- `src/core/provider_runtime/runtime.py` - registry-backed API Test/Task dispatch; existing Stripe/Refrens network methods preserved.
- `providers/packages/agiled/provider.json` - packaged Agiled API-key manifest; executable runtime intentionally fail-closed.
- `src/ui/main_window.py` - release-version markers only.

## Tests / release metadata

- `tests/test_provider_adapter_registry.py` - Agiled/registry/fail-closed regression coverage.
- `tests/test_repository_contracts.py` - v1.0.0.1.21 metadata contract.
- `pyproject.toml`
- `vibproject.ygit`
- `docs/docs.manifest.ygit`

## Public documentation synchronized

- `README.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `PROJECT_STRUCTURE.md`
- `VERSIONING.md`
- `COMPATIBILITY.md`
- `docs/index.md`
- `docs/user/usage.md`
- `docs/developer/architecture.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/api/provider-manifest.md`
- `docs/guides/providers.md`
- `docs/configuration/index.md`
- `docs/getting-started/installation.md`
- `docs/troubleshooting/index.md`
- `docs/features/ui-milestone.md`
- `docs/release-notes/1.0.0.1.21.md`

## Private project records synchronized

- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/PRE_P08_PROVIDER_ADAPTER_AGILED_IMPLEMENTATION_v1.0.0.1.21.md`
- `project/research/AGILED_API_CONTRACT_REVALIDATION_v1.0.0.1.21.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.21.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.21.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.21.md`
- `PATCH_MANIFEST_v1.0.0.1.21.md`

## Explicit exclusions

- no P08/P09+ behavior;
- no WorkerManager change;
- no SQLite schema change;
- no dependency change;
- no Refrens P11 Task enablement;
- no dynamic external Python provider loading/P13 completion;
- no Agiled network call until its current official API contract is authoritative.

## Verification summary

- Parent suite: 230/230 PASS.
- Target suite: 237/237 PASS.
- Compile: PASS.
- Repository audit: PASS.
- Deleted baseline non-cache files: 0.
- Patch wrapper directory: none.
- `__pycache__`, `.pyc`, `.pytest_cache`: excluded from patch.
