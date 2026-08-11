from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QHBoxLayout, QTableWidget, QVBoxLayout, QWidget

from ...core.state import AppState
from ..tokens import CONST
from ..widgets import DataGridPager, DataGridToolbar, button, card, data_grid_empty_label, data_table_item, page_header


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
        self.setProperty("dataPage", True)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        new = button("New Template", "primary")
        new.clicked.connect(self.on_new)
        root.addWidget(
            page_header(
                "Invoice Templates",
                "Reusable provider-ready invoice content. Customer, billing, shipping and payment details are deliberately excluded.",
                [new],
            )
        )

        host = card("Templates", "Each task selects one template; provider adapters map supported fields when invoices are created and sent.")
        self.pager = DataGridPager(on_changed=self.refresh)
        self.toolbar = DataGridToolbar(
            "Search templates...",
            on_changed=self._controls_changed,
            filters=(
                ("Currency", (("All currencies", ""),)),
                ("Type", (("All types", ""),)),
            ),
        )
        host.layout().addWidget(self.toolbar)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("InvoiceTemplatesDataTable")
        self.table.setHorizontalHeaderLabels(["TEMPLATE", "CURRENCY", "TYPE", "DUE", "ITEMS", "TAX", "ACTIONS"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        header = self.table.horizontalHeader()
        header.setSectionsClickable(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 80)
        host.layout().addWidget(self.table)
        self.empty = data_grid_empty_label("No templates found.")
        self.empty.setVisible(False)
        host.layout().addWidget(self.empty)
        host.layout().addWidget(self.pager)
        root.addWidget(host, 1)
        self.refresh()

    def _controls_changed(self) -> None:
        self.pager.reset()
        self.refresh()

    def refresh(self) -> None:
        templates = sorted(self.state.invoice_templates.values(), key=lambda item: item.name.casefold())
        currencies = sorted({item.currency.upper() for item in templates})
        invoice_types = sorted({item.invoice_type for item in templates})
        self.toolbar.set_filter_options(0, [("All currencies", ""), *((value, value) for value in currencies)])
        self.toolbar.set_filter_options(1, [("All types", ""), *((value, value) for value in invoice_types)])

        query = self.toolbar.query
        currency_filter = str(self.toolbar.filter_value(0) or "")
        type_filter = str(self.toolbar.filter_value(1) or "")
        filtered = [
            template
            for template in templates
            if (not currency_filter or template.currency.upper() == currency_filter)
            and (not type_filter or template.invoice_type == type_filter)
            and (
                not query
                or query
                in " ".join(
                    (
                        template.name,
                        template.currency.upper(),
                        template.invoice_type,
                        str(template.days_until_due),
                        str(len(template.items)),
                        "auto" if template.automatic_tax else "off",
                    )
                ).casefold()
            )
        ]
        start, end = self.pager.set_total(len(filtered))
        visible = filtered[start:end]

        self.table.setRowCount(0)
        for template in visible:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                template.name,
                template.currency.upper(),
                template.invoice_type,
                f"{template.days_until_due} days",
                str(len(template.items)),
                "Auto" if template.automatic_tax else "Off",
            ]
            for column, value in enumerate(values):
                cell = data_table_item(value, right_align=column in {3, 4})
                cell.setData(Qt.ItemDataRole.UserRole, template.id)
                self.table.setItem(row, column, cell)
            actions = QWidget()
            layout = QHBoxLayout(actions)
            layout.setContentsMargins(0, 1, 0, 1)
            layout.setSpacing(4)
            edit = button("Edit")
            edit.setObjectName("TableActionButton")
            edit.setFixedWidth(32)
            delete = button("Delete", "danger")
            delete.setObjectName("TableActionDangerButton")
            delete.setFixedWidth(44)
            edit.clicked.connect(lambda _checked=False, tid=template.id: self.on_edit(tid))
            delete.clicked.connect(lambda _checked=False, tid=template.id: self.on_delete(tid))
            layout.addWidget(edit)
            layout.addWidget(delete)
            self.table.setCellWidget(row, 6, actions)

        self.empty.setText("No matching records." if (query or currency_filter or type_filter) else "No templates found.")
        self.empty.setVisible(not visible)
