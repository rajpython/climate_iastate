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

from dashboard.components.ts_event_metrics import _region_key
from mhw.bottom.regions import BOTTOM_REGIONS

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "data" / "derived" / "cold_pool"

# Threshold label -> parquet column. Used by both the observed and model area views.
THRESHOLDS = {
    "≤ 2 °C  (headline index)": "area_lte2_km2",
    "≤ 1 °C": "area_lte1_km2",
    "≤ 0 °C": "area_lte0_km2",
    "≤ −1 °C": "area_lteminus1_km2",
}
# Model label -> source id. Filenames are built per region (coldpool_model_<id>_<region>…).
MODEL_SOURCES = {
    "Bering10K ROMS": "bering10k",
    "CEFI MOM6 NEP": "mom6_nep",
}
# Distinct line colour per model (observed is always black).
MODEL_COLORS = {
    "Bering10K ROMS": "steelblue",
    "CEFI MOM6 NEP": "darkorange",
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
    return sorted(regs, key=_region_key)


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
    return sorted(regs, key=_region_key)


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


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0.0


def threshold_short(thr_label: str) -> str:
    """'≤ 2 °C  (headline index)' -> '≤ 2 °C'."""
    return thr_label.split("  ")[0]
