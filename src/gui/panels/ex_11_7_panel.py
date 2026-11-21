from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.ex_11_7 import run_11_7
from src.core.result import AnalysisResult


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
    """Format mean cycle time untuk tampilan GUI."""
    return "N/A" if value is None else f"{value:.4f}"


class Exercise117Panel(QWidget):
    """Panel GUI untuk hasil Exercise 11.7 A-E."""

    open_case = Signal(str)

    def __init__(self, runner: Runner | None = None) -> None:
        super().__init__()

        self._runner = runner
        self._store: EventStore | None = None
        self._results: list[AnalysisResult] = []
        self._generation = 0
        self._running = False

        self.status = QLabel("Belum ada dataset aktif.")

        self.run_button = QPushButton("Jalankan 11.7 A-E")
        self.reset_button = QPushButton("Reset hasil")

        self.summary = QTableWidget(len(QUESTIONS), 5)
        self.summary.setHorizontalHeaderLabels(
            ["Kode", "Pertanyaan", "Jumlah case", "Mean (hari)", "Denominator"]
        )

        self.rule = QLabel("")
        self.rule.setWordWrap(True)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari case ID...")

        self.cases = QTableWidget(0, 1)
        self.cases.setHorizontalHeaderLabels(["Case ID"])

        self.open_button = QPushButton("Buka kasus")
        self.open_button.setEnabled(False)

        top = QHBoxLayout()
        top.addWidget(self.run_button)
        top.addWidget(self.reset_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addLayout(top)
        for widget in (
            self.summary,
            self.rule,
            self.search,
            self.cases,
            self.open_button,
        ):
            layout.addWidget(widget)

        self.run_button.clicked.connect(self.run)
        self.reset_button.clicked.connect(self.reset)
        self.summary.itemSelectionChanged.connect(self._show_selected)
        self.search.textChanged.connect(self._filter_cases)
        self.cases.itemSelectionChanged.connect(self._update_open_button)
        self.open_button.clicked.connect(self._emit_open_case)

        self.reset()

    def set_store(self, store: EventStore | None) -> None:
        """Dipanggil saat dataset diimpor/diganti; hasil dataset lama dibuang."""
        self._store = store
        self.reset()

    def run(self) -> None:
        """Jalankan analisis; gunakan runner A5 jika tersedia."""
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
            # Exception ditangkap di job agar dapat dilaporkan melalui callback
            # yang sama, tanpa mengubah kontrak runner A5.
            try:
                return run_11_7(store)
            except Exception as exc:
                error_holder.append(exc)
                return []

        def on_done(results: list[AnalysisResult]) -> None:
            # Abaikan hasil worker lama jika dataset telah diganti atau panel
            # telah di-reset saat worker masih berjalan.
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
        except Exception as exc:
            if generation == self._generation:
                self._on_error(exc)

    def reset(self) -> None:
        self._generation += 1
        self._running = False
        self._results = []

        self.summary.clearContents()
        self.summary.clearSelection()
        self.cases.setRowCount(0)
        self.rule.clear()
        self.search.clear()
        self.open_button.setEnabled(False)
        self.run_button.setEnabled(self._store is not None)

        if self._store is None:
            self.status.setText("Belum ada dataset aktif.")
        else:
            self.status.setText("Siap dijalankan.")

    def _on_done(self, results: list[AnalysisResult]) -> None:
        # menampilakan hasil analisis di GUI
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self._results = results

        self.summary.clearContents()
        self.cases.setRowCount(0)
        self.rule.clear()
        self.open_button.setEnabled(False)

        for row, result in enumerate(results[: self.summary.rowCount()]):
            values = [
                result.exercise_id,
                QUESTIONS.get(result.exercise_id, ""),
                f"{result.count:,}",
                format_days(result.mean_days),
                f"{result.denominator:,}",
            ]
            for column, value in enumerate(values):
                self.summary.setItem(row, column, QTableWidgetItem(value))

        if not results:
            self.status.setText("Analisis tidak menghasilkan data.")
            return

        unavailable = [result for result in results if result.status != "ok"]
        self.status.setText(
            unavailable[0].notes if unavailable else "Selesai."
        )
        
        
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
        # menampilkan kegagalan analisis
        self._running = False
        self.run_button.setEnabled(self._store is not None)
        self._results = []
        self.summary.clearContents()
        self.cases.setRowCount(0)
        self.rule.clear()
        self.open_button.setEnabled(False)
        self.status.setText(f"Analisis gagal: {error}")

    def _show_selected(self) -> None:
        row = self.summary.currentRow()
        if not (0 <= row < len(self._results)):
            self.rule.clear()
            self.cases.setRowCount(0)
            self.open_button.setEnabled(False)
            return

        result = self._results[row]
        self.rule.setText(
            f"Aturan: {result.rule_description} | "
            f"Terpilih: {result.count:,} dari {result.denominator:,} case | "
            f"Status: {result.status}"
            + (f" | {result.notes}" if result.notes else "")
        )

        self.cases.setRowCount(len(result.case_ids))
        for index, case_id in enumerate(result.case_ids):
            self.cases.setItem(
                index, 0, QTableWidgetItem(str(case_id))
            )

        self._filter_cases(self.search.text())
        self._update_open_button()

    def _filter_cases(self, text: str) -> None:
        """Filter daftar case berdasarkan teks Case ID."""
        needle = text.strip().casefold()

        for row in range(self.cases.rowCount()):
            item = self.cases.item(row, 0)
            if item is None:
                self.cases.setRowHidden(row, False)
                continue
            self.cases.setRowHidden(
                row,
                bool(needle) and needle not in item.text().casefold(),
            )

        self._update_open_button()

    def _update_open_button(self) -> None:
        """Aktifkan tombol hanya jika ada case yang dipilih dan terlihat."""
        self.open_button.setEnabled(self._selected_case_item() is not None)

    def _emit_open_case(self) -> None:
        # mengirim sinyal open_case dengan case ID yang dipilih
        item = self._selected_case_item()
        if item is not None:
            self.open_case.emit(item.text())

    def _selected_case_item(self) -> QTableWidgetItem | None:
        """Case yang benar-benar dipilih pengguna dan masih terlihat."""
        for item in self.cases.selectedItems():
            if not self.cases.isRowHidden(item.row()):
                return item
        return None