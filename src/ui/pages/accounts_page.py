from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from ...core.provider_manager import ProviderManager
from ...core.state import AppState
from ..widgets import button, card, label, page_header


class AccountsPage(QWidget):
    def __init__(self, state: AppState, providers: ProviderManager, on_add: Callable[[], None]):
        super().__init__()
        self.state = state
        self.providers = providers
        self.on_add = on_add
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        add = button("Add Account", "primary")
        add.clicked.connect(self.on_add)
        root.addWidget(
            page_header(
                "Accounts",
                "Added provider accounts are grouped by provider. An account assigned to one task cannot be selected by another task.",
                [add],
            )
        )

        host = card("Added Accounts", "Providers appear here only after they are installed or loaded from the Providers page.")
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Account / Provider", "Mode", "Status", "Assigned Task", "Credentials"])
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(False)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        host.layout().addWidget(self.tree)
        root.addWidget(host, 1)
        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        installed = self.providers.list_installed()
        if not installed:
            placeholder = QTreeWidgetItem(["No providers installed. Open Providers and install or load a provider.", "", "", "", ""])
            self.tree.addTopLevelItem(placeholder)
            return

        for provider in installed:
            provider_item = QTreeWidgetItem([provider.name, "", "Installed", "", f"{len(provider.credential_fields)} fields"])
            provider_item.setExpanded(True)
            accounts = self.state.accounts_for_provider(provider.id)
            for account in accounts:
                task_id = self.state.account_reservations.get(account.id)
                task_name = self.state.tasks.get(task_id).name if task_id and task_id in self.state.tasks else "Available"
                child = QTreeWidgetItem(
                    [
                        account.name,
                        account.mode,
                        account.status,
                        task_name,
                        "Stored in memory",
                    ]
                )
                provider_item.addChild(child)
            if not accounts:
                provider_item.addChild(QTreeWidgetItem(["No accounts added", "", "", "", ""]))
            self.tree.addTopLevelItem(provider_item)
