from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSizePolicy,
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
    bounded_popup_position,
    button,
    card,
    data_grid_empty_label,
    data_table_item,
    label,
    page_header,
)


class _CustomerListRow(QWidget):
    """Compact navigation row for one Customer List; domain behavior stays external."""

    selected = Signal(str)

    def __init__(
        self,
        list_id: str,
        name: str,
        count: int,
        *,
        on_delete: Callable[[str], None],
    ) -> None:
        super().__init__()
        self.list_id = list_id
        self._on_delete = on_delete
        self.setObjectName("CustomerListNavigationRow")
        self.setProperty("selected", False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 6, 3)
        layout.setSpacing(6)

        name_label = label(name, "CustomerListName", False)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(name_label, 1)

        count_badge = label(str(count), "CustomerListCountBadge", False)
        count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(count_badge)

        action_button = button("⋯")
        action_button.setObjectName("TableActionButton")
        action_button.setAccessibleName(f"Actions for {name}")
        action_button.setToolTip("List actions")
        action_button.setFixedSize(30, 24)
        menu = QMenu(action_button)
        menu.setObjectName("CustomerListActionMenu")
        menu.setMinimumWidth(116)
        delete_action = menu.addAction("Delete List")
        delete_action.triggered.connect(lambda _checked=False: self._delete())
        action_button.clicked.connect(lambda _checked=False: self._show_menu(action_button, menu))
        layout.addWidget(action_button)

    def _delete(self) -> None:
        self.selected.emit(self.list_id)
        self._on_delete(self.list_id)

    def _show_menu(self, control: QWidget, menu: QMenu) -> None:
        self.selected.emit(self.list_id)
        menu.exec(bounded_popup_position(control, menu))

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", bool(selected))
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.selected.emit(self.list_id)
        super().mousePressEvent(event)


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
                "Create separate customer lists with mandatory email; missing name uses the Settings default or email username, and missing country uses the Settings default or US.",
                [new],
            )
        )

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setObjectName("CustomerListsSplit")

        lists_card = card()
        add_list = button("＋")
        add_list.setObjectName("SectionIconButton")
        add_list.setAccessibleName("Add customer list")
        add_list.setToolTip("New List")
        add_list.setFixedSize(CONST.data_grid_control_height, CONST.data_grid_control_height)
        add_list.clicked.connect(self.on_new)
        self.lists_toolbar = DataGridToolbar(
            "Search lists...",
            on_changed=self._list_controls_changed,
            filters=(("Record state", (("All", ""), ("With customers", "with"), ("Empty", "empty"))),),
            title_text="Lists",
            actions=(add_list,),
        )
        lists_card.layout().addWidget(self.lists_toolbar)

        self.lists = QListWidget()
        self.lists.setObjectName("CustomerListsNavigationList")
        self.lists.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lists.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lists.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lists.setSpacing(0)
        self.lists.currentItemChanged.connect(self._selection_changed)
        lists_card.layout().addWidget(self.lists, 1)

        self.lists_empty = data_grid_empty_label("No customer lists found.")
        self.lists_empty.setVisible(False)
        lists_card.layout().addWidget(self.lists_empty)
        split.addWidget(lists_card)

        customers_card = card()
        self.import_button = button("Upload")
        self.import_button.clicked.connect(self._import_current)
        self.customer_pager = DataGridPager(on_changed=self._refresh_emails)
        self.customer_toolbar = DataGridToolbar(
            "Search customers...",
            on_changed=self._customer_controls_changed,
            filters=(("Country", (("All countries", ""),)),),
            title_text="Customers",
            actions=(self.import_button,),
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
        customers_card.layout().addWidget(self.email_table, 1)

        self.customers_empty = data_grid_empty_label("No customers found.")
        self.customers_empty.setVisible(False)
        customers_card.layout().addWidget(self.customers_empty)
        customers_card.layout().addWidget(self.customer_pager)
        split.addWidget(customers_card)

        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        split.setSizes([320, 760])
        root.addWidget(split, 1)
        self.refresh()

    def _list_controls_changed(self) -> None:
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

        self.lists.blockSignals(True)
        self.lists.clear()
        desired_item: QListWidgetItem | None = None
        for customer_list in records:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, customer_list.id)
            item.setToolTip(customer_list.name)
            item.setSizeHint(QSize(0, max(30, CONST.table_row_height)))
            self.lists.addItem(item)
            row = _CustomerListRow(
                customer_list.id,
                customer_list.name,
                customer_list.count,
                on_delete=self.on_delete,
            )
            row.selected.connect(self._select_list)
            self.lists.setItemWidget(item, row)
            if customer_list.id == desired:
                desired_item = item

        if desired_item is None and self.lists.count() > 0:
            desired_item = self.lists.item(0)
        if desired_item is not None:
            self.lists.setCurrentItem(desired_item)
            self.selected_list_id = str(desired_item.data(Qt.ItemDataRole.UserRole))
        else:
            self.selected_list_id = None
        self.lists.blockSignals(False)
        self._sync_list_row_selection()

        self.lists_empty.setText(
            "No matching records."
            if (self.lists_toolbar.query or self.lists_toolbar.filter_value(0))
            else "No customer lists found."
        )
        self.lists_empty.setVisible(not records)
        self._refresh_emails()

    def _select_list(self, list_id: str) -> None:
        for index in range(self.lists.count()):
            item = self.lists.item(index)
            if str(item.data(Qt.ItemDataRole.UserRole)) == list_id:
                self.lists.setCurrentItem(item)
                return

    def _sync_list_row_selection(self) -> None:
        current = self.lists.currentItem()
        for index in range(self.lists.count()):
            item = self.lists.item(index)
            row = self.lists.itemWidget(item)
            if isinstance(row, _CustomerListRow):
                row.set_selected(item is current)

    def _selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        self.selected_list_id = str(current.data(Qt.ItemDataRole.UserRole)) if current is not None else None
        self._sync_list_row_selection()
        self.customer_pager.reset()
        self._refresh_emails()

    def _refresh_emails(self) -> None:
        current = self.state.customer_lists.get(self.selected_list_id or "")
        enabled = current is not None
        self.import_button.setEnabled(enabled)

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
