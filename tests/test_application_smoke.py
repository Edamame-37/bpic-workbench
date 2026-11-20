"""Headless smoke tests for the initial desktop shell."""

from PySide6.QtWidgets import QApplication

from src.gui.main_window import APPLICATION_TITLE, NAVIGATION_AREAS, MainWindow
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
        assert window.tabs.count() == len(NAVIGATION_AREAS)
        assert [
            window.tabs.tabText(index) for index in range(window.tabs.count())
        ] == [title for title, _ in NAVIGATION_AREAS]
    finally:
        window.close()

