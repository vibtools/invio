from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ...core.state import AppState
from ..widgets import button, card, page_header


class InvoiceTemplatesPage(QWidget):
    def __init__(
        self,
        state: AppState,
        on_new: Callable[[], None],
        on_edit: Callable[[str], None],
        on_delete: Callable[[str], None],
    ):
        super().__init__()
        self.state = state
        self.on_new = on_new
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        new = button("New Template", "primary")
        new.clicked.connect(self.on_new)
        root.addWidget(
            page_header(
                "Invoice Templates",
                "Create reusable invoice content only. Billing, shipping and customer records are deliberately excluded from templates.",
                [new],
            )
        )

        host = card("Templates", "Invoice settings, memo/footer and line items are kept together as a reusable template definition.")
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Template", "Currency", "Due", "Items", "Tax", "Actions"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        host.layout().addWidget(self.table)
        root.addWidget(host, 1)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for template in sorted(self.state.invoice_templates.values(), key=lambda item: item.name.casefold()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                template.name,
                template.currency.upper(),
                f"{template.days_until_due} days",
                str(len(template.items)),
                "On" if template.automatic_tax else "Off",
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(Qt.ItemDataRole.UserRole, template.id)
                self.table.setItem(row, column, cell)
            actions = QWidget()
            from PySide6.QtWidgets import QHBoxLayout

            layout = QHBoxLayout(actions)
            layout.setContentsMargins(0, 1, 0, 1)
            layout.setSpacing(4)
            edit = button("Edit")
            delete = button("Delete", "danger")
            edit.clicked.connect(lambda _checked=False, tid=template.id: self.on_edit(tid))
            delete.clicked.connect(lambda _checked=False, tid=template.id: self.on_delete(tid))
            layout.addWidget(edit)
            layout.addWidget(delete)
            self.table.setCellWidget(row, 5, actions)
