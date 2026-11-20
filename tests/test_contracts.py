"""Tests for the shared D1 data contracts."""

import pandas as pd
import pytest

from src.core.event_store import EventStore
from src.core.result import AnalysisResult


def test_event_store_preserves_original_trace_position(
    synthetic_store: EventStore,
) -> None:
    first_case = synthetic_store.events.loc[
        synthetic_store.events["case:concept:name"] == "C001"
    ]

    assert first_case["time:timestamp"].nunique() == 1
    assert first_case["_trace_pos"].tolist() == [0, 1]
    assert first_case["concept:name"].tolist() == ["O_Cancelled", "O_Accepted"]


def test_event_store_rejects_duplicate_row_ids(synthetic_store: EventStore) -> None:
    invalid_events = synthetic_store.events.copy()
    invalid_events.loc[1, "_row_id"] = 0

    with pytest.raises(ValueError, match="_row_id must be unique"):
        EventStore(
            events=invalid_events,
            case_durations=synthetic_store.case_durations,
            metadata=synthetic_store.metadata,
        )


def test_analysis_result_accepts_unique_case_count() -> None:
    result = AnalysisResult(
        exercise_id="11.22",
        rule_description="Synthetic rule",
        count=1,
        denominator=2,
        case_ids=["C001"],
        percentage=50.0,
        evidence=pd.DataFrame({"case_id": ["C001"]}),
    )

    assert result.status == "ok"
    assert result.count == len(result.case_ids)


def test_analysis_result_distinguishes_unavailable_from_valid_zero() -> None:
    result = AnalysisResult(
        exercise_id="11.15",
        rule_description="Requires verified lifecycle",
        count=0,
        denominator=2,
        case_ids=[],
        status="unavailable",
        notes="lifecycle:transition is missing",
    )

    assert result.status == "unavailable"
    assert result.notes


def test_analysis_result_rejects_inconsistent_ok_count() -> None:
    with pytest.raises(ValueError, match="count must equal unique case IDs"):
        AnalysisResult(
            exercise_id="11.7 C",
            rule_description="Contains O_Accepted",
            count=2,
            denominator=2,
            case_ids=["C001"],
        )

