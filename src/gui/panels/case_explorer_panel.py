"""A4 - Case Explorer: cari case, lihat seluruh trace, sorot event pembukti.

Kontrak untuk panel lain (A2/A3/A4) dan main window (A5):
    explorer.set_store(store)                      # dataset baru / None
    explorer.open_case(case_id, highlight_row_ids)  # highlight_row_ids opsional

Contoh sambungan di main window:
    rework_panel.open_case_requested.connect(explorer.open_case)
    sequence_panel.open_case_requested.connect(explorer.open_case)
    ex_11_7_panel.open_case_requested.connect(explorer.open_case)
"""

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QListWidget,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import (
    ACTIVITY_COLUMN,
    CASE_ID_COLUMN,
    ROW_ID_COLUMN,
    TIMESTAMP_COLUMN,
    TRACE_POSITION_COLUMN,
    EventStore,
)
from src.core.ordering import (
    HIGHLIGHT_COLUMN,
    build_case_index,
    get_case_trace,
    search_case_ids,
)

HIGHLIGHT_COLOR = QColor(255, 230, 140)
LEADING_COLUMNS = (
    TRACE_POSITION_COLUMN,
    ROW_ID_COLUMN,
    ACTIVITY_COLUMN,
    TIMESTAMP_COLUMN,
    "lifecycle:transition",
    "org:resource",
)
SEARCH_LIMIT = 500


class DataFrameTableModel(QAbstractTableModel):
    """Model tabel read-only untuk DataFrame (Qt hanya merender baris yang terlihat).

    Baris dengan kolom ``_highlight`` bernilai True diberi latar kuning.
    Bisa diganti widget tabel bersama milik A5 bila sudah tersedia.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._df = pd.DataFrame()
        self._columns: list[str] = []

    def set_frame(self, df: pd.DataFrame, columns: list[str] | None = None) -> None:
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self._columns = columns if columns is not None else [
            c for c in self._df.columns if c != HIGHLIGHT_COLUMN
        ]
        self.endResetModel()

    def frame(self) -> pd.DataFrame:
        return self._df

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[index.row(), self._df.columns.get_loc(self._columns[index.column()])]
            return "" if pd.isna(value) else str(value)
        if role == Qt.ItemDataRole.BackgroundRole and HIGHLIGHT_COLUMN in self._df.columns:
            if bool(self._df.iat[index.row(), self._df.columns.get_loc(HIGHLIGHT_COLUMN)]):
                return QBrush(HIGHLIGHT_COLOR)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._columns[section]
        return str(section + 1)


def trace_columns(df: pd.DataFrame) -> list[str]:
    lead = [c for c in LEADING_COLUMNS if c in df.columns]
    rest = [c for c in df.columns if c not in lead and c not in (HIGHLIGHT_COLUMN, CASE_ID_COLUMN)]
    return lead + rest


def format_duration(store: EventStore, case_id: str) -> str:
    durations = store.case_durations
    row = durations[durations[CASE_ID_COLUMN].astype(str) == str(case_id)]
    if row.empty:
        return "durasi: N/A"
    return f"durasi: {float(row['duration_days'].iloc[0]):.4f} hari"


class CaseExplorerPanel(QWidget):
    case_changed = Signal(object)

    """Penelusuran case lintas latihan."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store: EventStore | None = None
        self._case_index: dict = {}
        self._case_ids: list[str] = []
        self.current_case: str | None = None

        self.status = QLabel("Belum ada dataset aktif.")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari case ID, mis. Application_652823628")
        self.case_list = QListWidget()
        self.info = QLabel("Belum ada case dipilih.")
        self.info.setWordWrap(True)
        self.evidence_info = QLabel("")
        self.evidence_info.setWordWrap(True)
        self.model = DataFrameTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.case_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.info)
        right_layout.addWidget(self.evidence_info)
        right_layout.addWidget(self.table)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(splitter)

        self.search.textChanged.connect(self._refresh_case_list)
        self.search.returnPressed.connect(self._open_typed_case)
        self.case_list.currentTextChanged.connect(self._on_list_selection)

    # ---- kontrak publik -------------------------------------------------
    def set_store(self, store: EventStore | None) -> None:
        """Ganti dataset: index dibangun ulang, case & highlight lama dihapus."""
        self._store = store
        self.current_case = None
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.model.set_frame(pd.DataFrame())
        self.info.setText("Belum ada case dipilih.")
        self.evidence_info.clear()
        if store is None:
            self._case_index, self._case_ids = {}, []
            self.status.setText("Belum ada dataset aktif.")
        else:
            self._case_index = build_case_index(store.events)
            self._case_ids = list(self._case_index.keys())
            self.status.setText(f"{len(self._case_ids):,} case tersedia.")
        self._refresh_case_list()
        self.case_changed.emit(None)

    def open_case(
        self,
        case_id: str,
        highlight_row_ids: list[object] | None = None,
    ) -> None:
        """Tampilkan seluruh event case; sorot ``_row_id`` pembukti bila ada."""
        if self._store is None:
            self.status.setText("Impor file XES terlebih dahulu.")
            return
        case_id = str(case_id)
        trace = get_case_trace(
            self._store.events, case_id, highlight_row_ids, case_index=self._case_index
        )
        self.model.set_frame(trace, trace_columns(trace))
        if trace.empty:
            self.current_case = None
            self.info.setText(f"Case '{case_id}' tidak ditemukan pada dataset aktif.")
            self.evidence_info.clear()
            self.case_changed.emit(None)
            return

        self.current_case = case_id
        self.info.setText(
            f"Case {case_id} — {len(trace):,} event — {format_duration(self._store, case_id)}"
        )
        self.evidence_info.setText(self._describe_highlights(trace, highlight_row_ids))
        first = trace.index[trace[HIGHLIGHT_COLUMN]]
        if len(first):
            self.table.scrollTo(self.model.index(int(first[0]), 0))
        self.case_changed.emit(case_id)

    def clear_selection(self) -> None:
        """Clear the displayed trace without rebuilding the active case index."""

        self.current_case = None
        self.model.set_frame(pd.DataFrame())
        self.info.setText("Belum ada case dipilih.")
        self.evidence_info.clear()
        self.case_list.clearSelection()
        self.case_changed.emit(None)

    # ---- internal -------------------------------------------------------
    @staticmethod
    def _describe_highlights(
        trace: pd.DataFrame,
        wanted: list[object] | None,
    ) -> str:
        if not wanted:
            return ""
        marked = trace[trace[HIGHLIGHT_COLUMN]]
        steps = " → ".join(
            f"[i={int(r[TRACE_POSITION_COLUMN])}] {r[ACTIVITY_COLUMN]} ({r[TIMESTAMP_COLUMN]})"
            for _, r in marked.iterrows()
        )
        text = f"Event pembukti disorot ({len(marked)}): {steps}"
        lost = len(set(wanted)) - len(marked)
        if lost > 0:
            text += f"  | PERINGATAN: {lost} row ID bukti tidak ada di case ini."
        return text

    def _refresh_case_list(self) -> None:
        self.case_list.blockSignals(True)
        self.case_list.clear()
        matches = search_case_ids(self._case_ids, self.search.text(), SEARCH_LIMIT)
        self.case_list.addItems(matches)
        self.case_list.blockSignals(False)

    def _on_list_selection(self, case_id: str) -> None:
        if case_id:
            self.open_case(case_id)

    def _open_typed_case(self) -> None:
        text = self.search.text().strip()
        if text:
            self.open_case(text)
