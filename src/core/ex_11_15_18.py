"""A3 - Exercise 11.15 dan 11.18 -> AnalysisResult.

Satuan hasil = CASE (bukan event). Hanya event ``lifecycle:transition == complete``
(terverifikasi, dinormalisasi) yang dihitung.
"""
from __future__ import annotations

import pandas as pd

from src.core import rework as rw
from src.core.result import AnalysisResult

DEFAULT_COMPLETE_VALUE = rw.DEFAULT_COMPLETE_VALUE


def _events(store) -> pd.DataFrame:
    return store if isinstance(store, pd.DataFrame) else store.events


def _denominator(events: pd.DataFrame) -> int:
    return int(events[rw.CASE_COL].nunique()) if rw.CASE_COL in events.columns else 0


def _rule_15(target: str, cv: str) -> str:
    return (
        f"Case dipilih bila aktivitas '{target}' (exact concept:name) memiliki >= {rw.MIN_COMPLETE} event "
        f"dengan lifecycle:transition == '{cv}' (normalisasi strip+casefold). "
        "Satuan: case; schedule/start/abort/kosong tidak dihitung."
    )


def _rule_18(target: str, cv: str) -> str:
    return (
        _rule_15(target, cv)
        + f" Tambahan 11.18: >= {rw.MIN_COMPLETE} complete dilakukan org:resource valid yang IDENTIK "
        "(resource null/kosong tidak dianggap sama). Case dihitung sekali."
    )


def _not_ok(exercise_id: str, rule: str, den: int, status: str, reason: str) -> AnalysisResult:
    # count=0 hanya placeholder; status != ok berarti angka itu TIDAK boleh ditampilkan sebagai jawaban.
    return AnalysisResult(
        exercise_id=exercise_id,
        rule_description=rule,
        count=0,
        denominator=den,
        case_ids=[],
        evidence=None,
        status=status,
        notes=reason,
    )


def _lifecycle_note(sel: rw.CompleteSelection) -> str:
    return (
        f"Aktivitas target (exact): '{sel.target}'; event target: {sel.target_rows}; "
        f"complete terverifikasi: {len(sel.complete)}; "
        f"nilai lifecycle asli pada event target: {sel.lifecycle_values}."
    )


def _unknown_note(sel: rw.CompleteSelection, undetermined: list[str], strict: bool) -> tuple[str, bool]:
    """(teks peringatan, apakah hasil harus dijadikan unavailable)."""
    parts = []
    if len(sel.unknown):
        parts.append(f"{len(sel.unknown)} event target tanpa lifecycle diabaikan (tidak dihitung complete).")
    if undetermined:
        sample = ", ".join(undetermined[:5])
        parts.append(
            f"PERINGATAN: {len(undetermined)} case belum terbukti karena event lifecycle kosong dapat mengubah "
            f"hasil (contoh: {sample}); count adalah BATAS BAWAH."
        )
        if strict:
            return " ".join(parts), True
    return " ".join(parts), False


def run_11_15(
    store,
    activity_name: str,
    complete_value: str = DEFAULT_COMPLETE_VALUE,
    strict_unknown: bool = False,
) -> AnalysisResult:
    """Case dengan aktivitas fraud SELESAI (complete) minimal 2x."""
    ev = _events(store)
    den = _denominator(ev)
    rule = _rule_15(activity_name, complete_value)
    sel = rw.select_complete_events(ev, activity_name, complete_value)
    if sel.status != "ok":
        return _not_ok("11.15", rule, den, sel.status, sel.reason)

    out = rw.repeated_complete(sel)
    warn, make_unavailable = _unknown_note(sel, out.undetermined_case_ids, strict_unknown)
    if make_unavailable:
        return _not_ok("11.15", rule, den, "unavailable", warn)
    notes = " ".join([_lifecycle_note(sel), warn]).strip()
    return AnalysisResult(
        exercise_id="11.15",
        rule_description=rule,
        count=len(out.case_ids),
        denominator=den,
        case_ids=out.case_ids,
        evidence=out.evidence,
        status="ok",
        notes=notes,
    )


def run_11_18(
    store,
    activity_name: str,
    complete_value: str = DEFAULT_COMPLETE_VALUE,
    strict_unknown: bool = False,
) -> AnalysisResult:
    """Case dengan aktivitas fraud complete minimal 2x oleh resource valid yang sama."""
    ev = _events(store)
    den = _denominator(ev)
    rule = _rule_18(activity_name, complete_value)
    sel = rw.select_complete_events(ev, activity_name, complete_value)
    if sel.status != "ok":
        return _not_ok("11.18", rule, den, sel.status, sel.reason)

    state = rw.resource_column_state(ev)
    if state == "absent":
        return _not_ok(
            "11.18", rule, den, "unavailable", "Kolom org:resource tidak ada; same-resource tidak dapat dibuktikan."
        )

    out = rw.same_resource_complete(sel)
    warn, make_unavailable = _unknown_note(sel, out.undetermined_case_ids, strict_unknown)
    if make_unavailable:
        return _not_ok("11.18", rule, den, "unavailable", warn)
    extra = []
    if out.complete_rows_without_valid_resource:
        extra.append(
            f"{out.complete_rows_without_valid_resource} event complete tanpa resource valid (null/kosong) "
            "tidak dihitung sebagai resource yang sama."
        )
    if state == "all_blank":
        extra.append(
            "PERINGATAN: org:resource kosong/null pada SELURUH log; count 0 berarti 'tidak terbukti', "
            "kemungkinan atribut tidak terisi (eskalasi ke A1)."
        )
    n_pairs = int((out.counts >= rw.MIN_COMPLETE).sum()) if len(out.counts) else 0
    extra.append(f"Pasangan (case, resource) memenuhi syarat: {n_pairs}; case unik: {len(out.case_ids)}.")
    notes = " ".join([_lifecycle_note(sel), *extra, warn]).strip()
    return AnalysisResult(
        exercise_id="11.18",
        rule_description=rule,
        count=len(out.case_ids),
        denominator=den,
        case_ids=out.case_ids,
        evidence=out.evidence,
        status="ok",
        notes=notes,
    )
