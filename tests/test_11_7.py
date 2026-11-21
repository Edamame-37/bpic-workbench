import pandas as pd
import pytest

from src.core.cycle_time import compute_case_durations, get_case_durations
from src.core.event_store import EventStore
from src.core.ex_11_7 import run_11_7


def build_store(cases: dict[str, list[tuple[str, str]]]) -> EventStore:
    rows, row_id = [], 0
    for case_id, trace in cases.items():
        for pos, (activity, ts) in enumerate(trace):
            rows.append({
                "case:concept:name": case_id, "concept:name": activity,
                "time:timestamp": pd.Timestamp(ts, tz="UTC"),
                "lifecycle:transition": "complete", "org:resource": "U01",
                "_trace_pos": pos, "_row_id": row_id,
            })
            row_id += 1
    events = pd.DataFrame(rows)
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


def by_id(results):
    return {r.exercise_id: r for r in results}


def test_T01_accepted_twice_counts_one_case():
    store = build_store({"c1": [("O_Accepted", "2024-01-01 10:00"), ("O_Accepted", "2024-01-02 10:00")]})
    r = by_id(run_11_7(store))["11.7 C"]
    assert r.count == 1 and r.case_ids == ["c1"]
    assert len(r.evidence) == 1


def test_T02_cancelled_in_middle_is_not_canceled_case():
    store = build_store({"c1": [("O_Cancelled", "2024-01-01 10:00"), ("A_Other", "2024-01-02 10:00")]})
    assert by_id(run_11_7(store))["11.7 E"].count == 0


def test_E_last_event_cancelled():
    store = build_store({"c1": [("A_Other", "2024-01-01 10:00"), ("O_Cancelled", "2024-01-02 10:00")]})
    r = by_id(run_11_7(store))["11.7 E"]
    assert r.case_ids == ["c1"] and r.evidence["_trace_pos"].tolist() == [1]


def test_T03_refused_and_accepted_in_both_groups():
    store = build_store({"c1": [("O_Refused", "2024-01-01 10:00"), ("O_Accepted", "2024-01-02 10:00")]})
    res = by_id(run_11_7(store))
    assert res["11.7 C"].case_ids == ["c1"] and res["11.7 D"].case_ids == ["c1"]


def test_T12_single_event_case_has_zero_duration():
    store = build_store({"c1": [("A_Other", "2024-01-01 10:00")]})
    assert get_case_durations(store)["duration_days"].tolist() == [0.0]


def test_A_and_B_values():
    store = build_store({
        "c1": [("A", "2024-01-01 00:00"), ("B", "2024-01-03 12:00")],  # 2.5 hari
        "c2": [("A", "2024-02-01 00:00"), ("B", "2024-02-02 00:00")],  # 1.0 hari
    })
    res = by_id(run_11_7(store))
    assert res["11.7 A"].count == 2 and res["11.7 A"].denominator == 2
    assert res["11.7 B"].mean_days == pytest.approx(1.75)


def test_mean_uses_full_trace_not_target_activity():
    store = build_store({"c1": [("A", "2024-01-01 00:00"), ("O_Accepted", "2024-01-02 00:00"),
                                ("Z", "2024-01-05 00:00")]})
    assert by_id(run_11_7(store))["11.7 C"].mean_days == pytest.approx(4.0)


def test_empty_group_gives_zero_and_none():
    store = build_store({"c1": [("A", "2024-01-01 10:00")]})
    r = by_id(run_11_7(store))["11.7 C"]
    assert r.count == 0 and r.mean_days is None and r.status == "ok" and r.notes


def test_T11_same_timestamp_follows_trace_pos_not_alphabetical():
    t = "2024-01-01 10:00"
    cancelled_last = build_store({"c1": [("O_Accepted", t), ("O_Cancelled", t)]})
    cancelled_first = build_store({"c1": [("O_Cancelled", t), ("O_Accepted", t)]})
    assert by_id(run_11_7(cancelled_last))["11.7 E"].count == 1
    assert by_id(run_11_7(cancelled_first))["11.7 E"].count == 0


def test_endpoint_uses_trace_position_when_dataframe_rows_are_shuffled():
    store = build_store({
        "c1": [
            ("O_Accepted", "2024-01-01 10:00"),
            ("O_Cancelled", "2024-01-01 10:00"),
        ]
    })
    shuffled_events = store.events.iloc[::-1].reset_index(drop=True)
    shuffled_store = EventStore(
        shuffled_events,
        store.case_durations,
        store.metadata,
    )

    result = by_id(run_11_7(shuffled_store))["11.7 E"]

    assert result.case_ids == ["c1"]
    assert result.evidence["_trace_pos"].tolist() == [1]


def test_timezone_aware_duration_is_not_shifted():
    events = pd.DataFrame([
        {"case:concept:name": "c1", "concept:name": "A", "_trace_pos": 0, "_row_id": 0,
         "time:timestamp": pd.Timestamp("2024-03-30 23:00", tz="UTC")},
        {"case:concept:name": "c1", "concept:name": "B", "_trace_pos": 1, "_row_id": 1,
         "time:timestamp": pd.Timestamp("2024-03-31 23:00", tz="UTC")},
    ])
    assert compute_case_durations(events)["duration_days"].iloc[0] == pytest.approx(1.0)


def test_loader_and_store_durations_agree(synthetic_store):
    recomputed = compute_case_durations(synthetic_store.events)
    pd.testing.assert_frame_equal(
        recomputed.reset_index(drop=True),
        get_case_durations(synthetic_store).reset_index(drop=True),
    )


def test_duration_cache_rejects_duplicate_case_rows():
    store = build_store({"c1": [("A", "2024-01-01 10:00")]})
    duplicated_durations = pd.concat(
        [store.case_durations, store.case_durations], ignore_index=True
    )
    with pytest.raises(ValueError, match="one row per case"):
        EventStore(store.events, duplicated_durations, store.metadata)


def test_duration_cache_must_match_active_event_cases():
    store = build_store({
        "c1": [("A", "2024-01-01 10:00")],
        "c2": [("B", "2024-01-02 10:00")],
    })
    incomplete_durations = store.case_durations.iloc[[0]].reset_index(drop=True)
    with pytest.raises(ValueError, match="match active event cases"):
        EventStore(store.events, incomplete_durations, store.metadata)


def test_contains_evidence_keeps_one_event_per_selected_case():
    store = build_store({
        "c1": [
            ("O_Accepted", "2024-01-01 10:00"),
            ("O_Accepted", "2024-01-02 10:00"),
        ],
        "c2": [
            ("O_Accepted", "2024-01-03 10:00"),
            ("O_Accepted", "2024-01-04 10:00"),
        ],
    })

    result = by_id(run_11_7(store))["11.7 C"]

    assert result.count == 2
    assert len(result.evidence) == 2
    assert result.evidence["case:concept:name"].is_unique


def test_run_does_not_mutate_events():
    store = build_store({"c1": [("O_Accepted", "2024-01-01 10:00"), ("Z", "2024-01-02 10:00")]})
    before = store.events.copy()
    run_11_7(store)
    pd.testing.assert_frame_equal(store.events, before)


def test_T15_empty_log_is_unavailable_not_valid_zero():
    results = run_11_7(build_empty_store())
    assert [r.status for r in results] == ["unavailable"] * 5
    assert all(r.count == 0 and r.denominator == 0 and r.mean_days is None for r in results)
    assert all("kosong" in r.notes.lower() for r in results)


def test_event_only_log_has_five_results_in_order():
    store = build_store({"c1": [("A", "2024-01-01 10:00")]})
    assert [r.exercise_id for r in run_11_7(store)] == [
        "11.7 A", "11.7 B", "11.7 C", "11.7 D", "11.7 E"]
