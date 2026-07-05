"""Routes for the AKFIN Groundfish Economic SAFE layer (commercial groundfish economics).

Fishery-dependent commercial economics at FMP-area resolution (BSAI / GOA / All Alaska) — catch,
ex-vessel value & price, wholesale value, effort, and fleet — from the AKFIN Economic SAFE reports.
``/reports`` lists the registry (no data needed); ``/{report_id}`` serves one report's tidy rows,
returning 503 when its parquet has not been built (house convention).

Build with: ``mhw-ingest-econ-safe`` (writes data/raw/econ_safe/<id>.parquet)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.schema import (
    EconDataPayload,
    EconMeasureInfo,
    EconReportInfo,
    EconReportListPayload,
)
from mhw.econ.safe_reports import SAFE_REPORTS, get_report

router = APIRouter()

ROOT    = Path(__file__).parents[2]
SAFE_DIR = ROOT / "data" / "raw" / "econ_safe"


def _load(report_id: str) -> pd.DataFrame:
    p = SAFE_DIR / f"{report_id}.parquet"
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Economic SAFE report {report_id!r} not ingested. Run: mhw-ingest-econ-safe",
        )
    return pd.read_parquet(p)


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → JSON-safe records (NaN/NA → None)."""
    clean = df.replace({np.nan: None}).astype(object).where(pd.notna(df), None)
    return clean.to_dict(orient="records")


@router.get("/econ/safe/reports", response_model=EconReportListPayload, tags=["Economic SAFE"])
def list_econ_reports():
    """List the Groundfish Economic SAFE report registry (metadata only)."""
    return EconReportListPayload(reports=[
        EconReportInfo(
            id=r.id, code=r.code, title=r.title, family=r.family,
            dimensions=list(r.dimensions),
            measures=[EconMeasureInfo(col=m.col, label=m.label, units=m.units, kind=m.kind)
                      for m in r.measures],
            year_span=r.year_span,
        )
        for r in SAFE_REPORTS.values()
    ])


@router.get("/econ/safe/{report_id}", response_model=EconDataPayload, tags=["Economic SAFE"])
def get_econ_report(
    report_id:  str,
    area:       str | None = Query(None, description="FMP-area code filter (bsai, goa, ak)"),
    start_year: int | None = Query(None, description="First year (inclusive)"),
    end_year:   int | None = Query(None, description="Last year (inclusive)"),
):
    """Return one Economic SAFE report's tidy rows, optionally filtered by area and year."""
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404,
                            detail=f"Unknown report {report_id!r}; known: {sorted(SAFE_REPORTS)}")
    df = _load(report.id)
    if area is not None and "area_code" in df.columns:
        df = df[df["area_code"] == area.lower()]
    if start_year is not None and "year" in df.columns:
        df = df[df["year"] >= start_year]
    if end_year is not None and "year" in df.columns:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No data in requested range")

    return EconDataPayload(
        report_id=report.id, code=report.code, title=report.title, family=report.family,
        columns=list(df.columns), records=_records(df),
        note=("Values kept as published by AKFIN; a suppressed_band column (where present) flags "
              "cells that are partially confidential (NOAA rule of three)."),
    )
