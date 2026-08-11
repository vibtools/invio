# Root Cause Verification — Invio v1.0.0.1.48.02

## Parent baseline
`Invio v1.0.0.1.48.01`

## Observed production failure
Windows runtime reports repeatedly failed inside `compact_message_box()` while installing custom dialog chrome:

`RuntimeError: libshiboken: Internal C++ object (PySide6.QtWidgets.QGridLayout) already deleted.`

The same failure was observed from Close Task confirmation, New Task validation warnings and Customer Import feedback, proving a shared popup-layer regression rather than independent backend/button failures.

## Exact root cause
`compact_message_box()` captured `box.layout()` and passed that Qt-owned layout wrapper into `install_dialog_chrome()`. The helper then changed top-level window flags/attributes via the frameless custom-chrome path before dereferencing the captured layout. For `QMessageBox`, Qt may rebuild its internally owned grid layout during those window mutations. The caller-held Shiboken wrapper can therefore reference a deleted C++ `QGridLayout` when `contentsMargins()` is read.

## Scope-locked fix
1. Every app-owned compact `QMessageBox` is forced to the Qt widget implementation with `DontUseNativeDialog` before title/text/button/chrome configuration.
2. Callers no longer pass `box.layout()` into `install_dialog_chrome()`.
3. `install_dialog_chrome()` applies frameless/translucent window mutation first, then reacquires `dialog.layout()` and validates it before margin access.
4. Existing popup wording, buttons, return values and all downstream business handlers remain unchanged.
5. Real PySide6 interaction tests exercise modal `exec()` and actual button clicks when PySide6 is installed.

## Frozen backend
Task state machine, AppState, WorkerManager, storage/schema, delivery ledger, provider runtime, customer import logic, invoice logic and settings are not modified.

## Approved P14 packaging compatibility correction
Public application/tag identity remains `1.0.0.1.48.02` / `v1.0.0.1.48.02`. Because Python packaging canonicalizes the numeric segment `02` to `2`, P14 wheel metadata/release-inventory validation expects `1.0.0.1.48.2` and `invio-1.0.0.1.48.2-py3-none-any.whl`. Portable ZIP/MSI naming, PE/MSI mapping, runtime/UI/business behavior and CI tag identity are unchanged.

## CI checkout availability
This historical verification record is intentionally allowlisted from the otherwise private `project/` tree because the frozen repository contract reads it during clean GitHub Actions checkout tests. No historical finding or runtime behavior is changed by this tracking correction.
