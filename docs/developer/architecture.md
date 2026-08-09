# Developer Architecture

## 1. Scope

Invio `v1.0.0.1.7` preserves the P01 PySide6/AppState/WorkerManager/provider-runtime architecture from `v1.0.0.1.6` and re-verifies the existing Add Account verification `QThread`, real provider API-test wiring, and verified-account Task gates. Provider invoice-send execution and the existing per-Task worker architecture remain unchanged.

## 2. Core responsibilities

- `src/core/provider_manager/`: validates provider manifests and handles packaged install, external load, and uninstall.
- `src/core/provider_runtime/`: snapshots task inputs and implements packaged-provider API execution.
- `src/core/settings/`: persistent non-sensitive user preferences.
- `src/core/state/`: runtime Accounts, Customer Lists, Invoice Templates, Tasks, and reservation invariants.
- `src/core/worker_manager/`: one `QThread` per active task and signal isolation.
- `src/invoices/templates/`: reusable invoice content and supported-currency normalization.
- `src/ui/`: frozen Vib Tools shell plus Dashboard/pages/dialogs.

## 3. Domain data flow

Provider installation controls provider visibility. Account creation uses that provider's manifest fields and requires a successful executable API Test before the account is saved as `Verified`. Invoice Templates remain customer-independent. Customer Lists remain email-only. Task creation validates all inputs, binds the selected template, and reserves selected accounts.

A bound template cannot be deleted while an open task references it. A selected account cannot be reserved by two tasks.

## 4. Execution flow

1. UI creates a Task in `AppState`.
2. Start asks `MainWindow._runner_for_task()` for either an explicitly injected provider runner or `ProviderRuntime.make_task_runner()`.
3. `ProviderRuntime` snapshots account credentials, customer emails, and a deep copy of the template before worker execution.
4. `WorkerManager.start()` creates a distinct `InvioTaskThread-<task id>` and moves the worker into it.
5. Provider HTTPS calls execute inside the worker runner.
6. Progress/status/log signals update task state, Reports, Dashboard, and Live Logs.
7. Closing the task releases reservations and clears runtime retry state.

No provider network operation is intentionally executed in the task GUI callback path. Add Account API verification likewise executes in its own dialog-owned `QThread`.

## 5. Stripe adapter

The built-in Stripe adapter uses HTTPS form requests without adding the Stripe SDK. It performs customer lookup/create, draft invoice creation with `collection_method=send_invoice`, invoice item creation, finalize, and send. Template currency is stored uppercase but sent lowercase. Amounts are converted to minor units with zero-decimal and ISK/UGX handling. Invoice item decimal quantity uses Stripe's decimal quantity field when required.

Stable recipient-to-account assignment prevents a Retry Failed operation from changing accounts merely because the retry set is smaller. Deterministic per-stage idempotency keys reduce accidental duplicate operations when a network call is retried by the user/task flow.

## 6. Refrens adapter and current data boundary

The adapter includes app-secret authentication, invoice payload construction, invoice creation, and the documented create-time email-delivery payload. Refrens requires `billedTo.name` and `billedTo.country`. Current Customer Lists provide only email. The task runner therefore rejects Refrens execution before the create call instead of inventing billing country. This preserves the approved template/customer scope.

## 7. UI flow

Dashboard is a read-only operational overview backed by current state. Invoice Template uses compact two-column sections and a scroll-safe item editor. Its scroll/content host is explicitly dark, compact cards are top-aligned and non-stretching, and Currency uses editable bounded completion against the existing catalog. Settings keeps its existing controls and now uses an explicit dark scroll/content backdrop. Live Logs and Reports are unchanged in this release.

## 8. Dependencies

- Python 3.12+
- PySide6 6.7+
- openpyxl 3.1+
- Python standard library for provider HTTP/JSON/form operations

No dependency change was made in `v1.0.0.1.7`.

## 9. Extension points

`MainWindow.register_task_runner(provider_id, runner)` remains the explicit custom-provider execution hook. Future customer-data expansion, credential persistence, or additional provider-specific fields require separate owner approval and are not silently introduced through provider manifests.

## v1.0.0.1.7 verified P01 account-verification path

`AddAccountDialog` receives the existing `MainWindow.provider_runtime`. Pressing API Test snapshots provider ID, mode, and credential values and moves an `_AccountVerificationWorker` to a dialog-owned `QThread`. The worker calls `ProviderRuntime.test_account()` and emits only success/failure text back to the GUI thread. Successful verification produces account status `Verified`; any provider/mode/credential change invalidates that state. `NewTaskDialog`, `AppState.create_task()`, and `MainWindow._runner_for_task()` all enforce `Verified` status, so UI bypass or later state mutation cannot start an unverified account. Task invoice sending continues to use the existing separate `WorkerManager` task-owned QThreads.

No new dependency, provider manifest, provider credential field, account mode, storage mechanism, or task-worker architecture is introduced by P01.
