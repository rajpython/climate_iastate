"""Depth-binned bottom-temperature profile for the model-only Arctic regions.

Backs the dashboard's Simpson's-paradox explanation on the Chukchi/Beaufort bottom-temperature
pages: the whole-shelf *mean* differs between the two shelves mostly because of their different
**depth distributions**, not because the water is warmer — so the page shows bottom temperature by
depth bin (area-weighted
bottom temperature *by depth bin*) and each bin's share of shelf area. Climatology: MOM6 NEP10k,
Jul–Sep, 2014–2024, area-weighted (cos-lat) on each region's analysis grid, ETOPO ≤ 200 m shelf.

CLI: mhw-build-arctic-profile
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from mhw.bottom.bathymetry import build_region_depth
from mhw.bottom.coldpool import cell_area_km2
from mhw.bottom.loader import load_bottom_temp, open_bottom_dataset
from mhw.bottom.regions import BEAUFORT, CHUKCHI, BottomRegion
from mhw.bottom.regrid import regrid_curvilinear_to_regular
from mhw.bottom.sources import MOM6_NEP

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

BINS = [(0, 10), (10, 20), (20, 30), (30, 50), (50, 100), (100, 200)]


# ---------------------------------------------------------------------------
# Pure helper (network-free, unit-testable)
# ---------------------------------------------------------------------------

def depth_profile_table(depth: np.ndarray, area: np.ndarray, bt: np.ndarray,
                        bins: list[tuple[int, int]] = BINS) -> pd.DataFrame:
    """Area-weighted bottom temperature and shelf-area share per depth bin.

    ``depth``/``area``/``bt`` are (lat, lon) on the same grid. Shelf = finite depth ≤ deepest bin
    and finite ``bt``. Returns one row per bin: depth_bin, depth_lo/hi, mean_bottom_temp, area_pct
    (share of total shelf area), n_cells.
    """
    shelf = np.isfinite(depth) & (depth <= bins[-1][1]) & np.isfinite(bt)
    tot = float(area[shelf].sum()) if shelf.any() else 0.0
    rows = []
    for lo, hi in bins:
        b = shelf & (depth > lo) & (depth <= hi)
        if not b.any() or tot == 0.0:
            rows.append({"depth_bin": f"{lo}–{hi} m", "depth_lo": lo, "depth_hi": hi,
                         "mean_bottom_temp": np.nan, "area_pct": 0.0, "n_cells": 0})
            continue
        w = area[b]
        rows.append({"depth_bin": f"{lo}–{hi} m", "depth_lo": lo, "depth_hi": hi,
                     "mean_bottom_temp": round(float(np.sum(bt[b] * w) / np.sum(w)), 2),
                     "area_pct": round(100 * float(w.sum()) / tot, 1), "n_cells": int(b.sum())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_profile(regions=(CHUKCHI, BEAUFORT), start: str = "2014-07-01",
                  end: str = "2024-09-30") -> pd.DataFrame:
    """Jul–Sep climatology bottom-temperature depth profile for each Arctic region (one frame, a ``region`` column)."""
    mds = open_bottom_dataset(MOM6_NEP)
    da = load_bottom_temp(MOM6_NEP, start, end, ds=mds)
    jas = da.sel(time=da["time"].dt.month.isin([7, 8, 9])).mean("time")   # climatology field
    out = []
    for reg in regions:
        if not isinstance(reg, BottomRegion):
            continue
        depth = build_region_depth(reg)
        area = cell_area_km2(reg.analysis_lats, reg.analysis_lons)
        bt = regrid_curvilinear_to_regular(jas.lat.values, jas.lon.values, jas.values,
                                           reg.analysis_lats, reg.analysis_lons, fill_nearest=False)
        tab = depth_profile_table(depth, area, bt)
        tab.insert(0, "region", reg.id)
        whole = float(np.sum(bt[np.isfinite(depth) & (depth <= 200) & np.isfinite(bt)] *
                             area[np.isfinite(depth) & (depth <= 200) & np.isfinite(bt)]) /
                      area[np.isfinite(depth) & (depth <= 200) & np.isfinite(bt)].sum())
        tab["whole_shelf_mean"] = round(whole, 2)
        print(f"{reg.id}: whole-shelf {whole:+.2f} °C; "
              + ", ".join(f"{r.depth_bin}:{r.mean_bottom_temp:+.1f}({r.area_pct:.0f}%)"
                          for r in tab.itertuples()))
        out.append(tab)
    return pd.concat(out, ignore_index=True)


def save_parquet(df: pd.DataFrame) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = DERIVED / "depth_profile_arctic.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Arctic bottom-temperature depth profile (Chukchi & Beaufort).")
    p.add_argument("--start", default="2014-07-01")
    p.add_argument("--end", default="2024-09-30")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df = build_profile(start=args.start, end=args.end)
    save_parquet(df)


if __name__ == "__main__":
    main()
