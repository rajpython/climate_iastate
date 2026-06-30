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
# Packaged bottom-temperature index (GOA/AI — by subarea, no cold-pool area)
# ---------------------------------------------------------------------------

# ESR Ecosystem-Subarea areas (10⁹ m², from AFSC "Alaska Marine Management Areas") — used to
# **area-weight** the region-wide GOA/AI mean bottom temperature across subareas (the packaged
# product ships per-subarea means with no weights, so a plain average over-weights the smaller
# subareas). Only subareas surveyed in a given year contribute.
_SUBAREA_AREA = {
    "Western Gulf of Alaska": 606.578, "Eastern Gulf of Alaska": 366.884,
    "Western Aleutians": 371.797, "Central Aleutians": 691.256, "Eastern Aleutians": 214.066,
}


def _area_weighted_mean(g: pd.DataFrame, col: str) -> float:
    """Area-weighted mean of *col* across a year's surveyed subareas (falls back to a plain
    mean if any subarea area is unknown)."""
    vals = g[col]
    # subarea may be a pandas Categorical (pyreadr reads R factors as such) — cast to str so the
    # dict-map yields a plain float Series that supports sum().
    wts = g["subarea"].astype(str).map(_SUBAREA_AREA)
    if wts.notna().all() and float(wts.sum()) > 0:
        return float((vals * wts.to_numpy()).sum() / float(wts.sum()))
    return float(vals.mean())


def aggregate_mean_temperature(long_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a by-subarea ``*_mean_temperature`` frame to one region-wide row per year.

    The packaged GOA/AI products report mean bottom (gear) temperature *per subarea* with no
    area weights, so the region-wide annual value is the **area-weighted** cross-subarea mean
    (weighted by ESR subarea area; only subareas surveyed that year contribute). Per-subarea
    bottom temps are kept as ``mean_bottom_temp_<slug>`` columns for the breakdown (e.g. Western
    vs Eastern GOA). Network-free + pure, so it is unit-tested directly.
    """
    df = long_df.copy()
    df["year"] = df["year"].astype(int)
    rows = []
    for yr, g in df.groupby("year"):
        row = {"year": int(yr),
               "mean_bottom_temp": round(_area_weighted_mean(g, "mean_bottom_temp"), 4)}
        if "mean_surface_temp" in g:
            row["mean_surface_temp"] = round(_area_weighted_mean(g, "mean_surface_temp"), 4)
        for _, r in g.iterrows():
            slug = str(r["subarea"]).split()[0].lower()   # "Western Gulf of Alaska" -> "western"
            row[f"mean_bottom_temp_{slug}"] = round(float(r["mean_bottom_temp"]), 4)
        if "last_update" in g:
            row["last_update"] = str(g["last_update"].max())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def fetch_mean_temperature(region: BottomRegion) -> pd.DataFrame:
    """Fetch *region*'s packaged bottom-temperature index (GOA/AI), aggregated region-wide.

    Reads the ``{region}_mean_temperature.rda`` (one row per subarea per survey year), renames
    via the region column map, and aggregates across subareas to one annual region-wide mean
    bottom temperature (plus per-subarea columns). Returns DataFrame sorted by year.
    """
    import pyreadr  # local import: optional-ish dep, only needed for this fetch

    obs = region.observed
    if obs is None or obs.kind != "mean_temperature":
        raise ValueError(
            f"Region {region.id!r} has no mean_temperature observed product "
            f"(kind={getattr(obs, 'kind', None)!r})."
        )

    print(f"Fetching AFSC observed bottom-temperature index ({region.id}: {obs.r_object}.rda) …")
    with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
        urllib.request.urlretrieve(obs.rda_url, tmp.name)
        result = pyreadr.read_r(tmp.name)

    if obs.r_object not in result:
        raise KeyError(
            f"Expected R object {obs.r_object!r} in {obs.rda_url}; found {list(result)}"
        )

    long_df = result[obs.r_object].rename(columns=dict(obs.column_map))
    long_df = long_df.dropna(subset=["year"]).copy()
    if obs.subarea:   # ESR subarea region: keep only its rows (single-subarea series)
        long_df = long_df[long_df["subarea"].astype(str) == obs.subarea].copy()
        if long_df.empty:
            raise ValueError(f"Subarea {obs.subarea!r} not found in {obs.r_object}.")
    out = aggregate_mean_temperature(long_df)
    print(
        f"  Bottom-temperature index: {len(out)} years, "
        f"{out['year'].min()}–{out['year'].max()} "
        f"(latest mean bottom temp: {out['mean_bottom_temp'].iloc[-1]:.2f} °C)"
    )
    return out


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
    if obs is None:
        raise ValueError(f"Region {region.id!r} has no observed product configured.")
    if obs.kind == "foss_hauls" or obs.foss_srvy:
        # FOSS survey hauls: bottom-temperature regions (slope) and GOA/AI, whose packaged
        # index is by-subarea only — the per-haul temps for replication come from FOSS.
        return _fetch_foss_hauls(region)
    if not obs.hauls_url:
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


def _fetch_foss_hauls(region: BottomRegion) -> pd.DataFrame:
    """Per-haul survey temps from the FOSS survey tables (bottom-temp regions, e.g. slope).

    Bottom-temperature regions (no cold-pool product) get their observed bottom temperature
    straight from the FOSS bottom-trawl haul records, reshaped to the same haul schema the
    survey-replicate engine consumes (``gear_temperature`` = FOSS ``bottom_temperature_c``).
    """
    from mhw.fetch.foss_catch import fetch_hauls

    obs = region.observed
    print(f"Fetching FOSS survey hauls ({region.id}: srvy={obs.foss_srvy}) …")
    h = fetch_hauls((obs.foss_srvy,))
    df = pd.DataFrame({
        "year": h["year"].astype(int),
        "stationid": h["hauljoin"].astype(str),
        "datetime": pd.to_datetime(h["date_time"]),
        "latitude": h["latitude"],
        "longitude": h["longitude"],
        "gear_temperature": h["bottom_temperature_c"],
        "surface_temperature": h.get("surface_temperature_c"),
        "bottom_depth": h["depth_m"],
    })
    df = df.dropna(subset=["gear_temperature", "latitude", "longitude"])
    if obs.subarea:   # ESR subarea region: clip parent-survey hauls to the subarea polygon
        df = _clip_hauls_to_subarea(df, region.id)
    df = df.sort_values(["year", "stationid"]).reset_index(drop=True)
    print(f"  Hauls: {len(df):,}, {df['year'].min()}–{df['year'].max()}")
    return df


def _clip_hauls_to_subarea(df: pd.DataFrame, region_id: str) -> pd.DataFrame:
    """Keep only hauls whose (lon, lat) fall inside the subarea's regions.geojson polygon."""
    import json

    import shapely
    from shapely.geometry import shape

    geojson = PROJECT_ROOT / "config" / "regions.geojson"
    fc = json.loads(geojson.read_text())
    poly = next((shape(f["geometry"]) for f in fc["features"]
                 if f["properties"]["id"] == region_id), None)
    if poly is None:
        return df
    inside = shapely.contains_xy(poly, df["longitude"].to_numpy(), df["latitude"].to_numpy())
    return df[inside]


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
    p.add_argument("--region", default="sebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--plot", action="store_true", help="Render a Plotly bar chart of the ≤2 °C index")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    region = get_region(args.region)
    kind = region.observed.kind if region.observed else None

    if kind == "cold_pool_index":
        df = fetch_coldpool_index(region)
        save_parquet(df, f"coldpool_index_observed_{region.id}.parquet")
        hauls = fetch_coldpool_hauls(region)
        save_parquet(hauls, f"coldpool_hauls_observed_{region.id}.parquet")
        if args.plot:
            plot_coldpool_plotly(df)
    elif kind == "mean_temperature":
        # GOA/AI: packaged bottom-temperature index (by subarea → region-wide annual mean) +
        # FOSS survey hauls for survey-replicated model validation. No cold-pool area index.
        df = fetch_mean_temperature(region)
        save_parquet(df, f"coldpool_index_observed_{region.id}.parquet")
        hauls = fetch_coldpool_hauls(region)
        save_parquet(hauls, f"coldpool_hauls_observed_{region.id}.parquet")
        print(f"  ({region.id}: bottom-temperature region — packaged index + FOSS hauls; "
              "no cold-pool area index)")
    elif kind == "foss_hauls":
        # Bottom-temperature region: no area index. Fetch the survey hauls; the observed
        # annual mean bottom temp is produced by the survey-replicate step.
        hauls = fetch_coldpool_hauls(region)
        save_parquet(hauls, f"coldpool_hauls_observed_{region.id}.parquet")
        print(f"  ({region.id}: bottom-temperature region — observed mean BT comes from "
              "survey replication, no area index)")
    else:
        raise ValueError(f"Region {region.id!r} has unsupported observed kind {kind!r}")


if __name__ == "__main__":
    main()
