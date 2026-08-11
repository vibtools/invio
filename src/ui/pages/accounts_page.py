from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from ...core.paths import asset_path
from ...core.provider_manager import ProviderManager
from ...core.state import AppState
from ..widgets import DataGridPager, DataGridToolbar, button, card, data_badge_host, data_grid_empty_label, page_header


_PROVIDER_LOGOS = {
    "stripe": "stripe.png",
    "refrens": "refrens.png",
    "agiled": "agiled.png",
    "odoo": "odoo.png",
}


def _compact_timestamp(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "Never"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return parsed.strftime("%b %d, %Y • %H:%M")


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
        self.edit_button = button("Edit")
        self.retest_button = button("Re-test")
        self.delete_button = button("Delete")
        self.add_button.clicked.connect(self.on_add)
        self.edit_button.clicked.connect(self._edit_selected)
        self.retest_button.clicked.connect(self._retest_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        root.addWidget(
            page_header(
                "Accounts",
                "Added provider accounts are grouped by provider. An account assigned to one task cannot be selected by another task.",
                [self.add_button, self.edit_button, self.retest_button, self.delete_button],
            )
        )

        host = card(
            "Added Accounts",
            "Installed providers and preserved accounts from uninstalled providers are shown here. Protected credentials are never displayed.",
        )
        self.pager = DataGridPager(on_changed=self.refresh)
        self.toolbar = DataGridToolbar(
            "Search accounts...",
            on_changed=self._controls_changed,
            filters=(
                ("Provider", (("All providers", ""),)),
                ("Status", (("All statuses", ""),)),
            ),
        )
        host.layout().addWidget(self.toolbar)

        self.tree = QTreeWidget()
        self.tree.setObjectName("AccountsDataTree")
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["ACCOUNT / PROVIDER", "MODE", "STATUS", "LAST API TEST", "ASSIGNED TASK", "CREDENTIALS"])
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.itemSelectionChanged.connect(self._update_actions)
        header = self.tree.header()
        header.setSectionsClickable(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        host.layout().addWidget(self.tree)
        self.empty = data_grid_empty_label("No accounts found.")
        self.empty.setVisible(False)
        host.layout().addWidget(self.empty)
        host.layout().addWidget(self.pager)
        root.addWidget(host, 1)
        self.refresh()

    def _controls_changed(self) -> None:
        self.pager.reset()
        self.refresh()

    def _selected_account_id(self) -> str:
        item = self.tree.currentItem()
        if item is None:
            return ""
        value = item.data(0, Qt.ItemDataRole.UserRole)
        return str(value) if value else ""

    def _update_actions(self) -> None:
        selected = bool(self._selected_account_id())
        self.edit_button.setEnabled(selected)
        self.retest_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)

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

    def _provider_icon(self, provider_id: str) -> QIcon:
        filename = _PROVIDER_LOGOS.get(provider_id.casefold())
        if not filename:
            return QIcon()
        path = asset_path("icons", "providers", filename)
        return QIcon(str(path)) if path.is_file() else QIcon()

    @staticmethod
    def _decorate_provider_row(item: QTreeWidgetItem) -> None:
        font = QFont(item.font(0))
        font.setWeight(QFont.Weight.DemiBold)
        brush = QBrush(QColor("#1A212E"))
        for column in range(item.columnCount()):
            item.setFont(column, font)
            item.setBackground(column, brush)

    def refresh(self) -> None:
        selected_id = self._selected_account_id()
        self.tree.clear()
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

        if not provider_ids:
            self.pager.set_total(0)
            self.empty.setText("No accounts found.")
            self.empty.setVisible(True)
            self._update_actions()
            return

        query = self.toolbar.query
        provider_filter = str(self.toolbar.filter_value(0) or "")
        status_filter = str(self.toolbar.filter_value(1) or "")

        records: list[tuple[str, object]] = []
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
                status_match = not status_filter or account.status == status_filter or provider_status == status_filter
                if status_match and (not query or query in searchable):
                    records.append((provider_id, account))

        start, end = self.pager.set_total(len(records))
        visible_records = records[start:end]
        visible_by_provider: dict[str, list[object]] = {}
        for provider_id, account in visible_records:
            visible_by_provider.setdefault(provider_id, []).append(account)

        for provider_id in provider_ids:
            provider = installed_by_id.get(provider_id)
            all_accounts = self.state.accounts_for_provider(provider_id)
            provider_name = provider.name if provider is not None else (all_accounts[0].provider_name if all_accounts else provider_id)
            provider_status = "Installed" if provider is not None else "Not Installed"
            if provider_filter and provider_id != provider_filter:
                continue
            page_accounts = visible_by_provider.get(provider_id, [])
            provider_search_match = not query or query in f"{provider_name} {provider_id} {provider_status}".casefold()
            show_empty_provider = (
                not all_accounts
                and self.pager.page == 1
                and provider_search_match
                and (not status_filter or provider_status == status_filter)
            )
            if not page_accounts and not show_empty_provider:
                continue

            credential_summary = f"{len(provider.credential_fields)} fields" if provider is not None else ""
            provider_item = QTreeWidgetItem([provider_name, "", provider_status, "", "", credential_summary])
            provider_item.setIcon(0, self._provider_icon(provider_id))
            provider_item.setToolTip(0, provider_name)
            provider_item.setToolTip(2, provider_status)
            provider_item.setExpanded(True)
            self._decorate_provider_row(provider_item)
            self.tree.addTopLevelItem(provider_item)
            self.tree.setItemWidget(provider_item, 2, data_badge_host(provider_status))

            for account in page_accounts:
                task_id = self.state.account_reservations.get(account.id)
                task_name = self.state.tasks.get(task_id).name if task_id and task_id in self.state.tasks else "Available"
                credential_state = "Protected storage" if account.credentials else "Unavailable"
                compact_time = _compact_timestamp(account.last_verification_at or "")
                child = QTreeWidgetItem(
                    [
                        account.name,
                        account.mode,
                        account.status,
                        compact_time,
                        task_name,
                        credential_state,
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, account.id)
                for column, value in enumerate(
                    (account.name, account.mode, account.status, account.last_verification_at or "Never", task_name, credential_state)
                ):
                    child.setToolTip(column, str(value))
                if account.verification_error_summary:
                    child.setToolTip(2, account.verification_error_summary)
                provider_item.addChild(child)
                self.tree.setItemWidget(child, 2, data_badge_host(account.status))
                assigned_tone = "success" if task_name == "Available" else "warning"
                self.tree.setItemWidget(child, 4, data_badge_host(task_name, assigned_tone))
                credential_tone = "success" if credential_state == "Protected storage" else "neutral"
                self.tree.setItemWidget(child, 5, data_badge_host(credential_state, credential_tone))
                if account.id == selected_id:
                    self.tree.setCurrentItem(child)

            if not all_accounts:
                provider_item.addChild(QTreeWidgetItem(["No accounts added", "", "", "", "", ""]))

        has_rows = bool(self.tree.topLevelItemCount())
        self.empty.setText("No matching records." if (query or provider_filter or status_filter) else "No accounts found.")
        self.empty.setVisible(not has_rows)
        self._update_actions()
