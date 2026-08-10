# Invio v1.0.0.1.40.1 Replace-Ready Delta Patch Manifest

Official parent baseline: **Invio v1.0.0.1.40**  
Target candidate: **Invio v1.0.0.1.40.1**

## Scope

- Refrens explicit post-create invoice email trigger and duplicate-invoice-safe failed-email retry.
- Settings-only alignment to the existing frozen Vib Tools UI tokens/components.
- GitHub/Nuitka duplicate keyring package-config correction.
- Required hotfix version, tests and directly related documentation synchronization.
- Agiled runtime remains fail-closed and unchanged.

## Delta inventory

- Added: **7**
- Modified: **38**
- Removed: **0**
- Total paths: **45**

| Change | Path |
|---|---|
| Modified | `.github/workflows/ci.yml` |
| Modified | `CHANGELOG.md` |
| Modified | `COMPATIBILITY.md` |
| Added | `PATCH_MANIFEST_v1.0.0.1.40.1.md` |
| Modified | `PROJECT_STRUCTURE.md` |
| Modified | `README.md` |
| Modified | `ROADMAP.md` |
| Modified | `SHA256SUMS.txt` |
| Modified | `VERSIONING.md` |
| Modified | `docs/api/refrens-runtime.md` |
| Modified | `docs/configuration/index.md` |
| Modified | `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md` |
| Modified | `docs/developer/ERROR_HANDLING.md` |
| Modified | `docs/developer/architecture.md` |
| Modified | `docs/docs.manifest.ygit` |
| Modified | `docs/getting-started/installation.md` |
| Modified | `docs/guides/providers.md` |
| Modified | `docs/index.md` |
| Added | `docs/release-notes/1.0.0.1.40.1.md` |
| Modified | `docs/troubleshooting/index.md` |
| Modified | `docs/user/usage.md` |
| Modified | `project/README.md` |
| Modified | `project/architecture/ARCHITECTURE.md` |
| Modified | `project/planning/PHASE_COMPLETION_LOG.md` |
| Modified | `project/planning/PRODUCTION_ROADMAP.md` |
| Modified | `project/planning/PRODUCTION_UPDATE_PROTOCOL.md` |
| Added | `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.1.md` |
| Added | `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.1.md` |
| Added | `project/specifications/BASELINE_FREEZE_v1.0.0.1.40.1.md` |
| Added | `project/specifications/P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.40.1.md` |
| Added | `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.40.1.md` |
| Modified | `pyproject.toml` |
| Modified | `scripts/build/version_info.py` |
| Modified | `src/core/provider_runtime/runtime.py` |
| Modified | `src/core/storage/domain_store.py` |
| Modified | `src/tasks/delivery_ledger.py` |
| Modified | `src/ui/main_window.py` |
| Modified | `src/ui/pages/settings_page.py` |
| Modified | `src/ui/styles.py` |
| Modified | `tests/test_p11_refrens_task.py` |
| Modified | `tests/test_p14_distribution_pipeline.py` |
| Modified | `tests/test_provider_runtime.py` |
| Modified | `tests/test_repository_contracts.py` |
| Modified | `tests/test_ui_contracts.py` |
| Modified | `vibproject.ygit` |

## Replacement contract

Extract this ZIP directly over the exact `v1.0.0.1.40` project root. No wrapper directory, file rename, file deletion or unrelated replacement is part of this delta. `SHA256SUMS.txt` covers every delta payload path except itself.
