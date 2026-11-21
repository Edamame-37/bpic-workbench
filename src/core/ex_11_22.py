"""Analisis O_Cancelled yang kemudian diikuti O_Accepted.

count       = case unik dengan O_Cancelled di posisi i dan O_Accepted di j > i
denominator = seluruh case log aktif (sebelum filter)
percentage  = 100 * count / denominator
Analisis level CASE, bukan per offer. Tidak ada angka hard-code.
"""

import pandas as pd

from src.core.event_store import CASE_ID_COLUMN, EventStore
from src.core.ordering import (
    eventually_follows_pairs,
    find_activity_label,
    missing_columns,
)
from src.core.result import AnalysisResult

EXERCISE_ID = "11.22"
CANCELLED = "O_Cancelled"
ACCEPTED = "O_Accepted"

RULE = (
    f"Case dipilih bila ada event {CANCELLED} pada posisi trace i dan event {ACCEPTED} "
    "pada posisi j dengan i < j (eventually follows: tidak harus bersebelahan, tidak "
    "harus offer yang sama, urutan menurut _trace_pos asli XES). Case dihitung sekali. "
    "Persentase = case terpilih / seluruh case log aktif x 100%."
)


def _events(store: EventStore | pd.DataFrame) -> pd.DataFrame:
    return store if isinstance(store, pd.DataFrame) else store.events


def _not_ok(denominator: int, status: str, notes: str) -> AnalysisResult:
    # count=0 hanya placeholder; status != "ok" berarti angka ini BUKAN jawaban.
    return AnalysisResult(
        exercise_id=EXERCISE_ID,
        rule_description=RULE,
        count=0,
        denominator=denominator,
        case_ids=[],
        status=status,
        notes=notes,
    )


def run_11_22(store: EventStore | pd.DataFrame) -> AnalysisResult:
    events = _events(store)

    missing = missing_columns(events)
    if missing:
        return _not_ok(0, "error", f"Kolom wajib tidak ada: {missing}")

    denominator = int(events[CASE_ID_COLUMN].nunique())
    if denominator == 0:
        return _not_ok(
            0, "unavailable",
            "Log kosong: tidak ada case pada dataset aktif, persentase tidak dapat dihitung.",
        )

    cancel_label = find_activity_label(events, CANCELLED)
    accept_label = find_activity_label(events, ACCEPTED)
    not_found = [
        name for name, label in ((CANCELLED, cancel_label), (ACCEPTED, accept_label))
        if label is None
    ]
    if not_found:
        return _not_ok(
            denominator, "unavailable",
            f"Aktivitas target tidak ditemukan pada log aktif: {', '.join(not_found)}.",
        )

    evidence = eventually_follows_pairs(events, cancel_label, accept_label)
    case_ids = evidence["case_id"].tolist()
    count = len(case_ids)
    notes = f"Label dipakai: '{cancel_label}' -> '{accept_label}'."
    if count == 0:
        notes += " Tidak ada case yang memenuhi aturan (hasil 0 yang sah)."

    return AnalysisResult(
        exercise_id=EXERCISE_ID,
        rule_description=RULE,
        count=count,
        denominator=denominator,
        case_ids=case_ids,
        percentage=100.0 * count / denominator,
        evidence=evidence,
        notes=notes,
    )
