from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QProgressBar, QScrollArea, QVBoxLayout, QWidget

from ...core.state import AppState
from ...tasks.models import LEGACY_SNAPSHOT_MESSAGE, Task
from ...tasks.state_machine import TaskActionPolicy, task_action_policy
from ..widgets import button, card, divider, label, metric_card, page_header, status_badge


class TaskCard(QWidget):
    def __init__(
        self,
        task: Task,
        on_start: Callable[[str], None],
        on_pause: Callable[[str], None],
        on_resume: Callable[[str], None],
        on_stop: Callable[[str], None],
        on_retry: Callable[[str], None],
        on_close: Callable[[str], None],
        policy_provider: Callable[[Task], TaskActionPolicy] | None = None,
    ):
        super().__init__()
        self.task = task
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_stop = on_stop
        self.on_retry = on_retry
        self.on_close = on_close
        self.policy_provider = policy_provider
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        panel = card()
        self.panel_layout = panel.layout()
        root.addWidget(panel)

        header = QHBoxLayout()
        title_host = QWidget()
        title_layout = QVBoxLayout(title_host)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(3)
        title_layout.addWidget(label(task.name, "CardTitle", False))
        header.addWidget(title_host, 1)

        self.start_btn = button("Start", "primary")
        self.pause_btn = button("Pause")
        self.resume_btn = button("Resume")
        self.stop_btn = button("Stop", "danger")
        self.retry_btn = button("Retry Failed")
        self.close_btn = button("Close Task")
        for widget, callback in (
            (self.start_btn, on_start),
            (self.pause_btn, on_pause),
            (self.resume_btn, on_resume),
            (self.stop_btn, on_stop),
            (self.retry_btn, on_retry),
            (self.close_btn, on_close),
        ):
            widget.clicked.connect(lambda _checked=False, cb=callback: cb(task.id))
            header.addWidget(widget)
        self.status_badge = status_badge(task.status)
        header.addWidget(self.status_badge)
        self.panel_layout.addLayout(header)
        self.panel_layout.addWidget(divider())

        summary = QHBoxLayout()
        for title_text, value in (
            ("Provider", task.provider_name),
            ("Invoice Template", task.invoice_template_name),
            ("Accounts", ", ".join(task.account_names)),
            ("Customer List", task.customer_list_name),
        ):
            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(2)
            block_layout.addWidget(label(title_text, "Caption", False))
            block_layout.addWidget(label(value, "Description", False))
            summary.addWidget(block, 1)
        self.panel_layout.addLayout(summary)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.panel_layout.addWidget(self.progress)

        metrics = QHBoxLayout()
        self.metric_values: dict[str, object] = {}
        for key, title_text, value, tone in (
            ("status", "Status", task.status, "neutral"),
            ("total", "Total", str(task.total), "neutral"),
            ("success", "Success", str(task.success), "success"),
            ("failed", "Failed", str(task.failed), "danger"),
            ("remaining", "Remaining", str(task.remaining), "neutral"),
        ):
            metric, value_label = metric_card(title_text, value, tone)
            metrics.addWidget(metric, 1)
            self.metric_values[key] = value_label
        self.panel_layout.addLayout(metrics)
        self.message = label(task.last_message, "Caption", False)
        self.panel_layout.addWidget(self.message)
        self.refresh(task)

    def refresh(self, task: Task) -> None:
        self.task = task
        self.status_badge.setText(task.status)
        self.metric_values["status"].setText(task.status)
        self.metric_values["total"].setText(str(task.total))
        self.metric_values["success"].setText(str(task.success))
        self.metric_values["failed"].setText(str(task.failed))
        self.metric_values["remaining"].setText(str(task.remaining))
        percent = int(task.processed * 100 / task.total) if task.total else 0
        self.progress.setValue(percent)
        self.message.setText(task.last_message)
        snapshot_ready = task.has_immutable_execution_snapshot
        policy = self.policy_provider(task) if self.policy_provider is not None else task_action_policy(task)
        self.start_btn.setText(policy.start_label)
        self.start_btn.setEnabled(snapshot_ready and policy.start_enabled)
        self.pause_btn.setEnabled(policy.pause_enabled)
        self.resume_btn.setEnabled(policy.resume_enabled)
        self.stop_btn.setEnabled(policy.stop_enabled)
        self.retry_btn.setEnabled(snapshot_ready and policy.retry_enabled)
        self.close_btn.setEnabled(policy.close_enabled)
        snapshot_tooltip = "" if snapshot_ready else LEGACY_SNAPSHOT_MESSAGE
        self.start_btn.setToolTip(policy.start_tooltip or snapshot_tooltip)
        self.retry_btn.setToolTip(policy.retry_tooltip or snapshot_tooltip)


class TasksPage(QWidget):
    def __init__(
        self,
        state: AppState,
        on_new: Callable[[], None],
        on_start: Callable[[str], None],
        on_pause: Callable[[str], None],
        on_resume: Callable[[str], None],
        on_stop: Callable[[str], None],
        on_retry: Callable[[str], None],
        on_close: Callable[[str], None],
        policy_provider: Callable[[Task], TaskActionPolicy] | None = None,
    ):
        super().__init__()
        self.state = state
        self.callbacks = (on_start, on_pause, on_resume, on_stop, on_retry, on_close)
        self.policy_provider = policy_provider
        self.cards: dict[str, TaskCard] = {}
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        new = button("New Task", "primary")
        new.clicked.connect(on_new)
        root.addWidget(
            page_header(
                "Tasks",
                "Independent tasks reserve their selected accounts and are designed to execute provider sending in separate backend threads without blocking the UI.",
                [new],
            )
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.host.setObjectName("PageInner")
        self.layout = QVBoxLayout(self.host)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.layout.addStretch(1)
        scroll.setWidget(self.host)
        root.addWidget(scroll, 1)
        self.refresh()

    def refresh(self) -> None:
        for task_id, widget in list(self.cards.items()):
            if task_id not in self.state.tasks:
                self.layout.removeWidget(widget)
                widget.deleteLater()
                self.cards.pop(task_id, None)
        for task in self.state.tasks.values():
            if task.id not in self.cards:
                card_widget = TaskCard(task, *self.callbacks, self.policy_provider)
                self.layout.insertWidget(self.layout.count() - 1, card_widget)
                self.cards[task.id] = card_widget
            else:
                self.cards[task.id].refresh(task)
        if not self.state.tasks and not hasattr(self, "empty"):
            self.empty = card("No Tasks", "Create a task after installing a provider, adding provider accounts, creating an invoice template and preparing a customer list.")
            self.layout.insertWidget(0, self.empty)
        elif self.state.tasks and hasattr(self, "empty"):
            self.layout.removeWidget(self.empty)
            self.empty.deleteLater()
            delattr(self, "empty")

    def refresh_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task and task_id in self.cards:
            self.cards[task_id].refresh(task)
