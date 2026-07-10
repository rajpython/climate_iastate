#!/usr/bin/env python3
"""
OBL-029 Step 4: Per-Zone SST Anomaly from Broad-Basin Field
=============================================================
Aggregates the broad-basin monthly SST anomaly field (from Step 2) to the 9
Alaska EEZ leaf zones using the dashboard masks (region_masks.zarr) and
cosine-latitude weights (weights.zarr) from the verified seal tarball.

This produces the SDL-018 predictand component: per-zone continuous SST anomaly
(area_frac / conditional means were in snap-obl028; this fills the SST-anom gap).

Aggregation contract (consistent with OBL-028):
  sst_anom_zone[t] = Σ_g(w_g * sst_anom_g[t]) / Σ_g(w_g)
  where g = cells in zone mask with valid (non-NaN) SST anomaly at time t.

Inputs:
  - data/interim/obl029/broadbasin_oisst_monthly.nc  (Step 2 output)
  - data/work/obl028-unpack/data/derived/masks/region_masks.zarr  (dashboard masks)
  - data/work/obl028-unpack/data/derived/weights/weights.zarr     (cos-lat weights)

Output: data/interim/obl029/zone_sst_anom_monthly.csv
  Columns: time, sst_anom_wgoa, sst_anom_egoa, sst_anom_ai_west,
           sst_anom_ai_central, sst_anom_ai_east, sst_anom_sebs,
           sst_anom_nbs, sst_anom_chukchi, sst_anom_beaufort

Run: /Users/rajpython/dev/acfr/.venv/bin/python scripts/obl029_04_zone_sst_anomaly.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import zarr

PROJECT_ROOT   = Path("/Users/rajpython/dev/acfr/projects/sst-forecast-method-review")
MONTHLY_NC     = PROJECT_ROOT / "data" / "interim" / "obl029" / "broadbasin_oisst_monthly.nc"
UNPACK_DIR     = PROJECT_ROOT / "data" / "work" / "obl028-unpack"
MASKS_ZARR     = UNPACK_DIR / "data" / "derived" / "masks" / "region_masks.zarr"
WEIGHTS_ZARR   = UNPACK_DIR / "data" / "derived" / "weights" / "weights.zarr"
OUT_DIR        = PROJECT_ROOT / "data" / "interim" / "obl029"
OUT_CSV        = OUT_DIR / "zone_sst_anom_monthly.csv"

# 9 leaf zones (same as OBL-028 LEAF_ZONES)
LEAF_ZONES = ["wgoa", "egoa", "ai_west", "ai_central", "ai_east", "sebs", "nbs", "chukchi", "beaufort"]

# Global OISST 0.25° grid parameters (same as OBL-028)
GLOBAL_LAT0 = -89.875
GLOBAL_LON0 = -179.875
GRID_STEP   = 0.25


def lon_0_360_to_global_col(lon_0_360: np.ndarray) -> np.ndarray:
    """Convert 0-360 lon to global column index (0-1439) in the -180/180 grid."""
    # First convert 0-360 to -180/180
    lon_180 = np.where(lon_0_360 > 180.0, lon_0_360 - 360.0, lon_0_360)
    # Then to global col index
    col = np.round((lon_180 - GLOBAL_LON0) / GRID_STEP).astype(int)
    return col


def lat_to_global_row(lat: np.ndarray) -> np.ndarray:
    """Convert latitude to global row index (0-719)."""
    return np.round((lat - GLOBAL_LAT0) / GRID_STEP).astype(int)


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] OBL-029 Step 4: zone SST anomaly aggregation")

    # -----------------------------------------------------------------------
    # Check inputs
    # -----------------------------------------------------------------------
    for p in [MONTHLY_NC, MASKS_ZARR, WEIGHTS_ZARR]:
        if not p.exists():
            print(f"ERROR: Missing input: {p}")
            sys.exit(1)

    # -----------------------------------------------------------------------
    # Load broad-basin monthly anomaly
    # -----------------------------------------------------------------------
    print(f"  Loading {MONTHLY_NC} ...")
    ds = xr.open_dataset(str(MONTHLY_NC))
    sst_anom = ds["sst_monthly_anom"].values   # (time, lat, lon)  float32
    lat_vals = ds.lat.values                    # 240 values, 20.125 to 79.875 N
    lon_vals = ds.lon.values                    # 480 values, 120.125 to 239.875 E (0-360)
    time_vals = pd.DatetimeIndex(ds.time.values)
    ntimes, nlat, nlon = sst_anom.shape
    print(f"  Loaded: shape={sst_anom.shape}, time={time_vals[0].date()}..{time_vals[-1].date()}")

    # Map broad-basin lat/lon to global grid indices
    lat_rows = lat_to_global_row(lat_vals)      # (240,)
    lon_cols = lon_0_360_to_global_col(lon_vals) # (480,)

    # -----------------------------------------------------------------------
    # Load global masks and weights
    # -----------------------------------------------------------------------
    print(f"  Loading masks from {MASKS_ZARR} ...")
    zm = zarr.open(str(MASKS_ZARR), mode="r")
    zw = zarr.open(str(WEIGHTS_ZARR), mode="r")

    # Global weights (720×1440)
    global_weights = zw["weights"][:]   # cosine-latitude weights, shape (720, 1440)

    # -----------------------------------------------------------------------
    # For each zone, extract the mask subset overlapping the broad basin
    # -----------------------------------------------------------------------
    results = {z: np.full(ntimes, np.nan, dtype=np.float32) for z in LEAF_ZONES}

    for zone in LEAF_ZONES:
        if zone not in zm:
            print(f"  WARNING: zone '{zone}' not found in masks zarr; skipping")
            continue

        # Global mask (720×1440), boolean
        zone_mask_global = zm[zone][:].astype(bool)   # shape (720, 1440)

        # Build the 2-D index arrays for the broad basin into the global grid
        # lat_rows: (nlat,) row indices in global grid
        # lon_cols: (nlon,) col indices in global grid
        # We create 2D arrays via broadcasting
        rows_2d = np.broadcast_to(lat_rows[:, None], (nlat, nlon))  # (240, 480)
        cols_2d = np.broadcast_to(lon_cols[None, :], (nlat, nlon))  # (240, 480)

        # Clip to valid global grid range (safety)
        valid_rc = (rows_2d >= 0) & (rows_2d < 720) & (cols_2d >= 0) & (cols_2d < 1440)

        # Zone membership for each broad-basin cell
        in_zone = np.zeros((nlat, nlon), dtype=bool)
        in_zone[valid_rc] = zone_mask_global[rows_2d[valid_rc], cols_2d[valid_rc]]

        # Weights for broad-basin cells in zone
        zone_weights = np.zeros((nlat, nlon), dtype=np.float64)
        zone_weights[valid_rc] = global_weights[rows_2d[valid_rc], cols_2d[valid_rc]]
        zone_weights = np.where(in_zone, zone_weights, 0.0)

        n_cells = int(in_zone.sum())
        if n_cells == 0:
            print(f"  WARNING: zone '{zone}' has 0 cells in broad-basin domain")
            continue

        print(f"  Zone {zone:12s}: {n_cells:5d} broad-basin cells")

        # Aggregate: weighted mean over zone cells at each time step
        for t in range(ntimes):
            anom_t = sst_anom[t].astype(np.float64)   # (nlat, nlon)
            valid_t = ~np.isnan(anom_t) & in_zone
            w_valid = np.where(valid_t, zone_weights, 0.0)
            w_sum = w_valid.sum()
            if w_sum > 0:
                results[zone][t] = float(np.sum(w_valid * np.where(valid_t, anom_t, 0.0)) / w_sum)

    ds.close()

    # -----------------------------------------------------------------------
    # Build output DataFrame
    # -----------------------------------------------------------------------
    df = pd.DataFrame({"time": time_vals.strftime("%Y-%m-%d")})
    for zone in LEAF_ZONES:
        df[f"sst_anom_{zone}"] = results[zone]

    # -----------------------------------------------------------------------
    # QA check
    # -----------------------------------------------------------------------
    print(f"\nQA Summary:")
    print(f"  Rows: {len(df)} (expected 534 for 1982-01 to 2026-06)")
    for col in df.columns[1:]:
        vals = df[col].dropna()
        n_nan = len(df) - len(vals)
        if len(vals) > 0:
            print(f"  {col:25s}: {len(vals)} valid, {n_nan} NaN, range [{vals.min():.2f}, {vals.max():.2f}] °C")
        else:
            print(f"  {col:25s}: ALL NaN — check mask overlap with broad-basin domain")

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    df.to_csv(str(OUT_CSV), index=False, float_format="%.4f")
    print(f"\n  Saved: {OUT_CSV} ({OUT_CSV.stat().st_size / 1e3:.0f} KB)")
    print(f"[{datetime.now(timezone.utc).isoformat()}] Step 4 COMPLETE")


if __name__ == "__main__":
    main()
