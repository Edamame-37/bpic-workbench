"""Interaction tests for the full-height overlay navigation drawer."""

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolButton

from src.gui.main_window import MainWindow

_app = QApplication.instance() or QApplication([])


def _wait_for_animation() -> None:
    QTest.qWait(220)
    _app.processEvents()


def test_drawer_opens_over_workspace_and_closes_from_scrim() -> None:
    window = MainWindow()
    window.show()
    try:
        assert not window.is_navigation_open()
        assert window.sidebar.x() == -window.sidebar.DRAWER_WIDTH
        assert not window.scrim.isVisible()

        window.header.menu_button.click()
        _wait_for_animation()

        assert window.is_navigation_open()
        assert window.sidebar.x() == 0
        assert window.sidebar.height() == window.root.height()
        assert window.scrim.isVisible()
        assert window.sidebar.geometry().intersects(window.header.geometry())

        QTest.mouseClick(window.scrim, Qt.MouseButton.LeftButton)
        _wait_for_animation()

        assert not window.is_navigation_open()
        assert window.sidebar.x() == -window.sidebar.DRAWER_WIDTH
        assert not window.scrim.isVisible()
    finally:
        window.close()


def test_drawer_closes_after_route_selection_and_escape() -> None:
    window = MainWindow()
    window.show()
    try:
        window.open_navigation()
        _wait_for_animation()
        window.sidebar.item("rework").button.click()
        _wait_for_animation()
        assert window.current_route() == "rework"
        assert not window.is_navigation_open()

        window.open_navigation()
        _wait_for_animation()
        QTest.keyClick(window, Qt.Key.Key_Escape)
        _wait_for_animation()
        assert not window.is_navigation_open()
    finally:
        window.close()


def test_drawer_group_can_be_collapsed_and_reopened() -> None:
    window = MainWindow()
    try:
        analyses = window.sidebar.group_container("ANALYSES")
        group_buttons = window.sidebar.findChildren(QToolButton)
        named_buttons = [button for button in group_buttons if button.text() == "ANALYSES"]
        assert len(named_buttons) == 1
        assert not analyses.isHidden()

        named_buttons[0].click()
        assert analyses.isHidden()
        named_buttons[0].click()
        assert not analyses.isHidden()
    finally:
        window.close()
