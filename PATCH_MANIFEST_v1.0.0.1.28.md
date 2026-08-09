# Patch Manifest — Invio v1.0.0.1.28

**Parent baseline:** Invio v1.0.0.1.27  
**Scope:** P10 forensic verification correction — durable uncertainty reconciliation  
**Apply mode:** Extract at project root and replace matching files.  

## Inventory

- Added files including this manifest: **6**
- Modified files: **28**
- Removed files: **0**
- Total delta files: **34**

## Exact delta paths

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.28.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/getting-started/installation.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.28.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.28.md`
- `project/research/P10_VERIFICATION_CORRECTION_v1.0.0.1.28.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.28.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.28.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/ui/main_window.py`
- `tests/test_p10_delivery_ledger.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Scope assertions

- P10 remains complete; production phase count remains 10/14 and P11 remains not started.
- SQLite remains schema v5 with exactly the existing three P10 ledger tables; no schema migration is introduced.
- Durable mutating ambiguity is reconciled only by a later successful operation with the same stage and exact same non-empty idempotency key.
- Unrelated later failures cannot hide unresolved historical mutating ambiguity.
- Historical frozen primary-account and assigned-account consistency is validated fail-closed.
- `Task.id` remains the Stripe idempotency identity; `run_id` remains audit/execution identity only.
- WorkerManager, Task state machine, scheduling adapter policy, schema definition, requirements and packaged provider manifests are not modified.
- No P11+ behavior, new UI page, dependency change, provider enablement or unrelated refactor is included.
- The delta contains no wrapper directory, cache directory, `.pyc`, local secrets or runtime data.
