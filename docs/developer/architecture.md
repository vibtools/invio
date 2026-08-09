# Developer Architecture

## 1. Scope

Invio `v1.0.0.1.14` preserves the verified P01-P04 architecture and applies only the scoped operational-storage/runtime correction described in this release. No new UI page, provider execution engine, Task thread architecture, Invoice Template customer fields, or Refrens production Task runner is introduced.

## 2. Core Responsibilities

- `src/core/provider_manager/`: provider manifest validation/install/load/uninstall.
- `src/core/provider_runtime/`: packaged-provider API verification and invoice execution.
- `src/core/settings/`: non-sensitive per-user JSON preferences.
- `src/core/state/`: domain invariants plus persistence coordination for state mutations.
- `src/core/storage/schema.py`: SQLite schema version and DDL.
- `src/core/storage/domain_store.py`: durable non-sensitive state, transactions, migration, validation and recovery.
- `src/core/storage/credential_store.py`: approved OS-protected credential access through Python `keyring`; no plaintext fallback.
- `src/core/worker_manager/`: one `QThread` per active Task.

## 3. Startup Data Flow

```text
QApplication
  -> SettingsManager
  -> DomainStore(domain.sqlite3)
       -> integrity/schema check
       -> migration if supported
  -> CredentialStore(keyring)
  -> DomainStore.load(CredentialStore)
       -> Accounts metadata + protected credentials
       -> Customer Lists/customer records
       -> Invoice Templates/items/terms
       -> Tasks/account selections/reservations
       -> active-state recovery to Stopped
  -> AppState(restored domain)
  -> existing MainWindow pages
```

Corrupt/newer/unrecognized domain storage aborts startup through a user-facing critical error and is not silently recreated.

## 4. Write/Transaction Flow

`AppState` remains the application domain API. With P02 stores attached, approved mutations commit their durable representation before the in-memory mutation is finalized.

Examples:

- Add Account: protected credential write -> SQLite account metadata transaction -> in-memory account.
- Edit Account: durable `Not Verified` safety marker -> protected credential replacement -> verified SQLite candidate; compensation restores prior secret/metadata only when it can do so completely.
- Customer import: complete ordered customer-record replacement in one transaction -> in-memory list update.
- Invoice Template save: template + items + terms in one transaction -> in-memory template.
- Task create: Task + ordered selected accounts + account reservations in one transaction -> in-memory Task/reservations.
- Task close: reservation release + Task deletion in one transaction -> in-memory removal.
- Worker status/progress: Task metadata update transaction; a storage failure requests Task stop instead of silently continuing without durable state.

## 5. Credential Boundary

SQLite table `accounts` stores `credential_ref`, not credential values. `CredentialStore` stores the provider credential dictionary under service `Vib Tools Invio` and username/reference `account:<account-id>`.

Production backend acceptance is fail-closed: only the approved core OS-protected backend families or a chainer composed only of those families are accepted. Test code injects an in-memory fake backend so tests never modify a developer's personal keyring.

## 6. Schema / Migration

Current schema version: **3**, tracked by `PRAGMA user_version`. Schema v2 added Account verification-health metadata. P04 schema v3 adds optional `name` and `country` columns to the existing `customer_emails` table; existing schema-v2 rows migrate losslessly with blank metadata. All supported migrations use WAL-aware pre-migration backup semantics.

Core tables:

- `accounts`
- `customer_lists`, `customer_emails`
- `invoice_templates`, `invoice_template_items`, `invoice_template_terms`
- `tasks`, `task_accounts`
- `account_reservations`

Foreign keys are enabled. Connections use `synchronous=FULL`; initialized storage uses WAL. Existing version-0 storage is backed up before migration. Future schema versions are rejected rather than downgraded.

## 7. Task Recovery Boundary

P02 recovers Task-level metadata only. `Running`, `Paused`, or `Stopping` is converted to existing status `Stopped` with a recovery message. P02 intentionally does not auto-resume external side effects.

Per-recipient attempts, provider customer/invoice IDs, durable idempotency evidence, failed-recipient retry records, and exact uncertain-side-effect reconciliation remain **P10**.

## 8. Threading

- Add Account API Test: existing dialog-owned verification `QThread`.
- Invoice sending: existing one `QThread` per active Task.
- P02 does not move provider network operations to the GUI thread and does not change WorkerManager.

## 9. Dependencies

- Python 3.12+
- PySide6 >=6.7,<7
- openpyxl >=3.1,<4
- keyring >=25.7,<26
- stdlib `sqlite3` for domain persistence

## 10. Current Extension Boundary

External provider manifest loading remains metadata-only unless a runner is registered. P04 does not change that provider architecture.

## v1.0.0.1.9 P02 verification correction

The storage architecture is unchanged from P02. The corrective release only hardens two boundaries: persistence-failure Stop handling is re-entrancy-safe, and loaded Task/account reservation state must be an exact match before `AppState` is constructed.


## 11. P03 Account Lifecycle and Provider Consistency

- `Account` adds `last_verification_at` and `verification_error_summary`; provider identity remains immutable during Edit.
- `AppState.update_account()` blocks Task-referenced accounts, commits a re-verified candidate through protected credentials plus SQLite, and compensates the protected secret if the metadata commit fails.
- `AppState.record_account_verification()` persists Verified/Not Verified, UTC attempt time, and a credential-scrubbed error summary.
- A real failed Re-test fails closed in current runtime memory even if the verification-health database write fails; successful re-verification is not promoted unless durable persistence succeeds.
- `AppState.delete_account()` fail-safely checks both reservation and Task references, removes the protected secret, deletes durable metadata, and restores the secret if the database delete fails.
- Accounts page remains the only account UI page; it adds Edit/Re-test/Delete actions and keeps accounts visible when their provider is not installed.
- Provider uninstall is blocked while a matching Task worker is active. Inactive Tasks/accounts/reservations remain durable. `_runner_for_task()` blocks Start/Retry while the provider is absent.
- WorkerManager, ProviderManager, provider manifests and provider send behavior are unchanged.


## v1.0.0.1.11 P03 verification correction

The architecture remains unchanged. `DomainStore` now creates migration backups through SQLite's backup API so the backup includes committed WAL state, and credential-loss recovery persists the Account's `Not Verified` health state before startup completes. `AppState.update_account()` uses an existing-store fail-closed staging state before protected credentials are replaced, preventing a process interruption or failed compensation from leaving a durable `Verified` row paired with partially changed credentials. No P04 data contract or new service layer is introduced.


## 12. P04 Customer Data Contract and Import

- `CustomerRecord` is provider-neutral: mandatory normalized email, optional explicit name, optional explicit uppercase two-letter ASCII country. No name/country inference is performed.
- `CustomerList.customers` is authoritative; the historical mutable `CustomerList.emails` list behavior is preserved through a customer-record-backed compatibility view/setter.
- `AppState.add_customers()` performs deterministic merge/enrichment and commits through `DomainStore.replace_customer_records()` before mutating the live list. `add_emails()` remains a compatibility wrapper.
- Structured CSV/TSV/XLSX/XLSM import is selected only when the first usable row contains an `email` header. TXT and files without that header retain legacy email extraction.
- SQLite schema v3 preserves the existing `customer_emails` table name/order and adds `name`/`country` metadata.
- `TaskSnapshot` now carries immutable-in-run `CustomerSnapshot` records plus a backward-compatible `customer_emails` property. This is still a start-time snapshot only; P05 will define/persist the Task-creation execution snapshot.
- Stripe batch logic remains email-based and unchanged in customer creation/reuse semantics. Refrens data can be supplied explicitly but its Task runner remains disabled until P11.

## 13. v1.0.0.1.13 P04 Verification Correction

No new architectural layer is introduced. `CustomerImportResult` carries source-row metadata alongside accepted records so `AppState.add_customers()` can keep existing-list conflict diagnostics row-aware. The customer model restores mutable-list compatibility for the pre-P04 `emails` surface while keeping `customers` authoritative. Import parser exceptions are normalized at the importer boundary. The unrelated Dashboard label change from v1.0.0.1.12 is reverted to the parent-baseline wording.
## 14. v1.0.0.1.14 Operational Storage Runtime Hotfix

No architectural layer or schema change is introduced. `DomainStore._create_migration_backup()` continues to use SQLite's live backup API so committed WAL pages are included, but it now explicitly closes the temporary destination connection before `Path.replace()` performs the atomic `.bak.tmp -> .bak` replacement. This is required on Windows because the SQLite connection context manager does not close the underlying file handle on `with` exit. The startup flow, schema v3, AppState/DomainStore/CredentialStore boundaries, ProviderRuntime, and one-QThread-per-active-Task WorkerManager remain unchanged.

