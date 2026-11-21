"""A4 - Uji GUI SequencePanel dan CaseExplorerPanel (headless)."""

from PySide6.QtWidgets import QApplication

from src.gui.panels.case_explorer_panel import CaseExplorerPanel
from src.gui.panels.sequence_panel import SequencePanel
from tests.test_ordering import build_empty_store, build_store

_app = QApplication.instance() or QApplication([])


def _store():
    return build_store({
        "c1": ["A_Create", "O_Cancelled", "O_Created", "O_Accepted"],
        "c2": ["O_Accepted", "O_Cancelled"],
        "c3": ["O_Refused"],
        "c4": ["O_Cancelled", "O_Accepted"],
    })


def test_sequence_panel_shows_count_denominator_percentage():
    panel = SequencePanel()
    panel.set_store(_store())
    panel.run()
    assert panel.count_label.text() == "Count: 2"
    assert panel.denominator_label.text() == "Denominator: 4"
    assert panel.percentage_label.text() == "Persentase: 50.00%"
    assert panel.model.rowCount() == 2


def test_sequence_panel_emits_case_and_pair_row_ids():
    panel = SequencePanel()
    panel.set_store(_store())
    panel.run()
    received = []
    panel.open_case_requested.connect(lambda cid, rows: received.append((cid, rows)))
    panel.table.selectRow(0)
    assert "i=1" in panel.timeline.text() and "j=3" in panel.timeline.text()
    panel.open_button.click()
    assert received == [("c1", [1, 3])]


def test_sequence_panel_search_hides_other_rows():
    panel = SequencePanel()
    panel.set_store(_store())
    panel.run()
    panel.search.setText("c4")
    assert panel.table.isRowHidden(0) and not panel.table.isRowHidden(1)


def test_sequence_panel_empty_log_is_not_a_fake_zero():
    panel = SequencePanel()
    panel.set_store(build_empty_store())
    panel.run()
    assert panel.count_label.text() == "Count: N/A"
    assert "kosong" in panel.notes.text().lower()


def test_sequence_panel_reset_and_new_store_discard_result():
    panel = SequencePanel()
    panel.set_store(_store())
    panel.run()
    panel.set_store(None)
    assert panel.result is None and panel.model.rowCount() == 0
    assert not panel.run_button.isEnabled()


def test_runner_result_from_old_dataset_is_ignored():
    pending = []
    panel = SequencePanel(runner=lambda job, done: pending.append((job, done)))
    panel.set_store(_store())
    panel.run()
    panel.set_store(build_store({"x": ["A"]}))
    job, done = pending[0]
    done(job())
    assert panel.result is None


def test_explorer_open_case_highlights_evidence_rows():
    store = _store()
    explorer = CaseExplorerPanel()
    explorer.set_store(store)
    explorer.open_case("c1", [1, 3])
    frame = explorer.model.frame()
    assert explorer.model.rowCount() == 4
    assert frame["_highlight"].tolist() == [False, True, False, True]
    assert "4 event" in explorer.info.text()
    assert "i=1" in explorer.evidence_info.text()


def test_explorer_unknown_case_and_dataset_change_clear_view():
    explorer = CaseExplorerPanel()
    explorer.set_store(_store())
    explorer.open_case("tidak-ada")
    assert "tidak ditemukan" in explorer.info.text()
    explorer.open_case("c1", [1])
    explorer.set_store(build_store({"z": ["A"]}))
    assert explorer.model.rowCount() == 0 and explorer.current_case is None


def test_explorer_search_and_open_from_list():
    explorer = CaseExplorerPanel()
    explorer.set_store(_store())
    explorer.search.setText("c3")
    assert explorer.case_list.count() == 1
    explorer.case_list.setCurrentRow(0)
    assert explorer.current_case == "c3"


def test_sequence_panel_wires_into_explorer():
    store = _store()
    panel, explorer = SequencePanel(), CaseExplorerPanel()
    panel.set_store(store)
    explorer.set_store(store)
    panel.open_case_requested.connect(explorer.open_case)
    panel.run()
    panel.table.selectRow(1)
    panel.open_button.click()
    assert explorer.current_case == "c4"
    assert explorer.model.frame()["_highlight"].tolist() == [True, True]
