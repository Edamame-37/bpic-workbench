"""CSV export for the eight BPIC17 analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

import pandas as pd

from src.core.event_store import CASE_ID_COLUMN
from src.core.result import AnalysisResult

EXPECTED_ANALYSIS_IDS: Final[tuple[str, ...]] = (
    "11.7 A",
    "11.7 B",
    "11.7 C",
    "11.7 D",
    "11.7 E",
    "11.15",
    "11.18",
    "11.22",
)

SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "analysis_id",
    "rule_description",
    "count",
    "denominator",
    "mean_days",
    "percentage",
    "status",
    "notes",
)
SELECTED_CASE_COLUMNS: Final[tuple[str, ...]] = ("analysis_id", "case_id")
EVIDENCE_PREFIX_COLUMNS: Final[tuple[str, ...]] = (
    "analysis_id",
    "case_id",
    "evidence_type",
)


@dataclass(frozen=True, slots=True)
class ExportPaths:
    """Paths created by one successful export operation."""

    summary: Path
    selected_cases: Path
    evidence: Path

    def all(self) -> tuple[Path, Path, Path]:
        return self.summary, self.selected_cases, self.evidence


def _ordered_results(results: Iterable[AnalysisResult]) -> list[AnalysisResult]:
    materialized = list(results)
    by_id: dict[str, AnalysisResult] = {}
    duplicates: set[str] = set()
    for result in materialized:
        if result.exercise_id in by_id:
            duplicates.add(result.exercise_id)
        by_id[result.exercise_id] = result

    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate analysis results: {names}")

    expected = set(EXPECTED_ANALYSIS_IDS)
    actual = set(by_id)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        raise ValueError("Expected exactly eight analysis results: " + "; ".join(details))

    return [by_id[analysis_id] for analysis_id in EXPECTED_ANALYSIS_IDS]


def _summary_frame(results: list[AnalysisResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        available = result.status == "ok"
        rows.append(
            {
                "analysis_id": result.exercise_id,
                "rule_description": result.rule_description,
                "count": result.count if available else "",
                "denominator": result.denominator,
                "mean_days": result.mean_days if available else "",
                "percentage": result.percentage if available else "",
                "status": result.status,
                "notes": result.notes,
            }
        )
    return pd.DataFrame(rows, columns=list(SUMMARY_COLUMNS))


def _selected_cases_frame(results: list[AnalysisResult]) -> pd.DataFrame:
    rows = [
        {"analysis_id": result.exercise_id, "case_id": str(case_id)}
        for result in results
        for case_id in result.case_ids
    ]
    return pd.DataFrame(rows, columns=list(SELECTED_CASE_COLUMNS))


def _evidence_type(analysis_id: str) -> str:
    return {
        "11.7 C": "matching_event",
        "11.7 D": "matching_event",
        "11.7 E": "endpoint_event",
        "11.15": "repeated_complete",
        "11.18": "same_resource_complete",
        "11.22": "eventually_follows_pair",
    }.get(analysis_id, "event")


def _normalise_evidence(result: AnalysisResult) -> pd.DataFrame | None:
    evidence = result.evidence
    if evidence is None or evidence.empty:
        return None

    frame = evidence.copy()
    if "case_id" not in frame.columns and CASE_ID_COLUMN in frame.columns:
        frame = frame.rename(columns={CASE_ID_COLUMN: "case_id"})
    if "case_id" not in frame.columns:
        raise ValueError(
            f"Evidence for {result.exercise_id} does not contain a case identifier"
        )

    frame["case_id"] = frame["case_id"].astype("string")
    frame.insert(0, "analysis_id", result.exercise_id)
    frame.insert(2, "evidence_type", _evidence_type(result.exercise_id))
    return frame


def _evidence_frame(results: list[AnalysisResult]) -> pd.DataFrame:
    frames = [
        frame
        for result in results
        if (frame := _normalise_evidence(result)) is not None
    ]
    if not frames:
        return pd.DataFrame(columns=list(EVIDENCE_PREFIX_COLUMNS))

    combined = pd.concat(frames, ignore_index=True, sort=False)
    remaining = [
        column
        for column in combined.columns
        if column not in EVIDENCE_PREFIX_COLUMNS
    ]
    return combined.loc[:, [*EVIDENCE_PREFIX_COLUMNS, *remaining]]


def export_results(
    results: Iterable[AnalysisResult],
    output_dir: str | Path,
) -> ExportPaths:
    """Write the complete analysis result set to three UTF-8 CSV files."""

    ordered = _ordered_results(results)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if not destination.is_dir():
        raise NotADirectoryError(f"Export destination is not a directory: {destination}")

    paths = ExportPaths(
        summary=destination / "summary.csv",
        selected_cases=destination / "selected_cases.csv",
        evidence=destination / "evidence.csv",
    )
    frames = (
        (_summary_frame(ordered), paths.summary),
        (_selected_cases_frame(ordered), paths.selected_cases),
        (_evidence_frame(ordered), paths.evidence),
    )

    temporary_paths: list[Path] = []
    try:
        for frame, final_path in frames:
            temporary_path = final_path.with_name(f".{final_path.name}.tmp")
            temporary_paths.append(temporary_path)
            frame.to_csv(
                temporary_path,
                index=False,
                encoding="utf-8",
                lineterminator="\n",
            )
        for temporary_path, final_path in zip(
            temporary_paths, paths.all(), strict=True
        ):
            temporary_path.replace(final_path)
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)

    return paths
