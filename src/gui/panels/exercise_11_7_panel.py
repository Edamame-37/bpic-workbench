"""GUI panel for case outcome and cycle-time analysis."""

from collections.abc import Callable, Iterable

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import CASE_ID_COLUMN, ROW_ID_COLUMN, EventStore
from src.core.ex_11_7 import run_11_7
from src.core.result import AnalysisResult
from src.gui.common import PageHeader, PrimaryButton, SearchField, SecondaryButton, SectionCard


QUESTIONS = {
    "11.7 A": "Jumlah seluruh case",
    "11.7 B": "Mean cycle time semua case",
    "11.7 C": "Successful cases",
    "11.7 D": "Unsuccessful cases",
    "11.7 E": "Canceled cases",
}

Runner = Callable[
    [
        Callable[[], list[AnalysisResult]],
        Callable[[list[AnalysisResult]], None],
    ],
    None,
]


def format_days(value: float | None) -> str:
    """Format mean cycle time for display without changing stored precision."""

    return "N/A" if value is None else f"{value:.4f}"


class CaseListModel(QAbstractTableModel):
    """Lightweight case-ID model suitable for large result sets."""

    def __init__(self) -> None:
        super().__init__()
        self._case_ids: list[str] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._case_ids)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else 1

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._case_ids[index.row()]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and section == 0
        ):
            return "Case ID"
        return None

    def set_case_ids(self, case_ids: Iterable[object]) -> None:
        self.beginResetModel()
        self._case_ids = [str(case_id) for case_id in case_ids]
        self.endResetModel()

    def case_id_at(self, row: int) -> str | None:
        if 0 <= row < len(self._case_ids):
            return self._case_ids[row]
        return None


class Exercise117Panel(QWidget):
    """Present case outcome and cycle-time results from the active EventStore."""

    open_case_requested = Signal(str, list)
    results_changed = Signal()

    def __init__(self, runner: Runner | None = None) -> None:
        super().__init__()

        self._runner = runner
        self._store: EventStore | None = None
        self._results: list[AnalysisResult] = []
        self._generation = 0
        self._running = False

        self.status = QLabel("Belum ada dataset aktif.")
        self.run_button = PrimaryButton("Jalankan Analisis", "rerun")
        self.reset_button = SecondaryButton("Reset hasil", "reset")

        self.summary = QTableWidget(len(QUESTIONS), 5)
        self.summary.setHorizontalHeaderLabels(
            ["Kode Analisis", "Metrik", "Jumlah case", "Mean (hari)", "Denominator"]
        )

        self.rule = QLabel("")
        self.rule.setWordWrap(True)

        self.search = SearchField("Cari case ID...")

        self._case_model = CaseListModel()
        self._case_filter = QSortFilterProxyModel(self)
        self._case_filter.setSourceModel(self._case_model)
        self._case_filter.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )
        self._case_filter.setFilterKeyColumn(0)

        self.cases = QTableView()
        self.cases.setModel(self._case_filter)
        self.cases.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.cases.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.cases.setSortingEnabled(True)

        self.open_button = SecondaryButton("Buka kasus", "explorer")
        self.open_button.setEnabled(False)

        header = PageHeader(
            "Outcome Kasus",
            "Hitung populasi case, cycle time, dan outcome proses secara konsisten.",
        )
        header.actions.addWidget(self.reset_button)
        header.actions.addWidget(self.run_button)

        summary_card = SectionCard(
            "Ringkasan hasil",
            "Pilih satu baris untuk melihat aturan dan daftar case pembentuk hasil.",
        )
        summary_card.body.addWidget(self.summary)

        case_controls = QHBoxLayout()
        case_controls.addWidget(self.search, 1)
        case_controls.addWidget(self.open_button)
        evidence_card = SectionCard("Case terpilih")
        evidence_card.body.addWidget(self.rule)
        evidence_card.body.addLayout(case_controls)
        evidence_card.body.addWidget(self.cases)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(self.status)
        layout.addWidget(summary_card, 1)
        layout.addWidget(evidence_card, 2)

        self.run_button.clicked.connect(self.run)
        self.reset_button.clicked.connect(self.reset)
        self.summary.itemSelectionChanged.connect(self._show_selected)
        self.search.textChanged.connect(self._filter_cases)
        self.cases.selectionModel().selectionChanged.connect(
            self._update_open_button
        )
        self.open_button.clicked.connect(self._emit_open_case)

        self.reset()

    def set_store(self, store: EventStore | None) -> None:
        """Replace the active dataset and discard results from the old dataset."""

        self._store = store
        self.reset()

    def results(self) -> list[AnalysisResult]:
        """Return the current results for integration and future CSV export."""

        return list(self._results)

    def run(self) -> None:
        """Run the analysis through the shared runner when one is available."""

        if self._running:
            return
        if self._store is None:
            self.status.setText("Impor file XES terlebih dahulu.")
            return

        store = self._store
        generation = self._generation
        error_holder: list[Exception] = []

        self._running = True
        self.run_button.setEnabled(False)
        self.status.setText("Menghitung...")

        def job() -> list[AnalysisResult]:
            try:
                return run_11_7(store)
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

    def reset(self) -> None:
        self._generation += 1
        self._running = False
        self._results = []

        self.summary.clearContents()
        self.summary.clearSelection()
        self._case_model.set_case_ids([])
        self.rule.clear()
        self.search.clear()
        self.open_button.setEnabled(False)
        self.run_button.setEnabled(self._store is not None)
        self.status.setText(
            "Belum ada dataset aktif."
            if self._store is None
            else "Siap dijalankan."
        )
        self.results_changed.emit()

    def _on_done(self, results: list[AnalysisResult]) -> None:
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self._results = results

        self.summary.clearContents()
        self._case_model.set_case_ids([])
        self.rule.clear()
        self.open_button.setEnabled(False)

        for row, result in enumerate(results[: self.summary.rowCount()]):
            is_available = result.status == "ok"
            values = [
                result.exercise_id,
                QUESTIONS.get(result.exercise_id, ""),
                f"{result.count:,}" if is_available else "N/A",
                format_days(result.mean_days),
                f"{result.denominator:,}" if is_available else "N/A",
            ]
            for column, value in enumerate(values):
                self.summary.setItem(row, column, QTableWidgetItem(value))

        if not results:
            self.status.setText("Analisis tidak menghasilkan data.")
            return

        unavailable = [result for result in results if result.status != "ok"]
        self.status.setText(unavailable[0].notes if unavailable else "Selesai.")
        self.results_changed.emit()

        selected_row = next(
            (
                index
                for index, result in enumerate(results)
                if result.exercise_id == "11.7 C"
            ),
            0,
        )
        if selected_row < min(len(results), self.summary.rowCount()):
            self.summary.selectRow(selected_row)

    def _on_error(self, error: Exception) -> None:
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self._results = []
        self.summary.clearContents()
        self._case_model.set_case_ids([])
        self.rule.clear()
        self.open_button.setEnabled(False)
        self.status.setText(f"Analisis gagal: {error}")
        self.results_changed.emit()

    def _show_selected(self) -> None:
        row = self.summary.currentRow()
        if not (0 <= row < len(self._results)):
            self.rule.clear()
            self._case_model.set_case_ids([])
            self.open_button.setEnabled(False)
            return

        result = self._results[row]
        selected_count = f"{result.count:,}" if result.status == "ok" else "N/A"
        denominator = (
            f"{result.denominator:,}" if result.status == "ok" else "N/A"
        )
        self.rule.setText(
            f"Aturan: {result.rule_description} | "
            f"Terpilih: {selected_count} dari {denominator} case | "
            f"Status: {result.status}"
            + (f" | {result.notes}" if result.notes else "")
        )

        self._case_model.set_case_ids(result.case_ids)
        self._filter_cases(self.search.text())

    def _filter_cases(self, text: str) -> None:
        self._case_filter.setFilterFixedString(text.strip())
        self._update_open_button()

    def _update_open_button(self, *_args: object) -> None:
        self.open_button.setEnabled(self._selected_case_id() is not None)

    def _emit_open_case(self) -> None:
        case_id = self._selected_case_id()
        if case_id is None:
            return
        self.open_case_requested.emit(case_id, self._evidence_row_ids(case_id))

    def _selected_case_id(self) -> str | None:
        selection_model = self.cases.selectionModel()
        if selection_model is None:
            return None
        selected_rows = selection_model.selectedRows(0)
        if not selected_rows:
            return None
        source_index = self._case_filter.mapToSource(selected_rows[0])
        return self._case_model.case_id_at(source_index.row())

    def _evidence_row_ids(self, case_id: str) -> list[object]:
        row = self.summary.currentRow()
        if not (0 <= row < len(self._results)):
            return []

        evidence = self._results[row].evidence
        if (
            evidence is None
            or evidence.empty
            or CASE_ID_COLUMN not in evidence.columns
            or ROW_ID_COLUMN not in evidence.columns
        ):
            return []

        matching_rows = evidence[
            evidence[CASE_ID_COLUMN].astype("string") == case_id
        ]
        return matching_rows[ROW_ID_COLUMN].dropna().tolist()
