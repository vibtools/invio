from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from ..widgets import card, label, page_header, status_badge, token_chip


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(page_header("Settings", "Application settings and runtime contracts."))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        appearance = card("Appearance", "The application UI follows the Vib Tools official Step-40J desktop design baseline.")
        appearance.layout().addWidget(token_chip("Dark only"))
        appearance.layout().addWidget(label("Colors, typography, spacing and control geometry follow the official Vib Tools desktop tokens.", "Caption"))
        grid.addWidget(appearance, 0, 0)

        runtime = card("Task Runtime", "Every active task owns a distinct worker-thread slot. Provider network sending is injected into that worker layer and never runs on the GUI thread.")
        runtime.layout().addWidget(status_badge("Thread-isolated", "success"))
        grid.addWidget(runtime, 0, 1)

        security = card("Account Data", "Credentials are kept in memory for the current application session. Persistent credential storage is not configured.")
        security.layout().addWidget(status_badge("No credential persistence", "warning"))
        grid.addWidget(security, 1, 0)

        provider = card("Provider Visibility", "Accounts and task provider selectors read only installed provider manifests from providers/registry.")
        provider.layout().addWidget(status_badge("Installed providers only", "success"))
        grid.addWidget(provider, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addLayout(grid)
        root.addStretch(1)
