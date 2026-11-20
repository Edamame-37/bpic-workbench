"""Synthetic event data that follows the shared EventStore schema."""

from collections.abc import Mapping

import pandas as pd

from src.core.event_store import EventStore


def build_synthetic_store(
    metadata: Mapping[str, object] | None = None,
) -> EventStore:
    """Build a small store with stable trace order and equal timestamps."""

    shared_timestamp = pd.Timestamp("2026-01-01T08:00:00Z")
    events = pd.DataFrame(
        [
            {
                "case:concept:name": "C001",
                "concept:name": "O_Cancelled",
                "time:timestamp": shared_timestamp,
                "lifecycle:transition": "complete",
                "org:resource": "U01",
                "_trace_pos": 0,
                "_row_id": 0,
            },
            {
                "case:concept:name": "C001",
                "concept:name": "O_Accepted",
                "time:timestamp": shared_timestamp,
                "lifecycle:transition": "complete",
                "org:resource": "U01",
                "_trace_pos": 1,
                "_row_id": 1,
            },
            {
                "case:concept:name": "C002",
                "concept:name": "O_Refused",
                "time:timestamp": pd.Timestamp("2026-01-03T08:00:00Z"),
                "lifecycle:transition": "complete",
                "org:resource": "U02",
                "_trace_pos": 0,
                "_row_id": 2,
            },
        ]
    )

    case_durations = pd.DataFrame(
        [
            {
                "case:concept:name": "C001",
                "timestamp_min": shared_timestamp,
                "timestamp_max": shared_timestamp,
                "duration_days": 0.0,
            },
            {
                "case:concept:name": "C002",
                "timestamp_min": pd.Timestamp("2026-01-03T08:00:00Z"),
                "timestamp_max": pd.Timestamp("2026-01-03T08:00:00Z"),
                "duration_days": 0.0,
            },
        ]
    )

    store_metadata = {
        "dataset_name": "synthetic",
        "event_count": 3,
        "case_count": 2,
    }
    if metadata is not None:
        store_metadata.update(metadata)

    return EventStore(
        events=events,
        case_durations=case_durations,
        metadata=store_metadata,
    )

