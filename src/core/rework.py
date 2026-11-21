"""A3 - Rework analytics: aktivitas target, filter complete-only, repeat per case/resource.

Fungsi di modul ini bekerja pada DataFrame event (``store.events``) dan TIDAK
mengubahnya. Semua keputusan "tidak terbukti" dikembalikan eksplisit
(status ``unavailable``/``error``), bukan sebagai count nol.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

CASE_COL = "case:concept:name"
ACT_COL = "concept:name"
TS_COL = "time:timestamp"
LIFECYCLE_COL = "lifecycle:transition"
RESOURCE_COL = "org:resource"
ROW_ID_COL = "_row_id"
TRACE_POS_COL = "_trace_pos"

DEFAULT_COMPLETE_VALUE = "complete"
MIN_COMPLETE = 2 
_EVIDENCE_REQUIRED = (ROW_ID_COL, TRACE_POS_COL, TS_COL)


# --------------------------------------------------------------------------
# Normalisasi
# --------------------------------------------------------------------------
def normalize_lifecycle(series: pd.Series) -> pd.Series:
    """strip().casefold(); null / string kosong menjadi <NA> (= tidak diketahui)."""
    s = series.astype("string").str.strip().str.casefold()
    return s.mask(s.fillna("x").eq(""))


def normalize_resource(series: pd.Series) -> pd.Series:
    """strip() saja (ID resource peka kapital); null / kosong menjadi <NA>."""
    s = series.astype("string").str.strip()
    return s.mask(s.fillna("x").eq(""))


# --------------------------------------------------------------------------
# Pencarian aktivitas target
# --------------------------------------------------------------------------
def list_fraud_activities(events: pd.DataFrame, keyword: str = "fraud") -> dict[str, int]:
    """Nama aktivitas unik (string asli) yang memuat ``keyword`` -> jumlah baris event."""
    if ACT_COL not in events.columns:
        return {}
    names = events[ACT_COL].dropna().astype(str)
    hit = names[names.str.casefold().str.contains(keyword.casefold(), regex=False)]
    return {str(k): int(v) for k, v in hit.value_counts().sort_index().items()}


def suggest_fraud_target(events: pd.DataFrame) -> str | None:
    """Nama target hanya jika kandidatnya TEPAT satu; selain itu None (pengguna harus memilih)."""
    candidates = list_fraud_activities(events)
    return next(iter(candidates)) if len(candidates) == 1 else None


# --------------------------------------------------------------------------
# Seleksi event complete
# --------------------------------------------------------------------------
@dataclass
class CompleteSelection:
    status: str  # ok / unavailable / error
    reason: str = ""
    target: str = ""
    complete_value: str = DEFAULT_COMPLETE_VALUE
    complete: pd.DataFrame = field(default_factory=pd.DataFrame)  # event target terverifikasi complete
    unknown: pd.DataFrame = field(default_factory=pd.DataFrame)  # event target tanpa lifecycle
    target_rows: int = 0
    lifecycle_values: dict[str, int] = field(default_factory=dict)  # nilai ASLI, termasuk <kosong>


def _fail(status: str, reason: str, target: str, cv: str) -> CompleteSelection:
    return CompleteSelection(status=status, reason=reason, target=target, complete_value=cv)


def select_complete_events(
    events: pd.DataFrame,
    activity_name: str,
    complete_value: str = DEFAULT_COMPLETE_VALUE,
) -> CompleteSelection:
    """Event dengan concept:name == activity_name (EXACT) dan lifecycle == complete_value.

    ``complete_value`` benar-benar dipakai (dinormalisasi strip+casefold seperti data).
    """
    target = "" if activity_name is None else str(activity_name)
    missing = [c for c in (CASE_COL, ACT_COL) if c not in events.columns]
    if missing:
        return _fail("error", f"Kolom wajib tidak ada pada EventStore: {missing}", target, complete_value)
    if events[CASE_COL].nunique() == 0:
        return _fail("unavailable", "Event log kosong (tidak ada case).", target, complete_value)
    if not target.strip():
        return _fail("unavailable", "Nama aktivitas target belum dipilih.", target, complete_value)

    wanted = normalize_lifecycle(pd.Series([complete_value])).iloc[0]
    if pd.isna(wanted):
        return _fail("error", "complete_value kosong.", target, complete_value)

    tmask = events[ACT_COL].eq(target).fillna(False).astype(bool).to_numpy()
    if not tmask.any():
        cands = list_fraud_activities(events)
        hint = f" Kandidat bernama 'fraud' di data: {cands}." if cands else " Tidak ada aktivitas bernama 'fraud'."
        return _fail(
            "unavailable",
            f"Aktivitas '{target}' tidak ditemukan (pencocokan exact pada concept:name).{hint}",
            target,
            complete_value,
        )
    if LIFECYCLE_COL not in events.columns:
        return _fail(
            "unavailable",
            "Kolom lifecycle:transition tidak ada; kejadian complete tidak dapat dibuktikan.",
            target,
            complete_value,
        )
    missing_ev = [c for c in _EVIDENCE_REQUIRED if c not in events.columns]
    if missing_ev:
        return _fail("error", f"Kolom evidence wajib tidak ada: {missing_ev}", target, complete_value)

    rows = events.loc[tmask]
    lc = normalize_lifecycle(rows[LIFECYCLE_COL])
    unknown_mask = lc.isna().to_numpy()
    if unknown_mask.all():
        return _fail(
            "unavailable",
            f"Seluruh {len(rows)} event '{target}' tidak memiliki nilai lifecycle:transition.",
            target,
            complete_value,
        )
    complete_mask = lc.eq(wanted).fillna(False).astype(bool).to_numpy()
    raw_values = rows[LIFECYCLE_COL].astype("string").fillna("<kosong>").value_counts()
    return CompleteSelection(
        status="ok",
        target=target,
        complete_value=complete_value,
        complete=rows.loc[complete_mask],
        unknown=rows.loc[unknown_mask],
        target_rows=len(rows),
        lifecycle_values={str(k): int(v) for k, v in raw_values.items()},
    )


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------
def _evidence_frame(rows: pd.DataFrame, extra: dict[str, object] | None = None) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "case_id": rows[CASE_COL].astype(str).to_numpy(),
            RESOURCE_COL: (rows[RESOURCE_COL].to_numpy() if RESOURCE_COL in rows.columns else pd.NA),
            ROW_ID_COL: rows[ROW_ID_COL].to_numpy(),
            TRACE_POS_COL: rows[TRACE_POS_COL].to_numpy(),
            ACT_COL: rows[ACT_COL].to_numpy(),
            LIFECYCLE_COL: rows[LIFECYCLE_COL].to_numpy(),  # nilai ASLI dari data
            TS_COL: rows[TS_COL].to_numpy(),
        }
    )
    for name, values in (extra or {}).items():
        out[name] = values
    return out.sort_values(["case_id", TRACE_POS_COL], kind="stable").reset_index(drop=True)


# --------------------------------------------------------------------------
# 11.15 - repeated complete
# --------------------------------------------------------------------------
@dataclass
class RepeatOutcome:
    counts: pd.Series
    case_ids: list[str]
    evidence: pd.DataFrame
    undetermined_case_ids: list[str] = field(default_factory=list)


def repeated_complete(sel: CompleteSelection, min_count: int = MIN_COMPLETE) -> RepeatOutcome:
    """Case dengan >= min_count event complete aktivitas target."""
    comp = sel.complete
    counts = comp.groupby(CASE_COL, observed=True).size() if len(comp) else pd.Series(dtype="int64")
    chosen = counts[counts >= min_count]
    ev_rows = comp[comp[CASE_COL].isin(chosen.index)]
    evidence = _evidence_frame(ev_rows, {"complete_count": ev_rows[CASE_COL].map(chosen).astype(int).to_numpy()})
    case_ids = sorted({str(c) for c in chosen.index})

    # case yang BELUM terbukti: complete + (lifecycle tak diketahui) >= min tetapi complete < min
    undetermined: list[str] = []
    if len(sel.unknown):
        unk = sel.unknown.groupby(CASE_COL, observed=True).size()
        for case, n_unk in unk.items():
            n_c = int(counts.get(case, 0))
            if n_c < min_count <= n_c + int(n_unk):
                undetermined.append(str(case))
    return RepeatOutcome(counts, case_ids, evidence, sorted(undetermined))


# --------------------------------------------------------------------------
# 11.18 - repeated complete by the same resource
# --------------------------------------------------------------------------
@dataclass
class SameResourceOutcome:
    counts: pd.Series  # index (case, resource) -> complete oleh resource itu
    case_ids: list[str]  # case UNIK
    evidence: pd.DataFrame
    complete_rows_without_valid_resource: int
    undetermined_case_ids: list[str] = field(default_factory=list)


def same_resource_complete(sel: CompleteSelection, min_count: int = MIN_COMPLETE) -> SameResourceOutcome:
    """Case dengan >= min_count complete oleh resource valid yang identik. Case dihitung sekali."""
    comp = sel.complete
    res = normalize_resource(comp[RESOURCE_COL])
    valid = res.notna().to_numpy()
    v = comp.loc[valid].copy()
    v[RESOURCE_COL] = res[valid].astype(object).to_numpy()
    counts = v.groupby([CASE_COL, RESOURCE_COL], observed=True).size() if len(v) else pd.Series(dtype="int64")
    if len(counts):
        chosen = counts[counts >= min_count].rename("resource_complete_count").reset_index()
    else:  # tidak ada resource valid sama sekali
        chosen = pd.DataFrame({CASE_COL: [], RESOURCE_COL: [], "resource_complete_count": []})

    if len(chosen):
        ev_rows = v.merge(chosen, on=[CASE_COL, RESOURCE_COL], how="inner")
    else:  # hindari merge dtype-mismatch pada tabel kosong
        ev_rows = v.iloc[0:0].assign(resource_complete_count=pd.Series(dtype="int64"))
    case_total = comp.groupby(CASE_COL, observed=True).size() if len(comp) else pd.Series(dtype="int64")
    evidence = _evidence_frame(
        ev_rows,
        {
            "resource_complete_count": ev_rows["resource_complete_count"].astype(int).to_numpy(),
            "complete_count": ev_rows[CASE_COL].map(case_total).astype(int).to_numpy(),
        },
    )
    case_ids = sorted({str(c) for c in chosen[CASE_COL]})

    undetermined: list[str] = []
    if len(sel.unknown):
        ures = normalize_resource(sel.unknown[RESOURCE_COL])
        u = sel.unknown.loc[ures.notna().to_numpy()].copy()
        u[RESOURCE_COL] = ures[ures.notna()].astype(object).to_numpy()
        if len(u):
            unk = u.groupby([CASE_COL, RESOURCE_COL], observed=True).size()
            for key, n_unk in unk.items():
                n_c = int(counts.get(key, 0))
                if n_c < min_count <= n_c + int(n_unk):
                    undetermined.append(str(key[0]))
    return SameResourceOutcome(
        counts, case_ids, evidence, int((~valid).sum()), sorted(set(undetermined) - set(case_ids))
    )


def resource_column_state(events: pd.DataFrame) -> str:
    """'absent' | 'all_blank' | 'ok' untuk org:resource pada SELURUH log."""
    if RESOURCE_COL not in events.columns:
        return "absent"
    return "ok" if normalize_resource(events[RESOURCE_COL]).notna().any() else "all_blank"
