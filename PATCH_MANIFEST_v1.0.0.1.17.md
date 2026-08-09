# Invio v1.0.0.1.17 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.17`  
**Official parent baseline:** reconstructed exact `Invio v1.0.0.1.16` non-cache tree  
**Parent tree SHA-256:** `61370f08748ba548517dd5adf15dff1b351b90c279840cb84bb84ba97a1f8ad1`  
**Scope:** P06 - Provider Capability and Preflight Validation  
**Production phase count:** 6 / 14

## Functional implementation

- Adds `src/core/provider_runtime/preflight.py` with immutable capability/profile/result contracts and pure provider/account/template/customer validation.
- Reconciles packaged manifest declarations with executable built-in Stripe/Refrens runtime capability.
- Reserves packaged provider IDs from external-manifest replacement and fails closed on execution-relevant packaged manifest/runtime mismatch.
- Runs candidate preflight before New Task persistence/account reservation.
- Runs Start/Retry preflight against P05 immutable Task inputs before runner construction.
- Revalidates Account verification health, mode, required credential presence, and Stripe mode/key consistency.
- Blocks unsupported Stripe `BOS`, Automatic Tax under the current customer-location contract, unsupported currency, and non-zero template percentage line tax before invoice creation.
- Pins Refrens authentication transport to canonical `https://api.refrens.com` before App ID/App Secret payload construction.
- Shows declared vs runtime provider capability on the existing Providers page.
- Preserves Refrens normal Task execution gate until P11.

## Runtime/source files changed

- `src/core/provider_manager/manager.py`
- `src/core/provider_runtime/__init__.py`
- `src/core/provider_runtime/preflight.py` (new)
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/providers_page.py`

## Test files changed

- `tests/test_provider_preflight.py` (new)
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`

## Release/documentation records

README, CHANGELOG, ROADMAP, VERSIONING, structure/compatibility, provider/task/template/user/configuration/troubleshooting/API/developer documentation and private production records are synchronized with P06.

New records:

- `docs/release-notes/1.0.0.1.17.md`
- `project/research/P06_IMPLEMENTATION_LOG_v1.0.0.1.17.md`
- `project/research/PROVIDER_CONTRACT_REVALIDATION_v1.0.0.1.17.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.17.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.17.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.17.md`
- `PATCH_MANIFEST_v1.0.0.1.17.md`

## Explicitly unchanged

- SQLite schema v4 and all `src/core/storage/*`
- WorkerManager and one-QThread-per-active-Task architecture
- `AppState`
- Account, Customer, Invoice Template and Task model packages
- packaged Stripe/Refrens provider manifests
- existing external `register_task_runner(provider_id, runner)` API
- dependency versions / `requirements.txt`
- unrelated pages and shared UI styles/tokens/widgets
- P07-P14 behavior

## Final verification gate

- exact v1.0.0.1.16 parent suite: **169/169 PASS**
- final v1.0.0.1.17 suite: **194/194 PASS**
- Python compile: PASS
- repository audit: PASS
- JSON/YGIT/TOML parse: PASS
- SQLite schema remains v4: PASS
- baseline Python symbol preservation: PASS
- protected out-of-scope byte comparison: PASS
- parent non-cache file deletion count: 0
- delta file count: **43**
- delta wrapper folder: none
- delta cache artifacts: none

Native PySide6 rendering, native OS keyring integration and live owner-provider certification are not claimed by this environment.
