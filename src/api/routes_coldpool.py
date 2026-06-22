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

import numpy as np

from api.schema import (
    ColdPoolPayload,
    ColdPoolRecord,
    SurveyReplicatePayload,
    SurveyReplicateRecord,
)
from mhw.bottom.regions import BOTTOM_REGIONS

router = APIRouter()

ROOT    = Path(__file__).parents[2]
RAW_DIR = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "data" / "derived" / "cold_pool"

# Modelled-source id -> user-facing source label (parquet filename is built per region).
_MODEL_LABELS = {
    "bering10k": "Bering10K ROMS (modelled, shelf domain)",
    "mom6_nep":  "CEFI MOM6 NEP (modelled, shelf domain)",
}

_MODEL_NOTE = (
    "Modelled cold pool over a depth-masked shelf domain at a fixed summer week — "
    "NOT strata-matched to the survey, so absolute areas run larger than observed. "
    "Compare interannual pattern and mean bottom temperature, not absolute area."
)


def _check_region(region: str) -> str:
    """Normalise + validate a region id (404 on unknown)."""
    key = region.lower()
    if key not in BOTTOM_REGIONS:
        raise HTTPException(status_code=404,
                            detail=f"Unknown region {region!r}; known: {sorted(BOTTOM_REGIONS)}")
    return key


def _load(region: str) -> pd.DataFrame:
    p = RAW_DIR / f"coldpool_index_observed_{region}.parquet"
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Cold-pool index not yet fetched for {region!r}. Run: mhw-fetch-coldpool --region {region}",
        )
    df = pd.read_parquet(p)
    return df.sort_values("year").reset_index(drop=True)


def _load_model(source: str, region: str) -> tuple[pd.DataFrame, str]:
    if source not in _MODEL_LABELS:
        raise HTTPException(status_code=404, detail=f"Unknown model source {source!r}")
    p = MODEL_DIR / f"coldpool_model_{source}_{region}.parquet"
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Modelled cold-pool not built for {source!r}/{region!r}. "
                   f"Run: mhw-build-coldpool-model --source {source} --region {region}",
        )
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True), _MODEL_LABELS[source]


def _clean(v) -> float | None:
    """NaN/inf -> None so the JSON stays valid."""
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) or math.isinf(f) else round(f, 4)


@router.get("/cold-pool/observed", response_model=ColdPoolPayload, tags=["Cold Pool"])
def get_cold_pool_observed(
    region:     str = Query("ebs", description="Bottom region id (e.g. ebs)"),
    start_year: int | None = Query(None, description="First survey year (inclusive)"),
    end_year:   int | None = Query(None, description="Last survey year (inclusive)"),
):
    """Return a region's AFSC observed cold-pool index time series.

    Headline field is ``area_lte2_km2`` (area of the survey footprint with bottom
    temperature ≤ 2 °C). Also returns the ≤1/0/−1 °C areas and mean bottom/surface
    temperatures.
    """
    region = _check_region(region)
    df = _load(region)
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No cold-pool data in requested range")

    return ColdPoolPayload(
        region=region,
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


@router.get("/cold-pool/modelled", response_model=ColdPoolPayload, tags=["Cold Pool"])
def get_cold_pool_modelled(
    source:     str = Query("bering10k", description="Model source id (bering10k, mom6_nep)"),
    region:     str = Query("ebs", description="Bottom region id (e.g. ebs)"),
    start_year: int | None = Query(None, description="First year (inclusive)"),
    end_year:   int | None = Query(None, description="Last year (inclusive)"),
):
    """Return a modelled cold-pool series for a region (regional ocean model, shelf domain).

    See the payload ``note``: absolute areas are not strata-matched to the survey —
    compare interannual pattern and mean bottom temperature, not absolute area.
    """
    region = _check_region(region)
    df, label = _load_model(source, region)
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No modelled cold-pool data in requested range")

    return ColdPoolPayload(
        source=label,
        region=region,
        note=_MODEL_NOTE,
        records=[
            ColdPoolRecord(
                year=int(r["year"]),
                area_lte2_km2=_clean(r.get("area_lte2_km2")),
                area_lte1_km2=_clean(r.get("area_lte1_km2")),
                area_lte0_km2=_clean(r.get("area_lte0_km2")),
                area_lteminus1_km2=_clean(r.get("area_lteminus1_km2")),
                mean_bottom_temp=_clean(r.get("mean_bottom_temp")),
                mean_surface_temp=None,
            )
            for _, r in df.iterrows()
        ],
    )


# Survey-replicate source labels.
_SR_SOURCES = {
    "bering10k": "Bering10K ROMS",
    "mom6_nep":  "CEFI MOM6 NEP",
}


@router.get("/cold-pool/survey-replicate", response_model=SurveyReplicatePayload, tags=["Cold Pool"])
def get_cold_pool_survey_replicate(
    source: str = Query("bering10k", description="Model source id (bering10k, mom6_nep)"),
    region: str = Query("ebs", description="Bottom region id (e.g. ebs)"),
):
    """Survey-replicated validation: model bottom temp sampled at the survey hauls.

    Returns per-year observed vs model mean bottom temperature (both over the same haul
    set) plus overall haul-level bias / RMSE / correlation — the literature-standard
    model-vs-survey comparison.
    """
    if source not in _SR_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source {source!r}")
    region = _check_region(region)
    annual_p = MODEL_DIR / f"survey_replicate_annual_{source}_{region}.parquet"
    hauls_p = MODEL_DIR / f"survey_replicate_{source}_{region}.parquet"
    if not annual_p.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Survey replicate not built for {source!r}/{region!r}. "
                   f"Run: mhw-build-survey-replicate --source {source} --region {region}",
        )
    annual = pd.read_parquet(annual_p).sort_values("year").reset_index(drop=True)

    bias = rmse = corr = None
    n_hauls = int(annual["n_hauls"].sum())
    if hauls_p.exists():
        h = pd.read_parquet(hauls_p)
        d = h["model_bottom_temp"] - h["obs_bottom_temp"]
        bias = round(float(d.mean()), 3)
        rmse = round(float(np.sqrt((d ** 2).mean())), 3)
        corr = round(float(np.corrcoef(h["model_bottom_temp"], h["obs_bottom_temp"])[0, 1]), 3)
        n_hauls = int(len(h))

    return SurveyReplicatePayload(
        source=_SR_SOURCES[source],
        bias_c=bias, rmse_c=rmse, corr=corr, n_hauls=n_hauls,
        records=[
            SurveyReplicateRecord(
                year=int(r["year"]),
                n_hauls=int(r["n_hauls"]),
                obs_mean_bottom_temp=_clean(r.get("obs_mean_bottom_temp")),
                model_mean_bottom_temp=_clean(r.get("model_mean_bottom_temp")),
                bias_c=_clean(r.get("bias_c")),
            )
            for _, r in annual.iterrows()
        ],
    )
