"""Shared result contract for exercise panels and CSV export."""

from dataclasses import dataclass
from typing import Final, Literal

import pandas as pd

AnalysisStatus = Literal["ok", "unavailable", "error"]
VALID_STATUSES: Final = frozenset({"ok", "unavailable", "error"})


@dataclass(slots=True)
class AnalysisResult:
    """Result of one BPIC17 exercise evaluated against the active log."""

    exercise_id: str
    rule_description: str
    count: int
    denominator: int
    case_ids: list[str]
    mean_days: float | None = None
    percentage: float | None = None
    evidence: pd.DataFrame | None = None
    status: AnalysisStatus = "ok"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Unsupported analysis status: {self.status}")
        if self.count < 0 or self.denominator < 0:
            raise ValueError("count and denominator cannot be negative")
        if self.count > self.denominator:
            raise ValueError("count cannot exceed denominator")

        unique_case_count = len(set(self.case_ids))
        if self.status == "ok" and self.count != unique_case_count:
            raise ValueError("For status='ok', count must equal unique case IDs")

