"""End-to-end integration tests for the implemented A1-A4 workflow."""

import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from tests.test_loader import _trace_xml, _write_xes


_app = QApplication.instance() or QApplication([])


def _wait_for_workers(window: MainWindow, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    stable_idle_checks = 0
    while time.monotonic() < deadline:
        _app.processEvents()
        if window.worker_manager.is_busy():
            stable_idle_checks = 0
        else:
            stable_idle_checks += 1
            if stable_idle_checks >= 2:
                return
        time.sleep(0.01)
    raise AssertionError("Worker tasks did not finish before timeout")


def _integrated_xes(tmp_path: Path) -> Path:
    traces = _trace_xml(
        "C001",
        [
            {
                "concept:name": "O_Cancelled",
                "time:timestamp": "2026-01-01T08:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U01",
            },
            {
                "concept:name": "O_Accepted",
                "time:timestamp": "2026-01-01T09:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U01",
            },
            {
                "concept:name": "W_Assess potential fraud",
                "time:timestamp": "2026-01-01T10:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U01",
            },
            {
                "concept:name": "W_Assess potential fraud",
                "time:timestamp": "2026-01-01T11:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U01",
            },
        ],
    ) + _trace_xml(
        "C002",
        [
            {
                "concept:name": "O_Refused",
                "time:timestamp": "2026-01-02T08:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U02",
            }
        ],
    )
    return _write_xes(tmp_path, "integrated.xes", traces)


def test_import_analyze_explore_and_invalid_dataset_reset(tmp_path: Path) -> None:
    window = MainWindow()
    try:
        window.dataset_panel.load_path(_integrated_xes(tmp_path))
        _wait_for_workers(window)

        store = window.dataset_panel.store()
        assert store is not None
        assert store.metadata["case_count"] == 2
        assert window.overview_panel.overview() is not None
        assert window.overview_panel.overview().total_events == 5
        assert [result.count for result in window.rework_panel.results()] == [1, 1]

        window.exercise_11_7_panel.run()
        window.sequence_panel.run()
        _wait_for_workers(window)

        assert len(window.exercise_11_7_panel.results()) == 5
        assert window.sequence_panel.result is not None
        assert window.sequence_panel.result.count == 1

        window.sequence_panel.table.selectRow(0)
        window.sequence_panel.open_button.click()
        assert window.case_explorer_panel.current_case == "C001"
        assert window.tabs.currentWidget() is window.case_explorer_panel
        assert window.case_explorer_panel.model.frame()["_highlight"].sum() == 2

        window.dataset_panel.load_path(tmp_path / "missing.xes")
        _wait_for_workers(window)

        assert window.dataset_panel.store() is None
        assert window.overview_panel.overview() is None
        assert window.exercise_11_7_panel.results() == []
        assert window.rework_panel.results() == []
        assert window.sequence_panel.result is None
        assert window.case_explorer_panel.current_case is None
    finally:
        _wait_for_workers(window)
        window.close()

