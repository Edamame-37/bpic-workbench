"""Uji urutan Cancel-Accept dan logika trace Penelusuran Kasus."""

import pandas as pd
import pytest

from src.core.cycle_time import compute_case_durations
from src.core.event_store import EventStore
from src.core.ex_11_22 import run_11_22
from src.core.ordering import (
    build_case_index,
    eventually_follows_pairs,
    get_case_trace,
    search_case_ids,
)


def build_store(
    cases: dict[str, list[str]],
    same_timestamp: bool = False,
    shuffle: bool = False,
) -> EventStore:
    """{case_id: [aktivitas sesuai urutan trace]} -> EventStore sintetis."""
    rows, row_id = [], 0
    base = pd.Timestamp("2016-01-01 08:00", tz="UTC")
    for case_id, activities in cases.items():
        for pos, activity in enumerate(activities):
            rows.append({
                "case:concept:name": case_id,
                "concept:name": activity,
                "time:timestamp": base if same_timestamp else base + pd.Timedelta(hours=pos),
                "lifecycle:transition": "complete",
                "org:resource": "U01",
                "_trace_pos": pos,
                "_row_id": row_id,
            })
            row_id += 1
    events = pd.DataFrame(rows)
    if shuffle:
        events = events.sample(frac=1, random_state=7).reset_index(drop=True)
    return EventStore(events, compute_case_durations(events), {"dataset_name": "test"})


def build_empty_store() -> EventStore:
    events = pd.DataFrame({
        "case:concept:name": pd.Series(dtype="object"),
        "concept:name": pd.Series(dtype="object"),
        "time:timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
        "_trace_pos": pd.Series(dtype="int64"),
        "_row_id": pd.Series(dtype="int64"),
    })
    return EventStore(events, compute_case_durations(events), {"dataset_name": "empty"})


def assert_pairs_are_real(store: EventStore, evidence: pd.DataFrame) -> None:
    """Invariant: kedua row ID ada, dari case yang sama, aktivitas benar, i < j."""
    ev = store.events.set_index("_row_id")
    for _, row in evidence.iterrows():
        cancel, accept = ev.loc[row["cancel_row_id"]], ev.loc[row["accept_row_id"]]
        assert cancel["case:concept:name"] == accept["case:concept:name"] == row["case_id"]
        assert cancel["concept:name"] == "O_Cancelled"
        assert accept["concept:name"] == "O_Accepted"
        assert cancel["_trace_pos"] == row["cancel_position"]
        assert accept["_trace_pos"] == row["accept_position"]
        assert row["cancel_position"] < row["accept_position"]


# ---- skenario wajib panduan --------------------------------------------
def test_T07_cancel_other_accept_passes_without_adjacency():
    store = build_store({"c1": ["O_Cancelled", "O_Created", "W_Call", "O_Accepted"]})
    r = run_11_22(store)
    assert r.status == "ok" and r.count == 1 and r.case_ids == ["c1"]
    assert_pairs_are_real(store, r.evidence)


def test_T08_accept_then_cancel_without_later_accept_fails():
    r = run_11_22(build_store({"c1": ["O_Accepted", "O_Cancelled", "A_Pending"]}))
    assert r.status == "ok" and r.count == 0 and r.case_ids == []


def test_T11_identical_timestamps_follow_trace_order_not_row_order():
    store = build_store(
        {"lolos": ["O_Cancelled", "O_Accepted"], "tidak": ["O_Accepted", "O_Cancelled"]},
        same_timestamp=True,
        shuffle=True,
    )
    r = run_11_22(store)
    assert r.case_ids == ["lolos"]
    assert_pairs_are_real(store, r.evidence)


def test_T14_many_pairs_counted_once_with_valid_pair():
    store = build_store({"c1": ["O_Cancelled", "O_Accepted", "O_Cancelled", "O_Accepted"]})
    r = run_11_22(store)
    assert r.count == 1 and len(r.evidence) == 1
    pair = r.evidence.iloc[0]
    assert (pair["cancel_position"], pair["accept_position"]) == (0, 1)
    assert_pairs_are_real(store, r.evidence)


# ---- tambahan dokumen A4 -----------------------------------------------
def test_accept_cancel_accept_passes_via_second_and_third_event():
    store = build_store({"c1": ["O_Accepted", "O_Cancelled", "O_Accepted"]})
    r = run_11_22(store)
    pair = r.evidence.iloc[0]
    assert r.count == 1 and (pair["cancel_position"], pair["accept_position"]) == (1, 2)


def test_pair_uses_first_accept_after_earliest_cancel():
    store = build_store({"c1": ["O_Cancelled", "X", "O_Accepted", "O_Cancelled", "O_Accepted"]})
    pair = run_11_22(store).evidence.iloc[0]
    assert (pair["cancel_position"], pair["accept_position"]) == (0, 2)


def test_cancel_only_does_not_pass():
    store = build_store({"c1": ["O_Cancelled"], "c2": ["O_Accepted"]})
    r = run_11_22(store)
    assert r.status == "ok" and r.count == 0


def test_denominator_is_all_active_cases_and_percentage():
    store = build_store({
        "c1": ["O_Cancelled", "O_Accepted"],
        "c2": ["O_Accepted"],
        "c3": ["A_Create Application"],
        "c4": ["O_Cancelled"],
    })
    r = run_11_22(store)
    assert (r.count, r.denominator) == (1, 4)
    assert r.percentage == pytest.approx(25.0)


def test_T15_empty_log_does_not_divide_by_zero():
    r = run_11_22(build_empty_store())
    assert r.status == "unavailable" and r.percentage is None and "kosong" in r.notes.lower()


def test_missing_target_activity_is_unavailable_not_zero():
    r = run_11_22(build_store({"c1": ["A_Create Application", "O_Cancelled"]}))
    assert r.status == "unavailable" and "O_Accepted" in r.notes and r.percentage is None


def test_shared_synthetic_fixture(synthetic_store):
    r = run_11_22(synthetic_store)
    assert (r.count, r.denominator, r.case_ids) == (1, 2, ["C001"])


def test_evidence_has_export_schema():
    r = run_11_22(build_store({"c1": ["O_Cancelled", "O_Accepted"]}))
    assert list(r.evidence.columns) == [
        "case_id", "cancel_row_id", "cancel_position", "cancel_timestamp",
        "accept_row_id", "accept_position", "accept_timestamp",
    ]


def test_eventually_follows_pairs_empty_when_activity_absent():
    store = build_store({"c1": ["A", "B"]})
    assert eventually_follows_pairs(store.events, "O_Cancelled", "O_Accepted").empty


# ---- Case Explorer core ------------------------------------------------
def test_case_trace_full_and_ordered_with_highlight():
    store = build_store({"c1": ["A_Create", "O_Cancelled", "O_Accepted"], "c2": ["X"]}, shuffle=True)
    r = run_11_22(store)
    pair = r.evidence.iloc[0]
    index = build_case_index(store.events)
    trace = get_case_trace(
        store.events, "c1", [pair["cancel_row_id"], pair["accept_row_id"]], case_index=index
    )
    assert trace["_trace_pos"].tolist() == [0, 1, 2]
    assert trace["_highlight"].tolist() == [False, True, True]


def test_string_row_ids_are_preserved_in_evidence_and_highlights():
    store = build_store({"c1": ["O_Cancelled", "O_Accepted"]})
    events = store.events.copy()
    events["_row_id"] = ["cancel-A", "accept-B"]
    string_id_store = EventStore(events, store.case_durations, store.metadata)

    result = run_11_22(string_id_store)
    trace = get_case_trace(
        string_id_store.events,
        "c1",
        ["cancel-A", "accept-B"],
    )

    assert result.evidence["cancel_row_id"].tolist() == ["cancel-A"]
    assert result.evidence["accept_row_id"].tolist() == ["accept-B"]
    assert trace["_highlight"].tolist() == [True, True]


def test_case_trace_unknown_case_is_empty():
    store = build_store({"c1": ["A"]})
    assert get_case_trace(store.events, "nope", case_index=build_case_index(store.events)).empty


def test_leading_zero_case_ids_are_preserved():
    store = build_store({"007": ["A"], "7": ["B"]})
    index = build_case_index(store.events)
    assert get_case_trace(store.events, "007", case_index=index)["concept:name"].tolist() == ["A"]


def test_search_case_ids_case_insensitive_and_limited():
    ids = ["Application_1", "Application_22", "Other"]
    assert search_case_ids(ids, "application_2") == ["Application_22"]
    assert search_case_ids(ids, "", limit=2) == ["Application_1", "Application_22"]
