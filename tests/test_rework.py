"""Unit test A3: 11.15 / 11.18 (T04, T05, T06, T09, T10 + edge cases)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from src.core import rework as rw
from src.core.ex_11_15_18 import run_11_15, run_11_18

FRAUD = "W_Assess potential fraud"
NA = None


@dataclass
class StubStore:
    """Pengganti EventStore A1 (hanya kontrak .events)."""

    events: pd.DataFrame


def make_store(cases: dict, drop=(), extra_other: bool = True) -> StubStore:
    """cases: {case_id: [(activity, lifecycle, resource), ...]} dalam urutan trace."""
    rows, rid = [], 0
    base = pd.Timestamp("2016-01-01", tz="UTC")
    for case, evs in cases.items():
        evs = list(evs)
        if extra_other:  # event lain berresource valid -> kolom resource 'ada' di log
            evs = [("A_Create Application", "complete", "U99")] + evs
        for pos, (act, lc, res) in enumerate(evs):
            rows.append(
                {
                    "case:concept:name": case,
                    "concept:name": act,
                    "lifecycle:transition": lc,
                    "org:resource": res,
                    "time:timestamp": base + pd.Timedelta(minutes=rid),
                    "_row_id": rid,
                    "_trace_pos": pos,
                }
            )
            rid += 1
    df = pd.DataFrame(rows)
    return StubStore(df.drop(columns=list(drop)))


def F(lc, res=NA, act=FRAUD):
    return (act, lc, res)


# ------------------------------------------------------------------ T04
def test_T04_scheduled_twice_complete_once():
    s = make_store({"c1": [F("schedule", "U01"), F("schedule", "U01"), F("complete", "U01")]})
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert (r15.status, r15.count, r15.case_ids) == ("ok", 0, [])
    assert (r18.status, r18.count, r18.case_ids) == ("ok", 0, [])


# ------------------------------------------------------------------ T05
def test_T05_two_complete_different_resources():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U02")]})
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert r15.case_ids == ["c1"] and r15.count == 1
    assert r18.status == "ok" and r18.count == 0 and r18.case_ids == []


# ------------------------------------------------------------------ T06
def test_T06_two_complete_same_resource():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01")]})
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert r15.case_ids == ["c1"]
    assert r18.case_ids == ["c1"] and r18.count == 1
    ev = r18.evidence
    assert len(ev) == 2 and set(ev["org:resource"]) == {"U01"}
    assert set(ev["resource_complete_count"]) == {2}
    assert set(ev["lifecycle:transition"]) == {"complete"}
    assert ev["_row_id"].is_unique and ev["_trace_pos"].tolist() == sorted(ev["_trace_pos"])


# ------------------------------------------------------------------ T09
@pytest.mark.parametrize("blank", [None, "", "   "])
def test_T09_two_complete_blank_resource(blank):
    s = make_store({"c1": [F("complete", blank), F("complete", blank)]})
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert r15.case_ids == ["c1"]
    assert r18.status == "ok" and r18.count == 0
    assert "tanpa resource valid" in r18.notes


def test_T09_null_and_blank_mixed_are_not_same_resource():
    s = make_store({"c1": [F("complete", None), F("complete", "")]})
    assert run_11_18(s, FRAUD).count == 0


def test_T09_whole_log_blank_resource_warns_loudly():
    s = make_store({"c1": [F("complete", None), F("complete", None)]}, extra_other=False)
    r18 = run_11_18(s, FRAUD)
    assert r18.status == "ok" and r18.count == 0 and "PERINGATAN" in r18.notes


# ------------------------------------------------------------------ T10
@pytest.mark.parametrize("fn", [run_11_15, run_11_18])
def test_T10_lifecycle_column_missing_is_unavailable(fn):
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01")]}, drop=["lifecycle:transition"])
    r = fn(s, FRAUD)
    assert r.status == "unavailable"
    assert r.evidence is None and r.case_ids == []
    assert "lifecycle" in r.notes.lower()


@pytest.mark.parametrize("fn", [run_11_15, run_11_18])
def test_T10_target_events_all_blank_lifecycle_is_unavailable(fn):
    s = make_store({"c1": [F(None, "U01"), F("", "U01")]})
    assert fn(s, FRAUD).status == "unavailable"


# ------------------------------------------------------------------ tambahan
def test_extra_complete_start_complete_different_resource():
    s = make_store({"c1": [F("complete", "U01"), F("start", "U01"), F("complete", "U02")]})
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert r15.case_ids == ["c1"]
    assert set(r15.evidence["lifecycle:transition"]) == {"complete"} and len(r15.evidence) == 2
    assert r18.count == 0


def test_extra_four_complete_two_resources_counts_one_case():
    s = make_store(
        {"c1": [F("complete", "U01"), F("complete", "U02"), F("complete", "U01"), F("complete", "U02")]}
    )
    r15, r18 = run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    assert r15.count == 1 and r15.evidence["complete_count"].eq(4).all()
    assert r18.count == 1 and r18.case_ids == ["c1"]
    assert len(r18.evidence) == 4  # dua grup resource, tetap satu case
    assert set(r18.evidence["org:resource"]) == {"U01", "U02"}


def test_extra_activity_absent_is_not_a_forced_zero():
    s = make_store({"c1": [("O_Accepted", "complete", "U01")]})
    for fn in (run_11_15, run_11_18):
        r = fn(s, FRAUD)
        assert r.status == "unavailable" and "tidak ditemukan" in r.notes
        assert r.denominator == 1


def test_extra_lifecycle_case_and_whitespace_variants():
    s = make_store(
        {"c1": [F("COMPLETE", "U01"), F(" Complete ", "U01")], "c2": [F("completed", "U01"), F("complete", "U01")]}
    )
    r15 = run_11_15(s, FRAUD)
    assert r15.case_ids == ["c1"]  # 'completed' bukan complete
    assert sorted(r15.evidence["lifecycle:transition"]) == [" Complete ", "COMPLETE"]  # nilai asli tampil


def test_extra_complete_value_parameter_is_honoured():
    s = make_store({"c1": [F("done", "U01"), F("done", "U01"), F("complete", "U01")]})
    assert run_11_15(s, FRAUD).count == 0
    r = run_11_15(s, FRAUD, complete_value="DONE")
    assert r.case_ids == ["c1"] and set(r.evidence["lifecycle:transition"]) == {"done"}
    assert "'DONE'" in r.rule_description


def test_extra_exact_name_required_no_silent_substring():
    s = make_store({"c1": [F("complete", "U01", act="W_Assess Potential Fraud")] * 2})
    r = run_11_15(s, FRAUD)  # kapitalisasi berbeda
    assert r.status == "unavailable"
    assert "W_Assess Potential Fraud" in r.notes  # kandidat disebutkan
    assert run_11_15(s, "W_Assess Potential Fraud").count == 1


def test_extra_other_activities_with_complete_are_ignored():
    s = make_store(
        {"c1": [F("complete", "U01"), ("W_Validate application", "complete", "U01"), ("W_Validate application", "complete", "U01")]}
    )
    assert run_11_15(s, FRAUD).count == 0


def test_extra_case_counted_once_and_denominator_is_whole_log():
    s = make_store(
        {
            "c1": [F("complete", "U01")] * 3,
            "c2": [F("complete", "U01"), F("schedule", "U01")],
            "c3": [("O_Accepted", "complete", "U01")],
        }
    )
    r = run_11_15(s, FRAUD)
    assert r.count == 1 and r.denominator == 3
    assert r.evidence["complete_count"].eq(3).all() and len(r.evidence) == 3
    assert run_11_18(s, FRAUD).count == 1


def test_extra_partial_unknown_lifecycle_is_flagged_as_lower_bound():
    s = make_store({"c1": [F("complete", "U01"), F(None, "U01")], "c2": [F("complete", "U01"), F("complete", "U01")]})
    r = run_11_15(s, FRAUD)
    assert r.status == "ok" and r.case_ids == ["c2"]
    assert "BATAS BAWAH" in r.notes and "c1" in r.notes
    strict = run_11_15(s, FRAUD, strict_unknown=True)
    assert strict.status == "unavailable" and strict.evidence is None


def test_extra_partial_unknown_lifecycle_for_11_18():
    s = make_store({"c1": [F("complete", "U01"), F("", "U01")]})
    r = run_11_18(s, FRAUD)
    assert r.count == 0 and "BATAS BAWAH" in r.notes
    assert run_11_18(s, FRAUD, strict_unknown=True).status == "unavailable"


def test_extra_resource_column_absent_only_11_18_unavailable():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01")]}, drop=["org:resource"])
    assert run_11_15(s, FRAUD).count == 1
    r18 = run_11_18(s, FRAUD)
    assert r18.status == "unavailable" and "org:resource" in r18.notes


def test_extra_resource_whitespace_is_stripped_but_case_sensitive():
    s = make_store({"c1": [F("complete", "U01"), F("complete", " U01 ")], "c2": [F("complete", "U01"), F("complete", "u01")]})
    assert run_11_18(s, FRAUD).case_ids == ["c1"]


def test_extra_missing_required_columns_gives_error_not_crash():
    s = make_store({"c1": [F("complete", "U01")] * 2}, drop=["_row_id"])
    assert run_11_15(s, FRAUD).status == "error"
    s2 = make_store({"c1": [F("complete", "U01")]}, drop=["concept:name"])
    assert run_11_15(s2, FRAUD).status == "error"


def test_extra_empty_log():
    s = StubStore(make_store({"c1": [F("complete", "U01")]}).events.iloc[0:0])
    r = run_11_15(s, FRAUD)
    assert r.status == "unavailable" and r.denominator == 0


def test_extra_store_events_not_mutated():
    s = make_store({"c1": [F("complete", " U01 "), F("complete", " U01 ")]})
    before = s.events.copy(deep=True)
    run_11_15(s, FRAUD), run_11_18(s, FRAUD)
    pd.testing.assert_frame_equal(before, s.events)


def test_extra_string_row_ids_are_preserved_in_evidence():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01")]})
    s.events["_row_id"] = [f"event-{index}" for index in range(len(s.events))]

    result = run_11_15(s, FRAUD)

    assert result.evidence["_row_id"].tolist() == ["event-1", "event-2"]


def test_extra_fraud_candidate_listing():
    s = make_store({"c1": [F("complete", "U01"), F("complete", "U01", act="W_Assess Potential Fraud")]})
    assert rw.list_fraud_activities(s.events) == {FRAUD: 1, "W_Assess Potential Fraud": 1}
    assert rw.suggest_fraud_target(s.events) is None  # ambigu -> pengguna harus memilih
    s2 = make_store({"c1": [F("complete", "U01")]})
    assert rw.suggest_fraud_target(s2.events) == FRAUD
