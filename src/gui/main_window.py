"""Integrated application shell for BPIC17 analysis panels."""

from PySide6.QtWidgets import QMainWindow, QTabWidget

from src.core.event_store import EventStore
from src.core.result import AnalysisResult
from src.gui.panels.about_panel import AboutPanel
from src.gui.panels.case_explorer_panel import CaseExplorerPanel
from src.gui.panels.dataset_panel import DatasetPanel
from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from src.gui.panels.export_panel import ExportPanel
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
    ("Export", "Ekspor summary, selected cases, dan evidence."),
    ("About", "Versi aplikasi, environment, dan metadata dataset."),
)


class MainWindow(QMainWindow):
    """Coordinate one active EventStore across all application panels."""

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
        self.export_panel = ExportPanel(runner=runner)
        self.about_panel = AboutPanel()

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.dataset_panel, NAVIGATION_AREAS[0][0])
        self.tabs.addTab(self.overview_panel, NAVIGATION_AREAS[1][0])
        self.tabs.addTab(self.exercise_11_7_panel, NAVIGATION_AREAS[2][0])
        self.tabs.addTab(self.rework_panel, NAVIGATION_AREAS[3][0])
        self.tabs.addTab(self.sequence_panel, NAVIGATION_AREAS[4][0])
        self._explorer_tab_index = self.tabs.addTab(
            self.case_explorer_panel, NAVIGATION_AREAS[5][0]
        )
        self.tabs.addTab(self.export_panel, NAVIGATION_AREAS[6][0])
        self.tabs.addTab(self.about_panel, NAVIGATION_AREAS[7][0])
        self.setCentralWidget(self.tabs)

        self.dataset_panel.store_changed.connect(self._set_store)
        self.overview_panel.open_case_requested.connect(self._open_case)
        self.exercise_11_7_panel.open_case_requested.connect(self._open_case)
        self.rework_panel.open_case_requested.connect(self._open_case)
        self.sequence_panel.open_case_requested.connect(self._open_case)
        self.exercise_11_7_panel.results_changed.connect(self._sync_export_results)
        self.rework_panel.results_changed.connect(self._sync_export_results)
        self.sequence_panel.results_changed.connect(self._sync_export_results)
        self.export_panel.reset_requested.connect(self._reset_results)
        self.export_panel.rerun_requested.connect(self._rerun_results)

    def _set_store(self, store: EventStore | None) -> None:
        self.export_panel.set_store(store)
        self.about_panel.set_store(store)
        self.overview_panel.set_store(store)
        self.exercise_11_7_panel.set_store(store)
        self.rework_panel.set_store(store)
        self.sequence_panel.set_store(store)
        self.case_explorer_panel.set_store(store)
        self._sync_export_results()

    def _open_case(self, case_id: str, row_ids: list[object]) -> None:
        self.case_explorer_panel.open_case(case_id, row_ids)
        self.tabs.setCurrentIndex(self._explorer_tab_index)

    def _collect_results(self) -> list[AnalysisResult]:
        return [
            *self.exercise_11_7_panel.results(),
            *self.rework_panel.results(),
            *self.sequence_panel.results(),
        ]

    def _sync_export_results(self) -> None:
        self.export_panel.set_results(self._collect_results())

    def _reset_results(self) -> None:
        """Clear derived results while preserving the parsed EventStore."""

        self.overview_panel.reset()
        self.exercise_11_7_panel.reset()
        self.rework_panel.reset_results()
        self.sequence_panel.reset()
        self.case_explorer_panel.clear_selection()
        self._sync_export_results()

    def _rerun_results(self) -> None:
        """Recompute all analyses from the active store without parsing XES again."""

        if self.dataset_panel.store() is None:
            return
        self._reset_results()
        self.overview_panel.refresh()
        self.exercise_11_7_panel.run()
        self.rework_panel.run_analysis()
        self.sequence_panel.run()
