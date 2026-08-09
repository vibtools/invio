# Invio v1.0.0.1.14 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.14`  
**Official parent baseline:** exact verified `Invio v1.0.0.1.13` non-cache tree  
**Parent tree SHA-256:** `4cb80aebd316710822ed156cbc770c678967eb61fad0e142e9e6fb2e5f8dba7a`  
**Scope:** database/runtime forensic correction only  
**Production phase count:** unchanged at 4 / 14

## Functional correction

`src/core/storage/domain_store.py::_create_migration_backup()` now explicitly closes the SQLite destination connection after `source.backup(destination)` and before the temporary backup file is atomically replaced. This removes the Windows self-lock that produced `WinError 32` during supported schema migration.

SQLite schema v3, migration scripts/order, WAL-aware live backup behavior, corruption/future-schema handling, all domain persistence contracts and protected credential technology are unchanged.

## Runtime/source files changed

- `src/core/storage/domain_store.py` - functional close-before-replace correction only.
- `src/ui/main_window.py` - release-version text only.
- `src/core/provider_runtime/runtime.py` - release User-Agent version text only.

No runtime/source file was added, deleted, renamed or moved.

## Test files changed

- `tests/test_storage.py` - Windows-safe migration backup handle-lifecycle regression test.
- `tests/test_repository_contracts.py` - v1.0.0.1.14 release metadata contract while retaining prior compatibility alias test methods.

## Release/documentation records

Relevant README/CHANGELOG/ROADMAP/versioning/compatibility/configuration/troubleshooting/developer/private project records are synchronized with `v1.0.0.1.14`.

New records:

- `docs/release-notes/1.0.0.1.14.md`
- `project/research/DATABASE_RUNTIME_FORENSIC_CORRECTION_v1.0.0.1.14.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.14.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.14.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.14.md`
- `PATCH_MANIFEST_v1.0.0.1.14.md`

## Explicitly unchanged

- SQLite schema version 3 and migration DDL
- CredentialStore/keyring mechanism and dependency versions
- AppState domain/persistence behavior
- ProviderManager
- WorkerManager and one-QThread-per-active-Task architecture
- Account, Customer, Invoice Template and Task model behavior
- UI page inventory/design/UX
- packaged provider manifests
- Stripe/Refrens provider execution behavior except User-Agent release version
- `requirements.txt`
- P05 and all later roadmap features

## Final verification gate

- exact v1.0.0.1.13 baseline suite: **137/137 PASS**
- final v1.0.0.1.14 suite: **139/139 PASS**
- Windows-lock simulation: baseline **FAIL as reproduced**, fixed release **PASS**
- Python compile: PASS
- repository audit: PASS
- JSON/YGIT/TOML parse: PASS
- baseline Python symbol preservation: PASS
- protected out-of-scope hash comparison: PASS
- parent non-cache file deletion count: 0
- delta file count: 35
- fresh parent + delta non-cache byte comparison: PASS
- delta wrapper folder: none
- delta cache artifacts: none

Native PySide6 rendering, native OS keyring integration and live Stripe/Refrens provider certification are not claimed by this environment.
