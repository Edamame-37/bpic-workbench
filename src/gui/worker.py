"""Thread-safe Qt worker runner for XES loading and background analyses (A1 + A5)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QObject, QThread, Signal, Slot

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

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._active: dict[int, tuple[QThread, FunctionWorker]] = {}
        self._next_id = 0

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

        self._active[task_id] = (thread, worker)

        def cleanup() -> None:
            self._active.pop(task_id, None)

        def handle_finished(result: object) -> None:
            try:
                on_done(result)  # type: ignore[arg-type]
            finally:
                thread.quit()

        def handle_error(exc: object) -> None:
            try:
                if on_error is not None and isinstance(exc, Exception):
                    on_error(exc)
            finally:
                thread.quit()

        if on_progress is not None:
            worker.progress.connect(on_progress)

        thread.started.connect(worker.run)
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(cleanup)

        thread.start()
        return task_id

    def wait_all(self, timeout_ms: int = 5000) -> bool:
        """Wait for all active worker threads to finish (primarily for tests/shutdown)."""
        all_finished = True
        for thread, _worker in list(self._active.values()):
            if thread.isRunning() and not thread.wait(timeout_ms):
                all_finished = False
        return all_finished
