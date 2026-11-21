from PySide6.QtWidgets import QApplication

from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from tests.test_11_7 import build_empty_store, build_store

_app = QApplication.instance() or QApplication([])

def _panel_with_data() -> Exercise117Panel:
    panel = Exercise117Panel()
    panel.set_store(build_store({
        "c1": [("O_Refused", "2024-01-01 10:00"), ("O_Accepted", "2024-01-03 10:00")],
        "c2": [("A_Other", "2024-01-01 10:00"), ("O_Cancelled", "2024-01-02 10:00")],
    }))
    return panel

def test_run_fills_five_rows_with_counts():
    panel = _panel_with_data()
    panel.run()
    counts = [panel.summary.item(r, 2).text() for r in range(5)]
    assert counts == ["2", "2", "1", "1", "1"]

def test_open_case_signal_and_reset():
    panel = _panel_with_data()
    panel.run()
    received = []
    panel.open_case.connect(received.append)
    panel.cases.selectRow(0)
    panel.open_button.click()
    assert received == ["c1"]
    panel.reset()
    assert panel.summary.item(0, 0) is None and panel.cases.rowCount() == 0

def test_set_store_discards_old_results():
    panel = _panel_with_data()
    panel.run()
    panel.set_store(None)
    assert panel.summary.item(0, 0) is None

def test_empty_log_shows_message_instead_of_zero_result():
    panel = Exercise117Panel()
    panel.set_store(build_empty_store())
    panel.run()
    assert "kosong" in panel.status.text().lower()