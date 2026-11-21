from collections.abc import Collection

import pandas as pd

from src.core.event_store import (
    CASE_ID_COLUMN,
    REQUIRED_DURATION_COLUMNS,
    TIMESTAMP_COLUMN,
    EventStore,
)

DURATION_COLUMNS = [CASE_ID_COLUMN, "timestamp_min", "timestamp_max", "duration_days"]


def compute_case_durations(events: pd.DataFrame) -> pd.DataFrame:
    required_columns = {CASE_ID_COLUMN, TIMESTAMP_COLUMN}
    missing_columns = required_columns.difference(events.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Event columns are missing: {missing}")
    if events[CASE_ID_COLUMN].isna().any():
        raise ValueError("Case IDs cannot contain null values")
    if events[TIMESTAMP_COLUMN].isna().any():
        raise ValueError("Timestamps cannot contain null values")

    grouped = events.groupby(CASE_ID_COLUMN, sort=False)[TIMESTAMP_COLUMN]
    result = pd.DataFrame(
        {"timestamp_min": grouped.min(), "timestamp_max": grouped.max()}
    ).reset_index()
    result["duration_days"] = (
        result["timestamp_max"] - result["timestamp_min"]
    ).dt.total_seconds() / 86400
    return result[DURATION_COLUMNS]


def get_case_durations(store: EventStore) -> pd.DataFrame:
    durations = store.case_durations
    missing = REQUIRED_DURATION_COLUMNS.difference(durations.columns)
    if missing:
        raise ValueError(f"Case-duration columns are missing: {sorted(missing)}")
    if durations[CASE_ID_COLUMN].isna().any():
        raise ValueError("Case-duration cache contains a null case ID")
    if durations[CASE_ID_COLUMN].duplicated().any():
        raise ValueError("Case-duration cache must contain one row per case")
    if durations["duration_days"].isna().any():
        raise ValueError("Case-duration cache contains an unavailable duration")
    if (durations["duration_days"] < 0).any():
        raise ValueError("Case durations cannot be negative")

    event_case_ids = set(store.events[CASE_ID_COLUMN].tolist())
    duration_case_ids = set(durations[CASE_ID_COLUMN].tolist())
    if event_case_ids != duration_case_ids:
        missing_cases = event_case_ids.difference(duration_case_ids)
        unexpected_cases = duration_case_ids.difference(event_case_ids)
        details = []
        if missing_cases:
            details.append(f"missing={_format_case_ids(missing_cases)}")
        if unexpected_cases:
            details.append(f"unexpected={_format_case_ids(unexpected_cases)}")
        raise ValueError(
            "Case-duration cache does not match active events: " + ", ".join(details)
        )

    return durations


def mean_duration_days(
    durations: pd.DataFrame,
    case_ids: Collection[object] | None = None,
) -> float | None:
    if case_ids is not None:
        durations = durations[durations[CASE_ID_COLUMN].isin(case_ids)]
    if durations.empty:
        return None
    return float(durations["duration_days"].mean())


def _format_case_ids(case_ids: Collection[object]) -> str:
    return "[" + ", ".join(sorted((repr(case_id) for case_id in case_ids))) + "]"
