from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Task

TASK_STATUSES = frozenset({"Ready", "Running", "Paused", "Stopping", "Stopped", "Failed", "Completed"})


class TaskAction(str, Enum):
    START = "Start"
    PAUSE = "Pause"
    RESUME = "Resume"
    STOP = "Stop"
    RESUME_REMAINING = "Resume Remaining"
    RETRY_FAILED = "Retry Failed"
    CLOSE = "Close Task"


class TaskExecutionMode(str, Enum):
    FIRST_RUN = "first_run"
    RESUME_REMAINING = "resume_remaining"
    RETRY_FAILED = "retry_failed"


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "Ready": frozenset({"Ready", "Running"}),
    "Running": frozenset({"Running", "Paused", "Stopping", "Stopped", "Failed", "Completed"}),
    "Paused": frozenset({"Paused", "Running", "Stopping", "Stopped", "Failed"}),
    "Stopping": frozenset({"Stopping", "Stopped", "Failed"}),
    "Stopped": frozenset({"Stopped", "Running"}),
    "Failed": frozenset({"Failed", "Running"}),
    "Completed": frozenset({"Completed"}),
}

COMPLETED_RESEND_MESSAGE = "This Task is complete. Create a new Task for another full execution."
FAILED_FULL_START_MESSAGE = "A failed Task cannot perform a full Start. Use Retry Failed."
STOPPED_CONTINUATION_MESSAGE = (
    "Resume Remaining sends only recipients that were not successfully completed in this run."
)
CONTINUATION_UNAVAILABLE_MESSAGE = (
    "The exact continuation recipient set is not available in this application session. "
    "Close this Task and create a new Task."
)
EXTERNAL_CONTINUATION_UNAVAILABLE_MESSAGE = (
    "This runner does not expose a safe recipient continuation set. Create a new Task for another full execution."
)
READY_NOT_PRISTINE_MESSAGE = (
    "This Ready Task already contains progress and cannot be treated as a first run. Close it and create a new Task."
)


@dataclass(frozen=True, slots=True)
class TaskActionPolicy:
    start_enabled: bool
    start_label: str
    start_tooltip: str
    pause_enabled: bool
    resume_enabled: bool
    stop_enabled: bool
    retry_enabled: bool
    retry_tooltip: str
    close_enabled: bool


def validate_status_transition(current: str, target: str) -> None:
    if current not in TASK_STATUSES:
        raise ValueError(f"Task has unsupported current status '{current}'.")
    if target not in TASK_STATUSES:
        raise ValueError(f"Task status '{target}' is not supported.")
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Task status transition {current} -> {target} is not allowed.")


def is_pristine_first_run(task: "Task") -> bool:
    return task.processed == 0 and task.success == 0 and task.failed == 0


def task_action_policy(
    task: "Task",
    *,
    resume_remaining_available: bool = False,
    retry_failed_available: bool = False,
    continuation_unavailable_message: str = CONTINUATION_UNAVAILABLE_MESSAGE,
) -> TaskActionPolicy:
    snapshot_ready = task.has_immutable_execution_snapshot
    status = task.status

    start_enabled = False
    start_label = "Start"
    start_tooltip = ""
    pause_enabled = False
    resume_enabled = False
    stop_enabled = False
    retry_enabled = False
    retry_tooltip = ""
    close_enabled = status in {"Ready", "Stopped", "Failed", "Completed"}

    if not snapshot_ready:
        from .models import LEGACY_SNAPSHOT_MESSAGE

        start_tooltip = LEGACY_SNAPSHOT_MESSAGE
        retry_tooltip = LEGACY_SNAPSHOT_MESSAGE
        return TaskActionPolicy(
            start_enabled=False,
            start_label=start_label,
            start_tooltip=start_tooltip,
            pause_enabled=False,
            resume_enabled=False,
            stop_enabled=False,
            retry_enabled=False,
            retry_tooltip=retry_tooltip,
            close_enabled=close_enabled,
        )

    if status == "Ready":
        start_enabled = is_pristine_first_run(task)
        if not start_enabled:
            start_tooltip = READY_NOT_PRISTINE_MESSAGE
    elif status == "Running":
        pause_enabled = True
        stop_enabled = True
        close_enabled = False
    elif status == "Paused":
        resume_enabled = True
        stop_enabled = True
        close_enabled = False
    elif status == "Stopping":
        close_enabled = False
    elif status == "Stopped":
        start_label = "Resume Remaining"
        start_enabled = resume_remaining_available
        start_tooltip = STOPPED_CONTINUATION_MESSAGE if start_enabled else continuation_unavailable_message
    elif status == "Failed":
        start_tooltip = FAILED_FULL_START_MESSAGE
        retry_enabled = retry_failed_available
        retry_tooltip = "Retry only the exact failed recipient set from this run." if retry_enabled else continuation_unavailable_message
    elif status == "Completed":
        start_tooltip = COMPLETED_RESEND_MESSAGE
        retry_tooltip = COMPLETED_RESEND_MESSAGE

    return TaskActionPolicy(
        start_enabled=start_enabled,
        start_label=start_label,
        start_tooltip=start_tooltip,
        pause_enabled=pause_enabled,
        resume_enabled=resume_enabled,
        stop_enabled=stop_enabled,
        retry_enabled=retry_enabled,
        retry_tooltip=retry_tooltip,
        close_enabled=close_enabled,
    )


def require_task_action(
    task: "Task",
    action: TaskAction,
    *,
    resume_remaining_available: bool = False,
    retry_failed_available: bool = False,
    continuation_unavailable_message: str = CONTINUATION_UNAVAILABLE_MESSAGE,
) -> TaskExecutionMode | None:
    if not task.has_immutable_execution_snapshot and action in {
        TaskAction.START,
        TaskAction.RESUME_REMAINING,
        TaskAction.RETRY_FAILED,
    }:
        from .models import LEGACY_SNAPSHOT_MESSAGE

        raise ValueError(LEGACY_SNAPSHOT_MESSAGE)

    status = task.status
    if action is TaskAction.START:
        if status == "Completed":
            raise ValueError(COMPLETED_RESEND_MESSAGE)
        if status == "Failed":
            raise ValueError(FAILED_FULL_START_MESSAGE)
        if status == "Stopped":
            raise ValueError("A stopped Task cannot perform a full Start. Use Resume Remaining.")
        if status != "Ready":
            raise ValueError(f"Start is not available while the Task is {status}.")
        if not is_pristine_first_run(task):
            raise ValueError(READY_NOT_PRISTINE_MESSAGE)
        return TaskExecutionMode.FIRST_RUN

    if action is TaskAction.RESUME_REMAINING:
        if status != "Stopped":
            raise ValueError(f"Resume Remaining is not available while the Task is {status}.")
        if not resume_remaining_available:
            raise ValueError(continuation_unavailable_message)
        return TaskExecutionMode.RESUME_REMAINING

    if action is TaskAction.RETRY_FAILED:
        if status != "Failed":
            raise ValueError(f"Retry Failed is not available while the Task is {status}.")
        if not retry_failed_available:
            raise ValueError(continuation_unavailable_message)
        return TaskExecutionMode.RETRY_FAILED

    if action is TaskAction.PAUSE:
        if status != "Running":
            raise ValueError(f"Pause is not available while the Task is {status}.")
        return None

    if action is TaskAction.RESUME:
        if status != "Paused":
            raise ValueError(f"Resume is not available while the Task is {status}.")
        return None

    if action is TaskAction.STOP:
        if status not in {"Running", "Paused"}:
            raise ValueError(f"Stop is not available while the Task is {status}.")
        return None

    if action is TaskAction.CLOSE:
        if status in {"Running", "Paused", "Stopping"}:
            raise ValueError("Stop the task before closing it.")
        return None

    raise ValueError(f"Unsupported Task action: {action}.")
