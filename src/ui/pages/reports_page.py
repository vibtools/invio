from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.state import AppState
from ...tasks.delivery_ledger import RecipientDeliveryReportRecord
from ..tokens import CONST
from ..widgets import (
    DataGridPager,
    DataGridToolbar,
    button,
    card,
    data_grid_empty_label,
    data_table_item,
    set_data_status_cell,
    page_header,
)


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
        self.setProperty("dataPage", True)
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
        self.task_pager = DataGridPager(on_changed=self._refresh_task_table)
        self.task_toolbar = DataGridToolbar(
            "Search tasks...",
            on_changed=self._task_controls_changed,
            filters=(
                ("Provider", (("All providers", ""),)),
                ("Status", (("All statuses", ""),)),
            ),
        )
        host.layout().addWidget(self.task_toolbar)
        self.table = QTableWidget(0, 9)
        self.table.setObjectName("ReportTable")
        self.table.setHorizontalHeaderLabels(
            ["TASK", "PROVIDER", "TEMPLATE", "ACCOUNTS", "CUSTOMER LIST", "TOTAL", "SUCCESS", "FAILED", "STATUS"]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        header = self.table.horizontalHeader()
        header.setSectionsClickable(False)
        for col in (0, 1, 5, 6, 7, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        host.layout().setContentsMargins(8, 8, 8, 8)
        host.layout().addWidget(self.table)
        self.task_empty = data_grid_empty_label("No task records found.")
        self.task_empty.setVisible(False)
        host.layout().addWidget(self.task_empty)
        host.layout().addWidget(self.task_pager)
        root.addWidget(host, 1)

        recipient_host = card(
            "Recipient Delivery History",
            "Provider acceptance is shown separately from independently confirmed email delivery.",
        )
        recipient_host.setObjectName("RecipientReportTableSurface")
        self.recipient_pager = DataGridPager(on_changed=self._refresh_recipient_table)
        self.recipient_toolbar = DataGridToolbar(
            "Search delivery history...",
            on_changed=self._recipient_controls_changed,
            filters=(
                ("Provider", (("All providers", ""),)),
                ("Safe status", (("All statuses", ""),)),
            ),
        )
        recipient_host.layout().addWidget(self.recipient_toolbar)
        self.recipient_table = QTableWidget(0, 11)
        self.recipient_table.setObjectName("RecipientReportTable")
        self.recipient_table.setHorizontalHeaderLabels(
            [
                "TASK",
                "RECIPIENT",
                "PROVIDER",
                "SAFE STATUS",
                "ATTEMPTS",
                "ACCOUNT REFERENCE",
                "PROVIDER INVOICE",
                "LAST STAGE",
                "ERROR CODE",
                "PROVIDER SEND ACCEPTANCE",
                "EMAIL DELIVERY",
            ]
        )
        self.recipient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.recipient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recipient_table.setAlternatingRowColors(True)
        self.recipient_table.verticalHeader().setVisible(False)
        self.recipient_table.verticalHeader().setDefaultSectionSize(CONST.table_row_height)
        recipient_header = self.recipient_table.horizontalHeader()
        recipient_header.setSectionsClickable(False)
        for col in (2, 3, 4, 8, 9):
            recipient_header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        for col in (0, 1, 5, 6, 7, 10):
            recipient_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        recipient_host.layout().setContentsMargins(8, 8, 8, 8)
        recipient_host.layout().addWidget(self.recipient_table)
        self.recipient_empty = data_grid_empty_label("No delivery records found.")
        self.recipient_empty.setVisible(False)
        recipient_host.layout().addWidget(self.recipient_empty)
        recipient_host.layout().addWidget(self.recipient_pager)
        root.addWidget(recipient_host, 2)
        self.refresh()

    def _task_controls_changed(self) -> None:
        self.task_pager.reset()
        self._refresh_task_table()

    def _recipient_controls_changed(self) -> None:
        self.recipient_pager.reset()
        self._refresh_recipient_table()

    def refresh(self) -> None:
        self._refresh_task_table()
        self._refresh_recipient_table()

    def _refresh_task_table(self) -> None:
        records = list(self.state.tasks.values())
        providers = sorted({task.provider_name for task in records}, key=str.casefold)
        statuses = sorted({task.status for task in records}, key=str.casefold)
        self.task_toolbar.set_filter_options(0, [("All providers", ""), *((value, value) for value in providers)])
        self.task_toolbar.set_filter_options(1, [("All statuses", ""), *((value, value) for value in statuses)])

        query = self.task_toolbar.query
        provider_filter = str(self.task_toolbar.filter_value(0) or "")
        status_filter = str(self.task_toolbar.filter_value(1) or "")
        filtered = [
            task
            for task in records
            if (not provider_filter or task.provider_name == provider_filter)
            and (not status_filter or task.status == status_filter)
            and (
                not query
                or query
                in " ".join(
                    (
                        task.name,
                        task.provider_name,
                        task.invoice_template_name,
                        ", ".join(task.account_names),
                        task.customer_list_name,
                        str(task.total),
                        str(task.success),
                        str(task.failed),
                        task.status,
                    )
                ).casefold()
            )
        ]
        start, end = self.task_pager.set_total(len(filtered))
        visible = filtered[start:end]

        self.table.setRowCount(0)
        for task in visible:
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
                if col == 8:
                    set_data_status_cell(self.table, row, col, value)
                else:
                    self.table.setItem(row, col, data_table_item(value, right_align=col in {5, 6, 7}))

        self.task_empty.setText("No matching records." if (query or provider_filter or status_filter) else "No task records found.")
        self.task_empty.setVisible(not visible)

    def _load_recipient_records(self) -> list[RecipientDeliveryReportRecord]:
        return list(self.on_load_recipients()) if self.on_load_recipients is not None else []

    def _refresh_recipient_table(self) -> None:
        records = self._load_recipient_records()
        providers = sorted({record.provider_id for record in records}, key=str.casefold)
        safe_statuses = sorted({record.safe_status for record in records}, key=str.casefold)
        self.recipient_toolbar.set_filter_options(0, [("All providers", ""), *((value, value) for value in providers)])
        self.recipient_toolbar.set_filter_options(1, [("All statuses", ""), *((value, value) for value in safe_statuses)])

        query = self.recipient_toolbar.query
        provider_filter = str(self.recipient_toolbar.filter_value(0) or "")
        safe_filter = str(self.recipient_toolbar.filter_value(1) or "")
        filtered: list[RecipientDeliveryReportRecord] = []
        for record in records:
            if provider_filter and record.provider_id != provider_filter:
                continue
            if safe_filter and record.safe_status != safe_filter:
                continue
            searchable = " ".join(
                (
                    record.task_name,
                    record.task_id,
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
                )
            ).casefold()
            if query and query not in searchable:
                continue
            filtered.append(record)

        start, end = self.recipient_pager.set_total(len(filtered))
        visible = filtered[start:end]
        self.recipient_table.setRowCount(0)
        for record in visible:
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
            badge_columns = {3, 8, 9, 10}
            for col, value in enumerate(values):
                if col in badge_columns and value:
                    set_data_status_cell(self.recipient_table, row, col, value)
                else:
                    self.recipient_table.setItem(row, col, data_table_item(value, right_align=col == 4))

        self.recipient_empty.setText(
            "No matching records." if (query or provider_filter or safe_filter) else "No delivery records found."
        )
        self.recipient_empty.setVisible(not visible)
