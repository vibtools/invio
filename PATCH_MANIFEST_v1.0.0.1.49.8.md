# Invio v1.0.0.1.49.8 — Replace-Ready Delta Patch Manifest

**Official parent:** Invio v1.0.0.1.49.7 @ `dd0cb058b2e85198e0e12f43680510ddfaee6f47`
**Scope:** Phase 3 — Sending Scheduler / Retry / Delay Controls

## Scope implemented

- Task Network Timeout: 10–120 seconds, default 30.
- Maximum Automatic Attempts: 1–3, default 3.
- Additional Recipient Delay: 0–60 seconds, default 0.
- Provider-specific lower/equal per-account rates only under a validated declared scheduling ceiling.
- Stripe ceiling 20 req/s/account; Refrens ceiling 1 req/s/account; Odoo remains without a numeric scheduling policy.
- Immutable per-Task sending-control snapshot and additive SQLite schema v5→v6 migration.
- External scheduling-policy validation hardening and existing Settings-page controls.
- Version/tests/documentation synchronization.

## Frozen boundaries

- Phase-1 Windows native TLS behavior unchanged.
- Phase-2 fatal provider-limit / Uncertain circuit breaker unchanged.
- WorkerManager one-QThread-per-Task architecture unchanged.
- Task state-machine statuses and P10 delivery-ledger table contract unchanged.
- OAuth/Easy Onboarding, IVX, credential storage and provider business payloads unchanged.
- Phase-4 Dynamic Tags not implemented.

## Verification

- Phase-3 affected targeted suite: **344 tests — PASS; 20 PySide6-gated skips in this Linux environment**.
- Current release/distribution contract suite: **96/96 PASS**.
- Corrected historical P10 schema expectation target: **2/2 PASS**.
- Corrective final full audit: **629 tests — 609 PASS, 20 PySide6-gated SKIP, 0 FAIL, 0 ERROR**.
- Syntax / repository privacy / provider visibility: **PASS**.
- Wheel build: **PASS**.
- P14 wheel audit: **PASS — 58 source modules / 12 exact runtime resources**.
- Frozen-boundary byte comparison: **PASS**.
- Native post-change Windows/Nuitka/MSI: **PENDING non-tag GitHub CI after owner applies/pushes this delta**.

## Exact delta inventory

- Added: **6**
- Modified: **47**
- Removed: **0**
- Total paths: **53**

`M` `.github/workflows/ci.yml`
`M` `CHANGELOG.md`
`M` `COMPATIBILITY.md`
`A` `PATCH_MANIFEST_v1.0.0.1.49.8.md`
`M` `PROJECT_STRUCTURE.md`
`M` `README.md`
`M` `ROADMAP.md`
`M` `SHA256SUMS.txt`
`M` `VERSIONING.md`
`M` `docs/api/provider-manifest.md`
`M` `docs/configuration/index.md`
`M` `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
`M` `docs/developer/ERROR_HANDLING.md`
`M` `docs/developer/architecture.md`
`M` `docs/docs.manifest.ygit`
`M` `docs/getting-started/installation.md`
`M` `docs/guides/providers.md`
`M` `docs/guides/tasks.md`
`M` `docs/index.md`
`A` `docs/release-notes/1.0.0.1.49.8.md`
`M` `docs/troubleshooting/index.md`
`M` `docs/user/usage.md`
`A` `project/planning/PHASE_03_SENDING_CONTROLS_COMPLETION_v1.0.0.1.49.8.md`
`M` `project/planning/PHASE_COMPLETION_LOG.md`
`M` `project/planning/PRODUCTION_ROADMAP.md`
`A` `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.8.md`
`A` `project/research/UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.49.8.md`
`A` `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.8.md`
`M` `pyproject.toml`
`M` `src/core/provider_runtime/external.py`
`M` `src/core/provider_runtime/runtime.py`
`M` `src/core/settings/__init__.py`
`M` `src/core/settings/manager.py`
`M` `src/core/state/app_state.py`
`M` `src/core/storage/domain_store.py`
`M` `src/core/storage/schema.py`
`M` `src/tasks/models/__init__.py`
`M` `src/tasks/models/task.py`
`M` `src/ui/main_window.py`
`M` `src/ui/pages/settings_page.py`
`M` `src/ui/styles.py`
`M` `tests/test_p08_reliability.py`
`M` `tests/test_p09_scheduling.py`
`M` `tests/test_p10_delivery_ledger.py`
`M` `tests/test_p13_external_adapters.py`
`M` `tests/test_p14_distribution_pipeline.py`
`M` `tests/test_repository_contracts.py`
`M` `tests/test_settings.py`
`M` `tests/test_state.py`
`M` `tests/test_storage.py`
`M` `tests/test_ui_contracts.py`
`M` `tests/test_ui_runtime_interactions.py`
`M` `vibproject.ygit`

No wrapper directory, `.pyc`, `__pycache__`, `invio.egg-info`, build cache, or generated runtime state belongs in the final ZIP.
