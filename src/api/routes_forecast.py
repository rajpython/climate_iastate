"""Routes for the short-term MHW forecast (v1).

The deployed product is LOFRA's damped-persistence module run on our own monthly ``area_frac``
(division of labor settled 2026-07-08). This router is **scaffolded ahead of the module delivery**:
zone roles load from ``config/forecast.yml`` now, and the data endpoints return **503** until the
first ``data/derived/forecast/`` artifact exists — so the route is live-safe before there is data.

URL conventions (under /v1 router prefix added in main.py):
    GET /forecast/zones            Zone-role map (persistence / climatology, ice caveat, onset)
    GET /forecast/{zone}           Per-zone lead forecasts (point + AR(1) band + L1 occurrence)
    GET /forecast/onset/sebs       SEBS onset WATCH state (elevated/normal) — not a probability
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schema import (
    ForecastLeadRecord,
    ForecastPayload,
    OnsetRecord,
    OnsetWatchPayload,
)
from mhw.forecast.deploy import (
    forecast_artifact_path,
    load_forecast_config,
    onset_artifact_path,
)

router = APIRouter()

ROOT = Path(__file__).parents[2]

_NBS_ICE_NOTE = (
    "NBS carries genuine one-month persistence skill and gets a forecast, but the satellite SST is "
    "ice-contaminated — no broad-field/LIM reading, and read the outlook with the ice caveat."
)
_CLIM_NOTE = (
    "Ice-affected zone: damped persistence falls below climatology by two months, so magnitude/area "
    "is shown as climatology only (a data limitation, not a skill result)."
)
_PERSIST_NOTE = (
    "Damped persistence of the current monthly anomaly, decaying toward climatology at the zone's "
    "own rate. Honesty ladder: L1 headline, L2 banded, L3 low-confidence watch."
)


def _cfg() -> dict:
    return load_forecast_config()


def _zone_meta(zone: str, cfg: dict) -> dict:
    z = cfg["zones"].get(zone)
    if z is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown forecast zone {zone!r}; known: {sorted(cfg['zones'])}",
        )
    return z


def _clean(v) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) or math.isinf(f) else round(f, 4)


@router.get("/forecast/zones", tags=["Forecast"])
def list_forecast_zones():
    """Return the zone-role map that wires the outlook tiles (no forecast data required)."""
    cfg = _cfg()
    return {
        "module_version": cfg.get("module_version"),
        "fit_vintage": cfg.get("fit_vintage"),
        "leads": cfg.get("leads", []),
        "zones": cfg.get("zones", {}),
    }


@router.get("/forecast/onset/sebs", response_model=OnsetWatchPayload, tags=["Forecast"])
def get_onset_watch():
    """SEBS heatwave-onset WATCH (elevated/normal) — a discrimination indicator, not a probability."""
    cfg = _cfg()
    p = onset_artifact_path()
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail="Onset watch not yet produced (awaiting the vendored forecast module).",
        )
    df = pd.read_parquet(p).sort_values("date").reset_index(drop=True)
    return OnsetWatchPayload(
        module_version=cfg.get("module_version"),
        fit_vintage=cfg.get("fit_vintage"),
        records=[
            OnsetRecord(
                date=pd.to_datetime(r["date"]).date(),
                state=str(r["state"]),
                threshold=float(r["threshold"]),
            )
            for _, r in df.iterrows()
        ],
    )


@router.get("/forecast/{zone}", response_model=ForecastPayload, tags=["Forecast"])
def get_forecast(zone: str):
    """Return a zone's lead forecasts (point + AR(1) band + L1 occurrence probability)."""
    zone = zone.lower()
    cfg = _cfg()
    meta = _zone_meta(zone, cfg)

    note = {"persistence": _PERSIST_NOTE, "climatology": _CLIM_NOTE}[meta["role"]]
    if meta.get("ice_caveat") and meta["role"] == "persistence":
        note = f"{note} {_NBS_ICE_NOTE}"

    p = forecast_artifact_path(zone)
    if not p.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Forecast not yet produced for {zone!r} (awaiting the vendored forecast module).",
        )
    df = pd.read_parquet(p)
    return ForecastPayload(
        zone=zone,
        role=meta["role"],
        ice_caveat=bool(meta.get("ice_caveat", False)),
        lim_reading=bool(meta.get("lim_reading", True)),
        module_version=cfg.get("module_version"),
        fit_vintage=cfg.get("fit_vintage"),
        note=note,
        records=[
            ForecastLeadRecord(
                lead=str(r["lead"]),
                lead_months=int(r["lead_months"]),
                confidence=str(r["confidence"]),
                method=str(r["method"]),
                point=_clean(r.get("point")),
                ar1_var=_clean(r.get("ar1_var")),
                band_lo=_clean(r.get("band_lo")),
                band_hi=_clean(r.get("band_hi")),
                l1_prob=_clean(r.get("l1_prob")),
            )
            for _, r in df.iterrows()
        ],
    )
