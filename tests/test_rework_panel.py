"""Smoke test panel A3 (offscreen) + presenter murni."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from src.gui.panels.rework_panel import ReworkPanel, case_table, evidence_for_case, status_headline
from src.core.ex_11_15_18 import run_11_15, run_11_18
from tests.test_rework import FRAUD, F, make_store

app = QApplication.instance() or QApplication([])


def _store():
    return make_store(
        {
            "c1": [F("complete", "U01"), F("complete", "U01")],
            "c2": [F("complete", "U01"), F("complete", "U02")],
            "c3": [F("schedule", "U01"), F("schedule", "U01"), F("complete", "U01")],
        }
    )


def test_presenter():
    s = _store()
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert "2 case dari 3 case" in status_headline(r15) and "CASE" in status_headline(r15)
    assert case_table(r15)["case_id"].tolist() == ["c1", "c2"]
    assert case_table(r18)["case_id"].tolist() == ["c1"]
    assert len(evidence_for_case(r15, "c2")) == 2


def test_unavailable_headline_has_no_number():
    s = make_store({"c1": [F("complete", "U01")] * 2}, drop=["lifecycle:transition"])
    r = run_11_15(s, FRAUD)
    h = status_headline(r)
    assert h.startswith("ANALISIS TIDAK TERSEDIA") and "0 case" not in h


def test_panel_flow_and_signal():
    p = ReworkPanel()
    p.set_store(_store())
    assert p.activity.currentText() == FRAUD
    r15, r18 = p.results()
    assert (r15.count, r18.count) == (2, 1)
    got = []
    p.open_case_requested.connect(lambda cid, rows: got.append((cid, rows)))
    p.page15.cases.selectRow(0)
    assert p.page15.evidence.rowCount() == 2 and p.page15.open_btn.isEnabled()
    p.page15.open_btn.click()
    assert got and got[0][0] == "c1" and len(got[0][1]) == 2
    p.run_analysis()  # rerun tanpa impor ulang
    assert len(p.results()) == 2


def test_panel_ambiguous_target_requires_choice():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01", act="W_Assess Potential Fraud")]})
    p = ReworkPanel()
    p.set_store(s)
    assert p.activity.currentText() == "" and p.results() == []
