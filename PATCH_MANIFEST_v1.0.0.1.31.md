# Invio v1.0.0.1.31 P12 Verification-Correction Delta Patch Manifest

**Parent baseline:** `Invio_v1.0.0.1.30_baseline.zip`  
**Target:** `Invio v1.0.0.1.31`  
**Scope:** P12 forensic verification correction only.

## Confirmed corrections

- Central provider-secret redaction now covers quoted JSON-style named secret/token fields.
- Recipient report provider acceptance requires durable provider send-stage success evidence.
- Unresolved mutating operation evidence remains `Uncertain` in support reporting even if a later recipient row claims success without reconciling the ambiguity.
- Conflicting historical primary/assigned account evidence causes recipient report generation to fail closed.
- P12 remains COMPLETE; P11 remains IMPLEMENTED / LIVE ACCEPTANCE PENDING; completed acceptance phases remain 11/14.

## Inventory summary

- Added: **6**
- Modified: **27**
- Removed: **0**
- Total delta paths: **33**

## Exact delta paths

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.31.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.31.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.31.md`
- `project/research/P12_VERIFICATION_CORRECTION_v1.0.0.1.31.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.31.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.31.md`
- `pyproject.toml`
- `src/core/observability.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/storage/domain_store.py`
- `src/ui/main_window.py`
- `tests/test_p12_observability.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

## Frozen boundaries

- SQLite schema remains v5 with exactly three P10 delivery-ledger tables.
- No provider request/business-flow change.
- No P09 scheduling or P10 idempotency/recovery semantic redesign.
- No WorkerManager, Task/customer/template model, provider manifest, dependency, Settings, page inventory or UI layout redesign.
- No P13/P14 implementation.
- No baseline file removal or rename.
- Final ZIP contains no wrapper folder or cache/bytecode artifacts.
