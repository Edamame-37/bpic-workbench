"""Tests for the persistent Disco-inspired application navigation."""

from PySide6.QtWidgets import QApplication
import pytest

from src.core.ex_11_15_18 import run_11_15, run_11_18
from src.core.ex_11_22 import run_11_22
from src.core.ex_11_7 import run_11_7
from src.gui.common import NAVIGATION_ROUTES
from src.gui.main_window import MainWindow

_app = QApplication.instance() or QApplication([])


def test_sidebar_exposes_and_navigates_every_route() -> None:
    window = MainWindow()
    try:
        assert window.sidebar.route_ids() == [
            route.route_id for route in NAVIGATION_ROUTES
        ]
        for route in NAVIGATION_ROUTES:
            window.sidebar.item(route.route_id).button.click()
            assert window.current_route() == route.route_id
            assert window.pages.currentWidget() is window._panels[route.route_id]
            assert window.header.title.text() == route.title
    finally:
        window.close()


def test_navigation_history_supports_back_and_forward() -> None:
    window = MainWindow()
    try:
        window.navigate("overview")
        window.navigate("exercise_11_7")

        window.go_back()
        assert window.current_route() == "overview"
        assert window.header.forward_button.isEnabled()

        window.go_forward()
        assert window.current_route() == "exercise_11_7"
        assert window.header.back_button.isEnabled()
    finally:
        window.close()


def test_route_shortcuts_select_corresponding_workspace() -> None:
    window = MainWindow()
    try:
        for route in NAVIGATION_ROUTES:
            window._shortcut_actions[f"route:{route.route_id}"].trigger()
            assert window.current_route() == route.route_id

        window._shortcut_actions["back"].trigger()
        assert window.current_route() == "export"
        window._shortcut_actions["forward"].trigger()
        assert window.current_route() == "about"
    finally:
        window.close()


def test_global_action_bar_routes_import_export_and_about(monkeypatch) -> None:
    window = MainWindow()
    import_calls: list[bool] = []
    monkeypatch.setattr(
        window.dataset_panel,
        "choose_file",
        lambda: import_calls.append(True),
    )
    try:
        window.navigate("overview")
        window.action_bar.import_button.click()
        assert import_calls == [True]
        assert window.current_route() == "dataset"

        window.action_bar.about_button.click()
        assert window.current_route() == "about"
    finally:
        window.close()


def test_dataset_context_results_badges_and_reset(synthetic_store) -> None:
    window = MainWindow()
    try:
        window.dataset_panel._on_done(synthetic_store)

        assert window.current_route() == "overview"
        assert "synthetic" in window.header.dataset.text()
        assert window.sidebar.item("dataset").badge.text() == "Ready"
        assert window.action_bar.reset_button.isEnabled()

        window.exercise_11_7_panel._on_done(run_11_7(synthetic_store))
        target = "W_Assess potential fraud"
        window.rework_panel._on_done(
            [run_11_15(synthetic_store, target), run_11_18(synthetic_store, target)]
        )
        window.sequence_panel._on_done(run_11_22(synthetic_store))

        assert window.sidebar.item("exercise_11_7").badge.text() == "5/5"
        assert window.sidebar.item("rework").badge.text() == "2/2"
        assert window.sidebar.item("sequence").badge.text() == "1/1"
        assert window.sidebar.item("export").badge.text() == "8/8"

        window.action_bar.reset_button.click()
        assert window.dataset_panel.store() is synthetic_store
        assert window.sidebar.item("exercise_11_7").badge.text() == "0/5"
        assert window.sidebar.item("export").badge.text() == "0/8"
    finally:
        window.worker_manager.wait_all()
        _app.processEvents()
        window.close()


def test_open_case_navigates_to_explorer_and_updates_breadcrumb(synthetic_store) -> None:
    window = MainWindow()
    try:
        window.dataset_panel._on_done(synthetic_store)
        window._open_case("C001", [0, 1])

        assert window.current_route() == "explorer"
        assert window.case_explorer_panel.current_case == "C001"
        assert "Case C001" in window.header.breadcrumb.text()
        assert window.sidebar.item("explorer").badge.text() == "Case C001"
    finally:
        window.worker_manager.wait_all()
        _app.processEvents()
        window.close()


def test_unknown_route_is_rejected() -> None:
    window = MainWindow()
    try:
        with pytest.raises(ValueError, match="Unknown navigation route"):
            window.navigate("missing")
    finally:
        window.close()
