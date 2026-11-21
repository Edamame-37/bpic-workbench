from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from tests.test_11_7 import build_empty_store, build_store


_app = QApplication.instance() or QApplication([])


def _panel_with_data() -> Exercise117Panel:
    panel = Exercise117Panel()
    panel.set_store(build_store({
        "c1": [
            ("O_Refused", "2024-01-01 10:00"),
            ("O_Accepted", "2024-01-03 10:00"),
        ],
        "c2": [
            ("A_Other", "2024-01-01 10:00"),
            ("O_Cancelled", "2024-01-02 10:00"),
        ],
    }))
    return panel


def test_run_fills_five_rows_with_counts():
    panel = _panel_with_data()

    panel.run()

    counts = [panel.summary.item(row, 2).text() for row in range(5)]
    assert counts == ["2", "2", "1", "1", "1"]


def test_open_case_signal_includes_evidence_row_ids():
    panel = _panel_with_data()
    panel.run()
    received: list[tuple[str, list[object]]] = []
    panel.open_case_requested.connect(
        lambda case_id, row_ids: received.append((case_id, row_ids))
    )

    panel.cases.selectRow(0)
    panel.open_button.click()

    assert received == [("c1", [1])]


def test_reset_clears_summary_and_case_model():
    panel = _panel_with_data()
    panel.run()

    panel.reset()

    assert panel.summary.item(0, 0) is None
    assert panel.cases.model().rowCount() == 0


def test_set_store_discards_old_results():
    panel = _panel_with_data()
    panel.run()

    panel.set_store(None)

    assert panel.summary.item(0, 0) is None
    assert panel.cases.model().rowCount() == 0


def test_empty_log_displays_na_instead_of_valid_zero():
    panel = Exercise117Panel()
    panel.set_store(build_empty_store())

    panel.run()

    assert "kosong" in panel.status.text().lower()
    assert panel.summary.item(0, 2).text() == "N/A"
    assert panel.summary.item(0, 4).text() == "N/A"


def test_search_filters_case_model_without_rebuilding_widgets():
    panel = _panel_with_data()
    panel.run()
    panel.summary.selectRow(0)

    panel.search.setText("C2")

    proxy_model = panel.cases.model()
    assert proxy_model.rowCount() == 1
    assert proxy_model.data(
        proxy_model.index(0, 0), Qt.ItemDataRole.DisplayRole
    ) == "c2"


def test_late_worker_result_is_ignored_after_dataset_switch():
    pending_jobs = []

    def runner(job, on_done):
        pending_jobs.append((job, on_done))

    panel = Exercise117Panel(runner=runner)
    panel.set_store(build_store({"old": [("O_Accepted", "2024-01-01")]}))
    panel.run()
    job, on_done = pending_jobs[0]

    panel.set_store(build_store({"new": [("O_Refused", "2024-02-01")]}))
    on_done(job())

    assert panel.summary.item(0, 0) is None
    assert panel.status.text() == "Siap dijalankan."
