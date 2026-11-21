"""Generate reproducible GUI screenshots for the team demonstration guide."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.cycle_time import compute_case_durations
from src.core.event_store import EventStore
from src.core.ex_11_15_18 import run_11_15, run_11_18
from src.core.ex_11_22 import run_11_22
from src.core.ex_11_7 import run_11_7
from src.gui.main_window import MainWindow

SCREENSHOT_DIRECTORY = PROJECT_ROOT / "docs" / "screenshots"
DEMO_OUTPUT_DIRECTORY = PROJECT_ROOT / "exports" / "demo"
FRAUD_ACTIVITY = "W_Assess potential fraud"


def build_demo_store() -> EventStore:
    """Create a small log that exercises every analysis and evidence view."""

    cases = {
        "C001": [
            ("A_Create Application", "U99"),
            (FRAUD_ACTIVITY, "U01"),
            (FRAUD_ACTIVITY, "U01"),
            ("O_Cancelled", "U01"),
            ("W_Call after cancellation", "U01"),
            ("O_Accepted", "U01"),
        ],
        "C002": [
            ("A_Create Application", "U99"),
            (FRAUD_ACTIVITY, "U02"),
            (FRAUD_ACTIVITY, "U03"),
            ("O_Refused", "U03"),
        ],
        "C003": [
            ("A_Create Application", "U99"),
            ("O_Accepted", "U04"),
        ],
        "C004": [
            ("A_Create Application", "U99"),
            ("O_Cancelled", "U05"),
        ],
    }

    rows: list[dict[str, object]] = []
    row_id = 0
    base_timestamp = pd.Timestamp("2017-01-01T08:00:00Z")
    for case_offset, (case_id, events) in enumerate(cases.items()):
        for trace_position, (activity, resource) in enumerate(events):
            rows.append(
                {
                    "case:concept:name": case_id,
                    "concept:name": activity,
                    "time:timestamp": base_timestamp
                    + pd.Timedelta(days=case_offset, hours=trace_position * 4),
                    "lifecycle:transition": "complete",
                    "org:resource": resource,
                    "_trace_pos": trace_position,
                    "_row_id": row_id,
                }
            )
            row_id += 1

    events = pd.DataFrame(rows)
    metadata = {
        "dataset_name": "demo_bpic17",
        "file_name": "demo_bpic17.xes",
        "file_size_bytes": 24_576,
        "sha256": "demo-synthetic-dataset",
        "event_count": len(events),
        "case_count": len(cases),
        "timezone_status": "UTC",
        "has_lifecycle": True,
        "has_resource": True,
        "warnings": (),
    }
    return EventStore(events, compute_case_durations(events), metadata)


def wait_for_background_work(window: MainWindow) -> None:
    """Wait for initial overview/rework jobs and deliver their callbacks."""

    window.worker_manager.wait_all(timeout_ms=15_000)
    application = QApplication.instance()
    if application is not None:
        application.processEvents()


def capture(window: MainWindow, route_id: str, filename: str) -> None:
    """Navigate to one workspace and save its rendered content."""

    window.navigate(route_id)
    QApplication.processEvents()
    QTest.qWait(80)
    target = SCREENSHOT_DIRECTORY / filename
    if not window.grab().save(str(target)):
        raise RuntimeError(f"Unable to write screenshot: {target}")


def populate_analysis_results(window: MainWindow, store: EventStore) -> None:
    """Populate every analysis synchronously for deterministic screenshots."""

    window.exercise_11_7_panel._on_done(run_11_7(store))
    window.rework_panel._on_done(
        [
            run_11_15(store, FRAUD_ACTIVITY),
            run_11_18(store, FRAUD_ACTIVITY),
        ]
    )
    window.sequence_panel._on_done(run_11_22(store))
    window.export_panel.set_output_directory(DEMO_OUTPUT_DIRECTORY)


def capture_all(window: MainWindow) -> None:
    """Capture navigation and all eight application workspaces."""

    window.navigate("dataset")
    window.open_navigation()
    QTest.qWait(240)
    capture_path = SCREENSHOT_DIRECTORY / "demo-00-navigation.png"
    if not window.grab().save(str(capture_path)):
        raise RuntimeError(f"Unable to write screenshot: {capture_path}")
    window.close_navigation()
    QTest.qWait(240)

    capture(window, "dataset", "demo-01-dataset.png")
    capture(window, "overview", "demo-02-overview.png")
    capture(window, "exercise_11_7", "demo-03-outcome-kasus.png")

    window.navigate("rework")
    window.rework_panel.page15.cases.selectRow(0)
    window.rework_panel.page15._on_case_selected()
    if window.rework_panel.page15.evidence.rowCount() == 0:
        raise RuntimeError("Demo rework result does not contain evidence")
    window.rework_panel.page15.cases.setMaximumHeight(165)
    window.rework_panel.page15.evidence.setMinimumHeight(165)
    window.rework_panel.page15.evidence.resizeRowsToContents()
    capture(window, "rework", "demo-04-rework.png")

    window.sequence_panel.table.selectRow(0)
    capture(window, "sequence", "demo-05-urutan-cancel-accept.png")

    sequence_result = window.sequence_panel.result
    if sequence_result is None or sequence_result.evidence is None:
        raise RuntimeError("Demo sequence result does not contain evidence")
    pair = sequence_result.evidence.iloc[0]
    window.case_explorer_panel.open_case(
        str(pair["case_id"]),
        [pair["cancel_row_id"], pair["accept_row_id"]],
    )
    capture(window, "explorer", "demo-06-penelusuran-kasus.png")
    capture(window, "export", "demo-07-export.png")
    capture(window, "about", "demo-08-info.png")


def main() -> int:
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1440, 900)
    window.show()
    application.processEvents()

    store = build_demo_store()
    window.dataset_panel._on_done(store)
    wait_for_background_work(window)
    populate_analysis_results(window, store)
    capture_all(window)

    window.worker_manager.wait_all()
    window.close()
    application.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
