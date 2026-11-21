import pandas as pd

from src.core.cycle_time import get_case_durations, mean_duration_days
from src.core.event_store import (
    ACTIVITY_COLUMN,
    CASE_ID_COLUMN,
    ROW_ID_COLUMN,
    TIMESTAMP_COLUMN,
    TRACE_POSITION_COLUMN,
    EventStore,
)
from src.core.result import AnalysisResult

ACCEPTED = "O_Accepted"
REFUSED = "O_Refused"
CANCELLED = "O_Cancelled"

EMPTY_LOG_NOTE = "Log kosong: tidak ada case pada dataset aktif, hasil tidak dapat dihitung."

OPTIONAL_EVIDENCE_COLUMNS = ("lifecycle:transition", "org:resource")


def _evidence(events: pd.DataFrame) -> pd.DataFrame:
    columns = [
        ROW_ID_COLUMN, CASE_ID_COLUMN, TRACE_POSITION_COLUMN,
        ACTIVITY_COLUMN, TIMESTAMP_COLUMN,
    ] + [c for c in OPTIONAL_EVIDENCE_COLUMNS if c in events.columns]
    return events[columns].sort_values([CASE_ID_COLUMN, TRACE_POSITION_COLUMN]).reset_index(drop=True)


def _selected(exercise_id, rule, case_ids, durations, evidence=None) -> AnalysisResult:
    ids = sorted(set(case_ids))
    return AnalysisResult(
        exercise_id=exercise_id,
        rule_description=rule,
        count=len(ids),
        denominator=len(durations),
        case_ids=ids,
        mean_days=mean_duration_days(durations, set(ids)),
        evidence=evidence,
        notes="" if ids else "Tidak ada case yang memenuhi aturan (mean = N/A).",
    )


def _contains(events: pd.DataFrame, activity: str) -> pd.DataFrame:
    return events[events[ACTIVITY_COLUMN] == activity]


def _last_events(events: pd.DataFrame) -> pd.DataFrame:
    ordered = events.sort_values([CASE_ID_COLUMN, TRACE_POSITION_COLUMN, ROW_ID_COLUMN], kind="stable")
    return ordered.groupby(CASE_ID_COLUMN, sort=False).tail(1)


def run_11_7(store: EventStore) -> list[AnalysisResult]:
    events = store.events
    durations = get_case_durations(store)
    all_ids = durations[CASE_ID_COLUMN].tolist()

    result_a = AnalysisResult(
        exercise_id="11.7 A",
        rule_description="Jumlah case unik pada seluruh log aktif",
        count=len(all_ids), denominator=len(all_ids), case_ids=sorted(set(all_ids)),
    )
    result_b = _selected(
        "11.7 B",
        "Mean (timestamp event terakhir - event pertama) seluruh case, satuan hari",
        all_ids, durations,
    )

    accepted = _contains(events, ACCEPTED)
    refused = _contains(events, REFUSED)
    last = _last_events(events)
    canceled = last[last[ACTIVITY_COLUMN] == CANCELLED]

    results = [
        result_a,
        result_b,
        _selected("11.7 C", f"Successful: case mengandung >= 1 event {ACCEPTED} (case dihitung 1x)",
                  accepted[CASE_ID_COLUMN], durations, _evidence(accepted)),
        _selected("11.7 D", f"Unsuccessful: case mengandung >= 1 event {REFUSED} (boleh overlap dengan C)",
                  refused[CASE_ID_COLUMN], durations, _evidence(refused)),
        _selected("11.7 E", f"Canceled: event TERAKHIR (_trace_pos terbesar) adalah {CANCELLED}",
                  canceled[CASE_ID_COLUMN], durations, _evidence(canceled)),
    ]
    if not all_ids:  
        for item in results:
            item.status = "unavailable"
            item.notes = EMPTY_LOG_NOTE
    return results