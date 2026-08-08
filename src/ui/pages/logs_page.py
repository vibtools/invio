from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QVBoxLayout, QWidget

from ..widgets import button, card, page_header


class LogsPage(QWidget):
    def __init__(self, on_clear: Callable[[], None], on_export: Callable[[], None]):
        super().__init__()
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(page_header("Live Logs", "Application, task and provider status messages. Secret values must never be written to this view."))
        host = card("Log Stream")
        actions = QHBoxLayout()
        clear = button("Clear")
        export = button("Export Logs")
        clear.clicked.connect(on_clear)
        export.clicked.connect(on_export)
        actions.addWidget(clear)
        actions.addWidget(export)
        actions.addStretch(1)
        host.layout().addLayout(actions)
        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setFont(QFont("Cascadia Mono", 10))
        host.layout().addWidget(self.viewer)
        root.addWidget(host, 1)

    def append(self, message: str) -> None:
        self.viewer.appendPlainText(message)

    def clear(self) -> None:
        self.viewer.clear()
