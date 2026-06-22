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

CLI: mhw-fetch-coldpool [--region ebs] [--plot]
"""
from __future__ import annotations

import argparse
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

from mhw.bottom.regions import BOTTOM_REGIONS, EBS, BottomRegion, get_region

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# The observed-product URLs / R-object / column map now live on each region descriptor
# (mhw.bottom.regions); EBS uses the AFSC `cold_pool_index` .rda + per-haul CSV. The
# per-haul temperatures are the basis for *survey replication* (sampling a model at each
# haul's location/date vs observed gear temp; Seelanki et al. 2025, Kearney 2021).


# ---------------------------------------------------------------------------
# Fetch & parse
# ---------------------------------------------------------------------------

def fetch_coldpool_index(region: BottomRegion = EBS) -> pd.DataFrame:
    """Fetch *region*'s observed cold-pool index from the coldpool repo.

    Returns
    -------
    pd.DataFrame
        One row per survey year, sorted ascending, with snake_case columns
        (``year`` as int; areas in km²; temperatures in °C). The headline
        index is ``area_lte2_km2``.
    """
    import pyreadr  # local import: optional-ish dep, only needed for this fetch

    obs = region.observed
    if obs is None or obs.kind != "cold_pool_index":
        raise ValueError(
            f"Region {region.id!r} has no cold_pool_index observed product "
            f"(kind={getattr(obs, 'kind', None)!r}). NBS/GOA/AI land in Phase 1."
        )

    print(f"Fetching AFSC observed cold-pool index ({region.id}: {obs.r_object}.rda) …")
    with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
        urllib.request.urlretrieve(obs.rda_url, tmp.name)
        result = pyreadr.read_r(tmp.name)

    if obs.r_object not in result:
        raise KeyError(
            f"Expected R object {obs.r_object!r} in {obs.rda_url}; found {list(result)}"
        )

    df = result[obs.r_object].rename(columns=dict(obs.column_map))
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

def fetch_coldpool_hauls(region: BottomRegion = EBS) -> pd.DataFrame:
    """Fetch the per-haul survey temperatures for *region* (the index stations).

    Returns
    -------
    pd.DataFrame with columns: year (int), stationid, datetime (survey haul time),
        latitude, longitude, gear_temperature (observed bottom temp, °C),
        surface_temperature, bottom_depth. One row per survey haul.
    """
    obs = region.observed
    if obs is None or not obs.hauls_url:
        raise ValueError(f"Region {region.id!r} has no per-haul survey product configured.")
    print(f"Fetching AFSC per-haul survey temperatures ({region.id}) …")
    df = pd.read_csv(obs.hauls_url)
    if obs.hauls_survey_id is not None:
        df = df[df["survey_definition_id"] == obs.hauls_survey_id]
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
        description="Fetch the AFSC observed cold-pool index (survey-derived, by region)."
    )
    p.add_argument("--region", default="ebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--plot", action="store_true", help="Render a Plotly bar chart of the ≤2 °C index")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    region = get_region(args.region)
    df = fetch_coldpool_index(region)
    save_parquet(df, f"coldpool_index_observed_{region.id}.parquet")
    hauls = fetch_coldpool_hauls(region)
    save_parquet(hauls, f"coldpool_hauls_observed_{region.id}.parquet")
    if args.plot:
        plot_coldpool_plotly(df)


if __name__ == "__main__":
    main()
