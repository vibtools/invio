from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.state import AppState
from ..widgets import button, card, label, page_header


class CustomerListsPage(QWidget):
    def __init__(
        self,
        state: AppState,
        on_new: Callable[[], None],
        on_import: Callable[[str], None],
        on_delete: Callable[[str], None],
    ):
        super().__init__()
        self.state = state
        self.on_new = on_new
        self.on_import = on_import
        self.on_delete = on_delete
        self.selected_list_id: str | None = None
        self.setObjectName("PageContent")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        new = button("New List", "primary")
        new.clicked.connect(self.on_new)
        root.addWidget(
            page_header(
                "Customer Lists",
                "Create separate customer lists and keep a different bulk email set inside each list.",
                [new],
            )
        )

        split = QSplitter(Qt.Orientation.Horizontal)
        lists_card = card("Lists", "Select a list to manage its email addresses.")
        self.lists = QTableWidget(0, 2)
        self.lists.setHorizontalHeaderLabels(["List", "Emails"])
        self.lists.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lists.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lists.verticalHeader().setVisible(False)
        self.lists.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.lists.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.lists.itemSelectionChanged.connect(self._selection_changed)
        lists_card.layout().addWidget(self.lists)
        split.addWidget(lists_card)

        emails_card = card("List Emails", "Upload CSV, TSV, Excel or text files. Only email addresses are stored in a customer list.")
        action_row = QHBoxLayout()
        self.import_button = button("Upload Emails")
        self.delete_button = button("Delete List", "danger")
        self.import_button.clicked.connect(self._import_current)
        self.delete_button.clicked.connect(self._delete_current)
        action_row.addWidget(self.import_button)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        emails_card.layout().addLayout(action_row)
        self.email_table = QTableWidget(0, 2)
        self.email_table.setHorizontalHeaderLabels(["#", "Email"])
        self.email_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.email_table.verticalHeader().setVisible(False)
        self.email_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.email_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        emails_card.layout().addWidget(self.email_table)
        split.addWidget(emails_card)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)
        self.refresh()

    def refresh(self, select_id: str | None = None) -> None:
        self.lists.setRowCount(0)
        desired = select_id or self.selected_list_id
        selected_row = -1
        for customer_list in sorted(self.state.customer_lists.values(), key=lambda item: item.name.casefold()):
            row = self.lists.rowCount()
            self.lists.insertRow(row)
            name = QTableWidgetItem(customer_list.name)
            name.setData(Qt.ItemDataRole.UserRole, customer_list.id)
            self.lists.setItem(row, 0, name)
            self.lists.setItem(row, 1, QTableWidgetItem(str(customer_list.count)))
            if customer_list.id == desired:
                selected_row = row
        if selected_row >= 0:
            self.lists.selectRow(selected_row)
        elif self.lists.rowCount() > 0:
            self.lists.selectRow(0)
        else:
            self.selected_list_id = None
            self._refresh_emails()

    def _selection_changed(self) -> None:
        row = self.lists.currentRow()
        if row < 0:
            self.selected_list_id = None
        else:
            item = self.lists.item(row, 0)
            self.selected_list_id = str(item.data(Qt.ItemDataRole.UserRole)) if item else None
        self._refresh_emails()

    def _refresh_emails(self) -> None:
        self.email_table.setRowCount(0)
        current = self.state.customer_lists.get(self.selected_list_id or "")
        enabled = current is not None
        self.import_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        if not current:
            return
        for index, email in enumerate(current.emails, 1):
            row = self.email_table.rowCount()
            self.email_table.insertRow(row)
            self.email_table.setItem(row, 0, QTableWidgetItem(str(index)))
            self.email_table.setItem(row, 1, QTableWidgetItem(email))

    def _import_current(self) -> None:
        if self.selected_list_id:
            self.on_import(self.selected_list_id)

    def _delete_current(self) -> None:
        if self.selected_list_id:
            self.on_delete(self.selected_list_id)
