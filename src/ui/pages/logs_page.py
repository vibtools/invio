from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QVBoxLayout, QWidget

from ..widgets import button, card, page_header


class LogsPage(QWidget):
    def __init__(self, on_clear: Callable[[], None], on_export: Callable[[], None]):
        super().__init__()
        self._auto_scroll = True
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

    def configure(self, *, auto_scroll: bool, max_entries: int) -> None:
        self._auto_scroll = bool(auto_scroll)
        self.viewer.document().setMaximumBlockCount(max(0, int(max_entries)))

    def append(self, message: str) -> None:
        scroll_bar = self.viewer.verticalScrollBar()
        previous_value = scroll_bar.value()
        self.viewer.appendPlainText(message)
        if self._auto_scroll:
            scroll_bar.setValue(scroll_bar.maximum())
        else:
            scroll_bar.setValue(min(previous_value, scroll_bar.maximum()))

    def clear(self) -> None:
        self.viewer.clear()
