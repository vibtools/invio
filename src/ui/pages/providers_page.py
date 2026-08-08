from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...core.provider_manager import ProviderManager, ProviderManifest
from ..tokens import CONST
from ..widgets import button, card, label, page_header, status_badge, vbox


class ProvidersPage(QWidget):
    def __init__(
        self,
        manager: ProviderManager,
        on_install: Callable[[str], None],
        on_load: Callable[[], None],
    ):
        super().__init__()
        self.manager = manager
        self.on_install = on_install
        self.on_load = on_load
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        load = button("Load Provider", "primary")
        load.clicked.connect(self.on_load)
        root.addWidget(
            page_header(
                "Providers",
                "Install or load provider packages. Only installed providers are available to Accounts and Tasks.",
                [load],
            )
        )
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.host, 1)
        self.refresh()

    def _provider_card(self, provider: ProviderManifest, installed: bool):
        item = QFrame()
        item.setObjectName("PluginCard")
        item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = vbox(item, (CONST.card_padding,) * 4, CONST.card_gap)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(5)
        version = label(f"v{provider.version}", "PluginCategoryChip", False)
        version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        top.addWidget(version)
        top.addStretch(1)
        top.addWidget(status_badge("Installed" if installed else "Available", "success" if installed else "neutral"))
        layout.addLayout(top)

        layout.addWidget(label(provider.name, "PluginCardTitle", False))
        description = label(provider.description, "PluginCardDescription", True)
        description.setToolTip(provider.description)
        layout.addWidget(description)

        capabilities = ", ".join(provider.capabilities) if provider.capabilities else "No capabilities declared"
        layout.addWidget(label(f"Capabilities: {capabilities}", "Caption"))
        layout.addWidget(label(f"Credential fields: {len(provider.credential_fields)}", "Caption", False))

        action = button("Installed") if installed else button("Install", "primary")
        action.setEnabled(not installed)
        if not installed:
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_install(pid))
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        row.addWidget(action)
        row.addStretch(1)
        layout.addLayout(row)
        return item

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        installed_ids = self.manager.installed_ids()
        providers = self.manager.list_available()
        external = [item for item in self.manager.list_installed() if item.id not in {p.id for p in providers}]
        providers.extend(external)
        if not providers:
            empty = card("No provider packages", "Use Load Provider to add a validated provider manifest.")
            self.grid.addWidget(empty, 0, 0)
            return
        for index, provider in enumerate(providers):
            self.grid.addWidget(self._provider_card(provider, provider.id in installed_ids), index // 3, index % 3)
        for column in range(3):
            self.grid.setColumnStretch(column, 1)
