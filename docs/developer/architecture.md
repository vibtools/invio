# Developer Architecture

## 1. Scope

Invio `v1.0.0.1.10` preserves the P01/P02 runtime, storage, provider and WorkerManager architecture while completing P03 account lifecycle, verification-health persistence and provider-install execution consistency. No new UI page, provider execution engine, Task thread architecture, Customer contract, or Invoice contract is introduced.

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
       -> Customer Lists/emails
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
- Customer email import: complete ordered email replacement in one transaction -> in-memory list update.
- Invoice Template save: template + items + terms in one transaction -> in-memory template.
- Task create: Task + ordered selected accounts + account reservations in one transaction -> in-memory Task/reservations.
- Task close: reservation release + Task deletion in one transaction -> in-memory removal.
- Worker status/progress: Task metadata update transaction; a storage failure requests Task stop instead of silently continuing without durable state.

## 5. Credential Boundary

SQLite table `accounts` stores `credential_ref`, not credential values. `CredentialStore` stores the provider credential dictionary under service `Vib Tools Invio` and username/reference `account:<account-id>`.

Production backend acceptance is fail-closed: only the approved core OS-protected backend families or a chainer composed only of those families are accepted. Test code injects an in-memory fake backend so tests never modify a developer's personal keyring.

## 6. Schema / Migration

Current schema version: **2**, tracked by `PRAGMA user_version`. Schema v2 adds only `last_verification_at` and `verification_error_summary` to `accounts`; existing schema-v1 databases migrate transactionally with a pre-migration backup.

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

External provider manifest loading remains metadata-only unless a runner is registered. P02 does not change that provider architecture.

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
