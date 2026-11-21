"""A3 - Panel Rework: Exercise 11.15 (Repeated Complete) dan 11.18 (Same Resource Complete).

Hanya menampilkan hasil ringkas + evidence per case (bukan data mentah log).
Integrasi: ``set_store(store)`` setelah impor; sinyal ``open_case_requested``
untuk Case Explorer A4 (case_id + _row_id yang di-highlight); ``results()``
untuk export A5. Re-run tidak memerlukan impor ulang.
"""
from __future__ import annotations

from collections.abc import Callable

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core import rework as rw
from src.core.ex_11_15_18 import DEFAULT_COMPLETE_VALUE, run_11_15, run_11_18
from src.core.result import AnalysisResult

MAX_TABLE_ROWS = 5000

Runner = Callable[
    [
        Callable[[], list[AnalysisResult]],
        Callable[[list[AnalysisResult]], None],
    ],
    None,
]


# ----------------------------------------------------------------------------
# Presenter murni (tanpa Qt) - diuji tanpa GUI
# ----------------------------------------------------------------------------
def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def status_headline(result: AnalysisResult) -> str:
    if result.status == "unavailable":
        return f"ANALISIS TIDAK TERSEDIA: {result.notes}"
    if result.status == "error":
        return f"ERROR: {result.notes}"
    return (
        f"{result.exercise_id}: {fmt_int(result.count)} case dari {fmt_int(result.denominator)} case "
        "pada log aktif (satuan: CASE, bukan event)"
    )


def case_table(result: AnalysisResult) -> pd.DataFrame:
    """Tabel per case (11.15) atau per (case, resource) (11.18) dari evidence."""
    ev = result.evidence
    if result.status != "ok" or ev is None or ev.empty:
        cols = ["case_id", "complete_count"] if result.exercise_id == "11.15" else [
            "case_id", rw.RESOURCE_COL, "resource_complete_count", "complete_count"]
        return pd.DataFrame(columns=cols)
    if result.exercise_id == "11.15":
        return ev[["case_id", "complete_count"]].drop_duplicates().reset_index(drop=True)
    cols = ["case_id", rw.RESOURCE_COL, "resource_complete_count", "complete_count"]
    return ev[cols].drop_duplicates().reset_index(drop=True)


def evidence_for_case(result: AnalysisResult, case_id: str, resource: str | None = None) -> pd.DataFrame:
    ev = result.evidence
    if ev is None or ev.empty:
        return pd.DataFrame()
    sel = ev[ev["case_id"] == str(case_id)]
    if resource is not None and rw.RESOURCE_COL in sel.columns:
        sel = sel[sel[rw.RESOURCE_COL] == resource]
    return sel.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Widget
# ----------------------------------------------------------------------------
def _fill(table: QTableWidget, df: pd.DataFrame) -> int:
    table.setSortingEnabled(False)
    table.clear()
    shown = df.iloc[:MAX_TABLE_ROWS]
    table.setColumnCount(len(shown.columns))
    table.setRowCount(len(shown))
    table.setHorizontalHeaderLabels([str(c) for c in shown.columns])
    for r, row in enumerate(shown.itertuples(index=False)):
        for c, val in enumerate(row):
            text = "" if pd.isna(val) else str(val)
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()
    return max(0, len(df) - len(shown))


def _new_table() -> QTableWidget:
    t = QTableWidget()
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return t


def _limit_message(omitted_rows: int) -> str:
    if omitted_rows <= 0:
        return ""
    return (
        f"Tampilan dibatasi {MAX_TABLE_ROWS:,} baris; "
        f"{omitted_rows:,} baris lainnya tidak ditampilkan."
    )


class _ExercisePage(QWidget):
    open_case_requested = Signal(str, list)

    def __init__(self, exercise_id: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.exercise_id = exercise_id
        self.result: AnalysisResult | None = None
        self.headline = QLabel("Belum dijalankan.")
        self.headline.setWordWrap(True)
        self.rule = QLabel()
        self.rule.setWordWrap(True)
        self.notes = QLabel()
        self.notes.setWordWrap(True)
        self.cases = _new_table()
        self.case_limit_note = QLabel()
        self.evidence = _new_table()
        self.evidence_limit_note = QLabel()
        self.open_btn = QPushButton("Buka di Case Explorer")
        self.open_btn.setEnabled(False)
        lay = QVBoxLayout(self)
        for w in (self.headline, self.rule, self.notes):
            lay.addWidget(w)
        lay.addWidget(QLabel("Case terpilih:"))
        lay.addWidget(self.cases, 2)
        lay.addWidget(self.case_limit_note)
        lay.addWidget(QLabel("Event pembukti (lifecycle & resource asli dari data):"))
        lay.addWidget(self.evidence, 2)
        lay.addWidget(self.evidence_limit_note)
        lay.addWidget(self.open_btn)
        self.cases.itemSelectionChanged.connect(self._on_case_selected)
        self.open_btn.clicked.connect(self._on_open)

    def clear_result(self) -> None:
        self.result = None
        self.headline.setText("Belum dijalankan.")
        self.headline.setStyleSheet("")
        self.rule.clear()
        self.notes.clear()
        self.case_limit_note.clear()
        self.evidence_limit_note.clear()
        _fill(self.cases, pd.DataFrame())
        _fill(self.evidence, pd.DataFrame())
        self.open_btn.setEnabled(False)

    def show_result(self, result: AnalysisResult) -> None:
        self.result = result
        self.headline.setText(status_headline(result))
        bad = result.status != "ok"
        self.headline.setStyleSheet("font-weight:bold;" + ("color:#b00020;" if bad else ""))
        self.rule.setText("Aturan: " + result.rule_description)
        self.notes.setText("" if bad else "Catatan: " + result.notes)
        omitted_cases = _fill(self.cases, case_table(result))
        self.case_limit_note.setText(_limit_message(omitted_cases))
        _fill(self.evidence, pd.DataFrame())
        self.evidence_limit_note.clear()
        self.open_btn.setEnabled(False)

    def _selected(self) -> tuple[str, str | None] | None:
        rows = self.cases.selectionModel().selectedRows()
        if not rows or self.result is None:
            return None
        r = rows[0].row()
        case_id = self.cases.item(r, 0).text()
        resource = None
        if self.exercise_id == "11.18":
            resource = self.cases.item(r, 1).text()
        return case_id, resource

    def _on_case_selected(self) -> None:
        sel = self._selected()
        if sel is None:
            return
        omitted_evidence = _fill(self.evidence, evidence_for_case(self.result, *sel))
        self.evidence_limit_note.setText(_limit_message(omitted_evidence))
        self.open_btn.setEnabled(True)

    def _on_open(self) -> None:
        sel = self._selected()
        if sel is None:
            return
        ev = evidence_for_case(self.result, sel[0])  # semua event pembukti case ini
        row_ids = ev[rw.ROW_ID_COL].dropna().tolist()
        self.open_case_requested.emit(sel[0], row_ids)


class ReworkPanel(QWidget):
    """Panel gabungan 11.15 + 11.18."""

    open_case_requested = Signal(str, list)  # (case_id, daftar _row_id untuk highlight)
    results_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        runner: Runner | None = None,
    ):
        super().__init__(parent)
        self._runner = runner
        self._store = None
        self._results: list[AnalysisResult] = []
        self._generation = 0
        self._running = False

        self.activity = QComboBox()
        self.activity.setEditable(True)
        self.activity.setMinimumWidth(320)
        self.lifecycle = QLineEdit(DEFAULT_COMPLETE_VALUE)
        self.lifecycle.setMaximumWidth(140)
        self.run_btn = QPushButton("Jalankan / jalankan ulang")
        self.run_btn.setEnabled(False)
        self.info = QLabel("Impor event log terlebih dahulu.")
        self.info.setWordWrap(True)

        top = QHBoxLayout()
        top.addWidget(QLabel("Aktivitas target (exact):"))
        top.addWidget(self.activity, 1)
        top.addWidget(QLabel("Nilai lifecycle complete:"))
        top.addWidget(self.lifecycle)
        top.addWidget(self.run_btn)

        self.page15 = _ExercisePage("11.15")
        self.page18 = _ExercisePage("11.18")
        tabs = QTabWidget()
        tabs.addTab(self.page15, "11.15 Repeated Complete")
        tabs.addTab(self.page18, "11.18 Same Resource Complete")

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.info)
        lay.addWidget(tabs, 1)

        self.run_btn.clicked.connect(self.run_analysis)
        for p in (self.page15, self.page18):
            p.open_case_requested.connect(self.open_case_requested)

    # -- API untuk shell ---------------------------------------------------
    def set_store(self, store) -> None:
        """Dipanggil setelah impor/impor ulang. Mengisi kandidat target & menjalankan bila tidak ambigu."""
        self._generation += 1
        self._running = False
        self._store = store
        self._results = []
        self.page15.clear_result()
        self.page18.clear_result()
        self.activity.clear()
        self.run_btn.setEnabled(store is not None)
        self.results_changed.emit()

        if store is None:
            self.info.setText("Impor event log terlebih dahulu.")
            return

        events = store.events
        cands = rw.list_fraud_activities(events)
        self.activity.addItems(list(cands))
        suggestion = rw.suggest_fraud_target(events)
        if suggestion:
            self.activity.setCurrentText(suggestion)
            self.info.setText(f"Target terdeteksi tepat satu: '{suggestion}'. Kandidat: {cands}")
            self.run_analysis()
        else:
            self.activity.setCurrentText("")
            msg = (
                f"Ada {len(cands)} kandidat target {cands}; pilih satu secara eksplisit lalu jalankan."
                if cands
                else "Tidak ada aktivitas yang memuat 'fraud' di log ini; ketik nama exact bila ada."
            )
            self.info.setText(msg)

    def run_analysis(self) -> None:
        if self._running:
            return
        if self._store is None:
            self.info.setText("Belum ada event log aktif.")
            return

        name = self.activity.currentText()
        cv = self.lifecycle.text()
        store = self._store
        generation = self._generation
        error_holder: list[Exception] = []

        self._running = True
        self.run_btn.setEnabled(False)
        self.info.setText("Menghitung analisis 11.15 dan 11.18...")

        def job() -> list[AnalysisResult]:
            try:
                return [
                    run_11_15(store, name, cv),
                    run_11_18(store, name, cv),
                ]
            except Exception as error:
                error_holder.append(error)
                return []

        def on_done(results: list[AnalysisResult]) -> None:
            if generation != self._generation:
                return
            if error_holder:
                self._on_error(error_holder[0])
            else:
                self._on_done(results)

        if self._runner is None:
            on_done(job())
            return

        try:
            self._runner(job, on_done)
        except Exception as error:
            if generation == self._generation:
                self._on_error(error)

    def _on_done(self, results: list[AnalysisResult]) -> None:
        self._running = False
        self.run_btn.setEnabled(self._store is not None)

        if len(results) != 2:
            self._on_error(RuntimeError("Analisis rework tidak menghasilkan dua hasil"))
            return

        self.page15.show_result(results[0])
        self.page18.show_result(results[1])
        self._results = results
        self.info.setText("Analisis 11.15 dan 11.18 selesai.")
        self.results_changed.emit()

    def _on_error(self, error: Exception) -> None:
        self._running = False
        self.run_btn.setEnabled(self._store is not None)
        self._results = []
        self.page15.clear_result()
        self.page18.clear_result()
        self.info.setText(f"Analisis gagal: {error}")
        self.results_changed.emit()

    def results(self) -> list[AnalysisResult]:
        """Untuk export A5 (summary, cases, evidence)."""
        return list(self._results)
