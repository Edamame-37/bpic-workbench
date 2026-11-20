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
        self._validate_internal_event_identity()

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

    def _validate_internal_event_identity(self) -> None:
        if self.events[ROW_ID_COLUMN].isna().any():
            raise ValueError("_row_id cannot contain null values")
        if self.events[ROW_ID_COLUMN].duplicated().any():
            raise ValueError("_row_id must be unique")
        if self.events[TRACE_POSITION_COLUMN].isna().any():
            raise ValueError("_trace_pos cannot contain null values")

