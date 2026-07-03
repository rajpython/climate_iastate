"""Shared data loaders + constants for the cold-pool dashboard pages.

Used by both `pages/4_Cold_Pool_Observed.py` (observed index + survey-replicated
validation) and `pages/5_Cold_Pool_Models.py` (model comparison). Keeping the loaders
here avoids duplication and keeps the colour/threshold conventions consistent.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from mhw.bottom.regions import BOTTOM_REGIONS

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "data" / "derived" / "cold_pool"
OCEAN_HEALTH_DIR = ROOT / "data" / "derived" / "ocean_health"

# Threshold label -> parquet column. Used by both the observed and model area views.
THRESHOLDS = {
    "≤ 2 °C  (headline index)": "area_lte2_km2",
    "≤ 1 °C": "area_lte1_km2",
    "≤ 0 °C": "area_lte0_km2",
    "≤ −1 °C": "area_lteminus1_km2",
}
# Short display labels (legends, table columns, repeat mentions). The full official names — used
# for the FIRST mention in each model page's intro/footers — are in MODEL_FULL_NAMES below.
# "MOM6 NEP10k" is the CEFI MOM6-COBALT-NEP10k v1.0 model (NOAA GFDL); "Bering10K ROMS" is the
# ACLIM hindcast (B10K-K20_Level2_CORECFS).
MODEL_SOURCES = {
    "Bering10K ROMS": "bering10k",
    "MOM6 NEP10k": "mom6_nep",
}
# Distinct line colour per model (observed is always black).
MODEL_COLORS = {
    "Bering10K ROMS": "steelblue",
    "MOM6 NEP10k": "darkorange",
}
# Full official names + attribution — use ONCE, on first mention in a page's initial description.
MODEL_FULL_NAMES = {
    "Bering10K ROMS": "Bering10K ROMS (NOAA PMEL / UW — ACLIM hindcast B10K-K20_Level2_CORECFS)",
    "MOM6 NEP10k": "CEFI MOM6-COBALT-NEP10k v1.0 (NOAA GFDL)",
}


def region_label(region_id: str) -> str:
    """Full region name for titles (falls back to the upper-cased id)."""
    r = BOTTOM_REGIONS.get(region_id)
    return r.label if r else region_id.upper()


def ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 11 -> '11th', 23 -> '23rd' (shared by the bottom-state pages)."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@st.cache_data(show_spinner=False, ttl=3600)
def load_survey_footprint(region: str):
    """Convex-hull outline (lon, lat closed ring) of the survey hauls — the survey footprint.

    Drawn under the southern-extent reference lines for geographic context. Returns
    (lon_ring, lat_ring) as lists, or None if the haul file isn't built.
    """
    from scipy.spatial import ConvexHull

    p = RAW_DIR / f"coldpool_hauls_observed_{region}.parquet"
    if not p.exists():
        return None
    h = pd.read_parquet(p)
    pts = h[["longitude", "latitude"]].dropna().drop_duplicates().to_numpy()
    if len(pts) < 3:
        return None
    ring = pts[ConvexHull(pts).vertices]
    lon = list(ring[:, 0]) + [ring[0, 0]]   # close the ring
    lat = list(ring[:, 1]) + [ring[0, 1]]
    return lon, lat


@st.cache_data(show_spinner=False, ttl=3600)
def list_coldpool_regions() -> list[str]:
    """Cold-pool regions with an observed index on disk, in canonical south→north order.

    Restricted to ``product_kind == "cold_pool"`` so a bottom-temperature region's packaged
    index (GOA/AI also save a ``coldpool_index_observed_*.parquet``) can never leak onto the
    cold-pool-only pages (e.g. Cold-Pool Position).
    """
    regs = {p.stem.replace("coldpool_index_observed_", "")
            for p in RAW_DIR.glob("coldpool_index_observed_*.parquet")}
    regs = {rid for rid in regs
            if rid in BOTTOM_REGIONS and BOTTOM_REGIONS[rid].product_kind == "cold_pool"}
    return sorted(regs, key=_bt_key)


# Bottom-state region display order (south→north / west→east within an ecosystem). Distinct
# from the SST REGION_ORDER because the bottom-state ids differ (sebs, slope, GOA subareas).
_BT_REGION_ORDER = ["sebs", "nbs", "slope", "goa", "wgoa", "egoa",
                    "ai", "ai_west", "ai_central", "ai_east", "chukchi", "beaufort"]


def _bt_key(rid: str) -> tuple:
    return (_BT_REGION_ORDER.index(rid) if rid in _BT_REGION_ORDER
            else len(_BT_REGION_ORDER), rid)


def _has_model(rid: str) -> bool:
    return any((MODEL_DIR / f"coldpool_model_{sid}_{rid}.parquet").exists()
               for sid in MODEL_SOURCES.values())


@st.cache_data(show_spinner=False, ttl=3600)
def list_bottom_state_regions(group: str | None = None) -> list[str]:
    """All built bottom-state regions — cold-pool index *or* bottom-temp model — S→N order.

    This is the unified region list for the bottom-state pages: cold-pool regions (EBS, NBS)
    appear via their observed index, bottom-temperature regions (the Bering slope) via their
    built model series. Product-specific panels are then chosen per region by ``product_kind``.

    Pass ``group`` (e.g. ``"bering"``) to restrict to one geographic nav group — this is what
    lets the same bottom-state pages serve different geographic sections (Bering now; GOA/AI,
    Arctic in later phases) by filtering on ``BottomRegion.group``.
    """
    regs = {p.stem.replace("coldpool_index_observed_", "")
            for p in RAW_DIR.glob("coldpool_index_observed_*.parquet")}
    regs |= {rid for rid, r in BOTTOM_REGIONS.items()
             if r.product_kind == "bottom_temp" and _has_model(rid)}
    if group is not None:
        regs = {rid for rid in regs
                if rid in BOTTOM_REGIONS and BOTTOM_REGIONS[rid].group == group}
    return sorted(regs, key=_bt_key)


@st.cache_data(show_spinner="Loading cold-pool index …", ttl=3600)
def load_observed(region: str) -> pd.DataFrame | None:
    p = RAW_DIR / f"coldpool_index_observed_{region}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner="Computing observed southern extent …", ttl=3600)
def load_observed_southern_extent(region: str) -> pd.DataFrame | None:
    """Annual observed cold-pool southern extent from the survey hauls (model-free).

    Reads the per-haul observed temperatures (``coldpool_hauls_observed_<region>.parquet``) and,
    per year, takes the 5th-percentile latitude of hauls with bottom temperature ≤ 2 °C — the
    point-based analogue of the gridded model metric. Returns DataFrame[year, southern_extent_lat]
    or None if the haul file isn't built.
    """
    from mhw.bottom.position import southern_extent_points

    p = RAW_DIR / f"coldpool_hauls_observed_{region}.parquet"
    if not p.exists():
        return None
    h = pd.read_parquet(p)
    if not {"year", "latitude", "gear_temperature"}.issubset(h.columns):
        return None
    rows = [
        {"year": int(yr),
         "southern_extent_lat": southern_extent_points(g["latitude"].to_numpy(),
                                                       g["gear_temperature"].to_numpy())}
        for yr, g in h.groupby("year")
    ]
    out = pd.DataFrame(rows).dropna(subset=["southern_extent_lat"]).sort_values("year")
    return out.reset_index(drop=True) if not out.empty else None


@st.cache_data(show_spinner="Loading modelled cold pool …", ttl=3600)
def load_model(source_id: str, region: str, monthly: bool = False) -> pd.DataFrame | None:
    suffix = "_monthly" if monthly else ""
    p = MODEL_DIR / f"coldpool_model_{source_id}_{region}{suffix}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_kriged_area(source_id: str, region: str) -> pd.DataFrame | None:
    """Apples-to-apples modelled cold-pool AREA — the model's survey-replicated temps kriged
    through AFSC's exact pipeline (same 5 km grid, survey-area mask, ≤-threshold count), so it
    is directly comparable to the observed index in absolute km². None if not built
    (`mhw-build-kriged-area`). Columns: year, area_lte{2,1,0,-1}_km2, n_points."""
    p = MODEL_DIR / f"kriged_area_{source_id}_{region}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_observed_hauls(region: str) -> pd.DataFrame | None:
    """Per-haul survey temperatures (year, lat/lon, gear_temperature, surface_temperature) for the
    observed surface-vs-bottom diagnostic. None if no haul file (e.g. the Arctic — no survey)."""
    p = RAW_DIR / f"coldpool_hauls_observed_{region}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


@st.cache_data(show_spinner=False, ttl=3600)
def load_arctic_depth_profile() -> pd.DataFrame | None:
    """Arctic bottom-temperature depth profile (Chukchi + Beaufort) for the Simpson's-paradox panel. None if
    not built (`mhw-build-arctic-profile`)."""
    p = MODEL_DIR / "depth_profile_arctic.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


@st.cache_data(show_spinner=False, ttl=3600)
def load_shelf_surface(region: str) -> pd.DataFrame | None:
    """Observed summer open-water shelf-surface SST series (OISST) for the bottom-vs-surface
    diagnostic. None if not built (e.g. regions with no OISST file, like AI / slope)."""
    p = MODEL_DIR / f"oisst_shelf_surface_{region}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_survey_replicate_hauls(source_id: str, region: str) -> pd.DataFrame | None:
    """Per-haul survey-replicate frame (year, lat, lon, obs_bottom_temp, model_bottom_temp)
    for haul-level diagnostics (e.g. observed-vs-model scatter). None if not built."""
    p = MODEL_DIR / f"survey_replicate_{source_id}_{region}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


@st.cache_data(show_spinner="Loading survey-replicated comparison …", ttl=3600)
def load_survey_replicate(source_id: str, region: str):
    """Return (annual means df, haul-level skill dict) or (None, None) if not built."""
    ap = MODEL_DIR / f"survey_replicate_annual_{source_id}_{region}.parquet"
    if not ap.exists():
        return None, None
    annual = pd.read_parquet(ap).sort_values("year").reset_index(drop=True)
    skill = None
    hp = MODEL_DIR / f"survey_replicate_{source_id}_{region}.parquet"
    if hp.exists():
        h = pd.read_parquet(hp)
        d = h["model_bottom_temp"] - h["obs_bottom_temp"]
        skill = {
            "bias": float(d.mean()),
            "rmse": float(np.sqrt((d ** 2).mean())),
            "r": float(np.corrcoef(h["model_bottom_temp"], h["obs_bottom_temp"])[0, 1]),
            "n": int(len(h)),
        }
    return annual, skill


# ---------------------------------------------------------------------------
# Ocean-health layer (salinity now; oxygen etc. later) — observed + modelled shelf means
# ---------------------------------------------------------------------------

# Display name -> canonical variable id (keys of mhw.bottom.oceanhealth.VARIABLES).
OCEAN_HEALTH_VARS = {
    "Bottom salinity": "salinity",
    "Bottom dissolved oxygen": "oxygen",
    "Bottom pH": "ph",
}

# Observed product → raw parquet filename pattern (salinity = cold-pool index; O₂/pH = survey-CTD).
_OH_OBS_FILE = {
    "coldpool": "coldpool_index_observed_{region}.parquet",
    "survey_ctd": "survey_ctd_observed_{region}.parquet",
}


def _oh_meta(variable: str) -> dict:
    from mhw.bottom.oceanhealth import VARIABLES
    return VARIABLES[variable]


def _oh_obs_path(variable: str, region: str) -> Path:
    m = _oh_meta(variable)
    return RAW_DIR / _OH_OBS_FILE[m["obs_product"]].format(region=region)


@st.cache_data(show_spinner=False, ttl=3600)
def list_ocean_health_regions(variable: str, group: str | None = None) -> list[str]:
    """Regions with a non-null OBSERVED series for *variable* (optionally within *group*), S→N.

    Salinity/O₂/pH are EBS/NBS-only, so this naturally returns just those in the Bering; a region
    only appears once its observed product is fetched and carries a non-null value.
    """
    m = _oh_meta(variable)
    col = m["col"]
    pattern = _OH_OBS_FILE[m["obs_product"]].replace("{region}", "*")
    stem_prefix = pattern.split("*")[0]
    regs = []
    for p in RAW_DIR.glob(pattern):
        rid = p.stem.replace(stem_prefix, "")
        if rid not in BOTTOM_REGIONS:
            continue
        if group is not None and BOTTOM_REGIONS[rid].group != group:
            continue
        df = pd.read_parquet(p)
        if col in df.columns and df[col].notna().any():
            regs.append(rid)
    return sorted(set(regs), key=_bt_key)


@st.cache_data(show_spinner="Loading observed ocean-health series …", ttl=3600)
def load_ocean_health_observed(variable: str, region: str) -> pd.DataFrame | None:
    """Observed annual shelf-mean series → DataFrame[year, value], or None if unavailable."""
    col = _oh_meta(variable)["col"]
    p = _oh_obs_path(variable, region)
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if col not in df.columns:
        return None
    out = df[["year", col]].dropna(subset=[col]).rename(columns={col: "value"})
    return out.sort_values("year").reset_index(drop=True) if not out.empty else None


@st.cache_data(show_spinner="Loading modelled ocean-health series …", ttl=3600)
def load_ocean_health_model(variable: str, source_id: str, region: str) -> pd.DataFrame | None:
    """Modelled annual shelf-mean series → DataFrame[year, value], or None if not built."""
    col = _oh_meta(variable)["col"]
    p = OCEAN_HEALTH_DIR / f"oceanhealth_{variable}_{source_id}_{region}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if col not in df.columns:
        return None
    return df[["year", col]].rename(columns={col: "value"}).sort_values("year").reset_index(drop=True)


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0.0


def threshold_short(thr_label: str) -> str:
    """'≤ 2 °C  (headline index)' -> '≤ 2 °C'."""
    return thr_label.split("  ")[0]
