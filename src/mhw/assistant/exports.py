"""Data export — hand the user a downloadable CSV or Excel file.

Server-side and frontend-agnostic (mirrors :mod:`report`): writes into the shared downloads dir and
returns a token the API serves. Excel uses the xlsxwriter engine (installed; openpyxl is not).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd

from mhw.assistant.report import REPORTS_DIR

_MIME = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def build_export(df: pd.DataFrame, fmt: str = "csv", name: str = "data",
                 out_dir: Path | None = None) -> dict:
    """Write *df* to CSV/XLSX and return ``{token, filename, mime}``."""
    fmt = (fmt or "csv").lower()
    if fmt not in _MIME:
        fmt = "csv"
    out_dir = Path(out_dir) if out_dir else REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    token = f"{uuid.uuid4().hex}.{fmt}"
    path = out_dir / token
    if fmt == "xlsx":
        df.to_excel(path, index=False, engine="xlsxwriter")
    else:
        df.to_csv(path, index=False)
    safe = (name or "data").strip().replace(" ", "_")[:60] or "data"
    return {"token": token, "filename": f"{safe}.{fmt}", "mime": _MIME[fmt]}
