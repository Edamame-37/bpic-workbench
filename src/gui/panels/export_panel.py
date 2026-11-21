"""A5 export, reset, and rerun controls."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.export import EXPECTED_EXERCISE_IDS, ExportPaths, export_results
from src.core.result import AnalysisResult
from src.gui.common import (
    MetricCard,
    PageHeader,
    PrimaryButton,
    SecondaryButton,
    SectionCard,
    StatusBanner,
)

Exporter = Callable[[list[AnalysisResult], str | Path], ExportPaths]
Runner = Callable[
    [Callable[[], ExportPaths | None], Callable[[ExportPaths | None], None]],
    object,
]


class ExportPanel(QWidget):
    """Export the current eight results and coordinate reset/rerun actions."""

    reset_requested = Signal()
    rerun_requested = Signal()
    state_changed = Signal(str)

    def __init__(
        self,
        runner: Runner | None = None,
        exporter: Exporter = export_results,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._exporter = exporter
        self._store: EventStore | None = None
        self._results: list[AnalysisResult] = []
        self._output_directory: Path | None = None
        self._generation = 0
        self._running = False
        self.last_export: ExportPaths | None = None

        self.status = StatusBanner("Belum ada dataset aktif.")
        self.dataset = QLabel("Dataset: belum ada")
        self.dataset.setWordWrap(True)
        self.readiness_metric = MetricCard("Kesiapan hasil", "Hasil tersedia: 0/8")
        self.readiness = self.readiness_metric.value
        self.readiness.setWordWrap(True)

        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_path.setPlaceholderText("Pilih direktori tujuan export...")
        self.choose_button = SecondaryButton("Pilih direktori", "folder")
        self.export_button = PrimaryButton("Export CSV", "export")
        self.export_button.setEnabled(False)

        path_controls = QHBoxLayout()
        path_controls.addWidget(self.output_path, 1)
        path_controls.addWidget(self.choose_button)
        path_controls.addWidget(self.export_button)

        self.summary = QTableWidget(len(EXPECTED_EXERCISE_IDS), 4)
        self.summary.setHorizontalHeaderLabels(
            ["Exercise", "Status", "Count", "Denominator"]
        )
        self.summary.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.reset_button = SecondaryButton("Reset hasil", "reset")
        self.rerun_button = PrimaryButton("Jalankan ulang semua", "rerun")
        self.reset_button.setEnabled(False)
        self.rerun_button.setEnabled(False)
        header = PageHeader(
            "Export",
            "Verifikasi kelengkapan delapan hasil lalu simpan summary, cases, dan evidence.",
        )
        header.actions.addWidget(self.reset_button)
        header.actions.addWidget(self.rerun_button)

        result_card = SectionCard(
            "Status hasil analisis",
            "Semua exercise harus tersedia sebelum CSV dapat ditulis.",
        )
        result_card.body.addWidget(self.summary)

        output_card = SectionCard(
            "Direktori output",
            "Tiga file CSV akan ditulis ke direktori yang dipilih.",
        )
        output_card.body.addLayout(path_controls)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(self.status)
        layout.addWidget(self.dataset)
        layout.addWidget(self.readiness_metric)
        layout.addWidget(result_card, 1)
        layout.addWidget(output_card)

        self.choose_button.clicked.connect(self.choose_directory)
        self.export_button.clicked.connect(self.export)
        self.reset_button.clicked.connect(self.reset_requested)
        self.rerun_button.clicked.connect(self.rerun_requested)
        self._refresh()

    def set_store(self, store: EventStore | None) -> None:
        """Replace the active dataset and invalidate pending export callbacks."""

        self._generation += 1
        self._running = False
        self._store = store
        self._results = []
        self.last_export = None
        self._refresh()
        self.state_changed.emit("idle")

    def set_results(self, results: list[AnalysisResult]) -> None:
        self._results = list(results)
        self.last_export = None
        self._refresh()
        self.state_changed.emit("ready" if self._is_complete() else "idle")

    def results(self) -> list[AnalysisResult]:
        return list(self._results)

    def set_output_directory(self, path: str | Path | None) -> None:
        self._output_directory = Path(path) if path else None
        self.output_path.setText(
            str(self._output_directory) if self._output_directory is not None else ""
        )
        self._refresh_actions()

    def choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Pilih direktori export",
            str(self._output_directory or Path.cwd()),
        )
        if selected:
            self.set_output_directory(selected)

    def export(self) -> None:
        if self._running:
            return
        if not self._is_complete():
            self.status.set_warning("Lengkapi delapan hasil analisis sebelum export.")
            return
        if self._output_directory is None:
            self.status.set_warning("Pilih direktori tujuan export terlebih dahulu.")
            return

        results = list(self._results)
        destination = self._output_directory
        generation = self._generation
        errors: list[Exception] = []
        self._running = True
        self.last_export = None
        self.status.set_loading("Menulis summary, selected cases, dan evidence...")
        self.state_changed.emit("exporting")
        self._refresh_actions()

        def job() -> ExportPaths | None:
            try:
                return self._exporter(results, destination)
            except Exception as error:
                errors.append(error)
                return None

        def on_done(paths: ExportPaths | None) -> None:
            if generation != self._generation:
                return
            self._running = False
            if errors or paths is None:
                error = errors[0] if errors else RuntimeError("Export tidak menghasilkan file")
                self.status.set_error(f"Export gagal: {error}")
                self.state_changed.emit("error")
                self._refresh_actions()
                return
            self.last_export = paths
            names = ", ".join(path.name for path in paths.all())
            self.status.set_success(f"Export selesai: {names}")
            self.state_changed.emit("success")
            self._refresh_actions()

        if self._runner is None:
            on_done(job())
            return
        try:
            self._runner(job, on_done)
        except Exception as error:
            if generation == self._generation:
                self._running = False
                self.status.set_error(f"Export gagal: {error}")
                self.state_changed.emit("error")
                self._refresh_actions()

    def _is_complete(self) -> bool:
        ids = [result.exercise_id for result in self._results]
        return len(ids) == len(EXPECTED_EXERCISE_IDS) and set(ids) == set(
            EXPECTED_EXERCISE_IDS
        )

    def _refresh(self) -> None:
        by_id = {result.exercise_id: result for result in self._results}
        for row, exercise_id in enumerate(EXPECTED_EXERCISE_IDS):
            result = by_id.get(exercise_id)
            values = (
                exercise_id,
                result.status if result is not None else "belum dijalankan",
                (
                    str(result.count)
                    if result is not None and result.status == "ok"
                    else "N/A"
                ),
                str(result.denominator) if result is not None else "N/A",
            )
            for column, value in enumerate(values):
                self.summary.setItem(row, column, QTableWidgetItem(value))

        available = len(set(by_id).intersection(EXPECTED_EXERCISE_IDS))
        self.readiness.setText(f"Hasil tersedia: {available}/8")
        if self._store is None:
            self.dataset.setText("Dataset: belum ada")
            self.status.set_idle("Belum ada dataset aktif.")
        else:
            metadata = self._store.metadata
            name = metadata.get("file_name", metadata.get("dataset_name", "-"))
            sha256 = str(metadata.get("sha256", "-"))
            self.dataset.setText(f"Dataset: {name} | SHA-256: {sha256}")
            if self._is_complete():
                self.status.set_success("Delapan hasil siap diekspor.")
            else:
                self.status.set_idle("Jalankan seluruh analisis untuk melengkapi export.")
        self._refresh_actions()

    def _refresh_actions(self) -> None:
        has_store = self._store is not None
        self.choose_button.setEnabled(not self._running)
        self.export_button.setEnabled(
            not self._running
            and self._is_complete()
            and self._output_directory is not None
        )
        self.reset_button.setEnabled(has_store and not self._running)
        self.rerun_button.setEnabled(has_store and not self._running)
