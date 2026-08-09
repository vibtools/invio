# Patch Manifest — Invio v1.0.0.1.27

**Parent baseline:** Invio v1.0.0.1.26  
**Scope:** P10 — Persistent Delivery Ledger, Idempotency and Recovery  
**Apply mode:** Extract at project root and replace matching files.  

## Inventory

- Added files including this manifest: **8**
- Modified files: **32**
- Removed files: **0**
- Total delta files: **40**

## Exact delta paths

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.27.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/getting-started/installation.md`
- `docs/guides/providers.md`
- `docs/guides/tasks.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.27.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.27.md`
- `project/research/P10_IMPLEMENTATION_LOG_v1.0.0.1.27.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.27.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.27.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/core/storage/schema.py`
- `src/tasks/__init__.py`
- `src/tasks/delivery_ledger.py`
- `src/ui/main_window.py`
- `tests/test_p10_delivery_ledger.py`
- `tests/test_repository_contracts.py`
- `tests/test_storage.py`
- `vibproject.ygit`

## Scope assertions

- SQLite advances from schema v4 to v5 and adds exactly three P10 audit tables.
- `Task.id` remains the Stripe idempotency identity; P10 `run_id` is execution-audit identity only.
- WorkerManager, Task state-machine, requirements and packaged provider manifests are not modified.
- No P11+ behavior, new UI page, provider enablement, dependency change or unrelated refactor is included.
- ZIP must contain no wrapper directory, cache directory, `.pyc`, local secrets or runtime data.
