# Invio v1.0.0.1.12 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.12`  
**Official parent baseline:** `Invio_v1.0.0.1.11.zip`  
**Parent SHA-256:** `38416c66839e2fc6e8645675e6955d688dbf643cb1b9782b1083341d8d0df467`  
**Scope:** P04 - Customer Data Contract and Import Upgrade  
**Production phase count:** 4 / 14

## Runtime/source scope

- `src/customers/models/customer_list.py`: backward-compatible `CustomerRecord`/`CustomerList` contract.
- `src/customers/importers/email_importer.py`: structured customer import plus preserved legacy email import.
- `src/core/state/app_state.py`: transactional customer merge/enrichment while preserving `add_emails()`.
- `src/core/storage/schema.py`: schema v3.
- `src/core/storage/domain_store.py`: customer metadata load/save and v2->v3 migration.
- `src/core/provider_runtime/runtime.py`: customer-aware task snapshot and truthful P11 Refrens gate; Stripe email send behavior retained.
- `src/ui/pages/customer_lists_page.py`: existing page Email/Name/Country presentation and Upload Customers wording.
- `src/ui/pages/dashboard_page.py`: customer metric label corrected from email-specific wording.
- `src/ui/main_window.py`: structured import/merge summary integration and release marker.

## Tests

- Added `tests/test_customer_importers.py`.
- Extended state/storage/provider/UI/repository regression contracts.
- Final suite requirement: all baseline + P04 tests PASS.

## Documentation synchronized

README, CHANGELOG, ROADMAP, VERSIONING, PROJECT_STRUCTURE, COMPATIBILITY, user/provider/task/invoice/configuration/troubleshooting/developer documentation, production roadmap, phase ledger, P04 implementation log, production-readiness report, final verification report and baseline-freeze record.

## Explicitly unchanged

- Account lifecycle/model
- Invoice Template model/workflow
- Task model/state machine
- ProviderManager
- WorkerManager
- CredentialStore
- packaged provider manifests
- shared UI styles/tokens/widgets
- dependency set / `requirements.txt`
- Refrens production Task enablement
- P05 and later roadmap implementation

## Verification gate

- Python compile: PASS
- full unit/contract suite: PASS
- repository audit: PASS
- JSON/YGIT/TOML parse: PASS
- baseline top-level Python symbol preservation: PASS
- protected out-of-scope hash comparison: PASS
- fresh `v1.0.0.1.11 + delta` overlay byte comparison: PASS
- delta must contain no wrapper folder, `.pyc`, `__pycache__`, or `.pytest_cache`
