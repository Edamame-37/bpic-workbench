"""A4 - Panel Exercise 11.22 (eventually follows O_Cancelled -> O_Accepted).

Kontrak:
    panel.set_store(store)                  # dataset baru / None
    panel.open_case_requested(str, list)    # case_id, [cancel_row_id, accept_row_id]
    panel.results_changed                   # hasil baru / reset (untuk ekspor A5)
    panel.result                            # AnalysisResult terakhir atau None
"""

from collections.abc import Callable

import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.ex_11_22 import run_11_22
from src.core.ordering import EVIDENCE_COLUMNS
from src.core.result import AnalysisResult
from src.gui.panels.case_explorer_panel import DataFrameTableModel

Runner = Callable[
    [Callable[[], AnalysisResult | None], Callable[[AnalysisResult | None], None]],
    None,
]


def format_percentage(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


class SequencePanel(QWidget):
    open_case_requested = Signal(str, list)
    results_changed = Signal()

    def __init__(self, runner: Runner | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._runner = runner
        self._store: EventStore | None = None
        self._generation = 0
        self._running = False
        self.result: AnalysisResult | None = None

        self.status = QLabel("Belum ada dataset aktif.")
        self.run_button = QPushButton("Jalankan 11.22")
        self.reset_button = QPushButton("Reset hasil")

        self.count_label = QLabel("Count: –")
        self.denominator_label = QLabel("Denominator: –")
        self.percentage_label = QLabel("Persentase: –")
        for label in (self.count_label, self.denominator_label, self.percentage_label):
            label.setStyleSheet("font-size: 15px; font-weight: 600;")

        self.rule = QLabel("")
        self.rule.setWordWrap(True)
        self.notes = QLabel("")
        self.notes.setWordWrap(True)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari case ID pada hasil...")
        self.model = DataFrameTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.timeline = QLabel("Pilih satu baris untuk melihat pasangan cancel → accept.")
        self.timeline.setWordWrap(True)
        self.open_button = QPushButton("Buka di Case Explorer")
        self.open_button.setEnabled(False)

        buttons = QHBoxLayout()
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.reset_button)
        kpi = QHBoxLayout()
        for label in (self.count_label, self.denominator_label, self.percentage_label):
            kpi.addWidget(label)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addLayout(buttons)
        layout.addLayout(kpi)
        layout.addWidget(self.rule)
        layout.addWidget(self.notes)
        layout.addWidget(QLabel("Pasangan event pembukti (satu baris per case):"))
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.timeline)
        layout.addWidget(self.open_button)

        self.run_button.clicked.connect(self.run)
        self.reset_button.clicked.connect(self.reset)
        self.search.textChanged.connect(self._apply_filter)
        self.table.selectionModel().selectionChanged.connect(self._on_row_selected)
        self.table.doubleClicked.connect(lambda _: self._emit_open_case())
        self.open_button.clicked.connect(self._emit_open_case)

        self.reset()

    # ---- kontrak publik -------------------------------------------------
    def set_store(self, store: EventStore | None) -> None:
        self._store = store
        self.reset()

    def run(self) -> None:
        if self._running:
            return
        if self._store is None:
            self.status.setText("Impor file XES terlebih dahulu.")
            return

        store, generation = self._store, self._generation
        errors: list[Exception] = []
        self._running = True
        self.run_button.setEnabled(False)
        self.status.setText("Menghitung...")

        def job() -> AnalysisResult | None:
            try:
                return run_11_22(store)
            except Exception as exc:  # dilaporkan lewat callback yang sama
                errors.append(exc)
                return None

        def on_done(result: AnalysisResult | None) -> None:
            if generation != self._generation:
                return  # dataset sudah diganti / di-reset saat worker berjalan
            if errors or result is None:
                self._on_error(errors[0] if errors else RuntimeError("tanpa hasil"))
            else:
                self._on_done(result)

        if self._runner is None:
            on_done(job())
            return
        try:
            self._runner(job, on_done)
        except Exception as exc:
            if generation == self._generation:
                self._on_error(exc)

    def reset(self) -> None:
        self._generation += 1
        self._running = False
        self.result = None
        self.count_label.setText("Count: –")
        self.denominator_label.setText("Denominator: –")
        self.percentage_label.setText("Persentase: –")
        self.rule.clear()
        self.notes.clear()
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.model.set_frame(pd.DataFrame(columns=list(EVIDENCE_COLUMNS)))
        self.timeline.setText("Pilih satu baris untuk melihat pasangan cancel → accept.")
        self.open_button.setEnabled(False)
        self.run_button.setEnabled(self._store is not None)
        self.status.setText("Belum ada dataset aktif." if self._store is None else "Siap dijalankan.")
        self.results_changed.emit()

    # ---- internal -------------------------------------------------------
    def _on_done(self, result: AnalysisResult) -> None:
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self.result = result
        ok = result.status == "ok"

        self.count_label.setText(f"Count: {result.count:,}" if ok else "Count: N/A")
        self.denominator_label.setText(f"Denominator: {result.denominator:,}")
        self.percentage_label.setText(f"Persentase: {format_percentage(result.percentage)}")
        self.rule.setText(f"Aturan: {result.rule_description}")
        self.notes.setText(result.notes)
        self.notes.setStyleSheet("" if ok else "color:#b00020; font-weight:bold;")
        self.status.setText("Selesai." if ok else f"Status: {result.status}")
        evidence = result.evidence if result.evidence is not None else pd.DataFrame(
            columns=list(EVIDENCE_COLUMNS)
        )
        self.model.set_frame(evidence, list(EVIDENCE_COLUMNS))
        self._apply_filter(self.search.text())
        self.results_changed.emit()

    def _on_error(self, error: Exception) -> None:
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self.result = None
        self.model.set_frame(pd.DataFrame(columns=list(EVIDENCE_COLUMNS)))
        self.status.setText(f"Analisis gagal: {error}")
        self.results_changed.emit()

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().casefold()
        frame = self.model.frame()
        for row in range(len(frame)):
            hidden = bool(needle) and needle not in str(frame.iat[row, 0]).casefold()
            self.table.setRowHidden(row, hidden)
        self._on_row_selected()

    def _selected_row(self) -> pd.Series | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows or self.table.isRowHidden(rows[0].row()):
            return None
        return self.model.frame().iloc[rows[0].row()]

    def _on_row_selected(self, *_args) -> None:
        row = self._selected_row()
        self.open_button.setEnabled(row is not None)
        if row is None:
            self.timeline.setText("Pilih satu baris untuk melihat pasangan cancel → accept.")
            return
        self.timeline.setText(
            f"Case {row['case_id']}:  [i={row['cancel_position']}] O_Cancelled "
            f"({row['cancel_timestamp']})  ──▶  [j={row['accept_position']}] O_Accepted "
            f"({row['accept_timestamp']})"
        )

    def _emit_open_case(self) -> None:
        row = self._selected_row()
        if row is not None:
            self.open_case_requested.emit(
                str(row["case_id"]),
                [row["cancel_row_id"], row["accept_row_id"]],
            )
