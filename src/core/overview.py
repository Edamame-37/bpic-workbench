"""Overview service summarizing the active EventStore (Anggota 1)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from src.core.cycle_time import get_case_durations, mean_duration_days
from src.core.event_store import ACTIVITY_COLUMN, TIMESTAMP_COLUMN, EventStore


@dataclass(frozen=True, slots=True)
class OverviewSummary:
    """Dataset-level KPIs, activity frequencies, date range, and case durations."""

    total_cases: int
    total_events: int
    total_activities: int
    activity_frequencies: pd.DataFrame
    timestamp_min: pd.Timestamp | None
    timestamp_max: pd.Timestamp | None
    mean_cycle_time_days: float | None
    case_durations: pd.DataFrame
    metadata: Mapping[str, object]
    status: str = "ok"
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "total_events": self.total_events,
            "total_activities": self.total_activities,
            "activity_frequencies": self.activity_frequencies,
            "timestamp_min": self.timestamp_min,
            "timestamp_max": self.timestamp_max,
            "mean_cycle_time_days": self.mean_cycle_time_days,
            "case_durations": self.case_durations,
            "metadata": dict(self.metadata),
            "status": self.status,
            "warnings": list(self.warnings),
        }


def get_overview(store: EventStore) -> OverviewSummary:
    """Compute overview KPIs, activity counts, and case durations from EventStore."""
    events = store.events
    durations = get_case_durations(store)

    total_cases = int(len(durations))
    total_events = int(len(events))

    if total_events == 0 or total_cases == 0:
        empty_activities = pd.DataFrame(
            {
                "activity": pd.Series(dtype="object"),
                "count": pd.Series(dtype="int64"),
                "percentage": pd.Series(dtype="float64"),
            }
        )
        raw_warnings = store.metadata.get("warnings", ())
        warnings = (
            tuple(str(w) for w in raw_warnings)
            if isinstance(raw_warnings, (list, tuple))
            else ()
        )
        if not warnings:
            warnings = ("Log kosong: tidak ada case atau event pada dataset aktif.",)
        return OverviewSummary(
            total_cases=0,
            total_events=0,
            total_activities=0,
            activity_frequencies=empty_activities,
            timestamp_min=None,
            timestamp_max=None,
            mean_cycle_time_days=None,
            case_durations=durations,
            metadata=store.metadata,
            status="empty",
            warnings=warnings,
        )

    counts = events[ACTIVITY_COLUMN].value_counts()
    activity_df = pd.DataFrame(
        {
            "activity": [str(name) for name in counts.index],
            "count": counts.to_numpy(dtype="int64"),
        }
    )
    activity_df["percentage"] = (activity_df["count"] / float(total_events)) * 100.0
    activity_df = activity_df.sort_values(
        by=["count", "activity"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)

    timestamp_min = events[TIMESTAMP_COLUMN].min()
    timestamp_max = events[TIMESTAMP_COLUMN].max()
    mean_cycle_time = mean_duration_days(durations)

    raw_warnings = store.metadata.get("warnings", ())
    warnings = (
        tuple(str(w) for w in raw_warnings)
        if isinstance(raw_warnings, (list, tuple))
        else ()
    )

    return OverviewSummary(
        total_cases=total_cases,
        total_events=total_events,
        total_activities=int(len(activity_df)),
        activity_frequencies=activity_df,
        timestamp_min=timestamp_min,
        timestamp_max=timestamp_max,
        mean_cycle_time_days=mean_cycle_time,
        case_durations=durations,
        metadata=store.metadata,
        status="ok",
        warnings=warnings,
    )
