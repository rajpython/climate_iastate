"""Shared data loaders + helpers for the commercial-economics (Economic SAFE) pages.

Reads the tidy parquets built by ``mhw-ingest-econ-safe`` (``data/raw/econ_safe/<id>.parquet``)
directly, and exposes the report registry + FMP-area labels so the pages stay thin. Mirrors
``components/coldpool_data.py`` for the bottom-ocean layer.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from mhw.econ import areas
from mhw.econ.safe_reports import SAFE_REPORTS, get_report  # noqa: F401 (re-exported)

ROOT = Path(__file__).resolve().parents[3]
SAFE_DIR = ROOT / "data" / "raw" / "econ_safe"

# FMP-area display order for selectors.
FMP_ORDER = ("bsai", "goa", "ak")

# Distinct, colour-blind-friendly line colours cycled across selected series.
ECON_PALETTE = ["#1565c0", "#b35900", "#2e7d32", "#6a3d9a", "#c62828",
                "#0097a7", "#8d6e63", "#455a64", "#00695c", "#9e6c00"]


@st.cache_data(show_spinner=False, ttl=3600)
def load_safe_report(report_id: str) -> pd.DataFrame | None:
    """Load one Economic SAFE report's tidy parquet (None if not ingested)."""
    p = SAFE_DIR / f"{report_id}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def fmp_label(code: str) -> str:
    """Full FMP-area label for a code (e.g. 'goa' → 'Gulf of Alaska')."""
    return areas.fmp_area_label(code)


def available_areas(df: pd.DataFrame) -> list[str]:
    """FMP-area codes present in *df*, in display order."""
    if df is None or "area_code" not in df.columns:
        return []
    present = set(df["area_code"].dropna().unique())
    return [a for a in FMP_ORDER if a in present]
