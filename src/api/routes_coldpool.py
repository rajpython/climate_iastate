"""Routes for the AFSC observed cold-pool index (EBS bottom-trawl survey).

The observed cold-pool index is the validation target for modelled bottom
temperature (Bering10K ROMS, CEFI MOM6 NEP). Annual, summer-survey, lagged —
clearly *not* near-real-time, and labelled as such.

Fetch with: ``mhw-fetch-coldpool``  (writes data/raw/coldpool_index_observed.parquet)
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.schema import ColdPoolPayload, ColdPoolRecord

router = APIRouter()

ROOT    = Path(__file__).parents[2]
RAW_DIR = ROOT / "data" / "raw"
_PARQUET = RAW_DIR / "coldpool_index_observed.parquet"


def _load() -> pd.DataFrame:
    if not _PARQUET.exists():
        raise HTTPException(
            status_code=503,
            detail="Cold-pool index not yet fetched. Run: mhw-fetch-coldpool",
        )
    df = pd.read_parquet(_PARQUET)
    return df.sort_values("year").reset_index(drop=True)


def _clean(v) -> float | None:
    """NaN/inf -> None so the JSON stays valid."""
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) or math.isinf(f) else round(f, 4)


@router.get("/cold-pool/observed", response_model=ColdPoolPayload, tags=["Cold Pool"])
def get_cold_pool_observed(
    start_year: int | None = Query(None, description="First survey year (inclusive)"),
    end_year:   int | None = Query(None, description="Last survey year (inclusive)"),
):
    """Return the AFSC observed EBS cold-pool index time series.

    Headline field is ``area_lte2_km2`` (area of the survey footprint with bottom
    temperature ≤ 2 °C). Also returns the ≤1/0/−1 °C areas and mean bottom/surface
    temperatures.
    """
    df = _load()
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No cold-pool data in requested range")

    return ColdPoolPayload(
        records=[
            ColdPoolRecord(
                year=int(r["year"]),
                area_lte2_km2=_clean(r.get("area_lte2_km2")),
                area_lte1_km2=_clean(r.get("area_lte1_km2")),
                area_lte0_km2=_clean(r.get("area_lte0_km2")),
                area_lteminus1_km2=_clean(r.get("area_lteminus1_km2")),
                mean_bottom_temp=_clean(r.get("mean_bottom_temp")),
                mean_surface_temp=_clean(r.get("mean_surface_temp")),
            )
            for _, r in df.iterrows()
        ]
    )
