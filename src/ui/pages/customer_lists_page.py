from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.state import AppState
from ..tokens import CONST
from ..widgets import (
    DataGridPager,
    DataGridToolbar,
    button,
    card,
    data_grid_empty_label,
    data_table_item,
    page_header,
)


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
        self.setProperty("dataPage", True)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        new = button("New List", "primary")
        new.clicked.connect(self.on_new)
        root.addWidget(
            page_header(
                "Customer Lists",
                "Create separate customer lists with mandatory email; missing name/country are filled from Settings customer defaults.",
                [new],
            )
        )

        split = QSplitter(Qt.Orientation.Horizontal)
        lists_card = card("Lists", "Select a list to manage its customer records.")
        self.lists_pager = DataGridPager(on_changed=self._refresh_lists)
        self.lists_toolbar = DataGridToolbar(
            "Search lists...",
            on_changed=self._list_controls_changed,
            filters=(("Record state", (("All", ""), ("With customers", "with"), ("Empty", "empty"))),),
        )
        lists_card.layout().addWidget(self.lists_toolbar)
        self.lists = QTableWidget(0, 2)
        self.lists.setObjectName("CustomerListsDataTable")
        self.lists.setHorizontalHeaderLabels(["LIST", "CUSTOMERS"])
        self.lists.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lists.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lists.setAlternatingRowColors(True)
        self.lists.verticalHeader().setVisible(False)
        self.lists.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        self.lists.horizontalHeader().setSectionsClickable(False)
        self.lists.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.lists.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.lists.itemSelectionChanged.connect(self._selection_changed)
        lists_card.layout().addWidget(self.lists)
        self.lists_empty = data_grid_empty_label("No customer lists found.")
        self.lists_empty.setVisible(False)
        lists_card.layout().addWidget(self.lists_empty)
        lists_card.layout().addWidget(self.lists_pager)
        split.addWidget(lists_card)

        customers_card = card(
            "List Customers",
            "Upload CSV, TSV, Excel or text files. Email is mandatory; missing name uses the Settings default or email username, and missing country uses the Settings default or US.",
        )
        action_row = QHBoxLayout()
        self.import_button = button("Upload Customers")
        self.delete_button = button("Delete List", "danger")
        self.import_button.clicked.connect(self._import_current)
        self.delete_button.clicked.connect(self._delete_current)
        action_row.addWidget(self.import_button)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        customers_card.layout().addLayout(action_row)

        self.customer_pager = DataGridPager(on_changed=self._refresh_emails)
        self.customer_toolbar = DataGridToolbar(
            "Search customers...",
            on_changed=self._customer_controls_changed,
            filters=(("Country", (("All countries", ""),)),),
        )
        customers_card.layout().addWidget(self.customer_toolbar)
        self.email_table = QTableWidget(0, 4)
        self.email_table.setObjectName("CustomerRecordsDataTable")
        self.email_table.setHorizontalHeaderLabels(["#", "EMAIL", "NAME", "COUNTRY"])
        self.email_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.email_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.email_table.setAlternatingRowColors(True)
        self.email_table.verticalHeader().setVisible(False)
        self.email_table.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        self.email_table.horizontalHeader().setSectionsClickable(False)
        self.email_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.email_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.email_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.email_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        customers_card.layout().addWidget(self.email_table)
        self.customers_empty = data_grid_empty_label("No customers found.")
        self.customers_empty.setVisible(False)
        customers_card.layout().addWidget(self.customers_empty)
        customers_card.layout().addWidget(self.customer_pager)
        split.addWidget(customers_card)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)
        self.refresh()

    def _list_controls_changed(self) -> None:
        self.lists_pager.reset()
        self._refresh_lists()

    def _customer_controls_changed(self) -> None:
        self.customer_pager.reset()
        self._refresh_emails()

    def refresh(self, select_id: str | None = None) -> None:
        if select_id is not None:
            self.selected_list_id = select_id
        self._refresh_lists()

    def _filtered_lists(self):
        query = self.lists_toolbar.query
        state_filter = str(self.lists_toolbar.filter_value(0) or "")
        records = []
        for customer_list in sorted(self.state.customer_lists.values(), key=lambda item: item.name.casefold()):
            if state_filter == "with" and customer_list.count <= 0:
                continue
            if state_filter == "empty" and customer_list.count > 0:
                continue
            if query and query not in f"{customer_list.name} {customer_list.count}".casefold():
                continue
            records.append(customer_list)
        return records

    def _refresh_lists(self) -> None:
        desired = self.selected_list_id
        records = self._filtered_lists()
        start, end = self.lists_pager.set_total(len(records))
        visible = records[start:end]

        self.lists.blockSignals(True)
        self.lists.setRowCount(0)
        selected_row = -1
        for customer_list in visible:
            row = self.lists.rowCount()
            self.lists.insertRow(row)
            name = data_table_item(customer_list.name)
            name.setData(Qt.ItemDataRole.UserRole, customer_list.id)
            self.lists.setItem(row, 0, name)
            self.lists.setItem(row, 1, data_table_item(customer_list.count, right_align=True))
            if customer_list.id == desired:
                selected_row = row
        if selected_row < 0 and self.lists.rowCount() > 0:
            selected_row = 0
        if selected_row >= 0:
            self.lists.selectRow(selected_row)
            item = self.lists.item(selected_row, 0)
            self.selected_list_id = str(item.data(Qt.ItemDataRole.UserRole)) if item else None
        elif not visible:
            self.selected_list_id = None
        self.lists.blockSignals(False)

        self.lists_empty.setText("No matching records." if (self.lists_toolbar.query or self.lists_toolbar.filter_value(0)) else "No customer lists found.")
        self.lists_empty.setVisible(not visible)
        self._refresh_emails()

    def _selection_changed(self) -> None:
        row = self.lists.currentRow()
        if row < 0:
            self.selected_list_id = None
        else:
            item = self.lists.item(row, 0)
            self.selected_list_id = str(item.data(Qt.ItemDataRole.UserRole)) if item else None
        self.customer_pager.reset()
        self._refresh_emails()

    def _refresh_emails(self) -> None:
        current = self.state.customer_lists.get(self.selected_list_id or "")
        enabled = current is not None
        self.import_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

        countries = sorted({customer.country for customer in current.customers}, key=str.casefold) if current else []
        self.customer_toolbar.set_filter_options(0, [("All countries", ""), *((country, country) for country in countries)])

        records = list(current.customers) if current else []
        query = self.customer_toolbar.query
        country_filter = str(self.customer_toolbar.filter_value(0) or "")
        filtered = [
            customer
            for customer in records
            if (not country_filter or customer.country == country_filter)
            and (
                not query
                or query in f"{customer.email} {customer.name} {customer.country}".casefold()
            )
        ]
        start, end = self.customer_pager.set_total(len(filtered))
        visible = filtered[start:end]

        self.email_table.setRowCount(0)
        for offset, customer in enumerate(visible, start + 1):
            row = self.email_table.rowCount()
            self.email_table.insertRow(row)
            self.email_table.setItem(row, 0, data_table_item(offset, right_align=True))
            self.email_table.setItem(row, 1, data_table_item(customer.email))
            self.email_table.setItem(row, 2, data_table_item(customer.name))
            self.email_table.setItem(row, 3, data_table_item(customer.country))

        self.customers_empty.setText(
            "No matching records." if (query or country_filter) else "No customers found."
        )
        self.customers_empty.setVisible(not visible)

    def _import_current(self) -> None:
        if self.selected_list_id:
            self.on_import(self.selected_list_id)

    def _delete_current(self) -> None:
        if self.selected_list_id:
            self.on_delete(self.selected_list_id)
