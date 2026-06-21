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

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "data" / "derived" / "cold_pool"
OBSERVED_PARQUET = RAW_DIR / "coldpool_index_observed.parquet"

# Threshold label -> parquet column. Used by both the observed and model area views.
THRESHOLDS = {
    "≤ 2 °C  (headline index)": "area_lte2_km2",
    "≤ 1 °C": "area_lte1_km2",
    "≤ 0 °C": "area_lte0_km2",
    "≤ −1 °C": "area_lteminus1_km2",
}
# Full-shelf model series (≤200 m); Bering10K weekly snapshot, MOM6 July month.
MODEL_SOURCES = {
    "Bering10K ROMS": "coldpool_model_bering10k.parquet",
    "CEFI MOM6 NEP": "coldpool_model_mom6_nep.parquet",
}
# Same models on a matched July-monthly cadence (model-vs-model identical footing).
MODEL_MONTHLY = {
    "Bering10K ROMS": "coldpool_model_bering10k_monthly.parquet",
    "CEFI MOM6 NEP": "coldpool_model_mom6_nep_monthly.parquet",
}
# Distinct line colour per model (observed is always black).
MODEL_COLORS = {
    "Bering10K ROMS": "steelblue",
    "CEFI MOM6 NEP": "darkorange",
}
# Survey-replicate files per model: (annual means, per-haul).
SR_FILES = {
    "Bering10K ROMS": ("survey_replicate_annual_bering10k.parquet", "survey_replicate_bering10k.parquet"),
    "CEFI MOM6 NEP":  ("survey_replicate_annual_mom6_nep.parquet",  "survey_replicate_mom6_nep.parquet"),
}


@st.cache_data(show_spinner="Loading cold-pool index …", ttl=3600)
def load_observed() -> pd.DataFrame | None:
    if not OBSERVED_PARQUET.exists():
        return None
    return pd.read_parquet(OBSERVED_PARQUET).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner="Loading modelled cold pool …", ttl=3600)
def load_model(fname: str) -> pd.DataFrame | None:
    p = MODEL_DIR / fname
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner="Loading survey-replicated comparison …", ttl=3600)
def load_survey_replicate(model_label: str):
    """Return (annual means df, haul-level skill dict) or (None, None) if not built."""
    annual_fn, haul_fn = SR_FILES[model_label]
    ap = MODEL_DIR / annual_fn
    if not ap.exists():
        return None, None
    annual = pd.read_parquet(ap).sort_values("year").reset_index(drop=True)
    skill = None
    hp = MODEL_DIR / haul_fn
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
