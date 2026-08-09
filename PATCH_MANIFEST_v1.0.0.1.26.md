# Invio v1.0.0.1.26 Delta Patch Manifest

**Parent baseline:** `Invio v1.0.0.1.25_baseline.zip`  
**Target:** `Invio v1.0.0.1.26`  
**Scope:** P09 CI / repository-contract forensic verification correction  
**Production progress:** 9/14 complete; P10 next

## Root cause corrected

GitHub Actions run `31336019074`, job `93301866645`, failed because `test_p09_completion_records_are_synchronized` required private files under `/project/`, while the repository intentionally ignores that tree. The full private baseline therefore passed locally but a clean GitHub checkout failed deterministically.

## Implemented

- mandatory P09 CI completion assertions now use tracked public records;
- private `project/` records remain additionally verified when the full private baseline is present;
- explicit `v1.0.0.1.26` release metadata contract added while historical test names remain compatibility aliases;
- release/docs/private forensic records synchronized;
- P09 runtime behavior unchanged except release/User-Agent markers.

## Patch files

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.26.md`
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
- `docs/release-notes/1.0.0.1.26.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.26.md`
- `project/research/P09_CI_VERIFICATION_CORRECTION_v1.0.0.1.26.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.26.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.26.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Explicit exclusions / preserved behavior

- no P10+ runtime behavior;
- no P09 scheduler/rate/cooldown/failover semantic change;
- no WorkerManager change;
- no SQLite schema change;
- no dependency change;
- no Task assignment change;
- no Stripe invoice payload/business-flow/idempotency change;
- no Refrens P11 enablement;
- no Agiled execution change;
- no plugin architecture expansion;
- no Settings/page/dialog/layout/UX change;
- no publication of the private `/project/` tree;
- no baseline file removal or rename.

## Verification summary

- parent full private baseline: 277/277 PASS before correction;
- reported GitHub Actions checkout reproduced `FileNotFoundError` for ignored `project/` record;
- target full private baseline: 278/278 PASS;
- clean public-checkout simulation with `/project/` removed: 278/278 PASS;
- `scripts/test/audit.py`: PASS in both full-private and clean-public simulations;
- compileall `src`, `tests`, `main.py`: PASS;
- JSON/YGIT/TOML parse: PASS;
- runtime/main-window source is parent-equivalent after release-marker normalization;
- final parent-to-target non-cache diff: 6 additions + 24 modifications = 30 files; 0 removals;
- manifest vs actual diff paths: exact 30/30 match;
- fresh parent + sealed-delta overlay: 0 missing / 0 extra / 0 byte mismatch;
- fresh overlay full-private audit: 278/278 PASS;
- fresh overlay clean-public-checkout audit (`/project/` absent): 278/278 PASS;
- patch wrapper folder: none;
- cache artifacts excluded from final delta.
