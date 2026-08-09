# Invio v1.0.0.1.11 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.11`  
**Official parent baseline:** `Invio_v1.0.0.1.10.zip`  
**Parent SHA-256:** `66805a1fcf3bd232496112fddc1da051df315c244cf51b81b20d1360a48568da`  
**Scope:** P03 implementation verification/correction only  
**Production phase count:** 3 / 14 (unchanged)

## Corrective scope

The uploaded v1.0.0.1.10 P03 implementation initially passed its shipped automated suite, but deeper failure/recovery verification reproduced three P03 defects. This delta corrects only those defects and synchronizes release/test/documentation records.

1. **WAL-aware migration backup**
   - Replaces main-file-only migration backup with SQLite's live backup API so committed WAL state is included.
2. **Durable credential-loss fail-closed recovery**
   - Missing/unreadable protected credentials now persist `Not Verified` plus a safe error summary before startup completes.
3. **Cross-store Account Edit fail-closed safety**
   - Account Edit durably stages `Not Verified` before replacing protected credentials and only restores Verified prior state when compensation fully succeeds.

## Runtime/source files changed

- `src/core/storage/domain_store.py`
- `src/core/state/app_state.py`
- `src/core/provider_runtime/runtime.py` - release/User-Agent marker only
- `src/ui/main_window.py` - release marker only

## Test/metadata files changed

- `tests/test_storage.py`
- `tests/test_repository_contracts.py`
- `pyproject.toml`
- `vibproject.ygit`

## Documentation synchronized

- `README.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `.github/SECURITY.md`
- current user/developer/provider documentation
- production roadmap and phase-completion records
- P03 corrective forensic reports
- v1.0.0.1.11 release notes and baseline-freeze record

## Explicitly unchanged by scope

- ProviderManager implementation
- WorkerManager implementation and one-QThread-per-active-Task architecture
- SQLite schema version 2
- approved `keyring` credential-storage mechanism
- provider package manifests/credential definitions
- Account lifecycle UI actions introduced by v1.0.0.1.10
- Customer List model/workflow
- Invoice Template model/workflow
- Task model/state-machine redesign
- provider sending behavior
- P04 and later roadmap functionality
- dependencies

## Verification gate

Final release must satisfy all of the following before delivery:

- Python compile: PASS
- full unit/contract suite: PASS
- repository audit: PASS
- JSON/YGIT/TOML parse: PASS
- baseline top-level Python class/function preservation: PASS
- protected out-of-scope file comparison: PASS
- fresh `v1.0.0.1.10 + delta` overlay byte comparison: PASS (excluding generated cache artifacts)
- delta contains no wrapper folder, `.pyc`, `__pycache__`, or `.pytest_cache`

See:

- `project/research/P03_VERIFICATION_CORRECTION_v1.0.0.1.11.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.11.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.11.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.11.md`
