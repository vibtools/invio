from __future__ import annotations

from decimal import Decimal
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.provider_manager import ProviderManifest
from ..core.state import AppState
from ..invoices.templates import InvoiceTemplate
from .widgets import button, card, form_group, label


class NewCustomerListDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("New Customer List")
        self.setModal(True)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(label("Create Customer List", "PageTitle", False))
        layout.addWidget(label("Create a named list first, then upload customer email addresses into that list.", "Description"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Example: August Renewals")
        layout.addWidget(form_group("List name", self.name_edit))
        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        actions.button(QDialogButtonBox.StandardButton.Ok).setText("Create List")
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)

    def list_name(self) -> str:
        return self.name_edit.text().strip()


class AddAccountDialog(QDialog):
    def __init__(self, providers: list[ProviderManifest], parent: QWidget | None = None):
        super().__init__(parent)
        self.providers = providers
        self.credential_inputs: dict[str, QLineEdit] = {}
        self._validated = False
        self.setWindowTitle("Add Account")
        self.setModal(True)
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(label("Add Provider Account", "PageTitle", False))
        root.addWidget(label("Only installed providers are available. Credentials are kept in memory for the current application session.", "Description"))

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._rebuild_provider_fields)

        self.account_name = QLineEdit()
        self.account_name.setPlaceholderText("Account label")
        self.mode_combo = QComboBox()

        root.addWidget(form_group("Provider", self.provider_combo))
        root.addWidget(form_group("Account name", self.account_name))
        root.addWidget(form_group("Mode", self.mode_combo))

        self.credentials_card = card("Credentials", "Provider-defined credential fields")
        self.credentials_layout = self.credentials_card.layout()
        root.addWidget(self.credentials_card)

        self.validation_label = label("API test has not been run.", "Caption")
        root.addWidget(self.validation_label)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        cancel = button("Cancel")
        self.test_button = button("API Test")
        self.add_button = button("Add Account", "primary")
        cancel.clicked.connect(self.reject)
        self.test_button.clicked.connect(self._ui_validate_credentials)
        self.add_button.clicked.connect(self._accept_if_valid)
        action_row.addWidget(cancel)
        action_row.addWidget(self.test_button)
        action_row.addWidget(self.add_button)
        root.addLayout(action_row)

        self.provider_combo.currentIndexChanged.connect(lambda _index: self._reset_validation())
        self.account_name.textChanged.connect(lambda _text: self._reset_validation())
        self.mode_combo.currentIndexChanged.connect(lambda _index: self._reset_validation())
        self._rebuild_provider_fields()

    def _current_provider(self) -> ProviderManifest | None:
        provider_id = self.provider_combo.currentData()
        return next((item for item in self.providers if item.id == provider_id), None)

    def _clear_dynamic_widgets(self) -> None:
        while self.credentials_layout.count() > 2:
            item = self.credentials_layout.takeAt(2)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.credential_inputs.clear()

    def _rebuild_provider_fields(self) -> None:
        self._clear_dynamic_widgets()
        provider = self._current_provider()
        self.mode_combo.clear()
        if provider is None:
            return
        self.mode_combo.addItems(provider.account_modes or ("Default",))
        for field in provider.credential_fields:
            edit = QLineEdit()
            edit.setPlaceholderText(field.placeholder)
            if field.kind == "password":
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.textChanged.connect(lambda _text: self._reset_validation())
            self.credential_inputs[field.key] = edit
            self.credentials_layout.addWidget(form_group(field.label, edit, "Required" if field.required else "Optional"))
        self._reset_validation()

    def _reset_validation(self) -> None:
        self._validated = False
        self.validation_label.setText("API test has not been run.")

    def _required_fields_present(self) -> tuple[bool, str]:
        provider = self._current_provider()
        if provider is None:
            return False, "Install a provider first."
        if not self.account_name.text().strip():
            return False, "Account name is required."
        for field in provider.credential_fields:
            if field.required and not self.credential_inputs.get(field.key, QLineEdit()).text().strip():
                return False, f"{field.label} is required."
        return True, ""

    def _ui_validate_credentials(self) -> None:
        valid, message = self._required_fields_present()
        if not valid:
            QMessageBox.warning(self, "Account", message)
            return
        self._validated = True
        self.validation_label.setText("Credential structure validated. Network verification is unavailable for this provider integration.")

    def _accept_if_valid(self) -> None:
        valid, message = self._required_fields_present()
        if not valid:
            QMessageBox.warning(self, "Account", message)
            return
        if not self._validated:
            QMessageBox.information(
                self,
                "API Test Pending",
                "Run API Test first. This provider integration currently validates the required credential fields only.",
            )
            return
        self.accept()

    def payload(self) -> dict[str, Any]:
        provider = self._current_provider()
        assert provider is not None
        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "name": self.account_name.text().strip(),
            "mode": self.mode_combo.currentText(),
            "credentials": {key: field.text().strip() for key, field in self.credential_inputs.items()},
            "status": "API Test Pending",
        }


class InvoiceTemplateDialog(QDialog):
    def __init__(self, template: InvoiceTemplate | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Invoice Template")
        self.setModal(True)
        self.resize(760, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(label("Invoice Template", "PageTitle", False))
        root.addWidget(label("Templates contain invoice content only. Customer, billing and shipping data are not part of a template.", "Description"))

        meta = card("Template Settings")
        form = QFormLayout()
        self.name_edit = QLineEdit(template.name if template else "")
        self.currency = QComboBox()
        self.currency.setEditable(True)
        self.currency.addItems(["usd", "eur", "gbp", "aud", "cad", "bdt", "jpy", "inr", "sgd"])
        self.days_due = QSpinBox()
        self.days_due.setRange(1, 365)
        self.days_due.setValue(template.days_until_due if template else 30)
        if template:
            self.currency.setCurrentText(template.currency)
        form.addRow("Template name", self.name_edit)
        form.addRow("Currency", self.currency)
        form.addRow("Days until due", self.days_due)
        meta.layout().addLayout(form)
        root.addWidget(meta)

        content = card("Invoice Content")
        self.memo = QTextEdit()
        self.memo.setMaximumHeight(72)
        self.memo.setPlaceholderText("Invoice memo / description")
        self.footer = QTextEdit()
        self.footer.setMaximumHeight(72)
        self.footer.setPlaceholderText("Invoice footer")
        self.automatic_tax = QCheckBox("Enable provider automatic tax when supported")
        self.reuse_customer = QCheckBox("Reuse exact-email provider customer when supported")
        self.reuse_customer.setChecked(True)
        if template:
            self.memo.setPlainText(template.memo)
            self.footer.setPlainText(template.footer)
            self.automatic_tax.setChecked(template.automatic_tax)
            self.reuse_customer.setChecked(template.reuse_customer)
        content.layout().addWidget(form_group("Memo", self.memo))
        content.layout().addWidget(form_group("Footer", self.footer))
        content.layout().addWidget(self.automatic_tax)
        content.layout().addWidget(self.reuse_customer)
        root.addWidget(content)

        items_card = card("Invoice Items")
        self.items = QTableWidget(0, 3)
        self.items.setHorizontalHeaderLabels(["Description", "Quantity", "Unit amount"])
        self.items.horizontalHeader().setStretchLastSection(True)
        items_card.layout().addWidget(self.items)
        item_actions = QHBoxLayout()
        add_item = button("Add Item")
        remove_item = button("Remove Selected")
        add_item.clicked.connect(self._add_item)
        remove_item.clicked.connect(self._remove_selected)
        item_actions.addWidget(add_item)
        item_actions.addWidget(remove_item)
        item_actions.addStretch(1)
        items_card.layout().addLayout(item_actions)
        root.addWidget(items_card, 1)

        if template and template.items:
            for item in template.items:
                self._add_item(item.description, str(item.quantity), str(item.unit_amount))
        else:
            self._add_item("Service", "1", "10.00")

        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        actions.accepted.connect(self._validate_and_accept)
        actions.rejected.connect(self.reject)
        root.addWidget(actions)

    def _add_item(self, description: str = "", quantity: str = "1", amount: str = "0.00") -> None:
        row = self.items.rowCount()
        self.items.insertRow(row)
        for column, value in enumerate((description, quantity, amount)):
            self.items.setItem(row, column, QTableWidgetItem(value))

    def _remove_selected(self) -> None:
        rows = sorted({item.row() for item in self.items.selectedItems()}, reverse=True)
        for row in rows:
            self.items.removeRow(row)

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invoice Template", "Template name is required.")
            return
        if self.items.rowCount() == 0:
            QMessageBox.warning(self, "Invoice Template", "Add at least one invoice item.")
            return
        self.accept()

    def payload(self) -> dict[str, Any]:
        items: list[tuple[str, str, str]] = []
        for row in range(self.items.rowCount()):
            values: list[str] = []
            for column in range(3):
                cell = self.items.item(row, column)
                values.append(cell.text().strip() if cell else "")
            items.append((values[0], values[1], values[2]))
        return {
            "template_id": self.template.id if self.template else None,
            "name": self.name_edit.text().strip(),
            "currency": self.currency.currentText().strip(),
            "days_until_due": self.days_due.value(),
            "memo": self.memo.toPlainText().strip(),
            "footer": self.footer.toPlainText().strip(),
            "automatic_tax": self.automatic_tax.isChecked(),
            "reuse_customer": self.reuse_customer.isChecked(),
            "items": items,
        }


class NewTaskDialog(QDialog):
    def __init__(self, state: AppState, providers: list[ProviderManifest], parent: QWidget | None = None):
        super().__init__(parent)
        self.state = state
        self.providers = providers
        self.setWindowTitle("New Task")
        self.setModal(True)
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(label("Create Task", "PageTitle", False))
        root.addWidget(label("Select a provider, one or more available accounts from that provider, then select a customer list.", "Description"))

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._refresh_accounts)
        root.addWidget(form_group("Provider", self.provider_combo))

        root.addWidget(label("Accounts", "FormLabel", False))
        self.accounts = QListWidget()
        self.accounts.setMinimumHeight(140)
        root.addWidget(self.accounts)
        root.addWidget(label("Accounts already assigned to another task are not selectable.", "Caption"))

        self.customer_list = QComboBox()
        for item in sorted(state.customer_lists.values(), key=lambda value: value.name.casefold()):
            self.customer_list.addItem(f"{item.name}  ({item.count} emails)", item.id)
        root.addWidget(form_group("Customer list", self.customer_list))

        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        actions.button(QDialogButtonBox.StandardButton.Ok).setText("Create Task")
        actions.accepted.connect(self._validate_and_accept)
        actions.rejected.connect(self.reject)
        root.addWidget(actions)
        self._refresh_accounts()

    def _refresh_accounts(self) -> None:
        self.accounts.clear()
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return
        for account in self.state.accounts_for_provider(provider_id):
            reserved_by = self.state.account_reservations.get(account.id)
            text = f"{account.name}  •  {account.mode}  •  {account.status}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, account.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if reserved_by:
                task_name = self.state.tasks.get(reserved_by).name if reserved_by in self.state.tasks else "another task"
                item.setText(f"{text}  •  In use by {task_name}")
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.accounts.addItem(item)

    def selected_account_ids(self) -> list[str]:
        selected: list[str] = []
        for index in range(self.accounts.count()):
            item = self.accounts.item(index)
            if item.checkState() == Qt.CheckState.Checked and item.flags() & Qt.ItemFlag.ItemIsEnabled:
                selected.append(str(item.data(Qt.ItemDataRole.UserRole)))
        return selected

    def _validate_and_accept(self) -> None:
        if not self.provider_combo.currentData():
            QMessageBox.warning(self, "Task", "Install and select a provider.")
            return
        if not self.selected_account_ids():
            QMessageBox.warning(self, "Task", "Select at least one available account.")
            return
        if not self.customer_list.currentData():
            QMessageBox.warning(self, "Task", "Create and select a customer list.")
            return
        self.accept()

    def payload(self) -> dict[str, Any]:
        provider_id = str(self.provider_combo.currentData())
        provider = next(item for item in self.providers if item.id == provider_id)
        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "account_ids": self.selected_account_ids(),
            "customer_list_id": str(self.customer_list.currentData()),
        }
