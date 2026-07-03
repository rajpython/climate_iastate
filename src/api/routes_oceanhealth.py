"""Routes for bottom ocean-health indicators (Alaska shelf) — observed + modelled.

The ocean-health layer surfaces shelf conditions beyond bottom temperature, **observed
first**. Increment 1 is **bottom salinity**: the AFSC survey measures gear salinity for
EBS/NBS (the observed series, ``mean_bottom_salinity`` in the cold-pool product), and the
MOM6 NEP10k model provides the comparison (``sob``). Both are annual, summer-survey, lagged.

Unlike the cold pool there is **no area-below-threshold index** — salinity (and later oxygen)
are intensive shelf-mean conditions, not a footprint.

Build data with:
  observed  → ``mhw-fetch-coldpool --region <id>``          (writes data/raw/coldpool_index_observed_<id>.parquet)
  modelled  → ``mhw-build-ocean-health --variable salinity --source mom6_nep --region <id>``
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.schema import OceanHealthPayload, OceanHealthRecord
from mhw.bottom.oceanhealth import VARIABLES
from mhw.bottom.regions import BOTTOM_REGIONS

router = APIRouter()

ROOT      = Path(__file__).parents[2]
RAW_DIR   = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "data" / "derived" / "ocean_health"

# Model-source id -> user-facing label. Only sources that carry the variable are valid (checked
# at build time via BottomSource.variables); salinity is currently MOM6-only.
_MODEL_LABELS = {"mom6_nep": "MOM6 NEP10k (CEFI, modelled)"}

# Observed source per product: the packaged cold-pool index (salinity) vs the gapctd survey-CTD
# bottom O₂/pH product. Both are AFSC bottom-trawl survey, annual, summer, lagged.
_OBS_FILE = {
    "coldpool": "coldpool_index_observed_{region}.parquet",
    "survey_ctd": "survey_ctd_observed_{region}.parquet",
}
_OBS_FETCH = {
    "coldpool": "mhw-fetch-coldpool --region {region}",
    "survey_ctd": "mhw-fetch-survey-ctd --region {region}",
}
_OBS_NOTE = {
    "coldpool": (
        "Observed AFSC bottom-trawl survey {label} — annual, summer survey, lagged. EBS/NBS "
        "only; salinity sensor coverage begins ~2008 (EBS) / 2010 (NBS)."),
    "survey_ctd": (
        "Observed AFSC survey-CTD (SBE 19plus/43) {label} at each station's sea floor, "
        "averaged over the region — annual, summer survey, lagged. EBS/NBS, ~2021–present."),
}
_MODEL_NOTE = (
    "Modelled shelf-mean {label} over the same depth-masked shelf footprint as the "
    "cold-pool/bottom-temperature products (0.25° regrid, area-weighted). Model output, "
    "co-presented for comparison with the observed survey series."
)


def _check_region(region: str) -> str:
    key = region.lower()
    if key not in BOTTOM_REGIONS:
        raise HTTPException(status_code=404,
                            detail=f"Unknown region {region!r}; known: {sorted(BOTTOM_REGIONS)}")
    return key


def _check_variable(variable: str) -> str:
    key = variable.lower()
    if key not in VARIABLES:
        raise HTTPException(status_code=404,
                            detail=f"Unknown ocean-health variable {variable!r}; known: {sorted(VARIABLES)}")
    return key


def _clean(v) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) or math.isinf(f) else round(f, 4)


def _records(df: pd.DataFrame, col: str) -> list[OceanHealthRecord]:
    return [OceanHealthRecord(year=int(r["year"]), value=_clean(r.get(col)))
            for _, r in df.sort_values("year").iterrows()]


@router.get("/ocean-health/observed", response_model=OceanHealthPayload, tags=["Ocean Health"])
def get_ocean_health_observed(
    variable:   str = Query("salinity", description="Ocean-health variable (e.g. salinity)"),
    region:     str = Query("sebs", description="Bottom region id (EBS/NBS only for salinity)"),
    start_year: int | None = Query(None, description="First survey year (inclusive)"),
    end_year:   int | None = Query(None, description="Last survey year (inclusive)"),
):
    """Observed survey-derived ocean-health series (annual shelf mean)."""
    variable = _check_variable(variable)
    region = _check_region(region)
    meta = VARIABLES[variable]
    col = meta["col"]
    product = meta["obs_product"]
    p = RAW_DIR / _OBS_FILE[product].format(region=region)
    if not p.exists():
        raise HTTPException(status_code=503,
                            detail=f"Observed {variable!r} not fetched for {region!r}. "
                                   f"Run: {_OBS_FETCH[product].format(region=region)}")
    df = pd.read_parquet(p)
    if col not in df.columns:
        raise HTTPException(status_code=503,
                            detail=f"Observed {variable!r} ({col}) not available for {region!r}.")
    df = df[["year", col]].dropna(subset=[col])
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No observed data in requested range")
    return OceanHealthPayload(
        variable=variable, region=region, kind="observed",
        source=f"AFSC {BOTTOM_REGIONS[region].label} bottom-trawl survey (observed)",
        units=meta["units"],
        note=_OBS_NOTE[product].format(label=meta["label"].lower()),
        records=_records(df, col),
    )


@router.get("/ocean-health/modelled", response_model=OceanHealthPayload, tags=["Ocean Health"])
def get_ocean_health_modelled(
    variable:   str = Query("salinity", description="Ocean-health variable (e.g. salinity)"),
    source:     str = Query("mom6_nep", description="Model source id"),
    region:     str = Query("sebs", description="Bottom region id"),
    start_year: int | None = Query(None, description="First year (inclusive)"),
    end_year:   int | None = Query(None, description="Last year (inclusive)"),
):
    """Modelled annual shelf-mean ocean-health series."""
    variable = _check_variable(variable)
    region = _check_region(region)
    if source not in _MODEL_LABELS:
        raise HTTPException(status_code=404, detail=f"Unknown model source {source!r}")
    col = VARIABLES[variable]["col"]
    p = MODEL_DIR / f"oceanhealth_{variable}_{source}_{region}.parquet"
    if not p.exists():
        raise HTTPException(status_code=503,
                            detail=f"Modelled {variable!r} not built for {source!r}/{region!r}. "
                                   f"Run: mhw-build-ocean-health --variable {variable} --source {source} --region {region}")
    df = pd.read_parquet(p)
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    if df.empty:
        raise HTTPException(status_code=404, detail="No modelled data in requested range")
    return OceanHealthPayload(
        variable=variable, region=region, kind="modelled", source=_MODEL_LABELS[source],
        units=VARIABLES[variable]["units"],
        note=_MODEL_NOTE.format(label=VARIABLES[variable]["label"].lower()),
        records=_records(df, col),
    )
