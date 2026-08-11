# Root Cause Verification — Invio v1.0.0.1.48.01

## Parent baseline
`Invio v1.0.0.1.48.0`

## Reported symptom
A Completed Task displays an enabled **Close Task** button, but clicking it does not complete the close workflow on the owner Windows canary.

## End-to-end forensic trace

1. `TaskCard.close_btn.clicked` is wired to the `on_close(task.id)` callback.
2. `TasksPage` receives `MainWindow.close_task` as that callback.
3. `TaskAction.CLOSE` permits Ready, Stopped, Failed and Completed, and blocks Running/Paused/Stopping.
4. `WorkerManager.is_running(task_id)` remains the active-thread safety gate.
5. With confirmation enabled, `MainWindow.close_task()` blocks at the question dialog before calling `AppState.close_task()`.
6. `AppState.close_task()` and `DomainStore.delete_task_and_release()` were verified by the existing state/storage/P10 tests: the backend close path remained valid, releases account reservations, deletes Task/snapshot operational rows atomically and retains historical delivery-ledger evidence.

## Root cause
The regression is in the custom-chromed `QMessageBox` confirmation boundary introduced by the frameless dialog system, not in Task state/storage execution. The message box was customized without explicitly selecting Qt's non-native/widget dialog implementation first. Qt documents `QMessageBox.Option.DontUseNativeDialog` for this purpose and requires options, particularly this option, to be set before changing dialog properties or showing the dialog.

## Scope-locked correction
`compact_message_box()` gains an opt-in `force_widget_dialog` switch. Only the Close Task call passes `True`; the option is applied immediately after `QMessageBox` construction and before window title/text/icon/buttons/custom chrome. No other confirmation path changes behavior.

## CI checkout availability
This historical verification record is intentionally allowlisted from the otherwise private `project/` tree because the frozen repository contract reads it during clean GitHub Actions checkout tests. No historical finding or runtime behavior is changed by this tracking correction.
