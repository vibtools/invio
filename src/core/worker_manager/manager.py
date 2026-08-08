from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Protocol

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ...tasks.models import Task


@dataclass(slots=True)
class TaskExecutionContext:
    task: Task
    pause_gate: threading.Event
    stop_flag: threading.Event
    progress: Callable[[int, int, int, str], None]
    log: Callable[[str], None]


class TaskRunner(Protocol):
    def __call__(self, context: TaskExecutionContext) -> None: ...


class _TaskWorker(QObject):
    progress_changed = Signal(str, int, int, int, str)
    status_changed = Signal(str, str, str)
    log_message = Signal(str, str)
    finished = Signal(str, str)

    def __init__(self, task: Task, runner: TaskRunner):
        super().__init__()
        self.task = task
        self.runner = runner
        self.pause_gate = threading.Event()
        self.pause_gate.set()
        self.stop_flag = threading.Event()

    @Slot()
    def run(self) -> None:
        self.status_changed.emit(self.task.id, "Running", "Worker thread started")
        context = TaskExecutionContext(
            task=self.task,
            pause_gate=self.pause_gate,
            stop_flag=self.stop_flag,
            progress=lambda processed, success, failed, message: self.progress_changed.emit(
                self.task.id, processed, success, failed, message
            ),
            log=lambda message: self.log_message.emit(self.task.id, message),
        )
        final_status = "Completed"
        try:
            self.runner(context)
            if self.stop_flag.is_set():
                final_status = "Stopped"
        except Exception as exc:  # backend exceptions are isolated from the GUI thread
            final_status = "Failed"
            self.log_message.emit(self.task.id, f"Worker error: {exc}")
        self.finished.emit(self.task.id, final_status)

    def pause(self) -> None:
        self.pause_gate.clear()
        self.status_changed.emit(self.task.id, "Paused", "Task paused")

    def resume(self) -> None:
        self.pause_gate.set()
        self.status_changed.emit(self.task.id, "Running", "Task resumed")

    def stop(self) -> None:
        self.stop_flag.set()
        self.pause_gate.set()
        self.status_changed.emit(self.task.id, "Stopping", "Stop requested")


@dataclass(slots=True)
class _WorkerSlot:
    thread: QThread
    worker: _TaskWorker


class WorkerManager(QObject):
    """Owns one QThread per active task.

    Provider sending logic is injected as a runner. If no runner is registered
    for a provider, execution remains unavailable; registered runners execute on
    the task-owned worker thread rather than the GUI thread.
    """

    progress_changed = Signal(str, int, int, int, str)
    status_changed = Signal(str, str, str)
    log_message = Signal(str, str)
    finished = Signal(str, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._slots: dict[str, _WorkerSlot] = {}

    def is_running(self, task_id: str) -> bool:
        slot = self._slots.get(task_id)
        return bool(slot and slot.thread.isRunning())

    def start(self, task: Task, runner: TaskRunner) -> None:
        if self.is_running(task.id):
            return
        thread = QThread(self)
        thread.setObjectName(f"InvioTaskThread-{task.id}")
        worker = _TaskWorker(task, runner)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_changed.connect(self.progress_changed)
        worker.status_changed.connect(self.status_changed)
        worker.log_message.connect(self.log_message)
        worker.finished.connect(self._forward_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda tid=task.id: self._slots.pop(tid, None))
        self._slots[task.id] = _WorkerSlot(thread=thread, worker=worker)
        thread.start()

    def pause(self, task_id: str) -> None:
        slot = self._slots.get(task_id)
        if slot:
            slot.worker.pause()

    def resume(self, task_id: str) -> None:
        slot = self._slots.get(task_id)
        if slot:
            slot.worker.resume()

    def stop(self, task_id: str) -> None:
        slot = self._slots.get(task_id)
        if slot:
            slot.worker.stop()

    def stop_all(self, wait_ms: int = 1500) -> None:
        slots = list(self._slots.values())
        for slot in slots:
            slot.worker.stop()
        for slot in slots:
            if slot.thread.isRunning():
                slot.thread.wait(wait_ms)

    @Slot(str, str)
    def _forward_finished(self, task_id: str, status: str) -> None:
        self.finished.emit(task_id, status)
