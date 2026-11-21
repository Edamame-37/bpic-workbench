"""GUI panel for dataset overview, activity frequencies, and case durations (Anggota 1)."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
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
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import CASE_ID_COLUMN, EventStore
from src.core.overview import OverviewSummary, get_overview
from src.gui.common import MetricCard, PageHeader, SearchField, SecondaryButton, SectionCard

Runner = Callable[
    [
        Callable[[], OverviewSummary | None],
        Callable[[OverviewSummary | None], None],
    ],
    None,
]


def format_days(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f} hari"


def format_timestamp(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return str(value)


class ActivityFrequencyModel(QAbstractTableModel):
    """Table model for activity counts and percentages."""

    HEADERS = ("Aktivitas", "Jumlah Event", "Persentase (%)")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[str, int, float]] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid():
            return None
        activity, count, pct = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return activity
            if index.column() == 1:
                return f"{count:,}"
            return f"{pct:.2f}%"
        if role == Qt.ItemDataRole.UserRole:
            if index.column() == 0:
                return activity
            if index.column() == 1:
                return count
            return pct
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_activities(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        if df.empty:
            self._rows = []
        else:
            self._rows = [
                (str(row.activity), int(row.count), float(row.percentage))
                for row in df.itertuples(index=False)
            ]
        self.endResetModel()


class CaseDurationModel(QAbstractTableModel):
    """Lightweight model for case list + duration_days without QTableWidgetItem bloat."""

    HEADERS = ("Case ID", "Mulai", "Selesai", "Durasi (hari)")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[str, str, str, float]] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid():
            return None
        case_id, ts_min, ts_max, duration_days = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return case_id
            if index.column() == 1:
                return ts_min
            if index.column() == 2:
                return ts_max
            return f"{duration_days:.4f}"
        if role == Qt.ItemDataRole.UserRole:
            if index.column() == 3:
                return duration_days
            return (case_id, ts_min, ts_max, duration_days)[index.column()]
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def set_durations(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        if df.empty:
            self._rows = []
        else:
            self._rows = [
                (
                    str(row[0]),
                    str(row[1]),
                    str(row[2]),
                    float(row[3]),
                )
                for row in df[
                    [CASE_ID_COLUMN, "timestamp_min", "timestamp_max", "duration_days"]
                ].itertuples(index=False, name=None)
            ]
        self.endResetModel()

    def case_id_at(self, row: int) -> str | None:
        if 0 <= row < len(self._rows):
            return self._rows[row][0]
        return None


class OverviewPanel(QWidget):
    """Display dataset KPIs, activity frequencies, date range, and searchable cases."""

    open_case_requested = Signal(str, list)

    def __init__(
        self,
        parent: QWidget | None = None,
        runner: Runner | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._store: EventStore | None = None
        self._overview: OverviewSummary | None = None
        self._generation = 0
        self._running = False

        self.status = QLabel("Belum ada dataset aktif.")
        self.status.setWordWrap(True)

        self.metadata_label = QLabel("")
        self.metadata_label.setWordWrap(True)

        self.case_metric = MetricCard("Total case", "N/A")
        self.event_metric = MetricCard("Total event", "N/A")
        self.activity_metric = MetricCard("Aktivitas", "N/A")
        self.cycle_metric = MetricCard("Mean cycle time", "N/A", "hari")
        self.range_metric = MetricCard("Rentang waktu", "N/A")
        self.total_cases_label = self.case_metric.value
        self.total_events_label = self.event_metric.value
        self.total_activities_label = self.activity_metric.value
        self.date_range_label = self.range_metric.value
        self.mean_cycle_time_label = self.cycle_metric.value

        self._activity_model = ActivityFrequencyModel()
        self._activity_proxy = QSortFilterProxyModel(self)
        self._activity_proxy.setSourceModel(self._activity_model)
        self._activity_proxy.setSortRole(Qt.ItemDataRole.UserRole)

        self.activities = QTableView()
        self.activities.setModel(self._activity_proxy)
        self.activities.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.activities.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.activities.setSortingEnabled(True)

        self.search = SearchField("Cari case ID...")

        self._case_model = CaseDurationModel()
        self._case_filter = QSortFilterProxyModel(self)
        self._case_filter.setSourceModel(self._case_model)
        self._case_filter.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )
        self._case_filter.setFilterKeyColumn(0)
        self._case_filter.setSortRole(Qt.ItemDataRole.UserRole)

        self.cases = QTableView()
        self.cases.setModel(self._case_filter)
        self.cases.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.cases.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.cases.setSortingEnabled(True)

        self.open_button = SecondaryButton("Buka di Case Explorer", "explorer")
        self.open_button.setEnabled(False)

        case_header = QHBoxLayout()
        case_header.addWidget(self.search, 1)
        case_header.addWidget(self.open_button)

        metrics = QHBoxLayout()
        for card in (
            self.case_metric,
            self.event_metric,
            self.activity_metric,
            self.cycle_metric,
        ):
            metrics.addWidget(card)

        activity_card = SectionCard(
            "Frekuensi aktivitas",
            "Urutkan kolom untuk membandingkan volume dan proporsi aktivitas.",
        )
        activity_card.body.addWidget(self.activities)

        case_card = SectionCard(
            "Case dan durasi",
            "Cari case lalu buka jejak lengkapnya di Case Explorer.",
        )
        case_card.body.addLayout(case_header)
        case_card.body.addWidget(self.cases)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(PageHeader("Overview", "Ringkasan operasional dataset aktif."))
        layout.addWidget(self.status)
        layout.addWidget(self.metadata_label)
        layout.addLayout(metrics)
        layout.addWidget(self.range_metric)
        layout.addWidget(activity_card, 1)
        layout.addWidget(case_card, 2)

        self.search.textChanged.connect(self._filter_cases)
        self.cases.selectionModel().selectionChanged.connect(
            self._update_open_button
        )
        self.open_button.clicked.connect(self._emit_open_case)

        self.reset()

    def overview(self) -> OverviewSummary | None:
        return self._overview

    def set_store(self, store: EventStore | None) -> None:
        """Replace the active dataset, clear stale data, and compute overview."""
        self._store = store
        self.reset()
        if store is not None:
            self.refresh()

    def refresh(self) -> None:
        """Compute overview from the active EventStore without re-parsing XES."""
        if self._running or self._store is None:
            return

        store = self._store
        generation = self._generation
        error_holder: list[Exception] = []

        self._running = True
        self.status.setText("Menghitung ringkasan dataset...")

        def job() -> OverviewSummary | None:
            try:
                return get_overview(store)
            except Exception as exc:
                error_holder.append(exc)
                return None

        def on_done(summary: OverviewSummary | None) -> None:
            if generation != self._generation:
                return
            if error_holder or summary is None:
                self._on_error(
                    error_holder[0]
                    if error_holder
                    else RuntimeError("Overview tidak menghasilkan data")
                )
            else:
                self._on_done(summary)

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
        self._overview = None

        self.total_cases_label.setText("N/A")
        self.total_events_label.setText("N/A")
        self.total_activities_label.setText("N/A")
        self.date_range_label.setText("N/A")
        self.mean_cycle_time_label.setText("N/A")
        self.metadata_label.clear()
        self._activity_model.set_activities(pd.DataFrame())
        self._case_model.set_durations(pd.DataFrame())
        self.search.clear()
        self.open_button.setEnabled(False)
        self.status.setText(
            "Belum ada dataset aktif."
            if self._store is None
            else "Siap menampilkan ringkasan."
        )

    def _on_done(self, summary: OverviewSummary) -> None:
        self._running = False
        self._overview = summary

        if summary.status == "empty":
            self.total_cases_label.setText("0")
            self.total_events_label.setText("0")
            self.total_activities_label.setText("0")
            self.date_range_label.setText("N/A")
            self.mean_cycle_time_label.setText("N/A")
            self._activity_model.set_activities(pd.DataFrame())
            self._case_model.set_durations(pd.DataFrame())
            self.status.setText(
                summary.warnings[0]
                if summary.warnings
                else "Log kosong: tidak ada case pada dataset aktif."
            )
        else:
            self.total_cases_label.setText(f"{summary.total_cases:,}")
            self.total_events_label.setText(f"{summary.total_events:,}")
            self.total_activities_label.setText(f"{summary.total_activities:,}")
            self.date_range_label.setText(
                f"{format_timestamp(summary.timestamp_min)} s.d. {format_timestamp(summary.timestamp_max)}"
            )
            self.mean_cycle_time_label.setText(
                format_days(summary.mean_cycle_time_days)
            )
            self._activity_model.set_activities(summary.activity_frequencies)
            self._case_model.set_durations(summary.case_durations)
            self._filter_cases(self.search.text())
            self.status.setText("Overview siap.")

        meta = summary.metadata
        file_name = meta.get("file_name") or meta.get("dataset_name", "-")
        tz = meta.get("timezone_status", "-")
        has_lc = meta.get("has_lifecycle")
        has_res = meta.get("has_resource")
        meta_parts = [f"Dataset: {file_name}", f"Timezone: {tz}"]
        if has_lc is not None:
            meta_parts.append(f"lifecycle: {'ada' if has_lc else 'tidak ada'}")
        if has_res is not None:
            meta_parts.append(f"resource: {'ada' if has_res else 'tidak ada'}")
        if summary.warnings:
            meta_parts.append("Peringatan: " + " | ".join(summary.warnings))
        self.metadata_label.setText(" | ".join(meta_parts))

    def _on_error(self, error: Exception) -> None:
        self._running = False
        self._overview = None
        self.status.setText(f"Gagal memuat overview: {error}")

    def _filter_cases(self, text: str) -> None:
        self._case_filter.setFilterFixedString(text.strip())
        self._update_open_button()

    def _update_open_button(self, *_args: object) -> None:
        self.open_button.setEnabled(self._selected_case_id() is not None)

    def _selected_case_id(self) -> str | None:
        selection_model = self.cases.selectionModel()
        if selection_model is None:
            return None
        selected_rows = selection_model.selectedRows(0)
        if not selected_rows:
            return None
        source_index = self._case_filter.mapToSource(selected_rows[0])
        return self._case_model.case_id_at(source_index.row())

    def _emit_open_case(self) -> None:
        case_id = self._selected_case_id()
        if case_id is None:
            return
        self.open_case_requested.emit(case_id, [])
