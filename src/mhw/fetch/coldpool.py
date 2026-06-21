"""AFSC observed cold-pool index fetcher — EBS bottom-trawl survey validation target.

This is the *observed* (survey-derived) cold-pool index produced by NOAA AFSC, the
ground-truth against which modelled bottom temperature (Bering10K ROMS, CEFI MOM6
NEP) is validated. It is small, public, and directly downloadable — no model run or
NOAA request required.

Source
------
GitHub `afsc-gap-products/coldpool`, archived at Zenodo 10.5281/zenodo.16915337.
The canonical product is the R data object `cold_pool_index` (one row per survey
year). We read the `.rda` directly with ``pyreadr`` (no R install needed).

The cold-pool index is the area (km²) of the EBS bottom-trawl survey footprint with
bottom (gear) temperature ≤ a threshold; the headline index uses ≤ 2 °C, with ≤ 1, 0,
and −1 °C also published. Coverage: EBS 1982–present (no 2020 — survey cancelled).

CLI: mhw-fetch-coldpool [--plot]
"""
from __future__ import annotations

import argparse
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------
COLDPOOL_RDA_URL = (
    "https://raw.githubusercontent.com/afsc-gap-products/coldpool/main/"
    "data/cold_pool_index.rda"
)
_R_OBJECT = "cold_pool_index"

# Per-haul survey temperatures (the index stations used to build the cold-pool index).
# This is the basis for *survey replication*: sampling a model at each haul's location
# and date, then comparing to the observed gear temperature (the literature-standard
# model-vs-survey comparison; see Seelanki et al. 2025, Kearney 2021).
COLDPOOL_HAULS_URL = (
    "https://raw.githubusercontent.com/afsc-gap-products/coldpool/main/"
    "data/index_hauls_temperature_data.csv"
)

# Lowercase rename of the R object's columns -> API/parquet schema.
_COLUMN_MAP = {
    "YEAR": "year",
    "AREA_LTE2_KM2": "area_lte2_km2",
    "AREA_LTE1_KM2": "area_lte1_km2",
    "AREA_LTE0_KM2": "area_lte0_km2",
    "AREA_LTEMINUS1_KM2": "area_lteminus1_km2",
    "MEAN_GEAR_TEMPERATURE": "mean_bottom_temp",
    "MEAN_BT_LT100M": "mean_bottom_temp_lt100m",
    "MEAN_SURFACE_TEMPERATURE": "mean_surface_temp",
    "MEAN_GEAR_SALINITY": "mean_bottom_salinity",
    "LAST_UPDATE": "last_update",
}


# ---------------------------------------------------------------------------
# Fetch & parse
# ---------------------------------------------------------------------------

def fetch_coldpool_index() -> pd.DataFrame:
    """Fetch the AFSC observed cold-pool index from the coldpool repo.

    Returns
    -------
    pd.DataFrame
        One row per survey year, sorted ascending, with snake_case columns
        (``year`` as int; areas in km²; temperatures in °C). The headline
        index is ``area_lte2_km2``.
    """
    import pyreadr  # local import: optional-ish dep, only needed for this fetch

    print("Fetching AFSC observed cold-pool index (cold_pool_index.rda) …")
    with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
        urllib.request.urlretrieve(COLDPOOL_RDA_URL, tmp.name)
        result = pyreadr.read_r(tmp.name)

    if _R_OBJECT not in result:
        raise KeyError(
            f"Expected R object {_R_OBJECT!r} in {COLDPOOL_RDA_URL}; "
            f"found {list(result)}"
        )

    df = result[_R_OBJECT].rename(columns=_COLUMN_MAP)
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year").reset_index(drop=True)

    print(
        f"  Cold-pool index: {len(df)} years, "
        f"{df['year'].min()}–{df['year'].max()} "
        f"(latest ≤2 °C area: {df['area_lte2_km2'].iloc[-1]:,.0f} km²)"
    )
    return df


# ---------------------------------------------------------------------------
# Per-haul survey temperatures (for survey replication)
# ---------------------------------------------------------------------------

def fetch_coldpool_hauls() -> pd.DataFrame:
    """Fetch the per-haul EBS survey temperatures (the cold-pool index stations).

    Returns
    -------
    pd.DataFrame with columns: year (int), stationid, datetime (survey haul time),
        latitude, longitude, gear_temperature (observed bottom temp, °C),
        surface_temperature, bottom_depth. One row per survey haul.
    """
    print("Fetching AFSC per-haul survey temperatures (index_hauls_temperature_data.csv) …")
    df = pd.read_csv(COLDPOOL_HAULS_URL)
    df["datetime"] = pd.to_datetime(df["start_time"])
    df["year"] = df["year"].astype(int)
    keep = ["year", "stationid", "datetime", "latitude", "longitude",
            "gear_temperature", "surface_temperature", "bottom_depth"]
    df = df[keep].dropna(subset=["gear_temperature", "latitude", "longitude"])
    df = df.sort_values(["year", "stationid"]).reset_index(drop=True)
    print(f"  Hauls: {len(df):,}, {df['year'].min()}–{df['year'].max()}")
    return df


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_parquet(df: pd.DataFrame, fname: str = "coldpool_index_observed.parquet") -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / fname
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# Plot (optional)
# ---------------------------------------------------------------------------

def plot_coldpool_plotly(df: pd.DataFrame) -> Path:
    """Render the ≤2 °C cold-pool area index as a bar chart and save HTML."""
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["year"], y=df["area_lte2_km2"],
            marker_color="steelblue", name="Cold pool ≤2 °C",
            hovertemplate="%{x}: %{y:,.0f} km²<extra></extra>",
        )
    )
    fig.update_layout(
        title="AFSC Observed Cold-Pool Index — EBS bottom-trawl survey (area ≤ 2 °C)",
        xaxis_title="Survey year", yaxis_title="Area ≤ 2 °C (km²)",
        template="plotly_white", height=500, width=1000,
    )
    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "coldpool_index_observed.html"
    fig.write_html(str(html_path))
    print(f"  Plot (HTML) → {html_path}")
    return html_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch the AFSC observed cold-pool index (EBS bottom-trawl survey)."
    )
    p.add_argument("--plot", action="store_true", help="Render a Plotly bar chart of the ≤2 °C index")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df = fetch_coldpool_index()
    save_parquet(df)
    hauls = fetch_coldpool_hauls()
    save_parquet(hauls, "coldpool_hauls_observed.parquet")
    if args.plot:
        plot_coldpool_plotly(df)


if __name__ == "__main__":
    main()
