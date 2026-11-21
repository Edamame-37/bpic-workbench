"""Tests for A5 CSV export schemas and failure handling."""

from pathlib import Path

import pandas as pd
import pytest

from src.core.export import EXPECTED_EXERCISE_IDS, export_results
from src.core.result import AnalysisResult


def _result(
    exercise_id: str,
    *,
    case_ids: list[str] | None = None,
    evidence: pd.DataFrame | None = None,
    status: str = "ok",
    notes: str = "",
) -> AnalysisResult:
    selected = case_ids or []
    return AnalysisResult(
        exercise_id=exercise_id,
        rule_description=f"Rule for {exercise_id}",
        count=len(selected),
        denominator=2,
        case_ids=selected,
        mean_days=1.25 if exercise_id.startswith("11.7") else None,
        percentage=50.0 if exercise_id == "11.22" else None,
        evidence=evidence,
        status=status,
        notes=notes,
    )


def complete_results() -> list[AnalysisResult]:
    event_evidence = pd.DataFrame(
        {
            "case:concept:name": ["0001"],
            "_row_id": ["row-1"],
            "_trace_pos": [0],
            "concept:name": ["O_Accepted"],
            "time:timestamp": [pd.Timestamp("2026-01-01T08:00:00Z")],
        }
    )
    rework_evidence = pd.DataFrame(
        {
            "case_id": ["0001", "0001"],
            "_row_id": ["row-2", "row-3"],
            "_trace_pos": [1, 2],
            "lifecycle:transition": ["complete", "complete"],
            "org:resource": ["U01", "U01"],
        }
    )
    pair_evidence = pd.DataFrame(
        {
            "case_id": ["0001"],
            "cancel_row_id": ["row-4"],
            "cancel_position": [3],
            "cancel_timestamp": [pd.Timestamp("2026-01-01T09:00:00Z")],
            "accept_row_id": ["row-5"],
            "accept_position": [4],
            "accept_timestamp": [pd.Timestamp("2026-01-01T10:00:00Z")],
        }
    )
    evidence_by_id = {
        "11.7 C": event_evidence,
        "11.15": rework_evidence,
        "11.18": rework_evidence,
        "11.22": pair_evidence,
    }
    return [
        _result(
            exercise_id,
            case_ids=["0001"] if exercise_id not in {"11.7 A", "11.7 B"} else ["0001", "0002"],
            evidence=evidence_by_id.get(exercise_id),
        )
        for exercise_id in EXPECTED_EXERCISE_IDS
    ]


def test_export_writes_three_readable_csv_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "folder with spaces"

    paths = export_results(complete_results(), output_dir)

    assert paths.all() == (
        output_dir / "summary.csv",
        output_dir / "selected_cases.csv",
        output_dir / "evidence.csv",
    )
    assert all(path.is_file() for path in paths.all())

    summary = pd.read_csv(paths.summary, dtype={"exercise_id": "string"})
    assert summary["exercise_id"].tolist() == list(EXPECTED_EXERCISE_IDS)
    assert len(summary) == 8
    assert {
        "exercise_id",
        "rule_description",
        "count",
        "denominator",
        "mean_days",
        "percentage",
        "status",
        "notes",
    } == set(summary.columns)

    selected = pd.read_csv(paths.selected_cases, dtype="string")
    assert "0001" in selected["case_id"].tolist()

    evidence = pd.read_csv(paths.evidence, dtype="string")
    assert "0001" in evidence["case_id"].tolist()
    assert {
        "exercise_id",
        "case_id",
        "evidence_type",
        "_row_id",
        "cancel_row_id",
        "accept_row_id",
        "org:resource",
    } <= set(evidence.columns)
    assert set(evidence["evidence_type"]) >= {
        "matching_event",
        "repeated_complete",
        "same_resource_complete",
        "eventually_follows_pair",
    }


def test_unavailable_result_exports_blank_answer_and_reason(tmp_path: Path) -> None:
    results = complete_results()
    results[5] = _result(
        "11.15",
        status="unavailable",
        notes="Lifecycle tidak tersedia.",
    )

    paths = export_results(results, tmp_path)
    summary = pd.read_csv(paths.summary, dtype={"exercise_id": "string"})
    row = summary.loc[summary["exercise_id"] == "11.15"].iloc[0]

    assert row["status"] == "unavailable"
    assert row["notes"] == "Lifecycle tidak tersedia."
    assert pd.isna(row["count"])
    assert row["denominator"] == 2


@pytest.mark.parametrize(
    "mutate, expected_message",
    [
        (lambda results: results[:-1], "Expected exactly eight"),
        (lambda results: [*results, results[0]], "Duplicate exercise"),
    ],
)
def test_export_rejects_incomplete_or_duplicate_results(
    tmp_path: Path,
    mutate,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        export_results(mutate(complete_results()), tmp_path)


def test_export_rejects_destination_that_is_a_file(tmp_path: Path) -> None:
    destination = tmp_path / "not-a-directory"
    destination.write_text("occupied", encoding="utf-8")

    with pytest.raises((FileExistsError, NotADirectoryError)):
        export_results(complete_results(), destination)
