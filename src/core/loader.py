"""XES event-log loader and validator backed by PM4Py (Anggota 1)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform
import sys

import pandas as pd
import pm4py

from src.core.cycle_time import DURATION_COLUMNS, compute_case_durations
from src.core.event_store import (
    ACTIVITY_COLUMN,
    CASE_ID_COLUMN,
    ROW_ID_COLUMN,
    TIMESTAMP_COLUMN,
    TRACE_POSITION_COLUMN,
    EventStore,
)

LIFECYCLE_COLUMN = "lifecycle:transition"
RESOURCE_COLUMN = "org:resource"
REQUIRED_XES_ATTRIBUTES = (CASE_ID_COLUMN, ACTIVITY_COLUMN, TIMESTAMP_COLUMN)


class EventLogLoadError(Exception):
    """Raised when an XES file cannot be read or fails required validation."""


def _compute_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _is_blank_text(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip() == ""


def _preserve_case_id(value: object) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_timestamps(raw_timestamps: list[object]) -> tuple[pd.Series, str, list[str]]:
    """Convert raw timestamps without mixing naive and timezone-aware values."""
    if not raw_timestamps:
        return pd.Series(dtype="datetime64[ns, UTC]"), "empty", []

    aware_flags: list[bool] = []
    parsed_values: list[pd.Timestamp] = []
    for raw in raw_timestamps:
        if raw is None or pd.isna(raw):
            raise EventLogLoadError("Terdapat event dengan time:timestamp kosong atau null.")
        try:
            ts = pd.Timestamp(raw)
        except Exception as exc:
            raise EventLogLoadError(f"Format time:timestamp tidak valid: {raw!r}") from exc
        if pd.isna(ts):
            raise EventLogLoadError(f"Format time:timestamp tidak valid: {raw!r}")
        aware_flags.append(ts.tzinfo is not None)
        parsed_values.append(ts)

    has_aware = any(aware_flags)
    has_naive = not all(aware_flags)
    if has_aware and has_naive:
        raise EventLogLoadError(
            "Timestamp mencampur nilai timezone-aware dan naive dalam satu log."
        )

    warnings: list[str] = []
    if has_aware:
        tz_names = {str(ts.tzinfo) for ts in parsed_values}
        series = pd.to_datetime(parsed_values, utc=True)
        tz_status = f"aware (uniform {next(iter(tz_names))} -> UTC)" if len(tz_names) == 1 else "aware (mixed -> UTC)"
        return series, tz_status, warnings

    series = pd.to_datetime(parsed_values)
    warnings.append(
        "Timestamp tidak memiliki informasi zona waktu (naive); durasi dihitung langsung dari selisih waktu lokal."
    )
    return series, "naive", warnings


def _extract_rows_from_legacy_log(log: Iterable[object]) -> tuple[list[dict[str, object]], list[object]]:
    """Iterate PM4Py EventLog trace-by-trace to preserve exact XES event order."""
    rows: list[dict[str, object]] = []
    raw_timestamps: list[object] = []
    row_id = 0

    for trace_index, trace in enumerate(log):
        trace_attrs: Mapping[str, object] = getattr(trace, "attributes", {}) or {}
        trace_case_id = trace_attrs.get(CASE_ID_COLUMN)
        if trace_case_id is None:
            trace_case_id = trace_attrs.get(ACTIVITY_COLUMN)

        events_in_trace = list(trace)  # type: ignore[arg-type]
        if not events_in_trace:
            continue

        for trace_pos, event in enumerate(events_in_trace):
            if not isinstance(event, Mapping):
                raise EventLogLoadError(
                    f"Struktur event pada trace ke-{trace_index} tidak valid."
                )

            raw_case_id = trace_case_id if not _is_blank_text(trace_case_id) else event.get(CASE_ID_COLUMN)
            if _is_blank_text(raw_case_id):
                raise EventLogLoadError(
                    f"Atribut wajib '{CASE_ID_COLUMN}' hilang atau kosong pada trace ke-{trace_index}."
                )

            raw_activity = event.get(ACTIVITY_COLUMN)
            if _is_blank_text(raw_activity):
                raise EventLogLoadError(
                    f"Atribut wajib '{ACTIVITY_COLUMN}' hilang atau kosong pada case '{raw_case_id}' posisi {trace_pos}."
                )

            if TIMESTAMP_COLUMN not in event or event.get(TIMESTAMP_COLUMN) is None:
                raise EventLogLoadError(
                    f"Atribut wajib '{TIMESTAMP_COLUMN}' hilang atau kosong pada case '{raw_case_id}' posisi {trace_pos}."
                )

            row: dict[str, object] = dict(event)
            row[CASE_ID_COLUMN] = _preserve_case_id(raw_case_id)
            row[ACTIVITY_COLUMN] = str(raw_activity)
            row[TRACE_POSITION_COLUMN] = trace_pos
            row[ROW_ID_COLUMN] = row_id
            raw_timestamps.append(event.get(TIMESTAMP_COLUMN))
            rows.append(row)
            row_id += 1

    return rows, raw_timestamps


def _empty_events_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            CASE_ID_COLUMN: pd.Series(dtype="object"),
            ACTIVITY_COLUMN: pd.Series(dtype="object"),
            TIMESTAMP_COLUMN: pd.Series(dtype="datetime64[ns, UTC]"),
            TRACE_POSITION_COLUMN: pd.Series(dtype="int64"),
            ROW_ID_COLUMN: pd.Series(dtype="int64"),
        }
    )


def _empty_durations_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            CASE_ID_COLUMN: pd.Series(dtype="object"),
            "timestamp_min": pd.Series(dtype="datetime64[ns, UTC]"),
            "timestamp_max": pd.Series(dtype="datetime64[ns, UTC]"),
            "duration_days": pd.Series(dtype="float64"),
        }
    )[DURATION_COLUMNS]


def _inspect_optional_attributes(
    events: pd.DataFrame,
) -> tuple[bool, dict[str, int], bool, bool, list[str]]:
    warnings: list[str] = []

    has_lifecycle = LIFECYCLE_COLUMN in events.columns
    lifecycle_values: dict[str, int] = {}
    if has_lifecycle:
        counts = (
            events[LIFECYCLE_COLUMN]
            .astype("string")
            .fillna("<kosong>")
            .value_counts()
        )
        lifecycle_values = {str(k): int(v) for k, v in counts.items()}
    else:
        warnings.append(
            "Kolom opsional 'lifecycle:transition' tidak tersedia; analisis 11.15/11.18 akan berstatus unavailable."
        )

    has_resource = RESOURCE_COLUMN in events.columns
    has_nonblank_resource = False
    if has_resource:
        res = events[RESOURCE_COLUMN].astype("string").str.strip()
        has_nonblank_resource = bool(res.mask(res.fillna("x").eq("")).notna().any())
        if not has_nonblank_resource and not events.empty:
            warnings.append(
                "Kolom 'org:resource' ada tetapi seluruh nilainya kosong/null; analisis 11.18 tidak dapat membuktikan same-resource."
            )
    else:
        warnings.append(
            "Kolom opsional 'org:resource' tidak tersedia; analisis 11.18 akan berstatus unavailable."
        )

    return has_lifecycle, lifecycle_values, has_resource, has_nonblank_resource, warnings


def load_event_log(path: str | Path) -> EventStore:
    """Read and validate an XES file via PM4Py into a single EventStore."""
    if path is None or str(path).strip() == "":
        raise EventLogLoadError("Path file XES tidak boleh kosong.")

    file_path = Path(path)
    if not file_path.exists():
        raise EventLogLoadError(f"File XES tidak ditemukan: {file_path}")
    if not file_path.is_file():
        raise EventLogLoadError(f"Path bukan file yang valid: {file_path}")

    resolved_path = file_path.resolve()
    file_size = resolved_path.stat().st_size
    sha256 = _compute_sha256(resolved_path)

    try:
        log = pm4py.read_xes(str(resolved_path), return_legacy_log_object=True)
    except EventLogLoadError:
        raise
    except Exception as exc:
        raise EventLogLoadError(
            f"Gagal membaca file XES '{resolved_path.name}': {exc}"
        ) from exc

    rows, raw_timestamps = _extract_rows_from_legacy_log(log)
    if not rows:
        events = _empty_events_dataframe()
        case_durations = _empty_durations_dataframe()
        tz_status = "empty"
        tz_warnings = ["Event log kosong (0 event); statistik tidak dapat dihitung."]
        ts_min: pd.Timestamp | None = None
        ts_max: pd.Timestamp | None = None
    else:
        events = pd.DataFrame(rows)
        timestamps, tz_status, tz_warnings = _normalize_timestamps(raw_timestamps)
        events[TIMESTAMP_COLUMN] = timestamps
        events[TRACE_POSITION_COLUMN] = events[TRACE_POSITION_COLUMN].astype("int64")
        events[ROW_ID_COLUMN] = events[ROW_ID_COLUMN].astype("int64")
        case_durations = compute_case_durations(events)
        ts_min = events[TIMESTAMP_COLUMN].min()
        ts_max = events[TIMESTAMP_COLUMN].max()

    has_lifecycle, lifecycle_values, has_resource, has_nonblank_resource, attr_warnings = (
        _inspect_optional_attributes(events)
    )

    activity_counts = (
        {
            str(k): int(v)
            for k, v in events[ACTIVITY_COLUMN].value_counts().items()
        }
        if not events.empty
        else {}
    )

    warnings = [*tz_warnings, *attr_warnings]
    metadata: dict[str, object] = {
        "dataset_name": resolved_path.stem,
        "file_name": resolved_path.name,
        "file_path": str(resolved_path),
        "file_size_bytes": int(file_size),
        "sha256": sha256,
        "case_count": int(case_durations[CASE_ID_COLUMN].nunique()),
        "event_count": int(len(events)),
        "activity_count": len(activity_counts),
        "activities": activity_counts,
        "columns": list(events.columns),
        "timestamp_min": ts_min,
        "timestamp_max": ts_max,
        "timezone_status": tz_status,
        "has_lifecycle": has_lifecycle,
        "lifecycle_values": lifecycle_values,
        "has_resource": has_resource,
        "has_nonblank_resource": has_nonblank_resource,
        "is_empty": bool(events.empty),
        "warnings": warnings,
        "loaded_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "versions": {
            "python": sys.version.split()[0],
            "pm4py": getattr(pm4py, "__version__", "unknown"),
            "pandas": pd.__version__,
            "os": platform.platform(),
        },
    }

    return EventStore(
        events=events,
        case_durations=case_durations,
        metadata=metadata,
    )
