import pandas as pd

from src.core.event_store import (
    CASE_ID_COLUMN,
    REQUIRED_DURATION_COLUMNS,
    TIMESTAMP_COLUMN,
    EventStore,
)

DURATION_COLUMNS = [CASE_ID_COLUMN, "timestamp_min", "timestamp_max", "duration_days"]


def compute_case_durations(events: pd.DataFrame) -> pd.DataFrame:
    grouped = events.groupby(CASE_ID_COLUMN, sort=True)[TIMESTAMP_COLUMN]
    result = pd.DataFrame(
        {"timestamp_min": grouped.min(), "timestamp_max": grouped.max()}
    ).reset_index()
    result["duration_days"] = (
        result["timestamp_max"] - result["timestamp_min"]
    ).dt.total_seconds() / 86400
    return result[DURATION_COLUMNS]


def get_case_durations(store: EventStore) -> pd.DataFrame:
    missing = REQUIRED_DURATION_COLUMNS.difference(store.case_durations.columns)
    if missing:
        raise ValueError(f"Case-duration columns are missing: {sorted(missing)}")
    return store.case_durations


def mean_duration_days(durations: pd.DataFrame, case_ids: set | None = None) -> float | None:
    if case_ids is not None:
        durations = durations[durations[CASE_ID_COLUMN].isin(case_ids)]
    if durations.empty:
        return None
    return float(durations["duration_days"].mean())