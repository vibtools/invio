from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ...core.state import AppState
from ..widgets import button, card, page_header


class ReportsPage(QWidget):
    def __init__(self, state: AppState, on_export: Callable[[], None]):
        super().__init__()
        self.state = state
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        export = button("Export CSV")
        export.clicked.connect(on_export)
        root.addWidget(page_header("Reports", "Task-level sending summaries and outcome counters.", [export]))
        host = card("Task Reports", "Reports update from task state and include results supplied by active task runners.")
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Task", "Provider", "Accounts", "Customer List", "Total", "Success", "Failed", "Status"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in range(4, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        host.layout().addWidget(self.table)
        root.addWidget(host, 1)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for task in self.state.tasks.values():
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                task.name,
                task.provider_name,
                ", ".join(task.account_names),
                task.customer_list_name,
                str(task.total),
                str(task.success),
                str(task.failed),
                task.status,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
