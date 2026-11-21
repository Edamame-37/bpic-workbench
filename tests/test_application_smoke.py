"""Headless smoke tests for the initial desktop shell."""

from PySide6.QtWidgets import QApplication

from src.gui.main_window import APPLICATION_TITLE, NAVIGATION_AREAS, MainWindow
from src.gui.panels.about_panel import AboutPanel
from src.gui.panels.case_explorer_panel import CaseExplorerPanel
from src.gui.panels.dataset_panel import DatasetPanel
from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from src.gui.panels.export_panel import ExportPanel
from src.gui.panels.overview_panel import OverviewPanel
from src.gui.panels.rework_panel import ReworkPanel
from src.gui.panels.sequence_panel import SequencePanel
from src.main import create_application


def test_create_application_reuses_qt_instance() -> None:
    first_application = create_application([])
    second_application = create_application([])

    assert isinstance(first_application, QApplication)
    assert second_application is first_application


def test_main_window_registers_all_initial_areas() -> None:
    create_application([])
    window = MainWindow()

    try:
        assert window.windowTitle() == APPLICATION_TITLE
        assert window.pages.count() == len(NAVIGATION_AREAS)
        assert len(window.sidebar.route_ids()) == len(NAVIGATION_AREAS)
        assert window.current_route() == "dataset"
        assert window.header.title.text() == "Dataset & Status"
        assert not window.action_bar.reset_button.isEnabled()
        assert isinstance(window.dataset_panel, DatasetPanel)
        assert isinstance(window.overview_panel, OverviewPanel)
        assert isinstance(window.exercise_11_7_panel, Exercise117Panel)
        assert isinstance(window.rework_panel, ReworkPanel)
        assert isinstance(window.sequence_panel, SequencePanel)
        assert isinstance(window.case_explorer_panel, CaseExplorerPanel)
        assert isinstance(window.export_panel, ExportPanel)
        assert isinstance(window.about_panel, AboutPanel)
    finally:
        window.close()

