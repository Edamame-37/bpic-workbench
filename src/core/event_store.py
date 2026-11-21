"""Shared event-log data contract used by all analysis modules."""

from dataclasses import dataclass
from typing import Final, Mapping

import pandas as pd

CASE_ID_COLUMN: Final = "case:concept:name"
ACTIVITY_COLUMN: Final = "concept:name"
TIMESTAMP_COLUMN: Final = "time:timestamp"
TRACE_POSITION_COLUMN: Final = "_trace_pos"
ROW_ID_COLUMN: Final = "_row_id"

REQUIRED_EVENT_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        CASE_ID_COLUMN,
        ACTIVITY_COLUMN,
        TIMESTAMP_COLUMN,
        TRACE_POSITION_COLUMN,
        ROW_ID_COLUMN,
    }
)

REQUIRED_DURATION_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        CASE_ID_COLUMN,
        "timestamp_min",
        "timestamp_max",
        "duration_days",
    }
)


@dataclass(frozen=True, slots=True)
class EventStore:
    """Validated event log and its reusable per-case metadata.

    The loader owns construction of this object. Analysis modules must reuse the
    same instance and must not parse the XES file independently.
    """

    events: pd.DataFrame
    case_durations: pd.DataFrame
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        self._validate_required_columns()
        self._validate_events()
        self._validate_case_durations()

    def _validate_required_columns(self) -> None:
        missing_event_columns = REQUIRED_EVENT_COLUMNS.difference(self.events.columns)
        if missing_event_columns:
            missing = ", ".join(sorted(missing_event_columns))
            raise ValueError(f"Event columns are missing: {missing}")

        missing_duration_columns = REQUIRED_DURATION_COLUMNS.difference(
            self.case_durations.columns
        )
        if missing_duration_columns:
            missing = ", ".join(sorted(missing_duration_columns))
            raise ValueError(f"Case-duration columns are missing: {missing}")

    def _validate_events(self) -> None:
        for column in (CASE_ID_COLUMN, ACTIVITY_COLUMN, TIMESTAMP_COLUMN):
            if self.events[column].isna().any():
                raise ValueError(f"{column} cannot contain null values")

        if self.events[ROW_ID_COLUMN].isna().any():
            raise ValueError("_row_id cannot contain null values")
        if self.events[ROW_ID_COLUMN].duplicated().any():
            raise ValueError("_row_id must be unique")
        if self.events[TRACE_POSITION_COLUMN].isna().any():
            raise ValueError("_trace_pos cannot contain null values")
        if not pd.api.types.is_integer_dtype(self.events[TRACE_POSITION_COLUMN]):
            raise ValueError("_trace_pos must use an integer dtype")
        if (self.events[TRACE_POSITION_COLUMN] < 0).any():
            raise ValueError("_trace_pos cannot contain negative values")
        if self.events.duplicated(
            subset=[CASE_ID_COLUMN, TRACE_POSITION_COLUMN]
        ).any():
            raise ValueError("_trace_pos must be unique within each case")

    def _validate_case_durations(self) -> None:
        durations = self.case_durations
        if durations[CASE_ID_COLUMN].isna().any():
            raise ValueError("Case-duration cache cannot contain null case IDs")
        if durations[CASE_ID_COLUMN].duplicated().any():
            raise ValueError("Case-duration cache must contain one row per case")
        if durations["duration_days"].isna().any():
            raise ValueError("Case-duration cache cannot contain null durations")
        if (durations["duration_days"] < 0).any():
            raise ValueError("Case-duration cache cannot contain negative durations")

        event_case_ids = set(self.events[CASE_ID_COLUMN].tolist())
        duration_case_ids = set(durations[CASE_ID_COLUMN].tolist())
        if event_case_ids != duration_case_ids:
            raise ValueError("Case-duration cache must match active event cases")

