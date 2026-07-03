"""AFSC survey-CTD observed bottom oxygen + pH — the observed-first ocean-health target.

The AFSC bottom-trawl surveys carry a trawl-mounted SBE 19plus V2 CTD (with an SBE 43
dissolved-oxygen sensor and a pH sensor). NOAA's ``gapctd`` pipeline processes those casts and
publishes, per survey station, the **sea-floor dissolved oxygen** and **sea-floor pH** — a
regional, survey-time observed product in exactly the shape the board already uses for bottom
temperature and salinity (Rohan et al. 2023, NOAA Tech. Memo. NMFS-AFSC-475).

Source: NCEI Accession 0286094 (Eastern + Northern Bering Sea), one NetCDF per survey year.
Each file's ``index`` dimension is the per-cast record; the ``sea_floor_*`` variables are the
bottom value at each station. One file spans both SEBS and NBS (lat ~54–65 °N), so stations are
split to a region by the ``config/regions.geojson`` polygon at aggregation time.

Coverage: EBS/NBS **2021–present** (the SBE 43 O₂ + pH sensors were added ~2021). pH carries a
documented sensor-drift caveat, so it is plausibility-filtered and labelled provisional.

CLI: mhw-fetch-survey-ctd [--region sebs] [--start 2021] [--end 2024]
"""
from __future__ import annotations

import argparse
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from mhw.bottom.regions import BOTTOM_REGIONS, BottomRegion, get_region

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# NCEI Accession 0286094 (EBS+NBS), gapctd product. The arc-bucket + version are pinned like the
# MOM6 release id — bump when NCEI publishes a new version (annual). Verified live 2026-07-03:
# version 2.2 carries 2021–2024. One file per year: GAPCTD_EBS/<year>/GAPCTD_<year>_EBS.nc.
_NCEI_BASE = ("https://www.ncei.noaa.gov/data/oceans/archive/arc0221/0286094/2.2/"
              "data/0-data/GAPCTD_EBS")
# The Bering CTD accession serves SEBS + NBS together; both region ids read the same files and
# are split by polygon. (GOA/AI live in separate accessions — later increments.)
_CTD_REGION_GROUP = {"sebs": "ebs", "nbs": "ebs"}

_FILL_THRESHOLD = 1e30          # gapctd NetCDF fill (~9.97e36) is not decoded to NaN — mask it
_O2_VALID = (0.0, 15.0)         # ml/l — drop fills/negatives (EBS bottom O₂ ~4–10 ml/l)
_PH_VALID = (7.0, 8.5)          # total scale — drop ISFET sensor-drift outliers (typical ~7.6–8.1)

# Per-station (2-D, along `index`) variables we keep from each gapctd file.
_STATION_VARS = {
    "latitude": "latitude",
    "longitude": "longitude",
    "stationid": "stationid",
    "sea_floor_dissolved_oxygen": "o2_mll",
    "sea_floor_ph_reported_on_total_scale": "ph",
}


# ---------------------------------------------------------------------------
# Pure helpers (network-free, unit-testable)
# ---------------------------------------------------------------------------

def _mask_fill(a: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Return *a* as float with fills (>|1e30|) and out-of-range values set to NaN."""
    x = np.asarray(a, dtype="float64").copy()
    x[~np.isfinite(x)] = np.nan
    x[np.abs(x) > _FILL_THRESHOLD] = np.nan
    x[(x < lo) | (x > hi)] = np.nan
    return x


def station_frame(ds, year: int) -> pd.DataFrame:
    """Tidy per-station bottom O₂/pH frame from one open gapctd dataset (network-free).

    Fills are masked; pH is plausibility-filtered (sensor drift). Down/up profiles at the same
    station are averaged so each station contributes once. Returns columns
    ``(year, stationid, latitude, longitude, o2_mll, ph)``.
    """
    n = ds.sizes["index"]
    cols = {}
    for src, dst in _STATION_VARS.items():
        if src not in ds:
            # A survey year may predate O₂/pH processing (e.g. 2021 EBS has neither) — NaN it,
            # so that year simply contributes no valid values to the series.
            cols[dst] = np.full(n, np.nan)
            continue
        vals = np.asarray(ds[src].values)
        if dst == "stationid":
            cols[dst] = [str(s).strip() for s in vals]
        elif dst == "o2_mll":
            cols[dst] = _mask_fill(vals, *_O2_VALID)
        elif dst == "ph":
            cols[dst] = _mask_fill(vals, *_PH_VALID)
        else:
            cols[dst] = np.asarray(vals, dtype="float64")
    df = pd.DataFrame(cols)
    df["year"] = int(year)
    # Average down/up profiles per station (a station may appear twice).
    df = (df.groupby(["year", "stationid"], as_index=False)
            .agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"),
                 o2_mll=("o2_mll", "mean"), ph=("ph", "mean")))
    return df[["year", "stationid", "latitude", "longitude", "o2_mll", "ph"]]


def regional_annual_means(stations: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-station bottom O₂/pH to one region-wide row per year (network-free).

    Simple across-station mean per year (an intensive quantity; the survey-station mean is the
    observed convention, matching the cold-pool ``mean_gear_temperature``). Years with no valid
    values for a variable get NaN there. Columns: ``year, mean_bottom_oxygen, mean_bottom_ph,
    n_stations_o2, n_stations_ph``.
    """
    rows = []
    for yr, g in stations.groupby("year"):
        rows.append({
            "year": int(yr),
            "mean_bottom_oxygen": round(float(g["o2_mll"].mean()), 4) if g["o2_mll"].notna().any() else np.nan,
            "mean_bottom_ph": round(float(g["ph"].mean()), 4) if g["ph"].notna().any() else np.nan,
            "n_stations_o2": int(g["o2_mll"].notna().sum()),
            "n_stations_ph": int(g["ph"].notna().sum()),
        })
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def clip_to_region(stations: pd.DataFrame, region_id: str) -> pd.DataFrame:
    """Keep only stations whose (lon, lat) fall inside *region_id*'s regions.geojson polygon."""
    import json

    import shapely
    from shapely.geometry import shape

    geojson = PROJECT_ROOT / "config" / "regions.geojson"
    fc = json.loads(geojson.read_text())
    poly = next((shape(f["geometry"]) for f in fc["features"]
                 if f["properties"]["id"] == region_id), None)
    if poly is None:
        return stations
    inside = shapely.contains_xy(poly, stations["longitude"].to_numpy(),
                                 stations["latitude"].to_numpy())
    return stations[inside].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fetch (network)
# ---------------------------------------------------------------------------

def _year_url(year: int) -> str:
    return f"{_NCEI_BASE}/{year}/GAPCTD_{year}_EBS.nc"


def _download(url: str, dest: str, timeout: int = 60, retries: int = 3) -> None:
    """Stream *url* to *dest* with a socket timeout + retries.

    Uses a browser User-Agent: the NCEI archive server stalls the default ``Python-urllib``
    agent (and ``urlretrieve`` has no timeout, so it hangs forever). A normal UA downloads in
    ~1 s.
    """
    import shutil
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (marine.iastate.ai fetcher)"})
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            return
        except Exception as exc:  # noqa: BLE001 — retry on transient network stalls
            last = exc
            print(f"    (attempt {attempt}/{retries} failed: {exc}; retrying)")
    raise last


def fetch_ctd_stations(start: int = 2021, end: int = 2024) -> pd.DataFrame:
    """Download the Bering gapctd files for *start..end* and return all per-station rows."""
    import xarray as xr

    cache_dir = DATA_RAW / "ctd_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in range(start, end + 1):
        # Cache the source NetCDF so re-runs (and the second Bering region) don't re-download.
        local = cache_dir / f"GAPCTD_{year}_EBS.nc"
        try:
            if not local.exists() or local.stat().st_size == 0:
                print(f"Fetching survey-CTD bottom O₂/pH ({year}) … {_year_url(year)}")
                _download(_year_url(year), str(local))
            else:
                print(f"Using cached survey-CTD file for {year} ({local.name})")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ds = xr.open_dataset(local, mask_and_scale=True)
        except Exception as exc:  # noqa: BLE001 — a missing survey year is not fatal
            print(f"  (skip {year}: {exc})")
            continue
        f = station_frame(ds, year)
        ds.close()
        print(f"  {year}: {len(f)} stations, O₂ valid {int(f['o2_mll'].notna().sum())}, "
              f"pH valid {int(f['ph'].notna().sum())}")
        frames.append(f)
    if not frames:
        return pd.DataFrame(columns=["year", "stationid", "latitude", "longitude", "o2_mll", "ph"])
    return pd.concat(frames, ignore_index=True)


def save_parquet(df: pd.DataFrame, fname: str) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / fname
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch AFSC survey-CTD observed bottom oxygen + pH (gapctd, NCEI).")
    p.add_argument("--region", default="sebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--start", type=int, default=2021, help="First survey year")
    p.add_argument("--end", type=int, default=2024, help="Last survey year")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    region: BottomRegion = get_region(args.region)
    if region.id not in _CTD_REGION_GROUP:
        raise SystemExit(f"Survey-CTD O₂/pH not available for {region.id!r} "
                         f"(Bering only for now: {sorted(_CTD_REGION_GROUP)}).")

    # SEBS and NBS share the same source files — reuse the cached all-Bering station frame if it
    # already covers the requested years (so a second region doesn't re-download).
    group = _CTD_REGION_GROUP[region.id]
    cache = DATA_RAW / f"survey_ctd_stations_{group}.parquet"
    if cache.exists():
        stations = pd.read_parquet(cache)
        have = set(stations["year"].unique())
        if set(range(args.start, args.end + 1)) <= have:
            print(f"Reusing cached stations {cache.name} ({sorted(have)}).")
        else:
            stations = fetch_ctd_stations(args.start, args.end)
            save_parquet(stations, cache.name)
    else:
        stations = fetch_ctd_stations(args.start, args.end)
        if stations.empty:
            print("No CTD stations fetched — check connectivity / year range.")
            return
        save_parquet(stations, cache.name)

    clipped = clip_to_region(stations, region.id)
    annual = regional_annual_means(clipped)
    print(f"  {region.id}: {len(clipped)} stations → {len(annual)} survey years")
    save_parquet(annual, f"survey_ctd_observed_{region.id}.parquet")


if __name__ == "__main__":
    main()
