## v1.0.0.1.49.2 architecture correction

The provider-account setup architecture is unchanged. `AddAccountDialog` now probes the optional Easy Onboarding runtime capability defensively through one local helper. This restores the additive boundary promised by v1.49.1: Browser OAuth-only collaborators remain valid, while a full `ProviderRuntime` still composes OAuth, `prepare_external_account()`, and API verification. No core provider runtime, Task/WorkerManager, storage, delivery-ledger, MSI or dependency architecture changes are introduced.

## v1.0.0.1.49.1 — Optional browser OAuth boundary

Browser OAuth extends P13 without replacing External Provider Adapter v1. `ProviderManager` parses the optional manifest declaration; `ExternalAdapterRegistry` validates provider OAuth hooks; `ProviderRuntime` creates authorization sessions, restricts OAuth network endpoints to HTTPS, validates completion output and never persists access tokens; `oauth.py` owns state, PKCE, redirect identity and loopback callback primitives; `AddAccountDialog` orchestrates the system browser and transfers only approved credential updates into the existing account form. Account persistence remains the unchanged AppState/DomainStore/OS-keyring path.

MSI packaging remains per-user LocalAppData. WiX now adds only a Start Menu launch component and uninstall cleanup; no installer architecture or UpgradeCode change is made.

## v1.0.0.1.49 UI architecture note

No new UI subsystem is introduced. Existing `page_header`, `section_toolbar`, `DataGridToolbar`, `QTableWidget`, provider cards and settings cards remain the architecture. The change adjusts local spacing/search geometry and table header resize/scroll policies only.

## v1.0.0.1.48.9 UI composition

`page_header()` remains the shared page-header component. `DataGridToolbar` now optionally owns a section title/actions on the same row, and `section_toolbar()` provides the same hierarchy for non-table controls. Customer Lists remains a view over the existing `AppState` callbacks and introduces no domain/service layer.

## v1.0.0.1.48.8 UI Architecture Note

Canonical status rendering remains in the existing shared widget layer. The Accounts table now respects the renderer's natural status-cell size hint instead of imposing a consumer-specific fixed width.

## v1.0.0.1.48.7 UI Architecture Note

The existing shared UI component layer is the single source for semantic status rendering. `data_status_tone()` classifies status values, `status_display_text()` applies the approved visible marker, `set_status_badge()` updates badges, and `set_data_status_cell()` owns table-cell composition without duplicate raw visible text.

## v1.0.0.1.48.6 UI Architecture Note

`AccountsPage` remains the same flat `QTableWidget` presentation/controller adapter over `AppState` and `ProviderManager`. `ACCOUNT`/`PROVIDER` share stretch space, `STATUS`/`ACTION` remain compact fixed columns, Accounts-only QSS supplies the approved semantic colors, and the existing child `QMenu` is bounded to the intersection of the owning Invio window and active screen available geometry before `exec()`. No backend, global-token, or shared-widget architecture changes.

## v1.0.0.1.48.5 UI Architecture Note

`AccountsPage` remains a presentation/controller adapter over the existing `AppState` and `ProviderManager`. The prior `QTreeWidget` provider hierarchy is replaced with a `QTableWidget` projection of account records only. Provider installation state is resolved at refresh time solely to derive the visible provider name/status and existing filter semantics. Row actions call the existing `on_edit`, `on_retest`, and `on_delete` callbacks without changing their contracts.

No domain, storage, provider-runtime, task-state or WorkerManager architecture changes are introduced.

## v1.0.0.1.48.4 UI Architecture Note

`NewTaskDialog` remains the existing `QDialog` owned by the Tasks workflow. The update changes only local widget composition: one local toolbar row, the existing `QTableWidget` + `DataGridPager`, and one local bottom configuration/action row. Shared `DataGridToolbar`, `DataGridPager`, `build_dialog_shell`, styling tokens, AppState, Task creation, ProviderRuntime and WorkerManager contracts are not redesigned.

## v1.0.0.1.48.3 CI/Public-Checkout Verification Boundary

Application architecture is unchanged. The CI contract has two verification contexts: tracked public repository records must always be testable from an Actions checkout, while `project/` is private internal material and may be additionally verified only when the full private baseline is present. The v1.48.02 narrow unignore exception violated that boundary by materializing a partial `project/` tree. `v1.0.0.1.48.3` removes those exceptions and guards the four newer private-record reads exactly like the established historical repository-contract checks. Build flow remains test → wheel → Windows native/wheel smoke → Nuitka OneDir → compiled credential smoke → WiX MSI → MSI smoke → checksum audit → artifact upload → exact-tag release.

## v1.0.0.1.48.02 QMessageBox Lifecycle Boundary

`compact_message_box()` is still the single app-owned message-box entry point. Custom Invio chrome requires the Qt widget implementation, so it now always enables `DontUseNativeDialog` before configuring/showing the box. `install_dialog_chrome()` no longer accepts an externally captured Qt-owned layout; after frameless/translucent window mutation it reacquires `dialog.layout()` and only then changes margins. This removes the stale Shiboken wrapper lifetime hazard without changing popup semantics.

## v1.0.0.1.48.01 Task Close Confirmation Boundary

The close engine remains `TaskCard.clicked -> MainWindow.close_task -> TaskAction.CLOSE guard -> active-worker guard -> confirmation -> AppState.close_task -> DomainStore.delete_task_and_release -> ProviderRuntime.clear_task -> page refresh`. The hotfix changes only the confirmation construction: Close Task opts into a widget-backed `QMessageBox` before custom chrome is installed; no state-machine, worker, persistence or provider-runtime architecture changes.

## v1.0.0.1.48.0 UI Architecture Note

The existing frameless-window architecture is preserved. `title_bars.py` now gives title-bar controls a compact right inset and renders app-owned form dialogs inside a translucent shadow margin with one `DialogSurface`; `dialogs.py` no longer adds duplicate body `PageTitle` headings. No runtime/data architecture changes.

## v1.0.0.1.47.0 UI Architecture Note

The existing PySide6 architecture is preserved. `MainWindow` owns one `MainTitleBar`; app-owned form dialogs use `build_dialog_shell()` to compose `DialogTitleBar -> DialogBody`, while `compact_message_box()` keeps its Qt-owned body and receives custom overlay chrome. Shared visual states remain QSS/token driven. No new UI framework or dependency is introduced.

## v1.0.0.1.46.0 window-chrome boundary

`src/ui/title_bars.py` owns `TitleBar`, `MainTitleBar`, `DialogTitleBar` and scoped frameless move/resize handoff. MainWindow and application-owned dialogs opt into this layer without changing their existing body layouts, callbacks, persistence or runtime architecture. Native file dialogs remain outside this boundary.

# Developer Architecture

## v1.0.0.1.45.0 UI boundary

Providers Page retains the existing `QGridLayout`/card architecture. The reflow lifecycle now hides cards before layout removal/rebuild and only shows visible cards after `grid.addWidget(...)` has established parent ownership, preventing an unparented card from becoming a transient top-level Windows window. No provider/runtime architecture changes.

## v1.0.0.1.44.0 UI boundary

The shared `page_header()` and `card()` APIs keep their existing signatures but no longer render static description arguments. This is a presentation-only behavior inside frozen UI helpers; models, state, provider runtime, WorkerManager and data-grid architecture are unchanged.

## v1.0.0.1.43.0 Data Grid UI boundary

The owner-frozen `v1.0.0.1.42.0` runtime/business architecture is unchanged. v1.43.0 adds small shared UI helpers in `src/ui/widgets.py` for search/filter and in-memory pagination, then applies them only to Accounts, Customer Lists/Records, Invoice Templates, Reports, Invoice Items and New Task Accounts. Data filters/pagers never write application state. New Task keeps the same provider/account eligibility and payload IDs while presenting available accounts in a compact `QTableWidget`. No backend pagination, sorting, persistence key, model/schema change or dependency is introduced.


## v1.0.0.1.42.0 UI boundary

The owner-frozen `v1.0.0.1.41.1` runtime architecture is unchanged. v1.42.0 is limited to `src/ui/tokens.py`, `src/ui/styles.py`, `src/ui/dialogs.py`, `src/ui/pages/settings_page.py` plus directly required tests/version/docs. Form styling is selector-scoped to `QDialog` and `SettingsPage` so the approved Providers Page geometry remains frozen. Settings search is in-memory presentation state only and does not alter `AppSettings` or SettingsManager persistence.


## 1. Scope

Invio `v1.0.0.1.41` is the owner-frozen Providers Page UI baseline. `v1.0.0.1.41.1` is a Providers Page final-polish candidate layered directly on it. The P13 trusted external-provider contract, packaged provider runtime contracts, SQLite schema v5, dependencies, Task state machine, customer/template models and one-QThread-per-Task ownership remain frozen. The implementation delta is limited to Providers-page presentation, four packaged provider-logo resources and directly required packaging/version/test/documentation synchronization.

## 2. Core Responsibilities

### Providers Page presentation boundary in v1.0.0.1.41.1

`src/ui/pages/providers_page.py` retains the v1.41 220px/280px responsive card geometry and owns the live provider search filter, 40px provider-logo rendering, logo-below Verified/Available badge placement, three-line ellipsis, bottom-right version label and bottom-anchored card action. Visible runtime/credential metadata and capability chips are intentionally absent per owner approval. `src/ui/styles.py` owns the matching Provider-card/search/logo/version/Load Provider/Providers-Uninstall QSS. `assets/icons/providers/` contains the shipped provider logo PNGs. ProviderManager, ProviderRuntime and callbacks supplied by MainWindow are consumed unchanged.

- `src/core/provider_manager/`: provider manifest validation/install/load/uninstall.
- `src/core/provider_runtime/`: packaged adapter registry, P13 external adapter registry/host operation contract, Stripe/Refrens execution, P06 preflight and structured provider log emission.
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

## P13 external executable adapter architecture

`ExternalAdapterRegistry` discovers runtime-declared external manifests in the existing registry, validates fixed installed adapter copies, and records `Executable`, `Manifest only`, `Missing`, or `Incompatible` state without letting one broken adapter abort startup. Source bundles use `provider.json` plus fixed sibling `adapter.py`; install validates the staged source before atomic registry replacement. Adapter imports use a unique stdlib `importlib` module name, restore `sys.path`, and reject import-time `sys.path` mutation. This is trusted in-process execution, not a sandbox.

`ExternalProviderAdapterV1` reuses `ProviderCapabilityProfile` and optional `ProviderSchedulingPolicy`. API Test receives a narrow context whose request callback permits safe reads only. Task validation is side-effect-free. Recipient execution receives immutable recipient/template/account data and a host request callback. The host owns P08 retry classification and P10 write-ahead operation persistence; supported operation kinds are `SAFE_READ`, `IDEMPOTENT_MUTATION`, and `NON_IDEMPOTENT_MUTATION`. External mutation ledger stages are prefixed `external_mutation:` so existing restart recovery treats interrupted mutation as `Uncertain`.

Because the P05 snapshot does not persist an external adapter version, replacement/uninstall of an executable external provider is blocked while a current Task references that provider. This avoids fabricating historical executable-code identity without changing schema v5.


### P13 forensic safety invariants

External executable bundle installation validates staged immutable bytes before atomic registry replacement. Adapter import and `create_adapter()` failures, including `SystemExit`, are contained and a persistent `sys.path` mutation is restored/rejected. External API Test is accepted only after a successful host-managed `SAFE_READ`. Task validation/execution receives isolated template data, and recipient success requires successful host-managed mutation evidence whose final stage exactly matches the adapter result. Successful non-idempotent mutation followed by adapter failure or interrupted recipient finalization remains durable `Uncertain` when replay safety cannot be proven. This external-stage recovery interpretation uses the existing schema-v5 P10 ledger and does not change built-in Stripe/Refrens semantics.

## P13 verification correction - v1.0.0.1.33

Architecture remains frozen. `ExternalAdapterRegistry.validate_adapter()` now treats all post-entrypoint metadata/callable validation as a fail-closed boundary: `BaseException` from adapter attribute access/conversion becomes `ExternalAdapterError` and therefore `Incompatible` during discovery instead of escaping startup. `ProviderManager.uninstall()` now removes active registry names by staged `os.replace` operations and rolls the manifest back if the adapter move fails; cleanup of already-detached temporary files is best-effort. No external interface version, registry location, execution context, schema, QThread ownership or packaged-provider architecture changes.


## P14 packaging/resource boundary - v1.0.0.1.34 candidate

Source and wheel installations retain the same top-level `src/`, `providers/` and `assets/` resource shape. `src/core/paths.py` resolves that application root and validates the four runtime resources required at startup. Setuptools package data now carries the three existing provider manifests and checkmark asset, and `src.core.settings` is explicitly included in the wheel package inventory. No provider execution, storage or WorkerManager architecture changed. Native Windows and live-provider certification remain evidence-gated.


## v1.0.0.1.35 distribution build boundary

The runtime architecture remains unchanged. Distribution is an outer build layer:

`main.py` → Nuitka standalone/PySide6 → `Invio` OneDir → portable ZIP and generated WiX MSI.

`src/core/paths.py` continues to prefer the historical module-relative application root used by source/wheel installs. Only when those exact frozen resources are absent does it accept the executable directory, and only when all three packaged provider manifests plus the checkmark asset exist there. This supports compiled OneDir without broad path guessing.

The WiX MSI installs the OneDir per-user in LocalAppData specifically to preserve P13's existing writable `providers/registry` under the application root. No provider registry/storage migration was introduced.

### WiX build-tool compliance

WiX is a build-time installer tool, not an Invio runtime dependency. Maintainers using the release pipeline must comply with the applicable WiX/OSMF terms. The pinned v6.0.2 command is intentionally not given the v7-only explicit EULA-acceptance switch.


## v1.0.0.1.36 CI publication boundary

The v1.35 Windows distribution architecture is unchanged. `scripts/build/` is confirmed as tracked source required by CI; root `build/`/`dist/` remain generated output. The only runtime code correction is deterministic cleanup of a partially initialized SQLite connection on an exceptional open/setup path. No component relationship, provider runtime boundary, Task/QThread ownership, schema or UI flow changes.


## v1.0.0.1.37 P14 WiX verification boundary

The Windows distribution architecture remains `wheel/native smoke -> Nuitka OneDir -> portable ZIP -> WiX MSI -> MSI smoke -> checksums/artifact upload`. WiX remains a build-only pinned dependency at `6.0.2`. The setup guard now separates the CLI informational version from its canonical core version before equality validation, because WiX v6 may report the pinned package as `6.0.2+<build-metadata>`. This is a CI verification correction only; no application architecture boundary changes.


## v1.0.0.1.38 P14 release inventory boundary

The distribution pipeline remains `wheel/native smoke -> Nuitka OneDir -> portable ZIP -> WiX MSI -> MSI smoke -> checksums/artifact upload`. The WiX build now explicitly sets `-pdbtype none` so build debug symbols do not enter the release directory. No runtime architecture, installer destination, checksum algorithm, or release payload topology changes.
## v1.0.0.1.39 compiled CredentialStore certification boundary

The application credential architecture is unchanged: domain storage keeps only opaque credential references and `CredentialStore` uses Python `keyring` with the existing approved OS-backend allow-list and no plaintext fallback. The v1.39 correction is build/certification-only around that architecture: Nuitka explicitly includes the existing keyring dependency graph and preserves keyring distribution metadata, while CI launches compiled OneDir/MSI executables in a dedicated smoke mode that executes the production `CredentialStore.set_credentials() -> get_credentials() -> delete_credentials()` path. Normal application execution never enters the smoke hook.

## v1.0.0.1.40 correction boundaries

Email-only defaults are applied between `import_customers()` and `AppState.add_customers()`: configured name/country values are applied at import, otherwise email local-part / `US` fill missing identity data. This keeps Task snapshots explicit and independent of future Settings changes. Refrens create/send remains in the existing ProviderRuntime/P10 delivery path; only unsupported request-side string-list terms are removed. Application styling is additionally installed on `QApplication` so context menus/top-level popup surfaces share the existing dark QSS. Application icon lookup is `assets/icons/app.png` then `app.ico`, with Windows AppUserModelID and Nuitka executable icon wiring.

## v1.0.0.1.40.1 scoped correction flow

The provider/runtime architecture is unchanged. Refrens now expresses its existing send workflow as two explicit P10 operations inside the same Task-owned QThread: `refrens_invoice_create` persists the returned invoice `_id`, then `refrens_invoice_create_email` calls the post-create email endpoint. Retry Failed may reuse the durable invoice reference after a definitive email failure, while ambiguous mutations remain fail-closed. Settings continues using existing shared widgets/tokens; only Settings-specific overrides are removed. The Windows pipeline retains the same Nuitka OneDir architecture and compiled credential smoke but no longer feeds a duplicate user package-config entry for `keyring`. SQLite remains schema v5.

## v1.0.0.1.40.2 provider-adapter boundary

The built-in adapter registry architecture is unchanged. Agiled now binds only `_test_agiled_account`; it still has no Task batch handler. The API-test handler sends the protected key as an HTTP Bearer token to the exact current `https://api.agiled.ai/public/v1/me` safe-read. Declared Agiled manifest capabilities remain separate from effective executable capabilities, so only `api_test` is effective. No new scheduling policy, Task runner, schema, thread, dependency or external-adapter mechanism is introduced.

Refrens keeps its existing authentication -> invoice-create -> explicit invoice-email operation chain and durable invoice-reference reuse. v1.40.2 adds only HTTP status visibility at the provider logging boundary.


## v1.0.0.1.40.2 production Odoo plugin distribution

The production release adds no provider runtime interface or WorkerManager architecture. The validated Odoo adapter is stored as distribution source at `providers/plugins/odoo/` and is loaded through the existing P13 registry workflow. It is not placed under `providers/packages/`, so packaged-provider reservation/reconciliation semantics remain unchanged. Wheel metadata includes the plugin files, while the existing Nuitka `providers=providers` data inclusion carries the same tree into Windows distributions.

## Provider Easy Onboarding V1 architecture — v1.0.0.1.49.1

Easy Onboarding extends the existing external-provider boundary without changing External Provider Adapter v1. `ProviderManager` parses optional credential ownership/choices plus `onboarding.interface_version = 1`. `ExternalAdapterRegistry` validates the adapter's `ProviderOnboardingProfile` and `prepare_account()` method. `ProviderRuntime.prepare_external_account()` supplies a constrained host HTTPS request function and validates all returned credential updates against the installed manifest. `AddAccountDialog` orchestrates Quick Connect as Browser OAuth (when declared) → provider preparation/discovery → existing API Test → existing account save/protected credential boundary.

The UI keeps every manifest field internally so existing accounts and Advanced / Manual Setup remain lossless, but only user-required fields are visible in Quick Connect. Generated/discovered/managed values never require a provider-specific UI implementation. Provider account choices carry friendly labels and exact machine values.

Onboarding is outside Task execution. It does not use or modify the delivery ledger, WorkerManager, immutable Task snapshots, Task retry/resume semantics or provider send operations. Account-setup mutations have their own explicit SAFE_READ / IDEMPOTENT_MUTATION / NON_IDEMPOTENT_MUTATION retry rules.
