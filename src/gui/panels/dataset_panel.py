"""Dataset picker and asynchronous XES loading status panel."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.loader import load_event_log

Loader = Callable[[str | Path], EventStore]
Runner = Callable[
    [
        Callable[[], EventStore | None],
        Callable[[EventStore | None], None],
    ],
    None,
]


class DatasetPanel(QWidget):
    """Load one active XES dataset and publish its validated EventStore."""

    store_changed = Signal(object)
    load_started = Signal(str)
    load_failed = Signal(str)

    def __init__(
        self,
        runner: Runner | None = None,
        loader: Loader = load_event_log,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._loader = loader
        self._generation = 0
        self._running = False
        self._store: EventStore | None = None

        self.choose_button = QPushButton("Pilih file XES")
        self.status = QLabel("Belum ada dataset aktif.")
        self.status.setWordWrap(True)
        self.metadata = QLabel("")
        self.metadata.setWordWrap(True)
        self.warnings = QLabel("")
        self.warnings.setWordWrap(True)
        self.warnings.setStyleSheet("color:#8a4b00;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.choose_button)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.metadata)
        layout.addWidget(self.warnings)
        layout.addStretch(1)

        self.choose_button.clicked.connect(self.choose_file)

    def store(self) -> EventStore | None:
        return self._store

    def choose_file(self) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Pilih event log XES",
            "",
            "XES Event Log (*.xes *.xes.gz);;Semua File (*)",
        )
        if path:
            self.load_path(path)

    def load_path(self, path: str | Path) -> None:
        """Load a path and invalidate any previous dataset or pending result."""

        self._generation += 1
        generation = self._generation
        error_holder: list[Exception] = []

        self._running = True
        self._store = None
        self.choose_button.setEnabled(False)
        self.progress.setVisible(True)
        self.status.setText(f"Memuat {Path(path).name}...")
        self.metadata.clear()
        self.warnings.clear()
        self.store_changed.emit(None)
        self.load_started.emit(str(path))

        def job() -> EventStore | None:
            try:
                return self._loader(path)
            except Exception as error:
                error_holder.append(error)
                return None

        def on_done(store: EventStore | None) -> None:
            if generation != self._generation:
                return
            if error_holder or store is None:
                self._on_error(
                    error_holder[0]
                    if error_holder
                    else RuntimeError("Loader tidak menghasilkan EventStore")
                )
            else:
                self._on_done(store)

        if self._runner is None:
            on_done(job())
            return

        try:
            self._runner(job, on_done)
        except Exception as error:
            if generation == self._generation:
                self._on_error(error)

    def clear(self) -> None:
        self._generation += 1
        self._running = False
        self._store = None
        self.choose_button.setEnabled(True)
        self.progress.setVisible(False)
        self.status.setText("Belum ada dataset aktif.")
        self.metadata.clear()
        self.warnings.clear()
        self.store_changed.emit(None)

    def _on_done(self, store: EventStore) -> None:
        self._running = False
        self._store = store
        self.choose_button.setEnabled(True)
        self.progress.setVisible(False)

        metadata = store.metadata
        file_name = metadata.get("file_name") or metadata.get("dataset_name", "-")
        case_count = int(metadata.get("case_count", 0))
        event_count = int(metadata.get("event_count", 0))
        sha256 = str(metadata.get("sha256", "-"))
        self.status.setText("Dataset berhasil dimuat.")
        self.metadata.setText(
            f"File: {file_name} | Case: {case_count:,} | Event: {event_count:,} | "
            f"SHA-256: {sha256}"
        )

        raw_warnings = metadata.get("warnings", ())
        warning_items = (
            [str(item) for item in raw_warnings]
            if isinstance(raw_warnings, (list, tuple))
            else []
        )
        self.warnings.setText(
            "Peringatan: " + " | ".join(warning_items) if warning_items else ""
        )
        self.store_changed.emit(store)

    def _on_error(self, error: Exception) -> None:
        self._running = False
        self._store = None
        self.choose_button.setEnabled(True)
        self.progress.setVisible(False)
        self.status.setText(f"Gagal memuat dataset: {error}")
        self.metadata.clear()
        self.warnings.clear()
        self.load_failed.emit(str(error))

