# Developer Architecture

## 1. Scope

Invio `v1.0.0.1.5` uses the same PySide6/AppState/WorkerManager/provider-runtime architecture as `v1.0.0.1.4`. This release changes only Invoice Template presentation geometry plus release metadata/tests/documentation; provider/task execution semantics are unchanged.

## 2. Core responsibilities

- `src/core/provider_manager/`: validates provider manifests and handles packaged install, external load, and uninstall.
- `src/core/provider_runtime/`: snapshots task inputs and implements packaged-provider API execution.
- `src/core/settings/`: persistent non-sensitive user preferences.
- `src/core/state/`: runtime Accounts, Customer Lists, Invoice Templates, Tasks, and reservation invariants.
- `src/core/worker_manager/`: one `QThread` per active task and signal isolation.
- `src/invoices/templates/`: reusable invoice content and supported-currency normalization.
- `src/ui/`: frozen Vib Tools shell plus Dashboard/pages/dialogs.

## 3. Domain data flow

Provider installation controls provider visibility. Account creation uses that provider's manifest fields. Invoice Templates remain customer-independent. Customer Lists remain email-only. Task creation validates all inputs, binds the selected template, and reserves selected accounts.

A bound template cannot be deleted while an open task references it. A selected account cannot be reserved by two tasks.

## 4. Execution flow

1. UI creates a Task in `AppState`.
2. Start asks `MainWindow._runner_for_task()` for either an explicitly injected provider runner or `ProviderRuntime.make_task_runner()`.
3. `ProviderRuntime` snapshots account credentials, customer emails, and a deep copy of the template before worker execution.
4. `WorkerManager.start()` creates a distinct `InvioTaskThread-<task id>` and moves the worker into it.
5. Provider HTTPS calls execute inside the worker runner.
6. Progress/status/log signals update task state, Reports, Dashboard, and Live Logs.
7. Closing the task releases reservations and clears runtime retry state.

No provider network operation is intentionally executed in the task GUI callback path.

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

No dependency change was made in `v1.0.0.1.5`.

## 9. Extension points

`MainWindow.register_task_runner(provider_id, runner)` remains the explicit custom-provider execution hook. Future customer-data expansion, credential persistence, or additional provider-specific fields require separate owner approval and are not silently introduced through provider manifests.
