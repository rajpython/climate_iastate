#!/usr/bin/env python3
"""
OBL-029 Step 2: Monthly Aggregation + Climatology + Anomaly (Broad-Basin OISST)
==================================================================================
Reads all quarterly NetCDFs from Step 1 and produces:
  - Per-cell monthly mean SST (°C)
  - Per-cell ice flag monthly (fraction of days ice >= 0.15 per month)
  - Per-cell 1991-2020 monthly climatology (12 calendar months)
  - Per-cell monthly SST anomaly = monthly_mean - climatology (the LIM state input)
  - n_days: valid day count per cell per month

Output: data/interim/obl029/broadbasin_oisst_monthly.nc
  Dims: (time=534, lat=240, lon=480)   # 534 = Jan1982-Jun2026; Jun2026 is partial (15 days, n_days=15)
  Variables: sst_monthly_mean, ice_flag_monthly, sst_clim_monthly, sst_monthly_anom, n_days
  Note: ERDDAP ncdcOisst21Agg ends 2026-06-15T12:00:00Z. Q2 2026 covers Apr1-Jun15 (76 days).
        June 2026 n_days=15 (partial month). Climate indices end 2026-06 with publication-lag NaN.

Requires all 178 quarterly NetCDFs from Step 1 present in data/raw/obl029/quarterly/
  (178 includes 2026_Q2.nc = Apr 1 - Jun 15, 76 days; Jun is partial)

Run: /Users/rajpython/dev/acfr/.venv/bin/python scripts/obl029_02_monthly_aggregate.py
"""

import sys
from datetime import datetime, timezone, date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

PROJECT_ROOT  = Path("/Users/rajpython/dev/acfr/projects/sst-forecast-method-review")
QUARTERLY_DIR = PROJECT_ROOT / "data" / "raw" / "obl029" / "quarterly"
OUT_DIR       = PROJECT_ROOT / "data" / "interim" / "obl029"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_NC        = OUT_DIR / "broadbasin_oisst_monthly.nc"

BASELINE_START = 1991
BASELINE_END   = 2020
ICE_THRESHOLD  = 0.15  # NSIDC 15% threshold (consistent with OBL-022 G-T7)

YEAR_START = 1982
YEAR_END   = 2026
LAST_DATE  = "2026-06-16"  # ERDDAP dataset ends 2026-06-16 (Q2 2026: Apr-Jun 16, 77 days; Jun is partial)

QUARTERS = [
    ("Q1", "01", "03"),
    ("Q2", "04", "06"),
    ("Q3", "07", "09"),
    ("Q4", "10", "12"),
]


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] OBL-029 Step 2: monthly aggregation starting")

    # -----------------------------------------------------------------------
    # Enumerate and verify quarterly files
    # -----------------------------------------------------------------------
    last = date(int(LAST_DATE[:4]), int(LAST_DATE[5:7]), int(LAST_DATE[8:10]))
    tasks = []
    for year in range(YEAR_START, YEAR_END + 1):
        for q_label, q_m_start, q_m_end in QUARTERS:
            q_start_date = date(year, int(q_m_start), 1)
            if q_start_date > last:
                continue
            tasks.append((year, q_label))

    missing = []
    for year, q_label in tasks:
        fp = QUARTERLY_DIR / f"{year}_{q_label}.nc"
        if not fp.exists():
            missing.append(f"{year}_{q_label}")
    if missing:
        print(f"ERROR: {len(missing)} quarterly files missing. Run Step 1 first.")
        for m in missing[:5]:
            print(f"  MISSING: {m}")
        if len(missing) > 5:
            print(f"  ... and {len(missing)-5} more")
        sys.exit(1)

    print(f"  {len(tasks)} quarterly files found — all present")

    # -----------------------------------------------------------------------
    # Load all quarterly files, accumulate monthly sums
    # -----------------------------------------------------------------------
    first_fp = QUARTERLY_DIR / f"{tasks[0][0]}_{tasks[0][1]}.nc"
    with xr.open_dataset(str(first_fp)) as ds0:
        # ERDDAP OISST griddap files use 'latitude'/'longitude' coordinate names
        lat_coord = "latitude" if "latitude" in ds0.coords else "lat"
        lon_coord = "longitude" if "longitude" in ds0.coords else "lon"
        lat_vals = ds0[lat_coord].values.copy()
        lon_vals = ds0[lon_coord].values.copy()
    nlat, nlon = len(lat_vals), len(lon_vals)
    print(f"  Grid: {nlat} lat x {nlon} lon = {nlat*nlon:,} cells")

    monthly_accum = {}

    for idx, (year, q_label) in enumerate(tasks):
        fp = QUARTERLY_DIR / f"{year}_{q_label}.nc"
        if (idx + 1) % 20 == 0 or idx == 0:
            print(f"  Processing quarter {idx+1}/{len(tasks)}: {year}_{q_label}")
        with xr.open_dataset(str(fp)) as ds:
            times = pd.DatetimeIndex(ds.time.values)
            sst_arr = ds["sst"].values   # (time, lat, lon)
            ice_arr = ds["ice"].values   # (time, lat, lon)

        for i, t in enumerate(times):
            ym = (t.year, t.month)
            if ym not in monthly_accum:
                monthly_accum[ym] = {
                    "sst_sum": np.zeros((nlat, nlon), dtype=np.float64),
                    "sst_cnt": np.zeros((nlat, nlon), dtype=np.int32),
                    "ice_cnt": np.zeros((nlat, nlon), dtype=np.int32),
                    "n_days":  np.int32(0),
                }
            a = monthly_accum[ym]
            sst_slice = sst_arr[i]
            ice_slice = ice_arr[i]

            # QA: mask SST == exactly 0.0°C (int16=0 fill artifact in early OISST).
            # OISST v2.1 encodes missing data as _FillValue=-32768 (→NaN), but in some
            # early periods (1982-02/03, 1985-02) the ERDDAP returns int16=0 (→0.0°C)
            # for missing cells instead of the proper fill value. Threshold 0.005°C safely
            # catches only the exact-zero packed values; legitimate non-zero ocean SST
            # (incl. ice-proxy -1.8°C and polar near-zero) is unaffected.
            zero_fill = np.abs(sst_slice) < 0.005
            sst_slice = np.where(zero_fill, np.nan, sst_slice)

            valid_mask = ~np.isnan(sst_slice)
            a["sst_sum"] = np.where(valid_mask, a["sst_sum"] + sst_slice, a["sst_sum"])
            a["sst_cnt"] = np.where(valid_mask, a["sst_cnt"] + 1, a["sst_cnt"])
            ice_present = (~np.isnan(ice_slice)) & (ice_slice >= ICE_THRESHOLD)
            a["ice_cnt"] = np.where(valid_mask, a["ice_cnt"] + ice_present.astype(np.int32), a["ice_cnt"])
            a["n_days"] = a["n_days"] + np.int32(1)

    print(f"  Accumulated {len(monthly_accum)} year-month combinations")

    # -----------------------------------------------------------------------
    # Build monthly mean arrays
    # -----------------------------------------------------------------------
    sorted_yms = sorted(monthly_accum.keys())
    ntimes = len(sorted_yms)
    time_vals = np.array([np.datetime64(f"{ym[0]:04d}-{ym[1]:02d}-01") for ym in sorted_yms])

    sst_monthly  = np.full((ntimes, nlat, nlon), np.nan, dtype=np.float32)
    ice_frac_mon = np.full((ntimes, nlat, nlon), np.nan, dtype=np.float32)
    n_days_mon   = np.full((ntimes, nlat, nlon), 0, dtype=np.int16)

    for i, ym in enumerate(sorted_yms):
        a = monthly_accum[ym]
        cnt = a["sst_cnt"]
        valid = cnt > 0
        sst_monthly[i]  = np.where(valid, a["sst_sum"] / cnt, np.nan)
        ice_frac_mon[i] = np.where(valid, a["ice_cnt"] / cnt.clip(min=1), np.nan)
        n_days_mon[i]   = np.where(valid, cnt, 0).astype(np.int16)

    del monthly_accum

    # -----------------------------------------------------------------------
    # 1991-2020 monthly climatology
    # -----------------------------------------------------------------------
    print(f"  Computing 1991-2020 monthly climatology ...")
    sst_clim = np.full((12, nlat, nlon), np.nan, dtype=np.float32)
    for m in range(1, 13):
        base_mask = np.array([
            ym[1] == m and BASELINE_START <= ym[0] <= BASELINE_END
            for ym in sorted_yms
        ])
        if base_mask.sum() > 0:
            sst_clim[m-1] = np.nanmean(sst_monthly[base_mask], axis=0)

    # -----------------------------------------------------------------------
    # Monthly anomaly
    # -----------------------------------------------------------------------
    print(f"  Computing monthly anomaly ...")
    sst_anom = np.full((ntimes, nlat, nlon), np.nan, dtype=np.float32)
    for i, ym in enumerate(sorted_yms):
        sst_anom[i] = sst_monthly[i] - sst_clim[ym[1]-1]

    sst_clim_expanded = np.stack([sst_clim[ym[1]-1] for ym in sorted_yms], axis=0)

    # -----------------------------------------------------------------------
    # Build and save output Dataset
    # -----------------------------------------------------------------------
    print(f"  Building output Dataset (time={ntimes}, lat={nlat}, lon={nlon}) ...")

    ds_out = xr.Dataset(
        {
            "sst_monthly_mean": xr.DataArray(
                sst_monthly, dims=["time", "lat", "lon"],
                attrs={"long_name": "Monthly mean SST", "units": "degree_Celsius",
                       "baseline": "1991-2020 per-cell monthly climatology"}
            ),
            "ice_flag_monthly": xr.DataArray(
                ice_frac_mon, dims=["time", "lat", "lon"],
                attrs={"long_name": f"Fraction of days with ice >= {ICE_THRESHOLD}",
                       "units": "fraction [0,1]", "threshold": str(ICE_THRESHOLD),
                       "note": "NaN ice on valid SST cell = ice-free (OISST convention)"}
            ),
            "sst_clim_monthly": xr.DataArray(
                sst_clim_expanded, dims=["time", "lat", "lon"],
                attrs={"long_name": "Monthly SST climatology (1991-2020 baseline)",
                       "units": "degree_Celsius",
                       "baseline_period": f"{BASELINE_START}-{BASELINE_END}"}
            ),
            "sst_monthly_anom": xr.DataArray(
                sst_anom, dims=["time", "lat", "lon"],
                attrs={"long_name": "Monthly SST anomaly (deseasonalized, LIM state input)",
                       "units": "degree_Celsius",
                       "method": "sst_monthly_mean - sst_clim_monthly (1991-2020 baseline)"}
            ),
            "n_days": xr.DataArray(
                n_days_mon, dims=["time", "lat", "lon"],
                attrs={"long_name": "Valid day count per month-cell", "units": "days"}
            ),
        },
        coords={
            "time": xr.DataArray(time_vals, dims=["time"],
                                  attrs={"long_name": "Time (1st of month)"}),
            "lat":  xr.DataArray(lat_vals, dims=["lat"],
                                  attrs={"long_name": "Latitude", "units": "degrees_north"}),
            "lon":  xr.DataArray(lon_vals, dims=["lon"],
                                  attrs={"long_name": "Longitude (0-360)", "units": "degrees_east"}),
        },
        attrs={
            "title": "NOAA OISST v2.1 broad-basin monthly product (OBL-029)",
            "source": "Aggregated from ERDDAP ncdcOisst21Agg quarterly NetCDFs",
            "source_doi": "10.25921/RE9P-PT57",
            "domain": f"lat {lat_vals[0]:.3f}-{lat_vals[-1]:.3f}N, lon {lon_vals[0]:.3f}-{lon_vals[-1]:.3f}E (0-360)",
            "baseline_period": f"{BASELINE_START}-{BASELINE_END}",
            "ice_threshold": str(ICE_THRESHOLD),
            "lim_state_note": (
                "sst_monthly_anom is the LIM state input (deseasonalized monthly SST anomaly). "
                "Land cells are NaN. Ice-proxy SST retained. Lon: 0-360 deg E."
            ),
            "created": datetime.now(timezone.utc).isoformat(),
            "generating_script": "scripts/obl029_02_monthly_aggregate.py",
        }
    )

    enc = {
        "sst_monthly_mean":  {"zlib": True, "complevel": 4, "dtype": "float32"},
        "ice_flag_monthly":  {"zlib": True, "complevel": 4, "dtype": "float32"},
        "sst_clim_monthly":  {"zlib": True, "complevel": 4, "dtype": "float32"},
        "sst_monthly_anom":  {"zlib": True, "complevel": 4, "dtype": "float32"},
        "n_days":            {"zlib": True, "complevel": 4, "dtype": "int16"},
    }

    tmp_nc = OUT_NC.with_suffix(".nc.tmp")
    print(f"  Saving to {OUT_NC} ...")
    ds_out.to_netcdf(str(tmp_nc), encoding=enc)
    tmp_nc.rename(OUT_NC)

    sz_mb = OUT_NC.stat().st_size / 1e6
    print(f"  Saved: {OUT_NC} ({sz_mb:.1f} MB)")

    valid_cells = int(np.sum(~np.isnan(sst_anom[0])))
    anom_min = float(np.nanmin(sst_anom))
    anom_max = float(np.nanmax(sst_anom))
    print(f"\nQA Summary:")
    print(f"  Time steps:        {ntimes}")
    print(f"  Valid cells (t=0): {valid_cells:,} / {nlat*nlon:,}")
    print(f"  Anomaly range:     {anom_min:.2f} to {anom_max:.2f} °C")
    print(f"  Anomaly NaN frac:  {float(np.isnan(sst_anom).sum()) / sst_anom.size:.2%}")
    if anom_min < -15 or anom_max > 15:
        print(f"  WARNING: anomaly outside [-15, 15] — check fill value handling")
    print(f"\n[{datetime.now(timezone.utc).isoformat()}] Step 2 COMPLETE")


if __name__ == "__main__":
    main()
