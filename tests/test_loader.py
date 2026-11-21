"""Tests for A1 Data Foundation: XES loader, EventStore, overview, panel, and worker."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.core.ex_11_7 import run_11_7
from src.core.ex_11_15_18 import run_11_15, run_11_18
from src.core.loader import EventLogLoadError, load_event_log
from src.core.overview import get_overview
from src.gui.panels.overview_panel import OverviewPanel
from src.gui.worker import WorkerManager

_app = QApplication.instance() or QApplication([])


def _write_xes(tmp_path: Path, name: str, traces_xml: str) -> Path:
    xes_path = tmp_path / name
    content = (
        '<?xml version="1.0" encoding="UTF-8" ?>\n'
        '<log xes.version="1.0" xes.features="nested-attributes" '
        'xmlns="http://www.xes-standard.org/">\n'
        '  <extension name="Concept" prefix="concept" '
        'uri="http://www.xes-standard.org/concept.xesext"/>\n'
        '  <extension name="Time" prefix="time" '
        'uri="http://www.xes-standard.org/time.xesext"/>\n'
        '  <extension name="Lifecycle" prefix="lifecycle" '
        'uri="http://www.xes-standard.org/lifecycle.xesext"/>\n'
        '  <extension name="Organizational" prefix="org" '
        'uri="http://www.xes-standard.org/org.xesext"/>\n'
        f"{traces_xml}"
        "</log>\n"
    )
    xes_path.write_text(content, encoding="utf-8")
    return xes_path


def _trace_xml(case_id: str | None, events: list[dict[str, str]]) -> str:
    attrs = (
        f'    <string key="concept:name" value="{case_id}"/>\n'
        if case_id is not None
        else ""
    )
    event_blocks = []
    for ev in events:
        lines = ["    <event>"]
        for key, value in ev.items():
            tag = "date" if key == "time:timestamp" else "string"
            lines.append(f'      <{tag} key="{key}" value="{value}"/>')
        lines.append("    </event>")
        event_blocks.append("\n".join(lines))
    return f"  <trace>\n{attrs}" + "\n".join(event_blocks) + "\n  </trace>\n"


def test_t11_preserves_xes_trace_order_for_equal_timestamps(tmp_path: Path) -> None:
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
                "time:timestamp": "2026-01-01T08:00:00+00:00",
                "lifecycle:transition": "complete",
                "org:resource": "U01",
            },
        ],
    )
    path = _write_xes(tmp_path, "equal_ts.xes", traces)

    store = load_event_log(path)
    case_events = store.events[store.events["case:concept:name"] == "C001"]

    assert case_events["time:timestamp"].nunique() == 1
    assert case_events["_trace_pos"].tolist() == [0, 1]
    assert case_events["concept:name"].tolist() == ["O_Cancelled", "O_Accepted"]
    assert store.events["_row_id"].is_unique


def test_leading_zero_case_ids_are_not_merged(tmp_path: Path) -> None:
    traces = _trace_xml(
        "00123",
        [
            {
                "concept:name": "O_Accepted",
                "time:timestamp": "2026-01-01T08:00:00+00:00",
            }
        ],
    ) + _trace_xml(
        "123",
        [
            {
                "concept:name": "O_Refused",
                "time:timestamp": "2026-01-02T08:00:00+00:00",
            }
        ],
    )
    path = _write_xes(tmp_path, "leading_zeros.xes", traces)

    store = load_event_log(path)
    assert sorted(store.case_durations["case:concept:name"].tolist()) == ["00123", "123"]
    assert store.metadata["case_count"] == 2


def test_optional_lifecycle_and_resource_missing_still_imports(tmp_path: Path) -> None:
    traces = _trace_xml(
        "C1",
        [
            {
                "concept:name": "W_Assess potential fraud",
                "time:timestamp": "2026-01-01T08:00:00+00:00",
            },
            {
                "concept:name": "W_Assess potential fraud",
                "time:timestamp": "2026-01-01T09:00:00+00:00",
            },
        ],
    )
    path = _write_xes(tmp_path, "minimal_attrs.xes", traces)

    store = load_event_log(path)
    assert store.metadata["has_lifecycle"] is False
    assert store.metadata["has_resource"] is False
    assert store.metadata["warnings"]

    r15 = run_11_15(store, "W_Assess potential fraud")
    r18 = run_11_18(store, "W_Assess potential fraud")
    assert r15.status == "unavailable"
    assert r18.status == "unavailable"


def test_t13_missing_file_or_corrupt_xes_raises_structured_error(tmp_path: Path) -> None:
    with pytest.raises(EventLogLoadError, match="tidak ditemukan"):
        load_event_log(tmp_path / "does_not_exist.xes")

    corrupt = tmp_path / "corrupt.xes"
    corrupt.write_text("<not-valid-xml", encoding="utf-8")
    with pytest.raises(EventLogLoadError):
        load_event_log(corrupt)


def test_t13_missing_required_attributes_rejected(tmp_path: Path) -> None:
    missing_activity = _trace_xml(
        "C1",
        [{"time:timestamp": "2026-01-01T08:00:00+00:00"}],
    )
    path = _write_xes(tmp_path, "missing_act.xes", missing_activity)
    with pytest.raises(EventLogLoadError, match="concept:name"):
        load_event_log(path)

    missing_case_id = _trace_xml(
        None,
        [
            {
                "concept:name": "O_Accepted",
                "time:timestamp": "2026-01-01T08:00:00+00:00",
            }
        ],
    )
    path_no_case = _write_xes(tmp_path, "missing_case.xes", missing_case_id)
    with pytest.raises(EventLogLoadError, match="case:concept:name"):
        load_event_log(path_no_case)


def test_t15_empty_log_handled_without_divide_by_zero(tmp_path: Path) -> None:
    path = _write_xes(tmp_path, "empty.xes", "")

    store = load_event_log(path)
    overview = get_overview(store)
    results_11_7 = run_11_7(store)

    assert store.metadata["is_empty"] is True
    assert overview.status == "empty"
    assert overview.total_cases == 0
    assert overview.total_events == 0
    assert overview.mean_cycle_time_days is None
    assert all(res.status == "unavailable" for res in results_11_7)


def test_reimport_same_file_is_deterministic(tmp_path: Path) -> None:
    traces = _trace_xml(
        "C1",
        [
            {
                "concept:name": "A_Create",
                "time:timestamp": "2026-01-01T00:00:00+00:00",
            },
            {
                "concept:name": "O_Accepted",
                "time:timestamp": "2026-01-03T00:00:00+00:00",
            },
        ],
    )
    path = _write_xes(tmp_path, "reimport.xes", traces)

    first = load_event_log(path)
    second = load_event_log(path)

    assert first.metadata["sha256"] == second.metadata["sha256"]
    assert first.metadata["case_count"] == second.metadata["case_count"] == 1
    assert first.metadata["event_count"] == second.metadata["event_count"] == 2
    pd.testing.assert_frame_equal(first.events, second.events)
    pd.testing.assert_frame_equal(first.case_durations, second.case_durations)


def test_get_overview_computes_kpis_and_mean_cycle_time(tmp_path: Path) -> None:
    traces = _trace_xml(
        "C1",
        [
            {
                "concept:name": "A_Create",
                "time:timestamp": "2026-01-01T00:00:00+00:00",
            },
            {
                "concept:name": "O_Accepted",
                "time:timestamp": "2026-01-03T00:00:00+00:00",
            },
        ],
    ) + _trace_xml(
        "C2",
        [
            {
                "concept:name": "A_Create",
                "time:timestamp": "2026-01-02T00:00:00+00:00",
            }
        ],
    )
    path = _write_xes(tmp_path, "overview.xes", traces)
    store = load_event_log(path)

    summary = get_overview(store)

    assert summary.status == "ok"
    assert summary.total_cases == 2
    assert summary.total_events == 3
    assert summary.total_activities == 2
    assert summary.mean_cycle_time_days == pytest.approx(1.0)
    assert summary.activity_frequencies["activity"].tolist() == ["A_Create", "O_Accepted"]
    assert summary.activity_frequencies["count"].tolist() == [2, 1]


def test_overview_panel_flow_search_and_open_case(synthetic_store) -> None:
    panel = OverviewPanel()
    received: list[tuple[str, list[object]]] = []
    panel.open_case_requested.connect(
        lambda case_id, row_ids: received.append((case_id, row_ids))
    )

    panel.set_store(synthetic_store)
    assert panel.total_cases_label.text() == "2"
    assert panel.total_events_label.text() == "3"
    assert panel.mean_cycle_time_label.text() == "0.0000 hari"

    panel.search.setText("C002")
    assert panel.cases.model().rowCount() == 1
    assert (
        panel.cases.model().data(
            panel.cases.model().index(0, 0), Qt.ItemDataRole.DisplayRole
        )
        == "C002"
    )

    panel.cases.selectRow(0)
    assert panel.open_button.isEnabled()
    panel.open_button.click()
    assert received == [("C002", [])]

    panel.set_store(None)
    assert panel.total_cases_label.text() == "N/A"
    assert panel.cases.model().rowCount() == 0


def test_overview_panel_ignores_late_worker_result_after_switch(
    synthetic_store,
) -> None:
    pending_jobs = []

    def runner(job, on_done):
        pending_jobs.append((job, on_done))

    panel = OverviewPanel(runner=runner)
    panel.set_store(synthetic_store)
    job, on_done = pending_jobs[0]

    panel.set_store(None)
    on_done(job())

    assert panel.overview() is None
    assert panel.total_cases_label.text() == "N/A"
    assert panel.status.text() == "Belum ada dataset aktif."


def test_worker_manager_executes_job_and_delivers_result() -> None:
    manager = WorkerManager()
    results: list[int] = []
    errors: list[Exception] = []

    manager.run(
        lambda: 21 * 2,
        results.append,
        on_error=errors.append,
    )
    assert manager.wait_all(5000)
    _app.processEvents()

    assert results == [42]
    assert errors == []
    assert not manager.is_busy()
