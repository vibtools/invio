# Developer Architecture

## 1. Scope

Invio v1.0.0.1 is the production desktop architecture for the requested Vib Tools application. The page structure, domain boundaries, provider visibility rule, account-reservation invariant, and per-task threading boundary are defined. Packaged provider metadata currently includes Stripe and Refrens. Provider execution remains available only through a registered provider task runner, and persistent credential storage is not configured.

## 2. Folder structure and responsibilities

```text
main.py                         Desktop entry point
src/app.py                      QApplication bootstrap
src/ui/                         Step-40J shell, styles, reusable widgets, dialogs, pages
src/accounts/                   Account domain model
src/customers/                  Customer-list model and email import
src/invoices/templates/         Invoice-only template models
src/tasks/                      Task domain model
src/core/state/                 In-memory application state and invariants
src/core/provider_manager/      Provider manifest validation/install/load
src/core/worker_manager/        One-QThread-per-active-task execution boundary
providers/packages/             Packaged Stripe/Refrens provider manifests available to install
providers/registry/             Local installed-provider registry
assets/                         UI assets
config/                         Reserved project configuration location
data/                           Reserved runtime/data location
docs/                           Public project documentation
project/                        Private development/audit records; Git-ignored
scripts/test/audit.py           Repository compile/test/privacy audit
tests/                          Domain and repository contract tests
```

## 3. Component relationships

```text
MainWindow
  ├─ ProviderManager ── providers/packages + providers/registry
  ├─ AppState
  │   ├─ Account
  │   ├─ CustomerList
  │   ├─ InvoiceTemplate
  │   └─ Task + account_reservations
  ├─ Pages / dialogs
  │   └─ read/write through MainWindow callbacks and AppState
  └─ WorkerManager
      └─ QThread(task_id) -> injected provider TaskRunner
```

The UI does not import a provider SDK and does not execute provider code. Provider manifests describe provider identity, credential fields, account modes, and declared capabilities only. `src.core.provider_manager` publicly exports `ProviderManager`, `ProviderManifest`, `ProviderManifestError`, and `CredentialField`; this keeps the existing `MainWindow` error-handling import valid.

## 4. Data flow

### Provider installation

1. Providers page reads packaged manifests through `ProviderManager.list_available()`. Current packages are Stripe and Refrens.
2. User installs a packaged provider or loads a validated external manifest.
3. The manifest is copied to `providers/registry/<provider-id>.json`.
4. Accounts and Task dialogs read only `list_installed()`.
5. Consequently, a provider does not appear in those selectors before installation/loading.

### Account creation

1. Add Account receives installed provider manifests.
2. The selected manifest dynamically defines the credential fields and account modes.
3. Current **API Test** performs required-field/credential-structure validation only.
4. The account is added to in-memory `AppState` and grouped by provider in the Accounts tree.
5. Credentials remain runtime-only and are not persisted in v1.0.0.1.

### Customer-list import

1. User creates a named `CustomerList`.
2. Importer reads CSV, TSV, TXT, XLSX, or XLSM.
3. Email-like values are normalized and de-duplicated.
4. Imported emails are attached only to the selected named list.

### Invoice-template flow

1. User creates/edits a reusable `InvoiceTemplate`.
2. Template data contains invoice settings/content and line items only.
3. Customer, billing, and shipping fields are intentionally not part of the model.

### Task creation

1. User selects an installed provider.
2. Dialog shows accounts belonging to that provider.
3. Accounts already present in `account_reservations` are disabled.
4. User selects one or more free accounts and a non-empty customer list.
5. `AppState.create_task()` re-validates provider ownership and reservation state.
6. On success, every selected account is atomically reserved to that task in application state.
7. Closing a non-running task removes the task and releases its reservations.

## 5. Execution and threading flow

`WorkerManager` owns a separate `QThread` for every active task ID. It never uses a single global worker slot.

```text
Start Task
  -> MainWindow resolves provider runner
  -> WorkerManager.start(task, runner)
  -> create QThread + _TaskWorker for that task
  -> worker invokes TaskRunner(TaskExecutionContext)
  -> progress/status/log signals return to GUI
  -> finished -> thread.quit -> cleanup slot
```

`TaskExecutionContext` supplies:

- task snapshot/reference;
- cooperative `pause_gate`;
- cooperative `stop_flag`;
- progress callback;
- log callback.

Provider sending, when supplied by a registered provider runner, must execute inside the injected runner and must not execute on the GUI thread. If no runner is registered for a selected provider, Invio reports **Provider Unavailable** and sends nothing.

## 6. Account reservation invariant

`AppState.account_reservations` is a map of `account_id -> task_id`.

The invariant is:

```text
For every account ID, zero or one task may own the reservation.
```

Both the dialog and `AppState.create_task()` enforce this. The dialog restriction is usability; the state validation is authoritative for the current in-memory model. A future persistent backend must preserve the same invariant transactionally.

## 7. Provider API contract

### Manifest contract

Documented in `docs/api/provider-manifest.md`. Manifests are validated data and are not executable provider code.

### Task runner contract

Internal extension point:

```python
MainWindow.register_task_runner(provider_id, runner)
```

`runner` must satisfy the `TaskRunner` callable protocol and receive a `TaskExecutionContext`.

A future adapter must use account-scoped/request-scoped provider credentials. The legacy process-global Stripe key pattern is explicitly prohibited by the audit.

## 8. Public and internal interfaces

This desktop application does not expose a network/public API in v1.0.0.1.

Key internal APIs are:

- `ProviderManager.list_available()`
- `ProviderManager.list_installed()`
- `ProviderManager.install_packaged()`
- `ProviderManager.load_external()`
- `ProviderManifestError` (public provider-manager validation exception)
- `AppState.create_task()` / `close_task()`
- `AppState.accounts_for_provider()`
- `WorkerManager.start()` / `pause()` / `resume()` / `stop()`
- `MainWindow.register_task_runner()`

These are current architecture boundaries, not commitments to an external compatibility API.

## 9. Dependencies

- Python 3.12+
- PySide6 6.7+ for the official Vib Tools Qt desktop UI implementation
- openpyxl 3.1+ for XLSX/XLSM customer email import

No provider SDK is a dependency in v1.0.0.1.

## 10. Configuration and runtime state

- `providers/packages/` contains distributable Stripe and Refrens manifests.
- `providers/registry/` is local runtime installation state and is Git-ignored except `.gitkeep`.
- `project/` is personal/private development material and is Git-ignored.
- Domain data is currently in memory; no persistent domain-data format is configured.

## 11. Extension points frozen for backend work

Future explicitly approved implementation can add the following behind the current boundaries:

- persistent account/customer/template/task repositories;
- protected credential storage;
- provider-specific network adapters and actual API tests;
- task runners/sending;
- retry/idempotency state;
- persistent reports/logs.

Those implementations must preserve the approved UI/page structure, installed-provider visibility rule, provider-grouped accounts, account exclusivity, and per-task worker isolation unless the user explicitly approves a change.

## 12. Architecture decisions and feature history

- **ADR-0001:** PySide6 selected because the supplied official Vib Tools Step-40J validation application is implemented with PySide6 and this is a new blank Invio project rather than a modification of the legacy PyQt6 codebase.
- **0.1.0:** UI-first architecture created with eight requested pages, manifest-only provider registry, in-memory domain state, account reservation, and separate task thread manager.
- **1.0.0 baseline:** frozen the supplied current project containing the `ProviderManifestError` export fix and bundled Stripe/Refrens provider manifests.
- **1.0.0.1:** corrected the sidebar surface, aligned existing provider cards with the official Vib Tools Plugin Page visual contract, removed development-stage product labels from current application surfaces, and preserved all existing runtime/domain behavior.
- Legacy forensic findings and backend constraints are recorded privately in `project/research/FORENSIC_AUDIT_LEGACY_APP.md`.
