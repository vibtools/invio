# Invio v1.0.0.1.25 Delta Patch Manifest

**Parent baseline:** `Invio v1.0.0.1.24`  
**Target:** `Invio v1.0.0.1.25`  
**Scope:** P09 - Multi-Account Scheduling, Limits and Health  
**Roadmap progress:** 9/14 complete; P10 next

## Implemented

- frozen `recipient_ordinal_round_robin_v1` primary assignment preserved;
- Stripe 20 API requests/second/account, burst-1 runtime pacing;
- runtime-only account/provider health and 5/10/20/40/60-second cooldown progression;
- `Retry-After` extension of local cooldown;
- deterministic circular fallback only for not-yet-attempted recipients on recognized account-scoped rate-limit cooldown;
- current-session attempted-recipient account binding prevents cross-account replay during Resume/Retry;
- provider-wide cooldown without account hopping for timeout/disconnect/408/5xx;
- 401/403 runtime account blocking until successful account re-verification;
- deterministic customer/template/operation failures remain non-failover;
- one Task = one QThread and intra-Task concurrency remains 1.

## Patch files

- `CHANGELOG.md`
- `PATCH_MANIFEST_v1.0.0.1.25.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.25.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.25.md`
- `project/research/P09_IMPLEMENTATION_LOG_v1.0.0.1.25.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.25.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.25.md`
- `pyproject.toml`
- `src/core/provider_runtime/__init__.py`
- `src/core/provider_runtime/adapters.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `tests/test_p09_scheduling.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Explicit exclusions

- no P10+ runtime behavior or persistent delivery ledger;
- no SQLite schema change;
- no dependency change;
- no WorkerManager architecture change;
- no intra-Task parallelism;
- no random/weighted account routing;
- no already-attempted recipient cross-account replay;
- no Stripe invoice payload/business-flow change;
- no Refrens P11 Task enablement;
- no Agiled execution change;
- no provider/plugin architecture expansion;
- no Settings, page, dialog or layout redesign.

## Verification summary

- parent baseline suite: 259/259 PASS;
- target suite: 277/277 PASS;
- Python compile: PASS;
- `scripts/test/audit.py`: PASS;
- JSON/YGIT/TOML parse: PASS;
- repository privacy/provider visibility audits: PASS;
- `requirements.txt`, WorkerManager, schema v4 and Task assignment model are byte-identical to parent;
- parent-to-target non-cache diff before manifest: 6 additions + 25 modifications; 0 removals;
- final delta including this manifest: 7 additions + 25 modifications = 32 files; 0 removals;
- patch cache artifacts: excluded;
- native PySide6/keyring execution unavailable in current audit container.

Fresh parent + sealed-delta overlay: 0 missing / 0 extra / 0 byte mismatch; overlay suite 277/277 PASS; repository audit PASS.
