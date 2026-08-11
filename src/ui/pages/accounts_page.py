from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QMenu,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.provider_manager import ProviderManager
from ...core.state import AppState
from ..tokens import CONST
from ..widgets import (
    DataGridPager,
    DataGridToolbar,
    button,
    card,
    data_grid_empty_label,
    data_table_item,
    set_data_status_cell,
    label,
    page_header,
)



class AccountsPage(QWidget):
    def __init__(
        self,
        state: AppState,
        providers: ProviderManager,
        on_add: Callable[[], None],
        on_edit: Callable[[str], None],
        on_retest: Callable[[str], None],
        on_delete: Callable[[str], None],
    ):
        super().__init__()
        self.state = state
        self.providers = providers
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_retest = on_retest
        self.on_delete = on_delete
        self.setObjectName("PageContent")
        self.setProperty("dataPage", True)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.add_button = button("Add Account", "primary")
        self.add_button.clicked.connect(self.on_add)
        root.addWidget(
            page_header(
                "Accounts",
                "Added provider accounts are grouped by provider. An account assigned to one task cannot be selected by another task.",
                [self.add_button],
            )
        )

        host = card()
        self.pager = DataGridPager(on_changed=self.refresh)
        self.toolbar = DataGridToolbar(
            "Search accounts...",
            on_changed=self._controls_changed,
            filters=(
                ("Provider", (("All providers", ""),)),
                ("Status", (("All statuses", ""),)),
            ),
        )
        self._compose_toolbar()
        host.layout().addWidget(self.toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("AccountsDataTable")
        self.table.setHorizontalHeaderLabels(["ACCOUNT", "PROVIDER", "STATUS", "ACTION"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        header = self.table.horizontalHeader()
        header.setSectionsClickable(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # v1.48.8: let the canonical status cell item size hint drive the
        # Status column. A fixed pixel width is not portable across real Qt
        # font/DPI environments and can clip otherwise-correct shared badges.
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 68)
        for column in (0, 1):
            item = self.table.horizontalHeaderItem(column)
            if item is not None:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column in (2, 3):
            item = self.table.horizontalHeaderItem(column)
            if item is not None:
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        host.layout().addWidget(self.table)

        self.empty = data_grid_empty_label("No accounts found.")
        self.empty.setVisible(False)
        host.layout().addWidget(self.empty)
        host.layout().addWidget(self.pager)
        root.addWidget(host, 1)
        self.refresh()

    def _compose_toolbar(self) -> None:
        layout = self.toolbar.layout()
        while layout.count():
            layout.takeAt(0)
        layout.addWidget(label("Added Accounts List", "CardTitle", False))
        layout.addStretch(1)
        layout.addWidget(self.toolbar.search)
        for combo in self.toolbar.filters:
            layout.addWidget(combo)

    def _controls_changed(self) -> None:
        self.pager.reset()
        self.refresh()

    def _selected_account_id(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 0)
        if item is None:
            return ""
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else ""

    def _edit_selected(self) -> None:
        account_id = self._selected_account_id()
        if account_id:
            self.on_edit(account_id)

    def _retest_selected(self) -> None:
        account_id = self._selected_account_id()
        if account_id:
            self.on_retest(account_id)

    def _delete_selected(self) -> None:
        account_id = self._selected_account_id()
        if account_id:
            self.on_delete(account_id)

    def _row_actions(self, account_id: str) -> QWidget:
        host = QWidget()
        host.setObjectName("AccountsActionHost")
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(0)
        layout.addStretch(1)

        action_button = button("⋯")
        action_button.setObjectName("TableActionButton")
        action_button.setAccessibleName("Account actions")
        action_button.setToolTip("Account actions")
        action_button.setFixedSize(30, 24)

        menu = QMenu(action_button)
        menu.setObjectName("AccountsActionMenu")
        menu.setMinimumWidth(104)
        edit_action = menu.addAction("Edit")
        retest_action = menu.addAction("Re-test")
        delete_action = menu.addAction("Delete")
        edit_action.triggered.connect(lambda _checked=False, aid=account_id: self.on_edit(aid))
        retest_action.triggered.connect(lambda _checked=False, aid=account_id: self.on_retest(aid))
        delete_action.triggered.connect(lambda _checked=False, aid=account_id: self.on_delete(aid))
        action_button.clicked.connect(
            lambda _checked=False, control=action_button, popup=menu: self._show_row_actions(control, popup)
        )
        layout.addWidget(action_button)
        layout.addStretch(1)
        return host

    @staticmethod
    def _menu_safe_geometry(control: QWidget) -> QRect:
        window = control.window()
        window_rect = QRect(window.mapToGlobal(QPoint(0, 0)), window.size())
        screen = control.screen()
        if screen is None:
            return window_rect
        safe = window_rect.intersected(screen.availableGeometry())
        return safe if not safe.isEmpty() else window_rect

    @classmethod
    def _bounded_menu_position(cls, control: QWidget, menu: QMenu) -> QPoint:
        menu.ensurePolished()
        menu_size = menu.sizeHint()
        safe = cls._menu_safe_geometry(control)
        anchor = QRect(control.mapToGlobal(QPoint(0, 0)), control.size())

        # Right-align the popup to the row control so it naturally opens inward
        # from the table edge, then clamp to both the app window and screen.
        preferred_x = anchor.right() - menu_size.width() + 1
        max_x = max(safe.left(), safe.right() - menu_size.width() + 1)
        x = min(max(preferred_x, safe.left()), max_x)

        below_y = anchor.bottom() + 1
        above_y = anchor.top() - menu_size.height()
        if below_y + menu_size.height() - 1 <= safe.bottom():
            y = below_y
        elif above_y >= safe.top():
            y = above_y
        else:
            max_y = max(safe.top(), safe.bottom() - menu_size.height() + 1)
            y = min(max(below_y, safe.top()), max_y)
        return QPoint(x, y)

    def _show_row_actions(self, control: QWidget, menu: QMenu) -> None:
        menu.exec(self._bounded_menu_position(control, menu))

    def refresh(self) -> None:
        selected_id = self._selected_account_id()
        installed = self.providers.list_installed()
        installed_by_id = {provider.id: provider for provider in installed}
        account_provider_ids = {account.provider_id for account in self.state.accounts.values()}
        provider_ids = [provider.id for provider in installed]
        provider_ids.extend(sorted(account_provider_ids - set(provider_ids)))

        provider_options = [("All providers", "")]
        provider_options.extend(
            (
                installed_by_id.get(provider_id).name
                if installed_by_id.get(provider_id) is not None
                else next(
                    (account.provider_name for account in self.state.accounts_for_provider(provider_id)),
                    provider_id,
                ),
                provider_id,
            )
            for provider_id in provider_ids
        )
        self.toolbar.set_filter_options(0, provider_options)

        account_statuses = sorted({account.status for account in self.state.accounts.values()}, key=str.casefold)
        status_options = [("All statuses", ""), ("Installed", "Installed"), ("Not Installed", "Not Installed")]
        status_options.extend((status, status) for status in account_statuses if status not in {"Installed", "Not Installed"})
        self.toolbar.set_filter_options(1, status_options)

        query = self.toolbar.query
        provider_filter = str(self.toolbar.filter_value(0) or "")
        status_filter = str(self.toolbar.filter_value(1) or "")

        records: list[tuple[str, str, str, object]] = []
        for provider_id in provider_ids:
            provider = installed_by_id.get(provider_id)
            accounts = self.state.accounts_for_provider(provider_id)
            provider_name = provider.name if provider is not None else (accounts[0].provider_name if accounts else provider_id)
            provider_status = "Installed" if provider is not None else "Not Installed"
            if provider_filter and provider_id != provider_filter:
                continue
            for account in accounts:
                task_id = self.state.account_reservations.get(account.id)
                task_name = self.state.tasks.get(task_id).name if task_id and task_id in self.state.tasks else "Available"
                credential_state = "Protected storage" if account.credentials else "Unavailable"
                searchable = " ".join(
                    (
                        provider_name,
                        provider_id,
                        provider_status,
                        account.name,
                        account.mode,
                        account.status,
                        account.last_verification_at or "Never",
                        task_name,
                        credential_state,
                    )
                ).casefold()
                row_status = account.status if provider is not None else "Not Installed"
                status_match = not status_filter or row_status == status_filter or provider_status == status_filter
                if status_match and (not query or query in searchable):
                    records.append((provider_id, provider_name, row_status, account))

        start, end = self.pager.set_total(len(records))
        visible_records = records[start:end]

        self.table.setRowCount(0)
        selected_row = -1
        for provider_id, provider_name, row_status, account in visible_records:
            row = self.table.rowCount()
            self.table.insertRow(row)

            account_item = data_table_item(account.name)
            account_item.setData(Qt.ItemDataRole.UserRole, account.id)
            account_item.setToolTip(account.name)
            self.table.setItem(row, 0, account_item)

            provider_item = data_table_item(provider_name)
            provider_item.setData(Qt.ItemDataRole.UserRole, provider_id)
            provider_item.setToolTip(provider_name)
            self.table.setItem(row, 1, provider_item)

            tooltip = account.verification_error_summary if account.verification_error_summary else row_status
            set_data_status_cell(
                self.table,
                row,
                2,
                row_status,
                tooltip=tooltip,
                align=Qt.AlignmentFlag.AlignHCenter,
            )
            self.table.setCellWidget(row, 3, self._row_actions(account.id))

            if account.id == selected_id:
                selected_row = row

        if selected_row >= 0:
            self.table.selectRow(selected_row)

        has_rows = self.table.rowCount() > 0
        self.empty.setText("No matching records." if (query or provider_filter or status_filter) else "No accounts found.")
        self.empty.setVisible(not has_rows)
