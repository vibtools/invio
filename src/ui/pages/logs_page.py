from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPlainTextEdit, QVBoxLayout, QWidget

from ..widgets import button, label, page_header


class LogsPage(QWidget):
    def __init__(self, on_clear: Callable[[], None], on_export: Callable[[], None]):
        super().__init__()
        self._auto_scroll = True
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        save = button("Save Logs")
        clear = button("Clear Logs", "danger")
        save.clicked.connect(on_export)
        clear.clicked.connect(on_clear)
        root.addWidget(
            page_header(
                "Live Logs",
                "Application, provider and task execution events. Secret values are masked before display.",
                [save, clear],
            )
        )

        control_bar = QFrame()
        control_bar.setObjectName("CompactControlBar")
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(10, 6, 10, 6)
        control_layout.setSpacing(8)
        control_layout.addWidget(label("Log Stream", "CardTitle", False))
        control_layout.addStretch(1)
        self.auto_scroll_status = label("Auto-scroll: On", "Caption", False)
        control_layout.addWidget(self.auto_scroll_status)
        root.addWidget(control_bar)

        self.viewer = QPlainTextEdit()
        self.viewer.setObjectName("LogViewer")
        self.viewer.setReadOnly(True)
        self.viewer.setFont(QFont("Cascadia Mono", 10))
        root.addWidget(self.viewer, 1)

    def configure(self, *, auto_scroll: bool, max_entries: int) -> None:
        self._auto_scroll = bool(auto_scroll)
        self.auto_scroll_status.setText("Auto-scroll: On" if self._auto_scroll else "Auto-scroll: Off")
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
