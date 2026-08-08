from __future__ import annotations

from decimal import Decimal
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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

from ..core.provider_manager import ProviderManifest
from ..core.state import AppState
from ..invoices.templates import InvoiceTemplate, SUPPORTED_INVOICE_CURRENCIES
from .widgets import button, card, form_group, label


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


class NewCustomerListDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("New Customer List")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.48, preferred_height=250, min_width=480, max_width=680, min_height=230
        )
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
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.64, preferred_height=450, min_width=760, max_width=920, min_height=390
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)
        root.addWidget(label("Add Provider Account", "PageTitle", False))
        root.addWidget(label("Only installed providers are available. Credentials are kept in memory for the current application session.", "Description"))

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._rebuild_provider_fields)

        self.account_name = QLineEdit()
        self.account_name.setPlaceholderText("Account label")
        self.mode_combo = QComboBox()

        account_fields = QWidget()
        account_grid = QGridLayout(account_fields)
        account_grid.setContentsMargins(0, 0, 0, 0)
        account_grid.setHorizontalSpacing(12)
        account_grid.setVerticalSpacing(8)
        account_grid.addWidget(form_group("Provider", self.provider_combo), 0, 0)
        account_grid.addWidget(form_group("Mode", self.mode_combo), 0, 1)
        account_grid.addWidget(form_group("Account name", self.account_name), 1, 0, 1, 2)
        account_grid.setColumnStretch(0, 1)
        account_grid.setColumnStretch(1, 1)
        root.addWidget(account_fields)

        self.credentials_card = card("Credentials", "Provider-defined credential fields")
        self.credentials_host = QWidget()
        self.credentials_layout = QGridLayout(self.credentials_host)
        self.credentials_layout.setContentsMargins(0, 0, 0, 0)
        self.credentials_layout.setHorizontalSpacing(12)
        self.credentials_layout.setVerticalSpacing(8)
        self.credentials_card.layout().addWidget(self.credentials_host)
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
                form_group(field.label, edit, "Required" if field.required else "Optional"),
                row,
                column,
            )
        for column in range(column_count):
            self.credentials_layout.setColumnStretch(column, 1)
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
            input_widget = self.credential_inputs.get(field.key)
            if field.required and (input_widget is None or not input_widget.text().strip()):
                return False, f"{field.label} is required."
        return True, ""

    def _ui_validate_credentials(self) -> None:
        valid, message = self._required_fields_present()
        if not valid:
            compact_message_box(self, "Account", message, icon=QMessageBox.Icon.Warning)
            return
        self._validated = True
        self.validation_label.setText("Credential structure validated. Network verification is unavailable for this provider integration.")

    def _accept_if_valid(self) -> None:
        valid, message = self._required_fields_present()
        if not valid:
            compact_message_box(self, "Account", message, icon=QMessageBox.Icon.Warning)
            return
        if not self._validated:
            compact_message_box(
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
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.74, preferred_height=620, min_width=900, max_width=1080, min_height=520
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)
        root.addWidget(label("Invoice Template", "PageTitle", False))
        root.addWidget(
            _invoice_wrapped_label(
                "Reusable invoice content only. Customer, billing, shipping and payment details remain outside templates.",
                "Description",
            )
        )

        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_host = QWidget()
        content_host.setObjectName("DialogContent")
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        upper_host = QWidget()
        upper_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        upper = QGridLayout(upper_host)
        upper.setContentsMargins(0, 0, 0, 0)
        upper.setHorizontalSpacing(8)
        upper.setVerticalSpacing(8)

        settings_card = card("Template Settings")
        settings_card.layout().addWidget(
            _invoice_wrapped_label("Common invoice controls used by the selected provider at send time.")
        )
        settings_grid = QGridLayout()
        settings_grid.setContentsMargins(0, 0, 0, 0)
        settings_grid.setHorizontalSpacing(8)
        settings_grid.setVerticalSpacing(7)

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
        settings_grid.addWidget(
            _invoice_wrapped_label(
                "Displayed in uppercase; provider API formatting is handled automatically.", "Caption"
            ),
            2,
            0,
            1,
            2,
        )
        settings_grid.addWidget(_invoice_form_group("Invoice type", self.invoice_type), 3, 0, 1, 2)
        settings_grid.addWidget(
            _invoice_wrapped_label("BOS is used only by providers that support it.", "Caption"),
            4,
            0,
            1,
            2,
        )
        settings_grid.setColumnStretch(0, 2)
        settings_grid.setColumnStretch(1, 3)
        settings_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_card.layout().addLayout(settings_grid)
        upper.addWidget(settings_card, 0, 0, Qt.AlignmentFlag.AlignTop)

        content_card = card("Invoice Content")
        content_card.layout().addWidget(
            _invoice_wrapped_label(
                "Provider-supported headings and customer-facing notes are mapped by the active provider adapter."
            )
        )
        content_grid = QGridLayout()
        content_grid.setContentsMargins(0, 0, 0, 0)
        content_grid.setHorizontalSpacing(8)
        content_grid.setVerticalSpacing(7)
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

        secondary_card = card("Footer, Terms & Provider Options")
        secondary_grid = QGridLayout()
        secondary_grid.setContentsMargins(0, 0, 0, 0)
        secondary_grid.setHorizontalSpacing(8)
        secondary_grid.setVerticalSpacing(7)
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
        option_layout.setSpacing(5)
        option_layout.addWidget(self.automatic_tax)
        option_layout.addWidget(self.reuse_customer)
        secondary_grid.addWidget(option_host, 1, 0, 1, 2)
        secondary_grid.setColumnStretch(0, 1)
        secondary_grid.setColumnStretch(1, 1)
        secondary_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        secondary_card.layout().addLayout(secondary_grid)
        content_layout.addWidget(secondary_card, 0, Qt.AlignmentFlag.AlignTop)

        items_card = card("Invoice Items")
        items_card.layout().addWidget(
            _invoice_wrapped_label(
                "Tax rate is used by providers with direct line-tax support; Stripe automatic tax uses the option above."
            )
        )
        self.items = QTableWidget(0, 4)
        self.items.setObjectName("InvoiceItemsTable")
        self.items.setHorizontalHeaderLabels(["Description", "Quantity", "Unit amount", "Tax %"])
        self.items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.verticalHeader().setVisible(False)
        self.items.verticalHeader().setDefaultSectionSize(30)
        header = self.items.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.items.setMinimumHeight(150)
        self.items.setMaximumHeight(210)
        items_card.layout().addWidget(self.items)
        item_actions = QHBoxLayout()
        item_actions.setSpacing(5)
        add_item = button("Add Item")
        remove_item = button("Remove Selected")
        add_item.clicked.connect(self._add_item)
        remove_item.clicked.connect(self._remove_selected)
        item_actions.addWidget(add_item)
        item_actions.addWidget(remove_item)
        item_actions.addStretch(1)
        items_card.layout().addLayout(item_actions)
        content_layout.addWidget(items_card, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addStretch(1)

        if template and template.items:
            for item in template.items:
                self._add_item(item.description, str(item.quantity), str(item.unit_amount), str(item.tax_rate))
        else:
            self._add_item("Service", "1", "10.00", "0")

        scroll.setWidget(content_host)
        root.addWidget(scroll, 1)

        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        actions.accepted.connect(self._validate_and_accept)
        actions.rejected.connect(self.reject)
        root.addWidget(actions)

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
            self.items.setItem(row, column, QTableWidgetItem(value))

    def _remove_selected(self) -> None:
        rows = sorted({item.row() for item in self.items.selectedItems()}, reverse=True)
        for row in rows:
            self.items.removeRow(row)

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
        self.setWindowTitle("New Task")
        self.setModal(True)
        _apply_compact_dialog_geometry(
            self, parent, width_ratio=0.60, preferred_height=520, min_width=700, max_width=860, min_height=450
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)
        root.addWidget(label("Create Task", "PageTitle", False))
        root.addWidget(
            label(
                "Select a provider, one or more available provider accounts, an invoice template and a customer list.",
                "Description",
            )
        )

        self.provider_combo = QComboBox()
        for provider in providers:
            self.provider_combo.addItem(provider.name, provider.id)
        self.provider_combo.currentIndexChanged.connect(self._refresh_accounts)
        root.addWidget(form_group("Provider", self.provider_combo))

        root.addWidget(label("Accounts", "FormLabel", False))
        self.accounts = QListWidget()
        self.accounts.setMinimumHeight(104)
        root.addWidget(self.accounts)
        root.addWidget(label("Accounts already assigned to another task are not selectable.", "Caption"))

        selectors = QWidget()
        selectors_grid = QGridLayout(selectors)
        selectors_grid.setContentsMargins(0, 0, 0, 0)
        selectors_grid.setHorizontalSpacing(8)
        selectors_grid.setVerticalSpacing(0)
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

