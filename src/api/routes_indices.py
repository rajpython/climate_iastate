"""Routes for climate indices (AO daily, PDO monthly)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.schema import IndexPayload, IndexRecord

router = APIRouter()

ROOT    = Path(__file__).parents[2]
RAW_DIR = ROOT / "data" / "raw"


def _load_ao() -> pd.DataFrame:
    p = RAW_DIR / "ao_daily.parquet"
    if not p.exists():
        raise HTTPException(status_code=503, detail="AO index not yet fetched")
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values("date").reset_index(drop=True)


def _load_pdo() -> pd.DataFrame:
    p = RAW_DIR / "pdo_monthly.parquet"
    if not p.exists():
        raise HTTPException(status_code=503, detail="PDO index not yet fetched")
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values("date").reset_index(drop=True)


@router.get("/indices/ao", response_model=IndexPayload)
def get_ao(
    start: date | None = Query(None, description="Start date YYYY-MM-DD"),
    end:   date | None = Query(None, description="End date YYYY-MM-DD"),
):
    """Return AO daily index values."""
    df = _load_ao()
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    if df.empty:
        raise HTTPException(status_code=404, detail="No AO data in requested range")

    return IndexPayload(
        index="ao",
        frequency="daily",
        records=[
            IndexRecord(date=str(r["date"]), value=round(float(r["ao"]), 4))
            for _, r in df.iterrows()
        ],
    )


@router.get("/indices/pdo", response_model=IndexPayload)
def get_pdo(
    start: date | None = Query(None, description="Start date YYYY-MM-DD"),
    end:   date | None = Query(None, description="End date YYYY-MM-DD"),
):
    """Return PDO monthly index values."""
    df = _load_pdo()
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    if df.empty:
        raise HTTPException(status_code=404, detail="No PDO data in requested range")

    return IndexPayload(
        index="pdo",
        frequency="monthly",
        records=[
            IndexRecord(date=str(r["date"]), value=round(float(r["pdo"]), 4))
            for _, r in df.iterrows()
        ],
    )
