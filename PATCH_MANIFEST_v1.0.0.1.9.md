# Patch Manifest - Invio v1.0.0.1.9

**Parent baseline:** exact `Invio_v1.0.0.1.8.zip`  
**Parent SHA-256:** `49db5f5a80c00da3c862505a329ac4a6f94ea8f60c3df4198bb3dd764d24eb06`  
**Target:** `Invio v1.0.0.1.9`  
**Scope:** P02 verification/correction only

## Runtime corrections

- `src/ui/main_window.py`
  - makes active-Task persistence-failure Stop handling re-entrancy-safe by registering the fault guard before requesting Stop;
  - updates release display/startup marker to v1.0.0.1.9.
- `src/core/storage/domain_store.py`
  - requires persisted Task account selections and account reservations to match exactly at startup;
  - rejects an Account selected by multiple persisted Tasks.
- `src/core/provider_runtime/runtime.py`
  - release User-Agent marker only; provider API business behavior is unchanged.

## Regression/release tests

- `tests/test_storage.py`
  - missing persisted reservation rejection;
  - conflicting multi-Task Account selection rejection.
- `tests/test_ui_contracts.py`
  - persistence-fault guard-before-Stop contract.
- `tests/test_repository_contracts.py`
  - current v1.0.0.1.9 release marker verification while retaining prior test-method aliases.

## Documentation and release records

The patch synchronizes README/CHANGELOG/ROADMAP/version metadata, current docs, private project roadmap/phase ledger/architecture, historical v1.0.0.1.8 errata, new v1.0.0.1.9 release notes, correction report, final verification report, production-readiness report, and baseline-freeze record.

The detailed production roadmap footer is corrected from the stale `1/14 / P02 next` state to `2/14 / P03 next`.
`vibproject.ygit` is synchronized with the approved P02 keyring dependency and v1.0.0.1.9 release metadata; no dependency constraint is changed from the already-approved P02 technology lock.

## Explicitly unchanged

- ProviderManager code and provider manifests/packages.
- WorkerManager code and one-QThread-per-active-Task architecture.
- P01 Add Account/API-test UI and verification gates.
- Account/Customer/Invoice/Task domain model fields.
- SQLite schema version 1.
- Approved `keyring` credential technology and no-plaintext-fallback rule.
- Existing application page inventory/design.
- Stripe/Refrens provider invoice behavior.
- P03-P14 functionality.

## Delta inventory

- Added files: **6**
- Changed files: **30**
- Deleted baseline files: **0**
- Total replace-ready delta files: **36**

## Delivery contract

The delta ZIP is created from project-root-relative paths with no wrapper directory. It contains only added/changed non-transient files and no `__pycache__`, `.pyc`, `.pyo`, or `.pytest_cache` entries. No baseline file is deleted by this release.

Verification details are recorded in `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.9.md`.
