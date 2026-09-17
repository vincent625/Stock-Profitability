from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Any


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], fieldnames: list[str] | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows and not fieldnames:
        raise ValueError("fieldnames are required when rows are empty")
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    s = str(value).strip()
    if s in {"", "-", "N/A", "None", "null", "nan"}:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    v = as_float(value)
    return None if v is None else int(v)
