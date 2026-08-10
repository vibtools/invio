# Developer Architecture

## 1. Scope

Invio `v1.0.0.1.31` is the P12 forensic verification-correction baseline built directly on `v1.0.0.1.30`. P12 extends the existing Reports/Live Logs and schema-v5 ledger read/retention surfaces without changing provider send semantics, database schema, dependencies, Task state machine, customer model or one-QThread-per-Task ownership. P11 live Refrens acceptance remains a separate pending external evidence gate.

## 2. Core Responsibilities

- `src/core/provider_manager/`: provider manifest validation/install/load/uninstall.
- `src/core/provider_runtime/`: internal packaged-provider adapter registry, Stripe/Refrens API verification/invoice execution, P06 preflight and structured provider log emission.
- `src/core/observability.py`: non-persistent structured-log validation, provider-neutral secret/email redaction, spreadsheet-safe text handling and atomic export helpers.
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
       -> immutable Task execution snapshots
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
- Task create: Task + ordered selected accounts + account reservations + immutable execution snapshot in one transaction -> in-memory Task/reservations.
- Task close: reservation release + Task deletion in one transaction -> in-memory removal.
- Worker status/progress: Task metadata update transaction; a storage failure requests Task stop instead of silently continuing without durable state.

## 5. Credential Boundary

SQLite table `accounts` stores `credential_ref`, not credential values. `CredentialStore` stores the provider credential dictionary under service `Vib Tools Invio` and username/reference `account:<account-id>`.

Production backend acceptance is fail-closed: only the approved core OS-protected backend families or a chainer composed only of those families are accepted. Test code injects an in-memory fake backend so tests never modify a developer's personal keyring.

## 6. Schema / Migration

Current schema version: **5**, tracked by `PRAGMA user_version`. Schema v2 added Account verification-health metadata, schema v3 customer metadata, and P05 schema v4 immutable Task execution snapshots. P10 schema v5 adds exactly three delivery-ledger tables for runs, per-run recipients and provider operations. All supported migrations use WAL-aware pre-migration backup semantics and retain the v1.0.0.1.14 Windows close-before-replace fix.

Core tables:

- `accounts`
- `customer_lists`, `customer_emails`
- `invoice_templates`, `invoice_template_items`, `invoice_template_terms`
- `tasks`, `task_accounts`
- `account_reservations`
- `task_execution_snapshots`, `task_snapshot_customers`
- `task_snapshot_template`, `task_snapshot_template_items`, `task_snapshot_template_terms`

Foreign keys are enabled. Connections use `synchronous=FULL`; initialized storage uses WAL. Existing version-0 storage is backed up before migration. Future schema versions are rejected rather than downgraded.

## 7. Task Recovery Boundary

P02 recovers Task-level metadata only. `Running`, `Paused`, or `Stopping` is converted to existing status `Stopped` with a recovery message. P02 intentionally does not auto-resume external side effects.

`Task.id` is now the canonical logical run identity and P05 preserves immutable creation-time inputs, but per-recipient attempts, provider customer/invoice IDs, durable idempotency evidence, failed-recipient retry records, and exact uncertain-side-effect reconciliation remain **P10**.

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

External provider manifest loading remains metadata-only unless the historical injected runner API is registered. `v1.0.0.1.21` centralizes **packaged built-in** execution contracts only; dynamic executable loading for arbitrary external providers remains P13.

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
- P04 runtime `TaskSnapshot` still carries provider-runtime customer records and the backward-compatible email view. P05 now feeds it from the durable creation-time Task snapshot instead of live Customer List/Template state.
- Stripe batch logic remains email-based and unchanged in customer creation/reuse semantics. Refrens data can be supplied explicitly but its Task runner remains disabled until P11.

## 13. v1.0.0.1.13 P04 Verification Correction

No new architectural layer is introduced. `CustomerImportResult` carries source-row metadata alongside accepted records so `AppState.add_customers()` can keep existing-list conflict diagnostics row-aware. The customer model restores mutable-list compatibility for the pre-P04 `emails` surface while keeping `customers` authoritative. Import parser exceptions are normalized at the importer boundary. The unrelated Dashboard label change from v1.0.0.1.12 is reverted to the parent-baseline wording.
## 14. v1.0.0.1.14 Operational Storage Runtime Hotfix

No architectural layer or schema change is introduced. `DomainStore._create_migration_backup()` continues to use SQLite's live backup API so committed WAL pages are included, but it now explicitly closes the temporary destination connection before `Path.replace()` performs the atomic `.bak.tmp -> .bak` replacement. This is required on Windows because the SQLite connection context manager does not close the underlying file handle on `with` exit. The startup flow, schema v3, AppState/DomainStore/CredentialStore boundaries, ProviderRuntime, and one-QThread-per-active-Task WorkerManager remain unchanged.


## 15. P05 Immutable Task Execution Snapshot

`TaskExecutionSnapshot` is captured by `AppState.create_task()` before the Task is persisted. Its frozen model contains provider ID, ordered Account IDs, assignment strategy, ordered `CustomerRecord` recipients, and a frozen invoice-template copy with frozen item/term data. The `Task` object stores this snapshot; `Task.total` is set from its recipient count.

`DomainStore.create_task_with_reservations()` persists the Task, account bindings, reservations, snapshot metadata, recipients and template copy in the same SQLite transaction. Snapshot rows have no normal update path and are deleted with the Task. `ProviderRuntime._snapshot()` no longer reads live Customer List or Invoice Template content; it validates and converts the durable Task snapshot into the existing runtime `TaskSnapshot`.

The ordered `task_accounts` rows remain the durable account-assignment basis, and the snapshot records the assignment strategy `recipient_ordinal_round_robin_v1`. Provider credentials are not copied into SQLite snapshot tables; execution still resolves credentials from the protected Account state after existing P03 verification/provider-install gates.

Schema-v3 Tasks migrate with snapshot state `LegacyUnavailable`. Because pre-P05 releases never persisted creation-time recipients/template copies, migration does not fabricate them from current state. Legacy Tasks keep metadata/counters/reservations and can be closed, but Start/Retry fail closed in both UI and backend.

`Task.id` is the canonical logical run identity. Starting, pausing, stopping or retrying the same Task does not create another run identity. A materially different full execution requires a new Task and therefore a new Task ID/snapshot. P07 now formalizes resend-state policy; P10 still owns the durable recipient delivery ledger and restart recovery.
## 16. v1.0.0.1.16 P05 verification correction

The P05 architecture remains unchanged: Task creation captures immutable input, schema v4 persists it, and ProviderRuntime consumes that snapshot. The correction tightens invariants at the existing boundaries: `DomainStore.create_task_with_reservations()` rejects missing/legacy snapshots for new Tasks, captured progress must agree with processed recipients, and `DomainStore.update_task()` no longer updates the immutable `total` column after Task creation. No new table/module/page is introduced.

## P06 provider capability/preflight boundary

`src/core/provider_runtime/preflight.py` is a pure validation boundary between the P05 immutable Task inputs and provider runner creation. `ProviderCapabilityProfile` defines the current executable built-in contract; `PreflightResult`/`PreflightIssue` return deterministic user-correctable failures without network or domain mutation.

Flow: `NewTaskDialog payload -> preflight_candidate -> AppState.create_task/P05 snapshot`, and `Task Start/Retry -> P03 installed/account gates -> preflight_task -> injected/built-in runner -> WorkerManager`. `ProviderRuntime.make_task_runner()` also rechecks built-in static template/customer inputs so direct runtime use cannot bypass Stripe BOS/tax safety.

ProviderManager remains manifest-only. P06 adds packaged-manifest lookup and reserves packaged IDs against external-manifest collision, but does not load executable external adapters. Refrens endpoint trust validation is performed before authentication payload construction. SQLite remains schema v4; no preflight state is persisted.


## v1.0.0.1.18 P06 contract boundary

Provider preflight remains a pure validation layer. The executable built-in manifest contract is now independent of mutable packaged JSON, while valid provider execution architecture and WorkerManager boundaries are unchanged.

## v1.0.0.1.19 P07 execution-state architecture

P07 adds `src/tasks/state_machine.py` as the single transition/action-policy contract for the existing Task statuses. AppState enforces status transitions; MainWindow uses the same policy before actions; TasksPage renders button labels/enabled state from that policy. WorkerManager remains unchanged.

ProviderRuntime extends its process-local delivery state with failed and pending recipient sets. For built-in Stripe, all continuation/retry recipients are projected back into the immutable P05 recipient ordering before execution. Runtime progress is derived from those same sets, preventing UI/database counts from describing a different continuation set.

A fresh First Run initializes `pending` to every frozen recipient and `failed` to empty. A controlled recipient success removes that address from pending/failed; a controlled provider failure moves it from pending to failed. Stop leaves both sets intact, so Resume Remaining is exactly their union. Retry Failed executes only the failed set. Unexpected exceptions mark continuation unsafe rather than guessing.

These sets are deliberately not added to SQLite in P07. Startup recovery therefore preserves aggregate Task metadata but marks exact continuation unavailable; no recipient list is reconstructed from counters. Schema remains v4, and P10 remains the durable delivery/recovery phase.

## v1.0.0.1.20 P07 terminal-signal integration

The P07 status graph itself is unchanged. Qt worker terminal signals and GUI control actions are asynchronous, so MainWindow now reconciles a late queued `Completed` against an already accepted `Paused`/`Stopping`/`Stopped` control state by resolving the final state to existing `Stopped`. This keeps the state machine authoritative instead of adding `Paused/Stopping -> Completed` transitions.

MainWindow also consults `WorkerManager.is_running(task.id)` for Pause/Resume/Stop policy and action guards. WorkerManager code and one-QThread-per-active-Task architecture are unchanged. ProviderRuntime failed/pending set semantics are unchanged; a safe empty set is distinguished only at the action/message boundary.

## 17. v1.0.0.1.21 Internal Packaged-Provider Adapter Registry

`src/core/provider_runtime/adapters.py` owns execution-relevant packaged-provider truth: manifest execution contract, capability profile, API-test handler name and Task-batch handler name. `preflight.py` consumes this registry for manifest/runtime reconciliation and capability checks, while `ProviderRuntime` resolves its existing provider functions through the same registry.

This removes duplicated provider-ID dispatch without moving network implementations or changing their semantics. Stripe binds to the existing Stripe API-test and `_run_stripe_batch` methods. Refrens binds only to its existing API-test method and has no Task handler, preserving the P11 gate. Agiled has a manifest/runtime contract but no executable handlers/capabilities, so API Test and Task execution fail closed before transport. `ProviderManager` still never imports/executes provider code and dynamic external provider execution remains P13.

## 18. v1.0.0.1.22 Verification Boundary

The architecture is unchanged from `v1.0.0.1.21`. Verification adds explicit tests that packaged Agiled installation remains manifest-only, executable Stripe/Refrens handler names resolve to callable existing `ProviderRuntime` methods, Agiled has no executable handler, and the UI remains generic/manifest-driven rather than adding an Agiled-specific branch. No adapter discovery/runtime subsystem is added.

## 19. P08 Reliability Boundary - v1.0.0.1.23

The task concurrency boundary is unchanged: `MainWindow -> WorkerManager -> one QThread -> ProviderRuntime runner`. ProviderRuntime classifies transport failures and performs recipient-level bounded retry. The retry helper receives the same immutable Task snapshot and already selected AccountSnapshot, so account assignment and `Task.id`-based Stripe idempotency keys remain stable.

`WorkerManager.stop_all()` is now non-blocking and cooperative. It emits `all_stopped` only after the final task-owned thread finishes. `MainWindow.closeEvent()` ignores the first accepted shutdown request while workers are active, requests Stop, remains responsive, and performs the final close after `all_stopped`. No forced QThread termination is used.


## 20. P08 Verification Correction Boundary - v1.0.0.1.24

No architecture boundary changes. `_stdlib_transport()` now contains the complete approved transient-disconnect boundary for `IncompleteRead` and TLS EOF/clean-close cases, and preserves known HTTP status/Retry-After data when an HTTP-error body is truncated. `ProviderRuntime -> WorkerManager -> one task-owned QThread -> MainWindow` remains unchanged; no P09 scheduler/failover, P10 ledger, provider adapter, schema, dependency, or UI architecture is introduced.


## 21. P09 Scheduling Boundary - v1.0.0.1.25

The immutable Task snapshot still owns the frozen account order and `recipient_ordinal_round_robin_v1` primary mapping. `ProviderAdapterContract` now exposes an internal optional scheduling policy; Stripe declares 20 requests/second/account with burst 1 and bounded runtime health cooldown settings. `ProviderRuntime` owns monotonic per-account request slots plus runtime-only account/provider health. Failover is a deterministic circular choice only before a recipient's first provider request and only when its primary account is cooling from a recognized account-scoped limiter condition. Attempted recipients, provider/network failures, deterministic operation failures and permanent account-auth failures never cross accounts. The existing one-Task-one-QThread WorkerManager boundary remains unchanged.


## 22. P09 CI verification boundary - v1.0.0.1.26

No runtime architecture changes. The repository privacy boundary is explicit: `/project/` remains private and Git-ignored, therefore public CI tests cannot require it. Public release/roadmap records are the mandatory GitHub-checkout verification surface; full private-baseline audits additionally validate `project/` records when present.

## 23. P10 durable delivery architecture - v1.0.0.1.27

P10 adds `src/tasks/delivery_ledger.py` and advances the existing `DomainStore` schema from v4 to v5 with exactly three tables: `task_delivery_runs`, `task_delivery_recipients`, and `task_delivery_operations`. The tables intentionally retain historical delivery evidence after a live Task is closed. A unique `run_id` identifies each First Run / Resume Remaining / Retry Failed invocation, while `Task.id` remains the canonical logical Stripe idempotency identity.

For supported Stripe Task traffic the flow is `ProviderRuntime -> durable Started operation transaction -> existing transport -> durable operation result -> durable recipient result`. The write-ahead commit is required before transport. Provider customer/invoice IDs, exact assigned account, P08 attempt number, existing deterministic idempotency key, timestamps and sanitized errors are persisted. On startup `DomainStore` marks unfinished runs `Interrupted`, classifies unresolved mutating operations `Uncertain`, derives latest recipient outcomes and reconciles Task aggregate counters. ProviderRuntime reads that durable summary for restart-safe Resume Remaining / Retry Failed and hydrates only a runtime cache from it. WorkerManager remains one Task = one QThread; P09 scheduling and provider business flow are unchanged.

## 24. P10 durable uncertainty reconciliation - v1.0.0.1.28

The schema-v5 architecture is unchanged. `DomainStore` now reconstructs uncertainty across the full Task delivery history rather than trusting only the newest per-run recipient result. Mutating ambiguity is keyed by `(stage, idempotency_key)`; only later `Succeeded` evidence for the same non-empty identity resolves it. Historical primary/assigned Account consistency is validated across runs. ProviderRuntime continues to consume the same durable summary interface, so no WorkerManager, Task-state or UI architecture changes are introduced.

## P11 Refrens Task pipeline - v1.0.0.1.29

P11 enables the existing packaged Refrens adapter without adding a subsystem. The flow is `P06 preflight -> P10 begin_delivery_run -> existing task QThread -> Refrens auth -> invoice-create/email -> P10 operation/result reconciliation`. Customer data comes only from the immutable P05 `CustomerRecord` snapshot. P09 pacing is 1 request/second/account with burst 1 for Refrens, while provider-wide health suppresses speculative account hopping. Authentication can use P08 bounded retry; the invoice mutation is single-shot because the approved/current Refrens contract has no provider idempotency key in Invio. The ledger stores no JWT/App Secret and records the returned invoice `_id` as provider invoice/reference evidence. Schema remains v5 and WorkerManager is unchanged.

## P12 Observability Architecture - v1.0.0.1.30

`src/core/observability.py` provides structured log metadata validation, provider-neutral secret redaction, recipient-email masking, spreadsheet-safe text conversion and atomic text/CSV writes. `DomainStore.recipient_delivery_report()` derives support rows directly from the schema-v5 P10 ledger; `clear_closed_delivery_history()` transactionally removes only runs whose Task row no longer exists. `WorkerManager` keeps one QThread per Task and preserves `TaskExecutionContext.log`, adding only an optional structured-log callback/signal. No persistent log store is introduced.


## P12 verification correction - v1.0.0.1.31

The P12 architecture is unchanged. Central observability remains in `src/core/observability.py`; ledger-backed reporting remains in `DomainStore`; Reports and Live Logs remain the only affected UI surfaces. The correction expands named-secret parsing to quoted JSON-style fields and tightens recipient report evidence rules so provider acceptance requires a successful provider send stage. Historical account-assignment conflicts fail closed. No schema, thread ownership, provider-send path, dependency or page architecture changes are introduced.
