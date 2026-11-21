"""A4 - Urutan event (eventually follows) dan penelusuran trace untuk Case Explorer.

Semua urutan memakai ``_trace_pos`` dari loader A1 (urutan asli XES), BUKAN
sorting timestamp, supaya event dengan timestamp identik tetap benar (T11).
"""

from typing import Final

import numpy as np
import pandas as pd

from src.core.event_store import (
    ACTIVITY_COLUMN,
    CASE_ID_COLUMN,
    REQUIRED_EVENT_COLUMNS,
    ROW_ID_COLUMN,
    TIMESTAMP_COLUMN,
    TRACE_POSITION_COLUMN,
)

HIGHLIGHT_COLUMN: Final = "_highlight"

EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "case_id",
    "cancel_row_id",
    "cancel_position",
    "cancel_timestamp",
    "accept_row_id",
    "accept_position",
    "accept_timestamp",
)


def missing_columns(events: pd.DataFrame) -> list[str]:
    """Kolom wajib EventStore yang tidak ada (kosong = aman)."""
    return sorted(REQUIRED_EVENT_COLUMNS.difference(events.columns))


def find_activity_label(events: pd.DataFrame, target: str) -> str | None:
    """Label aktivitas yang benar-benar ada di log.

    Exact match didahulukan; bila tidak ada, dicoba tanpa membedakan huruf besar
    kecil dan spasi tepi. Mengembalikan label ASLI dataset atau ``None``.
    """
    labels = pd.Series(events[ACTIVITY_COLUMN].dropna().unique()).astype(str)
    if (labels == target).any():
        return target
    hits = labels[labels.str.strip().str.casefold() == target.strip().casefold()]
    return str(hits.iloc[0]) if len(hits) else None


def empty_evidence() -> pd.DataFrame:
    return pd.DataFrame(columns=list(EVIDENCE_COLUMNS))


def eventually_follows_pairs(
    events: pd.DataFrame,
    first_activity: str,
    then_activity: str,
) -> pd.DataFrame:
    """Satu pasangan bukti per case untuk aturan "A lalu (kapan pun) B".

    Case lolos bila ada posisi i < j dengan event i = A dan event j = B; tidak
    harus bersebelahan dan tidak melihat offer ID. Pasangan bukti: A paling awal
    dan B PERTAMA setelah A tersebut. Bila ada B setelah A mana pun, pasti ada B
    setelah A paling awal, jadi pemilihan ini tidak melewatkan case.
    """
    cols = [CASE_ID_COLUMN, TRACE_POSITION_COLUMN, ROW_ID_COLUMN, TIMESTAMP_COLUMN]
    a = events.loc[events[ACTIVITY_COLUMN] == first_activity, cols]
    b = events.loc[events[ACTIVITY_COLUMN] == then_activity, cols]
    if a.empty or b.empty:
        return empty_evidence()

    first_a = a.loc[a.groupby(CASE_ID_COLUMN, sort=False)[TRACE_POSITION_COLUMN].idxmin()]
    joined = b.merge(first_a, on=CASE_ID_COLUMN, suffixes=("_b", "_a"))
    joined = joined[joined[f"{TRACE_POSITION_COLUMN}_b"] > joined[f"{TRACE_POSITION_COLUMN}_a"]]
    if joined.empty:
        return empty_evidence()
    chosen = joined.loc[
        joined.groupby(CASE_ID_COLUMN, sort=False)[f"{TRACE_POSITION_COLUMN}_b"].idxmin()
    ]

    evidence = pd.DataFrame(
        {
            "case_id": chosen[CASE_ID_COLUMN].astype(str),
            "cancel_row_id": chosen[f"{ROW_ID_COLUMN}_a"],
            "cancel_position": chosen[f"{TRACE_POSITION_COLUMN}_a"].astype("int64"),
            "cancel_timestamp": chosen[f"{TIMESTAMP_COLUMN}_a"],
            "accept_row_id": chosen[f"{ROW_ID_COLUMN}_b"],
            "accept_position": chosen[f"{TRACE_POSITION_COLUMN}_b"].astype("int64"),
            "accept_timestamp": chosen[f"{TIMESTAMP_COLUMN}_b"],
        }
    )
    return evidence.sort_values("case_id", kind="stable").reset_index(drop=True)


def build_case_index(events: pd.DataFrame) -> dict[str, np.ndarray]:
    """Peta case_id (string asli, leading zero dipertahankan) -> posisi baris.

    Dibuat sekali per dataset agar membuka case tidak memindai 1 juta+ baris.
    """
    keys = events[CASE_ID_COLUMN].astype(str)
    return {str(k): v for k, v in keys.groupby(keys, sort=False).indices.items()}


def get_case_trace(
    events: pd.DataFrame,
    case_id: str,
    highlight_row_ids: list[object] | set[object] | None = None,
    case_index: dict[str, np.ndarray] | None = None,
) -> pd.DataFrame:
    """Seluruh event satu case, urut ``_trace_pos``, plus kolom ``_highlight``.

    DataFrame kosong bila case tidak ditemukan.
    """
    key = str(case_id)
    if case_index is not None:
        positions = case_index.get(key)
        trace = events.iloc[positions] if positions is not None else events.iloc[0:0]
    else:
        trace = events[events[CASE_ID_COLUMN].astype(str) == key]
    trace = trace.sort_values(TRACE_POSITION_COLUMN, kind="stable").reset_index(drop=True)
    wanted = set(highlight_row_ids or [])
    trace[HIGHLIGHT_COLUMN] = trace[ROW_ID_COLUMN].isin(wanted)
    return trace


def search_case_ids(case_ids: list[str], query: str, limit: int = 500) -> list[str]:
    """Case ID yang mengandung teks query (tanpa membedakan huruf besar kecil)."""
    needle = query.strip().casefold()
    if not needle:
        return case_ids[:limit]
    out: list[str] = []
    for cid in case_ids:
        if needle in cid.casefold():
            out.append(cid)
            if len(out) >= limit:
                break
    return out
