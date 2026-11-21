"""End-to-end integration tests for the implemented A1-A4 workflow."""

import time
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import QApplication

from src.core.event_store import EventStore
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
    parse_calls = 0
    loader = window.dataset_panel._loader

    def counting_loader(path):
        nonlocal parse_calls
        parse_calls += 1
        return loader(path)

    window.dataset_panel._loader = counting_loader
    try:
        window.dataset_panel.load_path(_integrated_xes(tmp_path))
        _wait_for_workers(window)

        store = window.dataset_panel.store()
        assert store is not None
        assert parse_calls == 1
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

        assert len(window.export_panel.results()) == 8
        export_dir = tmp_path / "export with spaces"
        window.export_panel.set_output_directory(export_dir)
        window.export_panel.export_button.click()
        _wait_for_workers(window)

        assert window.export_panel.last_export is not None
        summary = pd.read_csv(window.export_panel.last_export.summary)
        assert len(summary) == 8
        assert set(summary["exercise_id"].astype(str)) == {
            "11.7 A",
            "11.7 B",
            "11.7 C",
            "11.7 D",
            "11.7 E",
            "11.15",
            "11.18",
            "11.22",
        }
        assert store.metadata["sha256"] in window.about_panel.dataset.text()

        window.export_panel.reset_button.click()
        assert window.dataset_panel.store() is store
        assert window.exercise_11_7_panel.results() == []
        assert window.rework_panel.results() == []
        assert window.sequence_panel.results() == []
        assert parse_calls == 1

        window.export_panel.rerun_button.click()
        _wait_for_workers(window)

        assert len(window.export_panel.results()) == 8
        assert window.dataset_panel.store() is store
        assert parse_calls == 1

        window.dataset_panel.load_path(tmp_path / "missing.xes")
        _wait_for_workers(window)

        assert parse_calls == 2
        assert window.dataset_panel.store() is None
        assert window.overview_panel.overview() is None
        assert window.exercise_11_7_panel.results() == []
        assert window.rework_panel.results() == []
        assert window.sequence_panel.result is None
        assert window.case_explorer_panel.current_case is None
        assert window.export_panel.results() == []
        assert window.about_panel.dataset.text() == "Dataset aktif: belum ada."
    finally:
        _wait_for_workers(window)
        window.close()


def test_main_window_rejects_stale_dataset_load(synthetic_store) -> None:
    pending = []
    window = MainWindow()

    def manual_runner(job, on_done):
        pending.append((job, on_done))

    def named_store(name: str) -> EventStore:
        return EventStore(
            events=synthetic_store.events.copy(),
            case_durations=synthetic_store.case_durations.copy(),
            metadata={**synthetic_store.metadata, "file_name": name},
        )

    stores = {
        "dataset-a.xes": named_store("dataset-a.xes"),
        "dataset-b.xes": named_store("dataset-b.xes"),
    }
    window.dataset_panel._runner = manual_runner
    window.dataset_panel._loader = lambda path: stores[str(path)]
    try:
        window.dataset_panel.load_path("dataset-a.xes")
        window.dataset_panel.load_path("dataset-b.xes")
        first_job, first_done = pending[0]
        second_job, second_done = pending[1]

        second_done(second_job())
        first_done(first_job())

        assert window.dataset_panel.store() is stores["dataset-b.xes"]
        assert "dataset-b.xes" in window.dataset_panel.metadata.text()
        assert "dataset-b.xes" in window.about_panel.dataset.text()
    finally:
        _wait_for_workers(window)
        window.close()

