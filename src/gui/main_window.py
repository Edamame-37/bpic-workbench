"""Integrated application shell for BPIC17 analysis panels."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from src.core.event_store import EventStore
from src.gui.panels.case_explorer_panel import CaseExplorerPanel
from src.gui.panels.dataset_panel import DatasetPanel
from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from src.gui.panels.overview_panel import OverviewPanel
from src.gui.panels.rework_panel import ReworkPanel
from src.gui.panels.sequence_panel import SequencePanel
from src.gui.worker import WorkerManager

APPLICATION_TITLE = "BPIC17 Desktop Event Log Analyzer"

NAVIGATION_AREAS: tuple[tuple[str, str], ...] = (
    ("Dataset & Status", "Pilih dan validasi event log XES."),
    ("Overview", "Ringkasan dataset aktif."),
    ("Exercise 11.7", "Analisis Exercise 11.7 A-E."),
    ("Rework 11.15 & 11.18", "Analisis repeated complete dan same resource."),
    ("Exercise 11.22", "Analisis eventually-follows."),
    ("Case Explorer", "Penelusuran trace dan evidence."),
    ("Export", "Ekspor CSV akan diintegrasikan pada workstream A5."),
    ("About", "BPIC Workbench versi 0.1.0 — integrasi A1-A4."),
)


class MainWindow(QMainWindow):
    """Coordinate one active EventStore across all implemented feature panels."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APPLICATION_TITLE)
        self.resize(1200, 800)

        self.worker_manager = WorkerManager(self)
        runner = self.worker_manager.run

        self.dataset_panel = DatasetPanel(runner=runner)
        self.overview_panel = OverviewPanel(runner=runner)
        self.exercise_11_7_panel = Exercise117Panel(runner=runner)
        self.rework_panel = ReworkPanel(runner=runner)
        self.sequence_panel = SequencePanel(runner=runner)
        self.case_explorer_panel = CaseExplorerPanel()

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.dataset_panel, NAVIGATION_AREAS[0][0])
        self.tabs.addTab(self.overview_panel, NAVIGATION_AREAS[1][0])
        self.tabs.addTab(self.exercise_11_7_panel, NAVIGATION_AREAS[2][0])
        self.tabs.addTab(self.rework_panel, NAVIGATION_AREAS[3][0])
        self.tabs.addTab(self.sequence_panel, NAVIGATION_AREAS[4][0])
        self._explorer_tab_index = self.tabs.addTab(
            self.case_explorer_panel, NAVIGATION_AREAS[5][0]
        )
        self.tabs.addTab(
            self._build_placeholder_page(NAVIGATION_AREAS[6][1]),
            NAVIGATION_AREAS[6][0],
        )
        self.tabs.addTab(
            self._build_placeholder_page(NAVIGATION_AREAS[7][1]),
            NAVIGATION_AREAS[7][0],
        )
        self.setCentralWidget(self.tabs)

        self.dataset_panel.store_changed.connect(self._set_store)
        self.overview_panel.open_case_requested.connect(self._open_case)
        self.exercise_11_7_panel.open_case_requested.connect(self._open_case)
        self.rework_panel.open_case_requested.connect(self._open_case)
        self.sequence_panel.open_case_requested.connect(self._open_case)

    def _set_store(self, store: EventStore | None) -> None:
        self.overview_panel.set_store(store)
        self.exercise_11_7_panel.set_store(store)
        self.rework_panel.set_store(store)
        self.sequence_panel.set_store(store)
        self.case_explorer_panel.set_store(store)

    def _open_case(self, case_id: str, row_ids: list[object]) -> None:
        self.case_explorer_panel.open_case(case_id, row_ids)
        self.tabs.setCurrentIndex(self._explorer_tab_index)

    @staticmethod
    def _build_placeholder_page(message: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        return page

