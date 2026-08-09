from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from ...core.provider_manager import ProviderManager
from ...core.state import AppState
from ..widgets import button, card, page_header


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
        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Account / Provider", "Mode", "Status", "Last API Test", "Assigned Task", "Credentials"])
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.itemSelectionChanged.connect(self._update_actions)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        host.layout().addWidget(self.tree)
        root.addWidget(host, 1)
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

    def refresh(self) -> None:
        self.tree.clear()
        installed = self.providers.list_installed()
        installed_by_id = {provider.id: provider for provider in installed}
        account_provider_ids = {account.provider_id for account in self.state.accounts.values()}
        provider_ids = [provider.id for provider in installed]
        provider_ids.extend(sorted(account_provider_ids - set(provider_ids)))

        if not provider_ids:
            placeholder = QTreeWidgetItem(["No providers installed. Open Providers and install or load a provider.", "", "", "", "", ""])
            self.tree.addTopLevelItem(placeholder)
            self._update_actions()
            return

        for provider_id in provider_ids:
            provider = installed_by_id.get(provider_id)
            accounts = self.state.accounts_for_provider(provider_id)
            provider_name = provider.name if provider is not None else (accounts[0].provider_name if accounts else provider_id)
            provider_status = "Installed" if provider is not None else "Not Installed"
            credential_summary = f"{len(provider.credential_fields)} fields" if provider is not None else ""
            provider_item = QTreeWidgetItem([provider_name, "", provider_status, "", "", credential_summary])
            provider_item.setExpanded(True)

            for account in accounts:
                task_id = self.state.account_reservations.get(account.id)
                task_name = self.state.tasks.get(task_id).name if task_id and task_id in self.state.tasks else "Available"
                credential_state = "Protected storage" if account.credentials else "Unavailable"
                child = QTreeWidgetItem(
                    [
                        account.name,
                        account.mode,
                        account.status,
                        account.last_verification_at or "Never",
                        task_name,
                        credential_state,
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, account.id)
                if account.verification_error_summary:
                    child.setToolTip(2, account.verification_error_summary)
                provider_item.addChild(child)

            if not accounts:
                provider_item.addChild(QTreeWidgetItem(["No accounts added", "", "", "", "", ""]))
            self.tree.addTopLevelItem(provider_item)
        self._update_actions()
