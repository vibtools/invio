from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..accounts.models import Account
from ..core.provider_manager import ProviderManifest
from ..core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from ..core.state import AppState
from ..invoices.templates import InvoiceTemplate, SUPPORTED_INVOICE_CURRENCIES
from .tokens import CONST
from .widgets import (
    DataGridPager,
    DataGridToolbar,
    button,
    card,
    data_badge_host,
    data_table_item,
    form_group,
    label,
)


class _AccountVerificationWorker(QObject):
    succeeded = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        runtime: ProviderRuntime,
        provider_id: str,
        credentials: dict[str, str],
        mode: str,
    ) -> None:
        super().__init__()
        self.runtime = runtime
        self.provider_id = provider_id
        self.credentials = dict(credentials)
        self.mode = mode

    @Slot()
    def run(self) -> None:
        try:
            message = self.runtime.test_account(
                self.provider_id,
                self.credentials,
                mode=self.mode,
            )
        except ProviderRuntimeError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("API verification failed because of an unexpected internal error.")
        else:
            self.succeeded.emit(message)
        finally:
            self.finished.emit()


def _verification_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _apply_compact_dialog_geometry(
    dialog: QDialog,
    parent: QWidget | None,
    *,
    width_ratio: float,
    preferred_height: int,
    min_width: int,
    max_width: int,
    min_height: int,
) -> None:
    """Size application-owned dialogs relative to the main window.

    The width remains generous for readable forms while the height is capped to
    keep modal workflows compact. Native operating-system file dialogs are not
    altered by this helper.
    """
    width = min_width
    height = preferred_height
    if parent is not None and parent.width() > 0 and parent.height() > 0:
        width = max(min_width, min(max_width, int(parent.width() * width_ratio)))
        height = max(min_height, min(preferred_height, int(parent.height() * 0.72)))
    else:
        width = min(max_width, max(min_width, int(max_width * 0.9)))
        height = max(min_height, preferred_height)
    dialog.resize(width, height)


def compact_message_box(
    parent: QWidget | None,
    title: str,
    text: str,
    *,
    icon: QMessageBox.Icon = QMessageBox.Icon.Information,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    default_button: QMessageBox.StandardButton | None = None,
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(icon)
    box.setStandardButtons(buttons)
    if default_button is not None:
        box.setDefaultButton(default_button)
    width = 520
    if parent is not None and parent.width() > 0:
        width = max(440, min(640, int(parent.width() * 0.42)))
    box.setMinimumWidth(width)
    result = box.exec()
    return QMessageBox.StandardButton(result)


def _invoice_wrapped_label(text: str, role: str = "Description") -> QLabel:
    """Create wrapped Invoice Template text that keeps its required height.

    Invoice Template content lives inside a resizable scroll area.  The shared
    application label helper intentionally permits aggressive shrinking for
    general-purpose surfaces, but that policy can collapse wrapped form notes
    when this compact dialog is resized.  Keep this stricter sizing contract
    local to the Invoice Template UI so no unrelated page geometry changes.
    """
    item = label(text, role, True)
    policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    policy.setHeightForWidth(True)
    item.setSizePolicy(policy)
    return item


def _invoice_form_group(label_text: str, field: QWidget, help_text: str = "") -> QWidget:
    """Invoice-template-only form group with minimum-content height."""
    host = QWidget()
    host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    layout.addWidget(label(label_text, "FormLabel", False))
    layout.addWidget(field)
    if help_text:
        layout.addWidget(_invoice_wrapped_label(help_text, "Caption"))
    return host


def _dialog_card(title_text: str) -> QWidget:
    item = card(title_text)
    item.layout().setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
    item.layout().setSpacing(CONST.dialog_gap)
    return item


def _dialog_footer(primary_text: str, primary_handler: Callable[[], None], cancel_handler: Callable[[], None]) -> QWidget:
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(CONST.dialog_gap)
    layout.addStretch(1)
    cancel_button = button("Cancel")
    primary_button = button(primary_text, "primary")
    cancel_button.clicked.connect(cancel_handler)
    primary_button.clicked.connect(primary_handler)
    layout.addWidget(cancel_button)
    layout.addWidget(primary_button)
    return host


class NewCustomerListDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("New Customer List")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.48, preferred_height=250, min_width=480, max_width=680, min_height=230
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
        layout.setSpacing(CONST.dialog_gap)
        layout.addWidget(label("Create Customer List", "PageTitle", False))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Example: August Renewals")
        layout.addWidget(form_group("List name", self.name_edit))
        layout.addWidget(_dialog_footer("Create List", self.accept, self.reject))

    def list_name(self) -> str:
        return self.name_edit.text().strip()


class AddAccountDialog(QDialog):
    def __init__(
        self,
        providers: list[ProviderManifest],
        parent: QWidget | None = None,
        *,
        provider_runtime: ProviderRuntime | None = None,
        log_callback: Callable[[str], None] | None = None,
        account: Account | None = None,
    ):
        super().__init__(parent)
        self.providers = providers
        self.provider_runtime = provider_runtime or ProviderRuntime()
        self.log_callback = log_callback
        self.account = account
        self._provider_locked = account is not None
        self.credential_inputs: dict[str, QLineEdit] = {}
        self._validated = False
        self._last_verification_at = ""
        self._verification_thread: QThread | None = None
        self._verification_worker: _AccountVerificationWorker | None = None
        self._verification_credentials: dict[str, str] = {}
        self.setWindowTitle("Edit Account" if account is not None else "Add Account")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.64, preferred_height=450, min_width=760, max_width=920, min_height=390
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
        root.setSpacing(CONST.dialog_gap)
        root.addWidget(label("Edit Provider Account" if account is not None else "Add Provider Account", "PageTitle", False))

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._rebuild_provider_fields)

        self.account_name = QLineEdit(account.name if account is not None else "")
        self.account_name.setPlaceholderText("Account label")
        self.mode_combo = QComboBox()

        account_fields = QWidget()
        account_grid = QGridLayout(account_fields)
        account_grid.setContentsMargins(0, 0, 0, 0)
        account_grid.setHorizontalSpacing(CONST.dialog_gap)
        account_grid.setVerticalSpacing(CONST.dialog_gap)
        account_grid.addWidget(form_group("Provider", self.provider_combo), 0, 0)
        account_grid.addWidget(form_group("Mode", self.mode_combo), 0, 1)
        account_grid.addWidget(form_group("Account name", self.account_name), 1, 0, 1, 2)
        account_grid.setColumnStretch(0, 1)
        account_grid.setColumnStretch(1, 1)
        root.addWidget(account_fields)

        self.credentials_card = _dialog_card("Credentials")
        self.credentials_host = QWidget()
        self.credentials_layout = QGridLayout(self.credentials_host)
        self.credentials_layout.setContentsMargins(0, 0, 0, 0)
        self.credentials_layout.setHorizontalSpacing(CONST.dialog_gap)
        self.credentials_layout.setVerticalSpacing(CONST.dialog_gap)
        self.credentials_card.layout().addWidget(self.credentials_host)
        root.addWidget(self.credentials_card)

        self.validation_label = label("API test has not been run.", "Caption")
        root.addWidget(self.validation_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(CONST.dialog_gap)
        action_row.addStretch(1)
        self.cancel_button = button("Cancel")
        self.test_button = button("API Test")
        self.add_button = button("Save Changes" if account is not None else "Add Account", "primary")
        self.cancel_button.clicked.connect(self.reject)
        self.test_button.clicked.connect(self._ui_validate_credentials)
        self.add_button.clicked.connect(self._accept_if_valid)
        action_row.addWidget(self.cancel_button)
        action_row.addWidget(self.test_button)
        action_row.addWidget(self.add_button)
        root.addLayout(action_row)

        self.provider_combo.currentIndexChanged.connect(lambda _index: self._reset_validation())
        self.account_name.textChanged.connect(lambda _text: self._reset_validation())
        self.mode_combo.currentIndexChanged.connect(lambda _index: self._reset_validation())
        self._rebuild_provider_fields()
        self.provider_combo.setEnabled(not self._provider_locked)
        if account is not None:
            mode_index = self.mode_combo.findText(account.mode, Qt.MatchFlag.MatchFixedString)
            if mode_index >= 0:
                self.mode_combo.setCurrentIndex(mode_index)
            for key, value in account.credentials.items():
                field = self.credential_inputs.get(key)
                if field is not None:
                    field.setText(value)
            self._reset_validation()

    def _current_provider(self) -> ProviderManifest | None:
        provider_id = self.provider_combo.currentData()
        return next((item for item in self.providers if item.id == provider_id), None)

    def _clear_dynamic_widgets(self) -> None:
        while self.credentials_layout.count():
            item = self.credentials_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.credential_inputs.clear()

    def _rebuild_provider_fields(self) -> None:
        self._clear_dynamic_widgets()
        provider = self._current_provider()
        self.mode_combo.clear()
        if provider is None:
            self._update_api_test_availability()
            return
        self.mode_combo.addItems(provider.account_modes or ("Default",))
        column_count = 2 if len(provider.credential_fields) > 2 else 1
        for index, field in enumerate(provider.credential_fields):
            edit = QLineEdit()
            edit.setPlaceholderText(field.placeholder)
            if field.kind == "password":
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.textChanged.connect(lambda _text: self._reset_validation())
            self.credential_inputs[field.key] = edit
            row, column = divmod(index, column_count)
            self.credentials_layout.addWidget(
                form_group(field.label, edit),
                row,
                column,
            )
        for column in range(column_count):
            self.credentials_layout.setColumnStretch(column, 1)
        self._reset_validation()

    def _has_api_test_adapter(self) -> bool:
        provider = self._current_provider()
        return bool(provider and self.provider_runtime.supports_api_test(provider.id))

    def _update_api_test_availability(self) -> None:
        available = self._has_api_test_adapter()
        if not self._verification_running():
            self.test_button.setEnabled(available)
        if not available:
            self._validated = False
            self.validation_label.setText(
                "API Test is unavailable for this provider because no executable API-test adapter is installed."
            )

    def _reset_validation(self) -> None:
        if self._verification_running():
            return
        self._validated = False
        self._last_verification_at = ""
        if self._has_api_test_adapter():
            self.validation_label.setText("API test has not been run.")
        else:
            self.validation_label.setText(
                "API Test is unavailable for this provider because no executable API-test adapter is installed."
            )
        self._update_api_test_availability()

    def _required_fields_present(self) -> tuple[bool, str]:
        provider = self._current_provider()
        if provider is None:
            return False, "Install a provider first."
        if not self.account_name.text().strip():
            return False, "Account name is required."
        for field in provider.credential_fields:
            input_widget = self.credential_inputs.get(field.key)
            if field.required and (input_widget is None or not input_widget.text().strip()):
                return False, f"{field.label} is required."
        return True, ""

    def _credential_values(self) -> dict[str, str]:
        return {key: field.text().strip() for key, field in self.credential_inputs.items()}

    def _verification_running(self) -> bool:
        return self._verification_thread is not None and self._verification_thread.isRunning()

    def _set_verification_controls_enabled(self, enabled: bool) -> None:
        self.provider_combo.setEnabled(enabled and not self._provider_locked)
        self.account_name.setEnabled(enabled)
        self.mode_combo.setEnabled(enabled)
        for field in self.credential_inputs.values():
            field.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.add_button.setEnabled(enabled)
        self.test_button.setEnabled(enabled and self._has_api_test_adapter())

    def _safe_verification_message(self, message: str) -> str:
        safe = str(message).strip() or "Provider API verification failed."
        for secret in sorted((value for value in self._verification_credentials.values() if value), key=len, reverse=True):
            safe = safe.replace(secret, "***REDACTED***")
        return safe

    def _log_verification(self, message: str) -> None:
        if self.log_callback is not None:
            self.log_callback(message)

    def _ui_validate_credentials(self) -> None:
        """Preserved Add Account API-Test action hook; now performs real verification."""
        self._start_api_test()

    def _start_api_test(self) -> None:
        if self._verification_running():
            return
        valid, message = self._required_fields_present()
        if not valid:
            compact_message_box(self, "Account", message, icon=QMessageBox.Icon.Warning)
            return
        provider = self._current_provider()
        if provider is None:
            compact_message_box(self, "Account", "Install a provider first.", icon=QMessageBox.Icon.Warning)
            return
        if not self.provider_runtime.supports_api_test(provider.id):
            self._update_api_test_availability()
            compact_message_box(
                self,
                "API Test Unavailable",
                "This provider has no executable API-test adapter in the current Invio runtime.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        self._validated = False
        credentials = self._credential_values()
        self._verification_credentials = dict(credentials)
        mode = self.mode_combo.currentText().strip()
        self.validation_label.setText(f"Testing {provider.name} connection...")
        self._set_verification_controls_enabled(False)
        self._log_verification(
            f"API Test started: {provider.name}/{self.account_name.text().strip()} ({mode or 'Default'})."
        )

        thread = QThread(self)
        thread.setObjectName(f"InvioAccountApiTest-{provider.id}")
        worker = _AccountVerificationWorker(self.provider_runtime, provider.id, credentials, mode)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._verification_succeeded)
        worker.failed.connect(self._verification_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._verification_finished)
        thread.finished.connect(thread.deleteLater)
        self._verification_thread = thread
        self._verification_worker = worker
        thread.start()

    @Slot(str)
    def _verification_succeeded(self, message: str) -> None:
        safe = self._safe_verification_message(message)
        self._validated = True
        self._last_verification_at = _verification_timestamp()
        self.validation_label.setText(safe)
        provider = self._current_provider()
        provider_name = provider.name if provider is not None else "Provider"
        self._log_verification(
            f"API Test verified: {provider_name}/{self.account_name.text().strip()} ({self.mode_combo.currentText().strip() or 'Default'})."
        )
        compact_message_box(self, "API Test", safe, icon=QMessageBox.Icon.Information)

    @Slot(str)
    def _verification_failed(self, message: str) -> None:
        safe = self._safe_verification_message(message)
        self._validated = False
        self._last_verification_at = ""
        self.validation_label.setText(f"Verification failed: {safe}")
        provider = self._current_provider()
        provider_name = provider.name if provider is not None else "Provider"
        self._log_verification(
            f"API Test failed: {provider_name}/{self.account_name.text().strip()} ({self.mode_combo.currentText().strip() or 'Default'}): {safe}"
        )
        compact_message_box(self, "API Test Failed", safe, icon=QMessageBox.Icon.Warning)

    @Slot()
    def _verification_finished(self) -> None:
        self._verification_worker = None
        self._verification_thread = None
        self._verification_credentials.clear()
        self._set_verification_controls_enabled(True)
        self._update_api_test_availability()

    def _accept_if_valid(self) -> None:
        valid, message = self._required_fields_present()
        if not valid:
            compact_message_box(self, "Account", message, icon=QMessageBox.Icon.Warning)
            return
        if not self._has_api_test_adapter():
            compact_message_box(
                self,
                "API Test Unavailable",
                "This provider cannot become Task-ready because no executable API-test adapter is available.",
                icon=QMessageBox.Icon.Warning,
            )
            return
        if not self._validated:
            compact_message_box(
                self,
                "API Test Required",
                "Run API Test and complete a real provider verification before adding this account.",
                icon=QMessageBox.Icon.Warning,
            )
            return
        self.accept()

    def reject(self) -> None:  # type: ignore[override]
        if self._verification_running():
            self.validation_label.setText("API Test is still running. Wait for it to finish before closing this dialog.")
            return
        super().reject()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._verification_running():
            self.validation_label.setText("API Test is still running. Wait for it to finish before closing this dialog.")
            event.ignore()
            return
        super().closeEvent(event)

    def payload(self) -> dict[str, Any]:
        provider = self._current_provider()
        assert provider is not None
        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "name": self.account_name.text().strip(),
            "mode": self.mode_combo.currentText(),
            "credentials": self._credential_values(),
            "status": "Verified",
            "last_verification_at": self._last_verification_at,
            "verification_error_summary": "",
        }


class AccountRetestDialog(QDialog):
    """Run a real API verification against one already-saved account."""

    def __init__(
        self,
        account: Account,
        parent: QWidget | None = None,
        *,
        provider_runtime: ProviderRuntime | None = None,
        log_callback: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.account = account
        self.provider_runtime = provider_runtime or ProviderRuntime()
        self.log_callback = log_callback
        self._verification_thread: QThread | None = None
        self._verification_worker: _AccountVerificationWorker | None = None
        self._verification_credentials = dict(account.credentials)
        self.verified = False
        self.result_message = ""
        self.last_verification_at = ""
        self.setWindowTitle("Re-test Account")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.46, preferred_height=250, min_width=520, max_width=680, min_height=230
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
        root.setSpacing(CONST.dialog_gap)
        root.addWidget(label("Re-test Provider Account", "PageTitle", False))
        self.status_label = label("Starting API Test...", "Caption")
        root.addWidget(self.status_label)
        root.addStretch(1)
        self.close_button = button("Close")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.reject)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        QTimer.singleShot(0, self._start_api_test)

    def _safe_verification_message(self, message: str) -> str:
        safe = str(message).strip() or "Provider API verification failed."
        for secret in sorted((value for value in self._verification_credentials.values() if value), key=len, reverse=True):
            safe = safe.replace(secret, "***REDACTED***")
        return safe

    def _log_verification(self, message: str) -> None:
        if self.log_callback is not None:
            self.log_callback(message)

    def _start_api_test(self) -> None:
        if self._verification_thread is not None and self._verification_thread.isRunning():
            return
        if not self.provider_runtime.supports_api_test(self.account.provider_id):
            self.verified = False
            self.result_message = "API Test is unavailable because no executable API-test adapter is installed."
            self.last_verification_at = _verification_timestamp()
            self.status_label.setText(self.result_message)
            self.close_button.setEnabled(True)
            return
        if not self._verification_credentials:
            self.verified = False
            self.result_message = "Protected provider credentials are unavailable."
            self.last_verification_at = _verification_timestamp()
            self.status_label.setText(self.result_message)
            self.close_button.setEnabled(True)
            return

        self._log_verification(
            f"API Re-test started: {self.account.provider_name}/{self.account.name} ({self.account.mode or 'Default'})."
        )
        thread = QThread(self)
        thread.setObjectName(f"InvioAccountApiRetest-{self.account.id}")
        worker = _AccountVerificationWorker(
            self.provider_runtime, self.account.provider_id, self._verification_credentials, self.account.mode
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._verification_succeeded)
        worker.failed.connect(self._verification_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._verification_finished)
        thread.finished.connect(thread.deleteLater)
        self._verification_thread = thread
        self._verification_worker = worker
        thread.start()

    @Slot(str)
    def _verification_succeeded(self, message: str) -> None:
        self.verified = True
        self.result_message = self._safe_verification_message(message)
        self.last_verification_at = _verification_timestamp()
        self.status_label.setText(self.result_message)
        self._log_verification(
            f"API Re-test verified: {self.account.provider_name}/{self.account.name} ({self.account.mode or 'Default'})."
        )

    @Slot(str)
    def _verification_failed(self, message: str) -> None:
        self.verified = False
        self.result_message = self._safe_verification_message(message)
        self.last_verification_at = _verification_timestamp()
        self.status_label.setText(f"Verification failed: {self.result_message}")
        self._log_verification(
            f"API Re-test failed: {self.account.provider_name}/{self.account.name} ({self.account.mode or 'Default'}): {self.result_message}"
        )

    @Slot()
    def _verification_finished(self) -> None:
        self._verification_worker = None
        self._verification_thread = None
        self._verification_credentials.clear()
        self.close_button.setEnabled(True)
        self.accept()

    def reject(self) -> None:  # type: ignore[override]
        if self._verification_thread is not None and self._verification_thread.isRunning():
            self.status_label.setText("API Test is still running. Wait for it to finish before closing this dialog.")
            return
        super().reject()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._verification_thread is not None and self._verification_thread.isRunning():
            self.status_label.setText("API Test is still running. Wait for it to finish before closing this dialog.")
            event.ignore()
            return
        super().closeEvent(event)


class InvoiceTemplateDialog(QDialog):
    def __init__(self, template: InvoiceTemplate | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Invoice Template")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.74, preferred_height=620, min_width=900, max_width=1080, min_height=520
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
        root.setSpacing(CONST.dialog_gap)
        root.addWidget(label("Invoice Template", "PageTitle", False))

        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_host = QWidget()
        content_host.setObjectName("DialogContent")
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(CONST.dialog_gap)
        content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        upper_host = QWidget()
        upper_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        upper = QGridLayout(upper_host)
        upper.setContentsMargins(0, 0, 0, 0)
        upper.setHorizontalSpacing(CONST.dialog_gap)
        upper.setVerticalSpacing(CONST.dialog_gap)

        settings_card = _dialog_card("Template Settings")
        settings_grid = QGridLayout()
        settings_grid.setContentsMargins(0, 0, 0, 0)
        settings_grid.setHorizontalSpacing(CONST.dialog_gap)
        settings_grid.setVerticalSpacing(CONST.dialog_gap)

        self.name_edit = QLineEdit(template.name if template else "")
        self.name_edit.setPlaceholderText("Template name")
        self.currency = QComboBox()
        self.currency.setEditable(True)
        self.currency.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.currency.setDuplicatesEnabled(False)
        self.currency.setMaxVisibleItems(8)
        self.currency.addItems(SUPPORTED_INVOICE_CURRENCIES)
        self.currency.lineEdit().setPlaceholderText("Type to search currency")
        currency_completer = QCompleter(SUPPORTED_INVOICE_CURRENCIES, self.currency)
        currency_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        currency_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        currency_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        currency_completer.setMaxVisibleItems(8)
        currency_completer.popup().setObjectName("CurrencySearchResults")
        self.currency.setCompleter(currency_completer)
        self.days_due = QSpinBox()
        self.days_due.setRange(1, 365)
        self.days_due.setValue(template.days_until_due if template else 30)
        self.invoice_type = QComboBox()
        self.invoice_type.addItem("Invoice", "INVOICE")
        self.invoice_type.addItem("Bill of Supply", "BOS")
        if template:
            self.currency.setCurrentText(template.currency.upper())
            type_index = self.invoice_type.findData(template.invoice_type)
            if type_index >= 0:
                self.invoice_type.setCurrentIndex(type_index)
        else:
            self.currency.setCurrentText("USD")

        settings_grid.addWidget(_invoice_form_group("Template name", self.name_edit), 0, 0, 1, 2)
        settings_grid.addWidget(_invoice_form_group("Currency", self.currency), 1, 0)
        settings_grid.addWidget(_invoice_form_group("Days until due", self.days_due), 1, 1)
        settings_grid.addWidget(_invoice_form_group("Invoice type", self.invoice_type), 2, 0, 1, 2)
        settings_grid.setColumnStretch(0, 2)
        settings_grid.setColumnStretch(1, 3)
        settings_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_card.layout().addLayout(settings_grid)
        upper.addWidget(settings_card, 0, 0, Qt.AlignmentFlag.AlignTop)

        content_card = _dialog_card("Invoice Content")
        content_grid = QGridLayout()
        content_grid.setContentsMargins(0, 0, 0, 0)
        content_grid.setHorizontalSpacing(CONST.dialog_gap)
        content_grid.setVerticalSpacing(CONST.dialog_gap)
        self.invoice_title = QLineEdit(template.invoice_title if template else "Invoice")
        self.invoice_title.setPlaceholderText("Invoice")
        self.invoice_subtitle = QLineEdit(template.invoice_subtitle if template else "")
        self.invoice_subtitle.setPlaceholderText("Optional subtitle")
        self.memo = QTextEdit()
        self.memo.setFixedHeight(52)
        self.memo.setPlaceholderText("Optional invoice note / memo")
        self.customer_note = QTextEdit()
        self.customer_note.setFixedHeight(52)
        self.customer_note.setPlaceholderText("Optional customer-facing note")
        if template:
            self.memo.setPlainText(template.memo)
            self.customer_note.setPlainText(template.customer_note)
        content_grid.addWidget(_invoice_form_group("Invoice title", self.invoice_title), 0, 0)
        content_grid.addWidget(_invoice_form_group("Invoice subtitle (optional)", self.invoice_subtitle), 0, 1)
        content_grid.addWidget(_invoice_form_group("Invoice note (optional)", self.memo), 1, 0)
        content_grid.addWidget(_invoice_form_group("Customer note (optional)", self.customer_note), 1, 1)
        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)
        content_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_card.layout().addLayout(content_grid)
        upper.addWidget(content_card, 0, 1, Qt.AlignmentFlag.AlignTop)
        upper.setColumnStretch(0, 1)
        upper.setColumnStretch(1, 1)
        upper.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(upper_host, 0, Qt.AlignmentFlag.AlignTop)

        secondary_card = _dialog_card("Footer, Terms & Provider Options")
        secondary_grid = QGridLayout()
        secondary_grid.setContentsMargins(0, 0, 0, 0)
        secondary_grid.setHorizontalSpacing(CONST.dialog_gap)
        secondary_grid.setVerticalSpacing(CONST.dialog_gap)
        self.footer = QTextEdit()
        self.footer.setFixedHeight(52)
        self.footer.setPlaceholderText("Optional invoice footer")
        self.terms = QTextEdit()
        self.terms.setFixedHeight(52)
        self.terms.setPlaceholderText("Optional terms; one term per line")
        self.automatic_tax = QCheckBox("Enable provider automatic tax when supported")
        self.reuse_customer = QCheckBox("Reuse exact-email provider customer when supported")
        self.reuse_customer.setChecked(True)
        if template:
            self.footer.setPlainText(template.footer)
            self.terms.setPlainText("\n".join(template.terms))
            self.automatic_tax.setChecked(template.automatic_tax)
            self.reuse_customer.setChecked(template.reuse_customer)
        secondary_grid.addWidget(_invoice_form_group("Footer (optional)", self.footer), 0, 0)
        secondary_grid.addWidget(_invoice_form_group("Terms (optional)", self.terms), 0, 1)
        option_host = QWidget()
        option_layout = QVBoxLayout(option_host)
        option_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.setSpacing(CONST.dialog_gap)
        option_layout.addWidget(self.automatic_tax)
        option_layout.addWidget(self.reuse_customer)
        secondary_grid.addWidget(option_host, 1, 0, 1, 2)
        secondary_grid.setColumnStretch(0, 1)
        secondary_grid.setColumnStretch(1, 1)
        secondary_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        secondary_card.layout().addLayout(secondary_grid)
        content_layout.addWidget(secondary_card, 0, Qt.AlignmentFlag.AlignTop)

        items_card = _dialog_card("Invoice Items")
        self.items_pager = DataGridPager(on_changed=self._refresh_item_view)
        self.items_toolbar = DataGridToolbar(
            "Search items...",
            on_changed=self._item_controls_changed,
        )
        items_card.layout().addWidget(self.items_toolbar)
        self.items = QTableWidget(0, 4)
        self.items.setObjectName("InvoiceItemsTable")
        self.items.setHorizontalHeaderLabels(["DESCRIPTION", "QUANTITY", "UNIT AMOUNT", "TAX %"])
        self.items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setAlternatingRowColors(True)
        self.items.verticalHeader().setVisible(False)
        self.items.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        header = self.items.horizontalHeader()
        header.setSectionsClickable(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.items.setMinimumHeight(150)
        self.items.setMaximumHeight(210)
        items_card.layout().addWidget(self.items)
        item_actions = QHBoxLayout()
        item_actions.setSpacing(CONST.dialog_gap)
        add_item = button("Add Item")
        remove_item = button("Remove Selected")
        add_item.clicked.connect(self._add_item)
        remove_item.clicked.connect(self._remove_selected)
        item_actions.addWidget(add_item)
        item_actions.addWidget(remove_item)
        item_actions.addStretch(1)
        items_card.layout().addLayout(item_actions)
        items_card.layout().addWidget(self.items_pager)
        content_layout.addWidget(items_card, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addStretch(1)

        if template and template.items:
            for item in template.items:
                self._add_item(item.description, str(item.quantity), str(item.unit_amount), str(item.tax_rate))
        else:
            self._add_item("Service", "1", "10.00", "0")

        scroll.setWidget(content_host)
        root.addWidget(scroll, 1)

        root.addWidget(_dialog_footer("Save", self._validate_and_accept, self.reject))

    def _item_controls_changed(self) -> None:
        self.items_pager.reset()
        self._refresh_item_view()

    def _refresh_item_view(self) -> None:
        query = self.items_toolbar.query
        matching_rows: list[int] = []
        for row in range(self.items.rowCount()):
            values = [self.items.item(row, column).text() if self.items.item(row, column) else "" for column in range(4)]
            if not query or query in " ".join(values).casefold():
                matching_rows.append(row)
        start, end = self.items_pager.set_total(len(matching_rows))
        visible_rows = set(matching_rows[start:end])
        for row in range(self.items.rowCount()):
            self.items.setRowHidden(row, row not in visible_rows)

    def _add_item(
        self,
        description: str = "",
        quantity: str = "1",
        amount: str = "0.00",
        tax_rate: str = "0",
    ) -> None:
        row = self.items.rowCount()
        self.items.insertRow(row)
        for column, value in enumerate((description, quantity, amount, tax_rate)):
            self.items.setItem(row, column, data_table_item(value, right_align=column in {1, 2, 3}))
        self._refresh_item_view()

    def _remove_selected(self) -> None:
        rows = sorted({item.row() for item in self.items.selectedItems()}, reverse=True)
        for row in rows:
            self.items.removeRow(row)
        self._refresh_item_view()

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            compact_message_box(self, "Invoice Template", "Template name is required.", icon=QMessageBox.Icon.Warning)
            return
        currency_code = self.currency.currentText().strip().upper()
        if currency_code not in SUPPORTED_INVOICE_CURRENCIES:
            compact_message_box(
                self,
                "Invoice Template",
                "Type and select a supported currency from the search results.",
                icon=QMessageBox.Icon.Warning,
            )
            return
        self.currency.setCurrentText(currency_code)
        if self.items.rowCount() == 0:
            compact_message_box(self, "Invoice Template", "Add at least one invoice item.", icon=QMessageBox.Icon.Warning)
            return
        self.accept()

    def payload(self) -> dict[str, Any]:
        items: list[tuple[str, str, str, str]] = []
        for row in range(self.items.rowCount()):
            values: list[str] = []
            for column in range(4):
                cell = self.items.item(row, column)
                values.append(cell.text().strip() if cell else "")
            items.append((values[0], values[1], values[2], values[3]))
        return {
            "template_id": self.template.id if self.template else None,
            "name": self.name_edit.text().strip(),
            "currency": self.currency.currentText().strip().upper(),
            "days_until_due": self.days_due.value(),
            "invoice_title": self.invoice_title.text().strip(),
            "invoice_subtitle": self.invoice_subtitle.text().strip(),
            "invoice_type": str(self.invoice_type.currentData()),
            "memo": self.memo.toPlainText().strip(),
            "customer_note": self.customer_note.toPlainText().strip(),
            "footer": self.footer.toPlainText().strip(),
            "terms": [line.strip() for line in self.terms.toPlainText().splitlines() if line.strip()],
            "automatic_tax": self.automatic_tax.isChecked(),
            "reuse_customer": self.reuse_customer.isChecked(),
            "items": items,
        }


class NewTaskDialog(QDialog):
    def __init__(self, state: AppState, providers: list[ProviderManifest], parent: QWidget | None = None):
        super().__init__(parent)
        self.state = state
        self.providers = providers
        self._checked_account_ids: set[str] = set()
        self.setWindowTitle("New Task")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.60, preferred_height=520, min_width=700, max_width=860, min_height=450
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding)
        root.setSpacing(CONST.dialog_gap)
        root.addWidget(label("Create Task", "PageTitle", False))

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)
        root.addWidget(form_group("Provider", self.provider_combo))

        root.addWidget(label("Accounts", "FormLabel", False))
        self.accounts_pager = DataGridPager(on_changed=self._refresh_accounts)
        self.accounts_toolbar = DataGridToolbar(
            "Search accounts...",
            on_changed=self._account_controls_changed,
            filters=(
                ("Availability", (("All", ""), ("Available", "available"), ("Unavailable", "unavailable"))),
                ("Status", (("All statuses", ""),)),
            ),
        )
        root.addWidget(self.accounts_toolbar)
        self.accounts = QTableWidget(0, 4)
        self.accounts.setObjectName("NewTaskAccountsTable")
        self.accounts.setHorizontalHeaderLabels(["✓", "ACCOUNT NAME", "MODE", "STATUS"])
        self.accounts.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.accounts.setAlternatingRowColors(True)
        self.accounts.verticalHeader().setVisible(False)
        self.accounts.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        self.accounts.itemChanged.connect(self._account_item_changed)
        accounts_header = self.accounts.horizontalHeader()
        accounts_header.setSectionsClickable(False)
        accounts_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        accounts_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        accounts_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        accounts_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.accounts)
        root.addWidget(self.accounts_pager)

        selectors = QWidget()
        selectors_grid = QGridLayout(selectors)
        selectors_grid.setContentsMargins(0, 0, 0, 0)
        selectors_grid.setHorizontalSpacing(CONST.dialog_gap)
        selectors_grid.setVerticalSpacing(CONST.dialog_gap)
        self.invoice_template = QComboBox()
        for item in sorted(state.invoice_templates.values(), key=lambda value: value.name.casefold()):
            self.invoice_template.addItem(f"{item.name}  •  {item.currency.upper()}", item.id)
        self.customer_list = QComboBox()
        for item in sorted(state.customer_lists.values(), key=lambda value: value.name.casefold()):
            self.customer_list.addItem(f"{item.name}  ({item.count} emails)", item.id)
        selectors_grid.addWidget(form_group("Invoice template", self.invoice_template), 0, 0)
        selectors_grid.addWidget(form_group("Customer list", self.customer_list), 0, 1)
        selectors_grid.setColumnStretch(0, 1)
        selectors_grid.setColumnStretch(1, 1)
        root.addWidget(selectors)

        root.addWidget(_dialog_footer("Create Task", self._validate_and_accept, self.reject))
        self._refresh_accounts()

    def _provider_changed(self, _index: int) -> None:
        self._checked_account_ids.clear()
        self.accounts_pager.reset()
        self._refresh_accounts()

    def _account_controls_changed(self) -> None:
        self.accounts_pager.reset()
        self._refresh_accounts()

    def _account_rows(self):
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return []
        records = []
        for account in self.state.accounts_for_provider(provider_id):
            reserved_by = self.state.account_reservations.get(account.id)
            if account.status != "Verified":
                available = False
                display_status = account.status or "Not Verified"
                tooltip_status = f"{display_status} • API Test required"
            elif reserved_by:
                available = False
                task_name = self.state.tasks.get(reserved_by).name if reserved_by in self.state.tasks else "another task"
                display_status = f"In use by {task_name}"
                tooltip_status = display_status
            else:
                available = True
                display_status = "Verified"
                tooltip_status = "Verified • Available"
            records.append((account, available, display_status, tooltip_status))
        return records

    def _refresh_accounts(self) -> None:
        records = self._account_rows()
        statuses = sorted({account.status for account, _available, _display, _tip in records}, key=str.casefold)
        self.accounts_toolbar.set_filter_options(1, [("All statuses", ""), *((value, value) for value in statuses)])

        query = self.accounts_toolbar.query
        availability_filter = str(self.accounts_toolbar.filter_value(0) or "")
        status_filter = str(self.accounts_toolbar.filter_value(1) or "")
        filtered = []
        for record in records:
            account, available, display_status, tooltip_status = record
            if availability_filter == "available" and not available:
                continue
            if availability_filter == "unavailable" and available:
                continue
            if status_filter and account.status != status_filter:
                continue
            searchable = f"{account.name} {account.mode} {account.status} {display_status} {tooltip_status}".casefold()
            if query and query not in searchable:
                continue
            filtered.append(record)

        start, end = self.accounts_pager.set_total(len(filtered))
        visible = filtered[start:end]
        self.accounts.blockSignals(True)
        self.accounts.setRowCount(0)
        for account, available, display_status, tooltip_status in visible:
            row = self.accounts.rowCount()
            self.accounts.insertRow(row)
            checkbox = data_table_item("")
            checkbox.setData(Qt.ItemDataRole.UserRole, account.id)
            checkbox.setFlags(checkbox.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checkbox.setCheckState(Qt.CheckState.Checked if account.id in self._checked_account_ids else Qt.CheckState.Unchecked)
            if not available:
                checkbox.setFlags(checkbox.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self._checked_account_ids.discard(account.id)
            self.accounts.setItem(row, 0, checkbox)
            self.accounts.setItem(row, 1, data_table_item(account.name))
            self.accounts.setItem(row, 2, data_table_item(account.mode))
            status_item = data_table_item(display_status, tooltip=tooltip_status)
            self.accounts.setItem(row, 3, status_item)
            self.accounts.setCellWidget(row, 3, data_badge_host(display_status, "success" if available else "warning"))
        self.accounts.blockSignals(False)
        self._adjust_accounts_height(len(visible))

    def _adjust_accounts_height(self, visible_count: int) -> None:
        row_count = max(1, min(visible_count, self.accounts_pager.page_size))
        desired = CONST.table_header_height + row_count * CONST.table_row_height + 4
        height = min(CONST.data_grid_accounts_max_height, max(62, desired))
        self.accounts.setFixedHeight(height)

    def _account_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        account_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not account_id:
            return
        if item.checkState() == Qt.CheckState.Checked and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            self._checked_account_ids.add(account_id)
        else:
            self._checked_account_ids.discard(account_id)

    def selected_account_ids(self) -> list[str]:
        provider_id = self.provider_combo.currentData()
        selected: list[str] = []
        for account in self.state.accounts_for_provider(str(provider_id or "")):
            if account.id not in self._checked_account_ids:
                continue
            if account.status != "Verified" or self.state.account_reservations.get(account.id):
                continue
            selected.append(account.id)
        return selected

    def _validate_and_accept(self) -> None:
        if not self.provider_combo.currentData():
            compact_message_box(self, "Task", "Install and select a provider.", icon=QMessageBox.Icon.Warning)
            return
        if not self.selected_account_ids():
            compact_message_box(self, "Task", "Select at least one available account.", icon=QMessageBox.Icon.Warning)
            return
        if not self.invoice_template.currentData():
            compact_message_box(self, "Task", "Create and select an invoice template.", icon=QMessageBox.Icon.Warning)
            return
        if not self.customer_list.currentData():
            compact_message_box(self, "Task", "Create and select a customer list.", icon=QMessageBox.Icon.Warning)
            return
        self.accept()

    def payload(self) -> dict[str, Any]:
        provider_id = str(self.provider_combo.currentData())
        provider = next(item for item in self.providers if item.id == provider_id)
        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "account_ids": self.selected_account_ids(),
            "invoice_template_id": str(self.invoice_template.currentData()),
            "customer_list_id": str(self.customer_list.currentData()),
        }

