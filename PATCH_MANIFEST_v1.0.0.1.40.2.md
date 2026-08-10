# Invio v1.0.0.1.40.2 Replace-Ready Delta Patch Manifest

Official parent baseline: **Invio v1.0.0.1.40.1**  
Target candidate: **Invio v1.0.0.1.40.2**

## Scope

- Enable only the owner-supplied current Agiled Public API safe Account API Test: Bearer-authenticated `GET /public/v1/me`.
- Keep Agiled invoice Task sending fail-closed because the supplied contract exposes no invoice email/send operation and no field-level invoice mutation schema.
- Preserve the existing documented Refrens send flow and add explicit provider `CODE <HTTP status>` Live Logs visibility for live API-mail rejections.
- Synchronize only directly required version, tests and documentation.

## Delta inventory

- Added: **8**
- Modified: **35**
- Removed: **0**
- Total paths: **43**

| Change | Path |
|---|---|
| Modified | `.github/workflows/ci.yml` |
| Modified | `CHANGELOG.md` |
| Modified | `COMPATIBILITY.md` |
| Added | `docs/api/agiled-runtime.md` |
| Modified | `docs/api/refrens-runtime.md` |
| Modified | `docs/configuration/index.md` |
| Modified | `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md` |
| Modified | `docs/developer/architecture.md` |
| Modified | `docs/developer/ERROR_HANDLING.md` |
| Modified | `docs/docs.manifest.ygit` |
| Modified | `docs/getting-started/installation.md` |
| Modified | `docs/guides/providers.md` |
| Modified | `docs/index.md` |
| Added | `docs/release-notes/1.0.0.1.40.2.md` |
| Modified | `docs/troubleshooting/index.md` |
| Modified | `docs/user/usage.md` |
| Added | `PATCH_MANIFEST_v1.0.0.1.40.2.md` |
| Modified | `project/architecture/ARCHITECTURE.md` |
| Modified | `project/planning/PHASE_COMPLETION_LOG.md` |
| Modified | `project/planning/PRODUCTION_ROADMAP.md` |
| Modified | `project/planning/PRODUCTION_UPDATE_PROTOCOL.md` |
| Modified | `project/README.md` |
| Added | `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.2.md` |
| Added | `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.2.md` |
| Added | `project/specifications/BASELINE_FREEZE_v1.0.0.1.40.2.md` |
| Added | `project/specifications/P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.40.2.md` |
| Added | `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.40.2.md` |
| Modified | `PROJECT_STRUCTURE.md` |
| Modified | `providers/packages/agiled/provider.json` |
| Modified | `pyproject.toml` |
| Modified | `README.md` |
| Modified | `ROADMAP.md` |
| Modified | `SHA256SUMS.txt` |
| Modified | `src/core/provider_runtime/adapters.py` |
| Modified | `src/core/provider_runtime/runtime.py` |
| Modified | `src/ui/main_window.py` |
| Modified | `tests/test_p11_refrens_task.py` |
| Modified | `tests/test_p14_distribution_pipeline.py` |
| Modified | `tests/test_provider_adapter_registry.py` |
| Modified | `tests/test_provider_runtime.py` |
| Modified | `tests/test_repository_contracts.py` |
| Modified | `VERSIONING.md` |
| Modified | `vibproject.ygit` |

## Replacement contract

Extract this ZIP directly over the exact `v1.0.0.1.40.1` project root. No wrapper directory, file rename or file deletion is part of this delta. `SHA256SUMS.txt` covers every delta payload path except itself.

## Explicitly unchanged runtime boundaries

SQLite schema v5, runtime dependencies, WorkerManager, Task state machine, immutable snapshots, delivery-ledger semantics, Stripe, Refrens manifest/send endpoint/payload, Settings/UI design and credential-storage policy remain unchanged except for the exact provider runtime/logging behavior stated above.
