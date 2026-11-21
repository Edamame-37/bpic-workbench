"""Thread-safe Qt worker runner for XES loading and background analyses (A1 + A5)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QCoreApplication, QObject, QThread, Qt, Signal, Slot
from tqdm.auto import tqdm

T = TypeVar("T")


class FunctionWorker(QObject):
    """Execute a callable on a QThread without touching Qt widgets."""

    started = Signal()
    progress = Signal(str)
    finished = Signal(object)
    error = Signal(object)

    def __init__(self, job: Callable[[], Any]) -> None:
        super().__init__()
        self._job = job

    @Slot()
    def run(self) -> None:
        self.started.emit()
        try:
            result = self._job()
        except Exception as exc:
            self.error.emit(exc)
        else:
            self.finished.emit(result)


class WorkerManager(QObject):
    """Manage QThread + FunctionWorker lifecycles safely across multiple tasks.

    Compatible with the ``Runner`` callback signature
    ``(job: Callable[[], T], on_done: Callable[[T], None]) -> None``
    used by feature panels.
    """

    _result_ready = Signal(int, object)
    _error_ready = Signal(int, object)
    _progress_ready = Signal(int, str)
    _thread_finished = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # PM4Py imports tqdm.auto and creates its multiprocessing lock while
        # reading XES. Preload both on the GUI thread; lazy-importing asyncio or
        # synchronization modules in a QThread is unstable on Windows/Python 3.13.
        tqdm.get_lock()
        self._active: dict[
            int,
            tuple[
                QThread,
                FunctionWorker,
                Callable[[Any], None],
                Callable[[Exception], None] | None,
                Callable[[str], None] | None,
            ],
        ] = {}
        self._completion_received: set[int] = set()
        self._finished_threads: set[int] = set()
        self._next_id = 0
        self._result_ready.connect(self._deliver_result)
        self._error_ready.connect(self._deliver_error)
        self._progress_ready.connect(self._deliver_progress)
        self._thread_finished.connect(self._cleanup_task)

    def is_busy(self) -> bool:
        return bool(self._active)

    def active_count(self) -> int:
        return len(self._active)

    def run(
        self,
        job: Callable[[], T],
        on_done: Callable[[T], None],
        *,
        on_error: Callable[[Exception], None] | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> int:
        """Start ``job`` in a dedicated QThread and return its task id."""
        self._next_id += 1
        task_id = self._next_id

        thread = QThread(self)
        worker = FunctionWorker(job)
        worker.moveToThread(thread)

        self._active[task_id] = (
            thread,
            worker,
            on_done,
            on_error,
            on_progress,
        )

        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda result, current_id=task_id: self._result_ready.emit(
                current_id, result
            )
        )
        worker.error.connect(
            lambda error, current_id=task_id: self._error_ready.emit(
                current_id, error
            )
        )
        worker.progress.connect(
            lambda message, current_id=task_id: self._progress_ready.emit(
                current_id, message
            )
        )
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.finished.connect(thread.quit, Qt.ConnectionType.DirectConnection)
        worker.error.connect(thread.quit, Qt.ConnectionType.DirectConnection)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda current_id=task_id: self._thread_finished.emit(current_id)
        )

        thread.start()
        return task_id

    @Slot(int, object)
    def _deliver_result(self, task_id: int, result: object) -> None:
        task = self._active.get(task_id)
        try:
            if task is not None:
                task[2](result)
        finally:
            self._mark_completion_received(task_id)

    @Slot(int, object)
    def _deliver_error(self, task_id: int, error: object) -> None:
        task = self._active.get(task_id)
        try:
            if task is not None and task[3] is not None:
                if isinstance(error, Exception):
                    task[3](error)
        finally:
            self._mark_completion_received(task_id)

    @Slot(int, str)
    def _deliver_progress(self, task_id: int, message: str) -> None:
        task = self._active.get(task_id)
        if task is not None and task[4] is not None:
            task[4](message)

    @Slot(int)
    def _cleanup_task(self, task_id: int) -> None:
        self._finished_threads.add(task_id)
        self._finalize_task(task_id)

    def _mark_completion_received(self, task_id: int) -> None:
        self._completion_received.add(task_id)
        self._finalize_task(task_id)

    def _finalize_task(self, task_id: int) -> None:
        if (
            task_id not in self._completion_received
            or task_id not in self._finished_threads
        ):
            return
        self._active.pop(task_id, None)
        self._completion_received.discard(task_id)
        self._finished_threads.discard(task_id)

    def wait_all(self, timeout_ms: int = 5000) -> bool:
        """Wait for all active worker threads to finish (primarily for tests/shutdown)."""
        all_finished = True
        for thread, _worker, _on_done, _on_error, _on_progress in list(
            self._active.values()
        ):
            if thread.isRunning() and not thread.wait(timeout_ms):
                all_finished = False
        application = QCoreApplication.instance()
        if application is not None:
            application.processEvents()
        return all_finished
