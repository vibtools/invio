from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from ...core.provider_manager import ProviderManager, ProviderManifestError
from ...core.state import AppState
from ..widgets import button, card, label, metric_card, page_header


class DashboardPage(QWidget):
    """Compact live overview built only from current Invio application state."""

    def __init__(self, state: AppState, providers: ProviderManager, on_new_task: Callable[[], None]):
        super().__init__()
        self.state = state
        self.providers = providers
        self.setObjectName("PageContent")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        new_task = button("New Task", "primary")
        new_task.clicked.connect(on_new_task)
        root.addWidget(
            page_header(
                "Dashboard",
                "Live overview of provider readiness, invoice workflow data and task activity.",
                [new_task],
            )
        )

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.metric_values: dict[str, object] = {}
        for key, title_text in (
            ("providers", "Installed Providers"),
            ("accounts", "Accounts"),
            ("templates", "Templates"),
            ("customers", "Customer Emails"),
        ):
            panel, value = metric_card(title_text, "0")
            metrics.addWidget(panel, 1)
            self.metric_values[key] = value
        root.addLayout(metrics)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        readiness = card("Workspace Readiness")
        self.readiness_values: dict[str, object] = {}
        for title_text, key in (
            ("Installed providers", "installed"),
            ("Available accounts", "available_accounts"),
            ("Invoice templates", "template_count"),
            ("Customer lists with data", "ready_lists"),
        ):
            readiness.layout().addLayout(self._value_row(title_text, key, self.readiness_values))
        grid.addWidget(readiness, 0, 0)

        activity = card("Current Task Activity")
        self.activity_values: dict[str, object] = {}
        for title_text, key in (
            ("Running", "running"),
            ("Processed", "processed"),
            ("Successful", "success"),
            ("Failed", "failed"),
            ("Remaining", "remaining"),
        ):
            activity.layout().addLayout(self._value_row(title_text, key, self.activity_values))
        grid.addWidget(activity, 0, 1)

        task_summary = card("Task Summary")
        self.task_values: dict[str, object] = {}
        for title_text, key in (
            ("Ready", "ready"),
            ("Paused", "paused"),
            ("Completed", "completed"),
            ("Failed", "failed_tasks"),
        ):
            task_summary.layout().addLayout(self._value_row(title_text, key, self.task_values))
        grid.addWidget(task_summary, 1, 0)

        account_summary = card("Account Usage")
        self.account_values: dict[str, object] = {}
        for title_text, key in (
            ("Total accounts", "total_accounts"),
            ("Reserved by tasks", "reserved_accounts"),
            ("Available", "free_accounts"),
            ("Providers represented", "account_providers"),
        ):
            account_summary.layout().addLayout(self._value_row(title_text, key, self.account_values))
        grid.addWidget(account_summary, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addLayout(grid)

        next_step = card("Next Step")
        self.next_step = label("", "Description")
        next_step.layout().addWidget(self.next_step)
        root.addWidget(next_step)
        root.addStretch(1)
        self.refresh()

    @staticmethod
    def _value_row(title_text: str, key: str, target: dict[str, object]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(label(title_text, "Description", False), 1)
        value = label("0", "CardTitle", False)
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(value)
        target[key] = value
        return row

    def refresh(self) -> None:
        try:
            installed = self.providers.list_installed()
        except ProviderManifestError:
            installed = []

        accounts = list(self.state.accounts.values())
        templates = list(self.state.invoice_templates.values())
        customer_lists = list(self.state.customer_lists.values())
        tasks = list(self.state.tasks.values())
        customer_emails = sum(item.count for item in customer_lists)
        available_accounts = sum(1 for item in accounts if item.id not in self.state.account_reservations)
        ready_lists = sum(1 for item in customer_lists if item.count > 0)

        self.metric_values["providers"].setText(str(len(installed)))
        self.metric_values["accounts"].setText(str(len(accounts)))
        self.metric_values["templates"].setText(str(len(templates)))
        self.metric_values["customers"].setText(str(customer_emails))

        values = {
            "installed": len(installed),
            "available_accounts": available_accounts,
            "template_count": len(templates),
            "ready_lists": ready_lists,
        }
        for key, value in values.items():
            self.readiness_values[key].setText(str(value))

        running_statuses = {"Running", "Stopping"}
        activity_values = {
            "running": sum(1 for task in tasks if task.status in running_statuses),
            "processed": sum(task.processed for task in tasks),
            "success": sum(task.success for task in tasks),
            "failed": sum(task.failed for task in tasks),
            "remaining": sum(task.remaining for task in tasks),
        }
        for key, value in activity_values.items():
            self.activity_values[key].setText(str(value))

        task_values = {
            "ready": sum(1 for task in tasks if task.status in {"Ready", "Stopped"}),
            "paused": sum(1 for task in tasks if task.status == "Paused"),
            "completed": sum(1 for task in tasks if task.status == "Completed"),
            "failed_tasks": sum(1 for task in tasks if task.status == "Failed"),
        }
        for key, value in task_values.items():
            self.task_values[key].setText(str(value))

        account_values = {
            "total_accounts": len(accounts),
            "reserved_accounts": len(self.state.account_reservations),
            "free_accounts": available_accounts,
            "account_providers": len({account.provider_id for account in accounts}),
        }
        for key, value in account_values.items():
            self.account_values[key].setText(str(value))

        if not installed:
            message = "Install a provider from Providers to begin configuring invoice automation."
        elif not accounts:
            message = "Add a provider account before creating a task."
        elif not templates:
            message = "Create an invoice template for the content that tasks will send."
        elif not ready_lists:
            message = "Create a customer list and import at least one customer email address."
        elif not tasks:
            message = "Workspace data is ready. Create a task to bind provider accounts, a template and a customer list."
        elif any(task.status in running_statuses for task in tasks):
            message = "One or more tasks are running. Monitor progress in Tasks, Reports and Live Logs."
        elif any(task.failed > 0 for task in tasks):
            message = "A task has failed recipients. Review Live Logs, then use Retry Failed from the task card."
        else:
            message = "Workspace is ready. Existing tasks can be started or a new task can be created."
        self.next_step.setText(message)
