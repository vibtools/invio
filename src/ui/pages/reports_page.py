from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.state import AppState
from ...tasks.delivery_ledger import RecipientDeliveryReportRecord
from ..widgets import button, card, page_header


class ReportsPage(QWidget):
    def __init__(
        self,
        state: AppState,
        on_export: Callable[[], None],
        on_load_recipients: Callable[[], Iterable[RecipientDeliveryReportRecord]] | None = None,
        on_export_recipients: Callable[[], None] | None = None,
        on_clear_delivery_history: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.state = state
        self.on_load_recipients = on_load_recipients
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        export = button("Export Task CSV")
        export.clicked.connect(on_export)
        actions = [export]
        if on_export_recipients is not None:
            export_recipients = button("Export Recipient CSV")
            export_recipients.clicked.connect(on_export_recipients)
            actions.append(export_recipients)
        if on_clear_delivery_history is not None:
            clear_history = button("Clear Delivery History", "danger")
            clear_history.clicked.connect(on_clear_delivery_history)
            actions.append(clear_history)
        root.addWidget(
            page_header(
                "Reports",
                "Task summaries plus privacy-bounded recipient delivery history from the durable delivery ledger.",
                actions,
            )
        )

        host = card("Task Summary", "Current operational Task counters are preserved unchanged.")
        host.setObjectName("ReportTableSurface")
        self.table = QTableWidget(0, 9)
        self.table.setObjectName("ReportTable")
        self.table.setHorizontalHeaderLabels(
            ["Task", "Provider", "Template", "Accounts", "Customer List", "Total", "Success", "Failed", "Status"]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for col in (0, 1, 5, 6, 7, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        host.layout().setContentsMargins(8, 8, 8, 8)
        host.layout().addWidget(self.table)
        root.addWidget(host, 1)

        recipient_host = card(
            "Recipient Delivery History",
            "Provider acceptance is shown separately from independently confirmed email delivery.",
        )
        recipient_host.setObjectName("RecipientReportTableSurface")
        self.recipient_table = QTableWidget(0, 11)
        self.recipient_table.setObjectName("RecipientReportTable")
        self.recipient_table.setHorizontalHeaderLabels(
            [
                "Task",
                "Recipient",
                "Provider",
                "Safe Status",
                "Attempts",
                "Account Reference",
                "Provider Invoice",
                "Last Stage",
                "Error Code",
                "Provider Send Acceptance",
                "Email Delivery",
            ]
        )
        self.recipient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.recipient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recipient_table.verticalHeader().setVisible(False)
        recipient_header = self.recipient_table.horizontalHeader()
        for col in (2, 3, 4, 8, 9):
            recipient_header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        for col in (0, 1, 5, 6, 7, 10):
            recipient_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        recipient_host.layout().setContentsMargins(8, 8, 8, 8)
        recipient_host.layout().addWidget(self.recipient_table)
        root.addWidget(recipient_host, 2)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for task in self.state.tasks.values():
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                task.name,
                task.provider_name,
                task.invoice_template_name,
                ", ".join(task.account_names),
                task.customer_list_name,
                str(task.total),
                str(task.success),
                str(task.failed),
                task.status,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

        self.recipient_table.setRowCount(0)
        records = tuple(self.on_load_recipients()) if self.on_load_recipients is not None else ()
        for record in records:
            row = self.recipient_table.rowCount()
            self.recipient_table.insertRow(row)
            values = [
                f"{record.task_name} ({record.task_id})",
                record.recipient_email,
                record.provider_id,
                record.safe_status,
                str(record.attempts),
                record.account_reference,
                record.provider_invoice_reference,
                record.last_stage,
                record.error_code,
                record.provider_send_acceptance,
                record.email_delivery,
            ]
            for col, value in enumerate(values):
                self.recipient_table.setItem(row, col, QTableWidgetItem(value))
