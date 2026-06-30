"""Observed shelf *surface* temperature from NOAA OISST — the bottom-vs-surface diagnostic.

Pairs the modelled shelf *bottom* temperature with an **observed surface** series so the two can
be read together as a stratification / coupling diagnostic: where bottom ≈ surface the shelf is
well-mixed; a large summer gap means strong stratification (the cold pool; the ice-melt-capped
Arctic). This is a thermal-structure diagnostic, **not** a validation of bottom temperature —
surface and bottom are different quantities and decouple under summer stratification.

OISST sea-surface temperature under sea ice sits at the freezing point, so we average **open-water
shelf** cells only (ice concentration < a threshold), area-weighted, over the summer window. The
shelf is the ETOPO ≤ ``shelf_max_depth_m`` mask on the OISST grid. OISST is fetched per region by
the MHW engine (``data/raw/oisst_<region>_<year>.nc``, with ``sst`` and ``ice``).

CLI: mhw-build-shelf-surface --region goa
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.bottom.bathymetry import depth_grid_for
from mhw.bottom.coldpool import cell_area_km2
from mhw.bottom.loader import load_bottom_temp, open_bottom_dataset
from mhw.bottom.regions import BOTTOM_REGIONS, EBS, BottomRegion, get_region
from mhw.bottom.regrid import regrid_curvilinear_to_regular
from mhw.bottom.sources import SOURCES

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

_SUMMER_MONTHS = (7, 8, 9)
_ICE_MAX = 0.15        # exclude cells with ≥15% summer ice (OISST SST there is the freezing point)


# ---------------------------------------------------------------------------
# Pure helper (network-free, unit-testable)
# ---------------------------------------------------------------------------

def daily_then_time_mean(field: np.ndarray, sst: np.ndarray, ice: np.ndarray,
                         shelf: np.ndarray, areas: np.ndarray,
                         ice_max: float = _ICE_MAX) -> tuple[float, int]:
    """Daily-then-time mean of *field* over the open-water shelf (per-timestep ice mask).

    For each timestep, area-weight-average *field* over the cells that are **open water that
    step** (on the shelf, SST finite, ice < ``ice_max`` with NaN ice = open, *field* finite);
    then average those daily values over the window. This naturally down-weights cells that are
    open only briefly — they contribute on just their open days — rather than weighting every
    ever-open cell equally. ``field``/``sst``/``ice`` are ``(time, lat, lon)``; ``shelf``/``areas``
    are ``(lat, lon)``. Returns (mean, mean daily open-cell count); NaN/0 if never open.
    """
    open_t = (shelf[None, :, :] & np.isfinite(sst) & np.isfinite(field) & ~(ice >= ice_max))
    w = open_t * areas[None, :, :]
    den = w.sum(axis=(1, 2))                       # per-day open-water area weight
    num = (np.where(open_t, field, 0.0) * areas[None, :, :]).sum(axis=(1, 2))
    good = den > 0
    if not good.any():
        return float("nan"), 0
    daily = num[good] / den[good]                  # one open-water-shelf mean per day
    daily_cells = open_t.sum(axis=(1, 2))[good]
    return float(daily.mean()), int(round(float(daily_cells.mean())))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _oisst_files(region: BottomRegion) -> list[str]:
    return sorted(glob.glob(str(DATA_RAW / f"oisst_{region.id}_*.nc")))


def _squeeze_zlev(da: xr.DataArray) -> xr.DataArray:
    return da.isel(zlev=0) if "zlev" in da.dims else da


def build_shelf_surface_series(region: BottomRegion = EBS, months=_SUMMER_MONTHS,
                               ice_max: float = _ICE_MAX, model_bottom: bool | None = None) -> pd.DataFrame:
    """Annual summer open-water shelf-mean OISST SST for *region* (one row/year).

    For **model-only** regions (the Arctic — no survey), also co-locate the modelled bottom: the
    summer-mean MOM6 bottom temperature regridded to the OISST grid and averaged over the **same
    open-water shelf cells and the same window** → a ``model_bottom_temp`` column, so the surface
    and bottom on the page are co-located in space and time.
    """
    files = _oisst_files(region)
    if not files:
        return pd.DataFrame()
    if model_bottom is None:
        model_bottom = region.observed is None and not region.has_survey_hauls
    ds0 = xr.open_dataset(files[0])
    lat = np.sort(ds0["lat"].values)
    lon = np.sort(ds0["lon"].values)
    depth = depth_grid_for(lat, lon)                       # ETOPO depth on the OISST grid
    shelf = np.isfinite(depth) & (depth <= region.shelf_max_depth_m)
    areas = cell_area_km2(lat, lon)
    print(f"{region.id}: OISST grid {shelf.shape}, shelf cells (≤{region.shelf_max_depth_m:.0f} m) "
          f"= {int(shelf.sum())}{' [+ co-located model bottom]' if model_bottom else ''}")

    msrc = mds = None
    if model_bottom:
        msrc = SOURCES[region.valid_sources[0]]            # MOM6 NEP for the Arctic
        mds = open_bottom_dataset(msrc)

    rows = []
    for f in files:
        yr = int(Path(f).stem.split("_")[-1])
        ds = xr.open_dataset(f).sortby("lat").sortby("lon")
        summer = ds.sel(time=ds["time"].dt.month.isin(months))
        if summer["time"].size == 0:
            continue
        sst = _squeeze_zlev(summer["sst"]).values            # (time, lat, lon) daily
        ice = _squeeze_zlev(summer["ice"]).values
        mean_sst, n = daily_then_time_mean(sst, sst, ice, shelf, areas, ice_max)
        row = {"year": yr, "mean_surface_temp": round(mean_sst, 4) if np.isfinite(mean_sst) else None,
               "n_open_cells": n}
        if model_bottom and n > 0:
            # Co-locate the model bottom: build a daily field where each day carries its month's
            # MOM6 bottom (regridded to the OISST grid), then average over the SAME per-day open
            # cells and the SAME days as the surface.
            bottom_daily = _daily_model_bottom(msrc, mds, yr, months, summer["time"].values, lat, lon)
            if bottom_daily is not None:
                bt, _ = daily_then_time_mean(bottom_daily, sst, ice, shelf, areas, ice_max)
                row["model_bottom_temp"] = round(bt, 4) if np.isfinite(bt) else None
        rows.append(row)
        msg = f"{mean_sst:.2f} °C (n~{n})" if np.isfinite(mean_sst) else "no open water"
        print(f"  {yr}: surface {msg}" + (f", model bottom {row.get('model_bottom_temp')}" if model_bottom else ""))
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def _daily_model_bottom(src, mds, year: int, months, times, lat: np.ndarray,
                        lon: np.ndarray) -> np.ndarray | None:
    """Build a (time, lat, lon) model-bottom field on the OISST grid, each OISST day carrying its
    month's MOM6 bottom (regridded). None if the model has no data for the window."""
    da = load_bottom_temp(src, start=f"{year}-{months[0]:02d}-01",
                          end=f"{year}-{months[-1]:02d}-30", ds=mds)
    if da.sizes["time"] == 0:
        return None
    by_month = {}
    for i in range(da.sizes["time"]):
        step = da.isel(time=i)
        m = int(pd.Timestamp(step["time"].values).month)
        by_month[m] = regrid_curvilinear_to_regular(step.lat.values, step.lon.values,
                                                     step.values, lat, lon, fill_nearest=False)
    nan2d = np.full((lat.size, lon.size), np.nan)
    day_months = pd.DatetimeIndex(times).month
    return np.stack([by_month.get(int(m), nan2d) for m in day_months])


def save_parquet(df: pd.DataFrame, region: BottomRegion) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = DERIVED / f"oisst_shelf_surface_{region.id}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build observed summer open-water shelf-surface SST (OISST).")
    p.add_argument("--region", default="sebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    region = get_region(args.region)
    df = build_shelf_surface_series(region)
    if df.empty:
        print(f"No OISST files for {region.id} (data/raw/oisst_{region.id}_*.nc) — nothing built.")
        return
    save_parquet(df, region)


if __name__ == "__main__":
    main()
