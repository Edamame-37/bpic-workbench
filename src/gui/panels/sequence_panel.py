"""Panel urutan O_Cancelled yang kemudian diikuti O_Accepted.

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
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.ex_11_22 import run_11_22
from src.core.ordering import EVIDENCE_COLUMNS
from src.core.result import AnalysisResult
from src.gui.common import (
    MetricCard,
    PageHeader,
    PrimaryButton,
    SearchField,
    SecondaryButton,
    SectionCard,
    TimelineStep,
)
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
        self.run_button = PrimaryButton("Jalankan Analisis", "rerun")
        self.reset_button = SecondaryButton("Reset hasil", "reset")

        self.count_metric = MetricCard("Case memenuhi", "Count: N/A")
        self.denominator_metric = MetricCard("Populasi", "Denominator: N/A")
        self.percentage_metric = MetricCard("Proporsi", "Persentase: N/A")
        self.count_label = self.count_metric.value
        self.denominator_label = self.denominator_metric.value
        self.percentage_label = self.percentage_metric.value

        self.rule = QLabel("")
        self.rule.setWordWrap(True)
        self.notes = QLabel("")
        self.notes.setWordWrap(True)

        self.search = SearchField("Cari case ID pada hasil...")
        self.model = DataFrameTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.timeline = QLabel("Pilih satu baris untuk melihat pasangan cancel dan accept.")
        self.timeline.setWordWrap(True)
        self.cancel_step = TimelineStep("Event awal: O_Cancelled")
        self.accept_step = TimelineStep("Event berikutnya: O_Accepted")
        self.open_button = SecondaryButton("Buka di Case Explorer", "explorer")
        self.open_button.setEnabled(False)

        header = PageHeader(
            "Urutan Cancel-Accept",
            "Periksa apakah O_Cancelled pada sebuah case akhirnya diikuti O_Accepted.",
        )
        header.actions.addWidget(self.reset_button)
        header.actions.addWidget(self.run_button)
        kpi = QHBoxLayout()
        for card in (self.count_metric, self.denominator_metric, self.percentage_metric):
            kpi.addWidget(card)

        evidence_card = SectionCard(
            "Pasangan event pembukti",
            "Satu baris per case. Gunakan pencarian untuk mempersempit hasil.",
        )
        evidence_card.body.addWidget(self.search)
        evidence_card.body.addWidget(self.table)

        timeline_row = QHBoxLayout()
        timeline_row.addWidget(self.cancel_step)
        timeline_row.addWidget(self.accept_step)
        detail_card = SectionCard("Detail pasangan terpilih")
        detail_card.body.addWidget(self.timeline)
        detail_card.body.addLayout(timeline_row)
        detail_card.body.addWidget(self.open_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(self.status)
        layout.addLayout(kpi)
        layout.addWidget(self.rule)
        layout.addWidget(self.notes)
        layout.addWidget(evidence_card, 1)
        layout.addWidget(detail_card)

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

    def results(self) -> list[AnalysisResult]:
        """Return the current result using the shared export-panel contract."""

        return [] if self.result is None else [self.result]

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
        self.count_label.setText("Count: N/A")
        self.denominator_label.setText("Denominator: N/A")
        self.percentage_label.setText("Persentase: N/A")
        self.rule.clear()
        self.notes.clear()
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.model.set_frame(pd.DataFrame(columns=list(EVIDENCE_COLUMNS)))
        self.timeline.setText("Pilih satu baris untuk melihat pasangan cancel dan accept.")
        self.cancel_step.value.setText("Belum dipilih")
        self.accept_step.value.setText("Belum dipilih")
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
            self.timeline.setText("Pilih satu baris untuk melihat pasangan cancel dan accept.")
            self.cancel_step.value.setText("Belum dipilih")
            self.accept_step.value.setText("Belum dipilih")
            return
        self.timeline.setText(
            f"Case {row['case_id']}:  [i={row['cancel_position']}] O_Cancelled "
            f"({row['cancel_timestamp']}) to [j={row['accept_position']}] O_Accepted "
            f"({row['accept_timestamp']})"
        )
        self.cancel_step.value.setText(
            f"Position {row['cancel_position']} | {row['cancel_timestamp']}"
        )
        self.accept_step.value.setText(
            f"Position {row['accept_position']} | {row['accept_timestamp']}"
        )

    def _emit_open_case(self) -> None:
        row = self._selected_row()
        if row is not None:
            self.open_case_requested.emit(
                str(row["case_id"]),
                [row["cancel_row_id"], row["accept_row_id"]],
            )
