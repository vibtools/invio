# Patch Manifest - Invio v1.0.0.1.8

**Parent baseline:** `Invio_v1.0.0.1.7.zip`  
**Approved scope:** P02 - Durable Domain Storage and Protected Credentials  
**Patch format:** project-root replace-ready delta; no wrapper directory.

## Scope summary

- Adds schema-versioned SQLite persistence for the approved non-sensitive domain state.
- Adds owner-approved protected `keyring` credential storage with no plaintext fallback.
- Adds startup recovery, migration/corruption handling, transactional persistence and persistence-failure handling.
- Preserves P01 verification/provider sending/WorkerManager/page behavior outside the P02 persistence boundary.
- Synchronizes release/documentation/test records for `v1.0.0.1.8`.

## New files

- `PATCH_MANIFEST_v1.0.0.1.8.md`
- `docs/release-notes/1.0.0.1.8.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.8.md`
- `project/research/P02_IMPLEMENTATION_LOG_v1.0.0.1.8.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.8.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.8.md`
- `src/core/storage/__init__.py`
- `src/core/storage/credential_store.py`
- `src/core/storage/domain_store.py`
- `src/core/storage/schema.py`
- `tests/test_storage.py`

## Modified files

- `.github/SECURITY.md`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
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
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `pyproject.toml`
- `requirements.txt`
- `src/accounts/models/account.py`
- `src/app.py`
- `src/core/provider_runtime/runtime.py`
- `src/core/state/app_state.py`
- `src/ui/main_window.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

## Deleted baseline files

- None.

## Verification

- Full unit/contract suite: **82/82 PASS**.
- `scripts/test/audit.py`: **PASS**.
- No pre-existing top-level Python class/function removed or renamed.
- No packaged provider manifest, ProviderManager, WorkerManager, existing UI page, shared UI widget/style/token, Customer List model, Invoice Template model/currency catalog, or Task model change.
- Native Qt/OS-keyring/live-provider certification is not claimed in the audit container; P14 remains the live/native certification gate.

## Delta hygiene

- Exclude generated `__pycache__`, `.pyc`, `.pytest_cache`, local databases, settings, credential material, and temporary files.
- SHA-256 of the final ZIP is recorded in the adjacent `.sha256` artifact.

## Post-release verification correction

The exact delivered v1.0.0.1.8 artifact was re-audited and two P02 defects were found despite the original 82-test pass: persistence-failure Stop/status re-entrancy and incomplete exact reservation recovery validation. The detailed production-roadmap footer was also stale. `v1.0.0.1.9` is the corrective P02 verification release and supersedes the original final-verification claim without changing the P02 architecture or introducing P03 work.
