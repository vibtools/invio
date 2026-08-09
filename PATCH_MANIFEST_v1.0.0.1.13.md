# Invio v1.0.0.1.13 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.13`  
**Official parent baseline:** `Invio_v1.0.0.1.12.zip`  
**Parent SHA-256:** `566c1148257411ddccd8da8fae6f91a310cc96d47a9bf7e0962d7c3ac4e9c285`  
**Scope:** P04 forensic verification and correction only  
**Production phase count:** unchanged at 4 / 14

## Forensic corrections

1. Restores the pre-P04 mutable-list behavior of `CustomerList.emails` while keeping customer records authoritative and preserving matching name/country metadata.
2. Carries source-row metadata through structured import so conflicts against already-stored customer metadata remain row-number aware.
3. Tightens the approved two-letter country contract to ASCII alphabetic characters only; country remains optional and is never guessed.
4. Normalizes malformed workbook/parser failures to the existing `ValueError` import boundary instead of leaking parser-specific runtime exceptions into the UI workflow.
5. Reverts the unrelated P04 Dashboard label drift and restores the parent-baseline `Customer Emails` wording.

## Runtime/source files changed

- `src/customers/models/customer_list.py`
- `src/customers/importers/email_importer.py`
- `src/core/state/app_state.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/dashboard_page.py` - scope restoration only; restored to pre-P04 wording.

No runtime/source file was added, deleted, renamed, or moved.

## Test files changed

- `tests/test_customer_importers.py`
- `tests/test_provider_runtime.py`
- `tests/test_repository_contracts.py`
- `tests/test_state.py`
- `tests/test_ui_contracts.py`

Regression coverage includes mutable email compatibility, metadata-preserving mutation, row-aware existing-list conflicts, ASCII country validation, malformed-workbook containment, Refrens helper validation, release metadata, and restored Dashboard wording.

## Release/documentation files

Release metadata and relevant README/CHANGELOG/ROADMAP/versioning/compatibility/user/developer/private project records are synchronized with `v1.0.0.1.13`. Historical v1.0.0.1.12 P04 implementation/final-verification records retain their original history with an appended correction notice rather than being silently rewritten.

New records:

- `docs/release-notes/1.0.0.1.13.md`
- `project/research/P04_VERIFICATION_CORRECTION_v1.0.0.1.13.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.13.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.13.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.13.md`
- `PATCH_MANIFEST_v1.0.0.1.13.md`

## Explicitly unchanged

- SQLite schema version 3 and all `src/core/storage/*` implementation
- Account model/lifecycle
- Invoice Template model/workflow
- Task model/state machine
- ProviderManager
- WorkerManager and one-QThread-per-active-Task architecture
- CredentialStore and approved keyring technology
- Customer Lists page design/columns introduced by P04
- packaged provider manifests
- shared UI styles/tokens/widgets
- dependency set and `requirements.txt`
- Stripe email-only sending semantics
- Refrens production Task enablement (still P11)
- P05 immutable Task execution inputs and all later roadmap features

## Final verification gate

- exact uploaded v1.0.0.1.12 baseline pre-change suite: **128 / 128 PASS**
- final v1.0.0.1.13 suite: **137 / 137 PASS**
- Python compile: **PASS**
- repository audit: **PASS**
- JSON/YGIT/TOML parse: **PASS**
- baseline Python symbol preservation: **PASS**
- protected out-of-scope hash comparison: **PASS**
- parent non-cache file deletion count: **0**
- fresh `v1.0.0.1.12 + delta` non-cache byte comparison: **PASS**
- delta wrapper folder: **none**
- delta `.pyc` / `__pycache__` / `.pytest_cache`: **none**

The uploaded full parent baseline contains inherited generated cache artifacts. They are not source and are not included, modified, or silently deleted by this scope-locked delta.

Native PySide6 rendering, native OS keyring integration, and live Stripe/Refrens provider certification are not claimed by this environment.
