"""Routes for commercial landings (fishery-*dependent* harvest — the board's economics layer).

E1: statewide-Alaska commercial landings (tons) + ex-vessel value ($) by species/year from NOAA
FOSS. Distinct from the survey CPUE pages — this is *commercial harvest*, not the fishery-
independent survey, and resolves to statewide Alaska only (not sub-region). Reads the generated
parquet directly and returns 503 when it is missing (house convention).

Fetch with: ``mhw-fetch-landings-foss`` (writes data/raw/landings_foss_ak.parquet)
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.schema import LandingsPayload, LandingsRecord
from mhw.econ.sources import FOSS_LANDINGS

router = APIRouter()

ROOT    = Path(__file__).parents[2]
RAW_DIR = ROOT / "data" / "raw"


def _load() -> pd.DataFrame:
    p = RAW_DIR / f"landings_{FOSS_LANDINGS.id}.parquet"
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail="Commercial landings not yet fetched. Run: mhw-fetch-landings-foss",
        )
    return pd.read_parquet(p).sort_values(["year", "species"]).reset_index(drop=True)


def _clean(v) -> float | None:
    """NaN/inf -> None so the JSON stays valid."""
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) or math.isinf(f) else round(f, 2)


@router.get("/landings/statewide", response_model=LandingsPayload, tags=["Landings"])
def get_landings_statewide(
    species:    str | None = Query(None, description="Species name filter (case-insensitive substring)"),
    start_year: int | None = Query(None, description="First year (inclusive)"),
    end_year:   int | None = Query(None, description="Last year (inclusive)"),
):
    """Return statewide-Alaska commercial landings (t) and ex-vessel value ($) by species/year.

    Fishery-dependent commercial harvest (NOAA FOSS), distinct from the survey. Statewide only —
    there is no sub-region split in this source (see the payload ``note``).
    """
    df = _load()
    if species is not None:
        df = df[df["species"].str.contains(species, case=False, na=False)]
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No landings in requested range")

    return LandingsPayload(
        source=FOSS_LANDINGS.label,
        records=[
            LandingsRecord(
                year=int(r["year"]),
                species=str(r["species"]),
                species_code=(None if pd.isna(r.get("species_code")) else str(r.get("species_code"))),
                landings_t=_clean(r.get("landings_t")),
                value_usd=_clean(r.get("value_usd")),
            )
            for _, r in df.iterrows()
        ],
    )
