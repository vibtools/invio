# Invio v1.0.0.1.6 Delta Patch Manifest

**Baseline:** `Invio v1.0.0.1.5`  
**Target:** `Invio v1.0.0.1.6`  
**Approved scope:** P01 - Real Account API Verification  
**Patch format:** project-root replace-ready ZIP, no wrapper directory

## Runtime/source changes

- `src/core/provider_runtime/runtime.py`
  - executable API-test adapter capability query;
  - mode-aware Stripe account verification;
  - release User-Agent marker.
- `src/core/state/app_state.py`
  - authoritative `Verified` account gate during Task creation.
- `src/ui/dialogs.py`
  - dedicated account-verification worker/QThread;
  - real Add Account API Test;
  - current-session verification state/reset;
  - unsupported-adapter fail-closed UI;
  - credential-safe verification feedback;
  - unverified-account New Task disablement.
- `src/ui/main_window.py`
  - Add Account binding to the existing ProviderRuntime instance;
  - Start/Retry verification re-check;
  - release markers.

## Test changes

- `tests/test_provider_runtime.py`
- `tests/test_state.py`
- `tests/test_ui_contracts.py`
- `tests/test_repository_contracts.py`

## Release metadata

- `pyproject.toml`
- `vibproject.ygit`
- `docs/docs.manifest.ygit`

## Synchronized documentation

- `README.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `PROJECT_STRUCTURE.md`
- `docs/index.md`
- `docs/api/provider-manifest.md`
- `docs/developer/architecture.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/features/ui-milestone.md`
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `docs/release-notes/1.0.0.1.6.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/P01_IMPLEMENTATION_LOG_v1.0.0.1.6.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.6.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.6.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.6.md`
- `PATCH_MANIFEST_v1.0.0.1.6.md`

## Explicitly unchanged

- provider package manifests and provider credential fields/modes/IDs;
- `src/core/provider_manager/`;
- `src/core/worker_manager/`;
- Account, Customer List, Invoice Template and Task model files;
- Stripe/Refrens invoice create/send workflow semantics;
- `requirements.txt` and third-party technology stack;
- all unrelated pages/features/workflows.

## Verification

- Final compile: PASS.
- Final unit/contract suite: 62/62 PASS.
- Repository audit: PASS.
- Existing source class/function removals: 0.
- Deleted baseline files: 0.
- Fresh baseline + delta overlay equality: verified before delivery.
- ZIP SHA-256: supplied in companion `Invio_v1.0.0.1.6_delta_patch.zip.sha256` artifact.


## Post-release verification note

The exact full `v1.0.0.1.6.zip` later supplied for re-audit contained stale ignored Refrens registry state and therefore did not satisfy the stated 62/62 full-artifact test claim. `v1.0.0.1.7` is the corrective verification release. The P01 runtime source delta listed above remains the intended P01 implementation.
