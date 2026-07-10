#!/usr/bin/env python3
"""
OBL-029 Step 1: Broad-Basin OISST Daily Acquisition (ERDDAP HTTP griddap REST)
=================================================================================
Fetches NOAA OISST v2.1 daily SST and ice fraction over the broad North Pacific
+ Arctic domain. Quarterly chunks, checkpoint-based (skips existing quarterly files).

ACQUISITION PLAN (SDL-019 / A-007 open-boundary principle):
  Source:     NOAA OISST v2.1 AVHRR-Only (v02r01), same as OBL-019/022
  ERDDAP:     https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg
  Domain:     lat 20.125-79.875 deg N, lon 120.125-239.875 deg E (0-360 convention)
  Grid:       240 lat x 480 lon = 115,200 cells per day (17x OBL-022 GOA box)
  Period:     1982-01-01 -> 2026-06-30 (daily; aggregated to monthly in Step 2)
  Quarterly:  178 chunks, ~15-18 MB each, ~3.0 GB total interim
  Auth:       None (public ERDDAP, no credentials required)
  Note:       PSL THREDDS annual files tested but returned IncompleteRead on large files;
              ERDDAP quarterly approach confirmed working (same product, same grid)

DOMAIN RATIONALE (SDL-019 / A-007):
  - South 20 deg N: captures ENSO-forced North Pacific anomaly field
  - North 79.875 deg N: encompasses all 9 Alaska EEZ zones including Beaufort
  - West 120 deg E:  full Bering shelf (Russian side) + western Pacific jet entry
  - East 239.875 deg E (120.125 deg W): GOA and eastern North Pacific

Run: /Users/rajpython/dev/acfr/.venv/bin/python scripts/obl029_01_fetch_oisst_broadbasin.py
Re-run until "ACQUISITION COMPLETE" (checkpoint-based; skips existing quarterly files).
"""

import os
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
import xarray as xr

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT  = Path("/Users/rajpython/dev/acfr/projects/sst-forecast-method-review")
OUT_DIR       = PROJECT_ROOT / "data" / "raw" / "obl029"
QUARTERLY_DIR = OUT_DIR / "quarterly"
QUARTERLY_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT_DIR / "obl029_retrieval_log.txt"

ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg.nc"

# Broad basin (SDL-019 / A-007 open-boundary principle)
LAT_MIN, LAT_MAX = 20.125, 79.875   # 240 cells N-S
LON_MIN, LON_MAX = 120.125, 239.875 # 480 cells E-W (0-360 convention)

YEAR_START = 1982
YEAR_END   = 2026
LAST_DATE  = "2026-06-16"  # ERDDAP dataset ends 2026-06-16T12:00:00Z (verified via .das actual_range)

QUARTERS = [
    ("Q1", "01-01", "03-31"),
    ("Q2", "04-01", "06-30"),
    ("Q3", "07-01", "09-30"),
    ("Q4", "10-01", "12-31"),
]

MAX_RUN_S    = 7200   # 2-hour budget; enough to complete all remaining quarters
HTTP_TIMEOUT = 300    # per-request timeout (large domain needs longer)

ENCODING = {
    "sst": {"zlib": True, "complevel": 4, "dtype": "float32"},
    "ice": {"zlib": True, "complevel": 4, "dtype": "float32"},
}


def all_quarters():
    from datetime import datetime as dt
    last = dt(int(LAST_DATE[:4]), int(LAST_DATE[5:7]), int(LAST_DATE[8:10]))
    tasks = []
    for year in range(YEAR_START, YEAR_END + 1):
        for q_label, q_start, q_end in QUARTERS:
            q_s_dt = dt(year, int(q_start[:2]), int(q_start[3:]))
            if q_s_dt > last:
                continue
            q_e_dt = dt(year, int(q_end[:2]), int(q_end[3:]))
            t0 = q_s_dt.strftime("%Y-%m-%d")
            t1 = min(q_e_dt, last).strftime("%Y-%m-%d")
            tasks.append((year, q_label, t0, t1))
    return tasks


def quarter_path(year: int, q_label: str) -> Path:
    return QUARTERLY_DIR / f"{year}_{q_label}.nc"


def build_url(t0: str, t1: str) -> str:
    t0e = f"{t0}T12:00:00Z"
    t1e = f"{t1}T12:00:00Z"
    var_str = ",".join([
        f"{var}[({t0e}):1:({t1e})][0:1:0][({LAT_MIN}):1:({LAT_MAX})][({LON_MIN}):1:({LON_MAX})]"
        for var in ["sst", "ice"]
    ])
    return f"{ERDDAP_BASE}?{var_str}"


def fetch_quarter(year: int, q_label: str, t0: str, t1: str) -> str:
    dest     = quarter_path(year, q_label)
    dest_tmp = dest.with_suffix(".nc.tmp")
    raw_tmp  = dest.with_suffix(".nc.raw")
    t_q = time.time()

    try:
        max_retries = 3
        r = None
        for attempt in range(max_retries):
            url = build_url(t0, t1)
            try:
                r = requests.get(url, timeout=HTTP_TIMEOUT, stream=True)
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(15)
                    continue
                raise RuntimeError(f"Request timed out after {max_retries} attempts")
            if r.status_code == 200:
                break
            if r.status_code in (408, 429, 503):
                if attempt < max_retries - 1:
                    time.sleep(20 * (attempt + 1))
                    continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

        with open(raw_tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)

        ds_raw = xr.open_dataset(str(raw_tmp))
        sst_da = ds_raw["sst"].squeeze("zlev") if "zlev" in ds_raw["sst"].dims else ds_raw["sst"]
        ice_da = ds_raw["ice"].squeeze("zlev") if "zlev" in ds_raw["ice"].dims else ds_raw["ice"]

        sst_da = sst_da.where(sst_da > -9.0)
        ice_da = ice_da.where(ice_da >= 0.0)

        n_days   = int(len(sst_da.time))
        sst_vals = sst_da.values
        mean_sst = float(np.nanmean(sst_vals))
        nan_frac = float(np.isnan(sst_vals).mean())

        out = xr.Dataset(
            {
                "sst": sst_da.assign_attrs({
                    "long_name": "Sea Surface Temperature",
                    "units": "degree_Celsius",
                    "fill_mask": "sst < -9.0 set to NaN",
                }),
                "ice": ice_da.assign_attrs({
                    "long_name": "Sea Ice Fraction",
                    "units": "1",
                    "fill_mask": "ice < 0 set to NaN",
                }),
            },
            attrs={
                "title": "NOAA OISST v2.1 broad-basin quarterly chunk (OBL-029)",
                "erddap_dataset_id": "ncdcOisst21Agg",
                "product_doi": "10.25921/RE9P-PT57",
                "domain": f"lat {LAT_MIN}-{LAT_MAX}N lon {LON_MIN}-{LON_MAX}E (0-360)",
                "retrieved": datetime.now(timezone.utc).isoformat(),
            },
        )
        out.to_netcdf(str(dest_tmp), encoding=ENCODING)
        dest_tmp.rename(dest)
        ds_raw.close()

        elapsed = time.time() - t_q
        return (f"{year}_{q_label}: {n_days} days, mean_sst={mean_sst:.2f}°C, "
                f"nan_frac={nan_frac:.2%}, elapsed={elapsed:.0f}s, "
                f"size={dest.stat().st_size / 1e6:.1f}MB")
    finally:
        for p in [raw_tmp, dest_tmp]:
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass


def main():
    tasks       = all_quarters()
    total       = len(tasks)
    done_before = sum(1 for (y, q, t0, t1) in tasks if quarter_path(y, q).exists())

    log_lines = []
    def log(msg):
        ts   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        log_lines.append(line)

    log(f"OBL-029 OISST broad-basin ERDDAP quarterly fetch | {total} quarters | {done_before} already done")
    log(f"Domain: lat {LAT_MIN}-{LAT_MAX}N, lon {LON_MIN}-{LON_MAX}E | LAST_DATE={LAST_DATE}")

    t_start = time.time()
    done    = done_before
    failed  = []

    for year, q_label, t0, t1 in tasks:
        dest = quarter_path(year, q_label)
        if dest.exists():
            continue

        elapsed_total = time.time() - t_start
        if elapsed_total > MAX_RUN_S:
            log(f"Run budget ({MAX_RUN_S}s) reached. Done {done - done_before} new quarters. Re-run to continue.")
            break

        try:
            status = fetch_quarter(year, q_label, t0, t1)
            done  += 1
            log(f"OK  [{done}/{total}] {status}")
        except Exception as e:
            failed.append((year, q_label, str(e)))
            log(f"ERR [{year}_{q_label}] {e}")

    old_log = LOG_PATH.read_text() if LOG_PATH.exists() else ""
    LOG_PATH.write_text(old_log + "\n".join(log_lines) + "\n")

    done_after = sum(1 for (y, q, t0, t1) in tasks if quarter_path(y, q).exists())
    print(f"\n--- Summary ---")
    print(f"Total quarters: {total}  |  Done: {done_after}  |  Remaining: {total - done_after}")
    if failed:
        print(f"Failures this run ({len(failed)}): {failed}")
    if done_after == total:
        print("ACQUISITION COMPLETE — all quarterly files present.")
    else:
        print(f"Re-run to fetch remaining {total - done_after} quarters.")


if __name__ == "__main__":
    main()
