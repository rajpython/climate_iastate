"""Modelled EBS cold-pool index from regional ocean-model bottom temperature.

Derives an annual cold-pool series (area below temperature thresholds + mean shelf
bottom temperature) from a regional model's summer bottom-temperature field, on the
EBS **shelf** (the deep Bering basin is cold year-round and is *not* the cold pool, so
a depth mask is essential). Source-agnostic: works for any
:class:`~mhw.bottom.sources.BottomSource` via :mod:`mhw.bottom.loader`.

Comparability caveat (read before trusting absolute areas)
----------------------------------------------------------
The AFSC *observed* index is computed over the exact bottom-trawl **survey strata**
(~495,000 km²) at **survey time**. This modelled index uses a depth-masked EBS-shelf
*domain* and a fixed summer week, so **absolute areas run larger than observed** and
are not strata-matched. The defensible comparisons are therefore (1) the **interannual
pattern** and (2) **mean shelf bottom temperature** (an intensive quantity, far less
sensitive to the exact footprint). Strata-matched comparison (the ACLIM
survey-replicated series) is the rigorous next step.

CLI: mhw-build-coldpool-model --source bering10k --region ebs --start 1982 --end 2024
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.bottom.loader import load_bottom_temp, open_bottom_dataset
from mhw.bottom.regions import BOTTOM_REGIONS, EBS, BottomRegion, get_region
from mhw.bottom.position import cold_pool_position
from mhw.bottom.regrid import regrid_curvilinear_to_regular
from mhw.bottom.sources import SOURCES, BottomSource, BERING10K_K20_CORECFS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

# Cold-pool analysis parameters shared across cold-pool regions (EBS, NBS). The analysis
# grid and shelf-depth rule are per-region — see mhw.bottom.regions.BottomRegion.
THRESHOLDS_C = (2.0, 1.0, 0.0, -1.0)
_THRESH_COL = {2.0: "area_lte2_km2", 1.0: "area_lte1_km2", 0.0: "area_lte0_km2", -1.0: "area_lteminus1_km2"}
SURVEY_TARGET_MD = "07-04"   # representative survey-time week (mid-survey)
_KM_PER_DEG = 111.0


# ---------------------------------------------------------------------------
# Pure helpers (network-free, unit-testable)
# ---------------------------------------------------------------------------

def cell_area_km2(tgt_lats: np.ndarray, tgt_lons: np.ndarray, dlat: float = 0.25, dlon: float = 0.25) -> np.ndarray:
    """Per-cell area (km²) of a regular grid, cosine-latitude weighted."""
    lat_km = dlat * _KM_PER_DEG
    lon_km = dlon * _KM_PER_DEG * np.cos(np.deg2rad(tgt_lats))
    return (lat_km * lon_km)[:, None] * np.ones((1, tgt_lons.size))


def coldpool_area_km2(temp_grid: np.ndarray, shelf: np.ndarray, areas: np.ndarray, threshold: float) -> float:
    """Total shelf area (km²) where bottom temperature ≤ *threshold* (NaN-safe)."""
    sel = shelf & np.isfinite(temp_grid) & (temp_grid <= threshold)
    return float(np.sum(areas[sel]))


def mean_shelf_bottom_temp(temp_grid: np.ndarray, shelf: np.ndarray, areas: np.ndarray) -> float:
    """Area-weighted mean bottom temperature (°C) over valid shelf cells."""
    sel = shelf & np.isfinite(temp_grid)
    if not sel.any():
        return float("nan")
    return float(np.sum(temp_grid[sel] * areas[sel]) / np.sum(areas[sel]))


# ---------------------------------------------------------------------------
# Model ingest
# ---------------------------------------------------------------------------

def _shelf_mask_cache(region: BottomRegion) -> Path:
    return DERIVED / f"{region.id}_shelf_mask.npz"


def shelf_mask_from_model(ds: xr.Dataset, source: BottomSource,
                          region: BottomRegion = EBS) -> np.ndarray:
    """Regrid the model bottom depth and return a boolean shelf mask (≤ region depth).

    Bering10K exposes bottom depth as the ``z_w`` bottom interface; if no depth
    variable is found, fall back to 'all valid cells are shelf' (caller is warned).
    """
    tgt_lats, tgt_lons = region.analysis_lats, region.analysis_lons
    depth2d = None
    if "z_w" in ds:
        depth2d = (-ds["z_w"].isel({source.time_coord: 0, "s_w": 0})).values
    lat2d = ds[source.lat_coord].values
    lon2d = ds[source.lon_coord].values
    if depth2d is None:
        warnings.warn(f"{source.id}: no bottom-depth variable; shelf mask = full domain.")
        return np.ones((tgt_lats.size, tgt_lons.size), dtype=bool)
    depth_g = regrid_curvilinear_to_regular(lat2d, lon2d, depth2d, tgt_lats, tgt_lons, fill_nearest=False)
    mask = np.isfinite(depth_g) & (depth_g <= region.shelf_max_depth_m)
    if region.shelf_min_depth_m > 0:           # slope/deep bands: exclude the shallow shelf
        mask &= depth_g > region.shelf_min_depth_m
    return mask


def build_shelf_mask(region: BottomRegion = EBS, force: bool = False) -> np.ndarray:
    """Return the shared shelf mask on *region*'s 0.25° grid, building+caching if needed.

    The depth source is per-region (``region.mask_source``):
      * ``"bering10k"`` (Bering: EBS/NBS/slope) — derived from Bering10K's own z_w bathymetry,
        the validated, modeler-tuned depth for the Bering.
      * ``"etopo2022"`` (GOA/AI/Arctic) — a standalone global bathymetry, so the mask can be
        built where Bering10K is out of domain. Shown equivalent to the Bering10K mask on
        EBS/NBS cold-pool metrics (B1), so the Bering deliberately keeps Bering10K.
    Either way all model sources share the *identical* footprint, keeping them comparable.
    """
    if region.mask_source == "etopo2022":
        from mhw.bottom.bathymetry import shelf_mask_from_bathymetry
        return shelf_mask_from_bathymetry(region, force=force)
    cache = _shelf_mask_cache(region)
    if cache.exists() and not force:
        return np.load(cache)["shelf"]
    ds = open_bottom_dataset(BERING10K_K20_CORECFS)
    shelf = shelf_mask_from_model(ds, BERING10K_K20_CORECFS, region)
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.savez(cache, shelf=shelf, lats=region.analysis_lats, lons=region.analysis_lons)
    return shelf


def _nearest_summer_field(source: BottomSource, ds: xr.Dataset, year: int,
                          target_md: str = SURVEY_TARGET_MD, monthly: bool = False):
    """Return the model bottom-temp field for *year*.

    ``monthly=False`` (default): the single time step nearest *target_md* (a weekly
    snapshot for Bering10K, the July month for MOM6). ``monthly=True``: the **July
    monthly mean** — used to put weekly Bering10K on the same cadence as monthly MOM6
    for a like-for-like model-vs-model comparison.
    """
    da = load_bottom_temp(source, start=f"{year}-05-15", end=f"{year}-09-15", ds=ds)
    if da.sizes["time"] == 0:
        return None
    if monthly:
        jul = da.sel(time=da["time"].dt.month == 7)
        if jul.sizes["time"] == 0:
            return None
        return jul.mean("time")
    target = np.datetime64(f"{year}-{target_md}")
    idx = int(np.abs(da["time"].values - target).argmin())
    return da.isel(time=idx)


def build_model_coldpool_series(
    source: BottomSource = BERING10K_K20_CORECFS,
    start: int = 1982,
    end: int = 2024,
    target_md: str = SURVEY_TARGET_MD,
    monthly: bool = False,
    region: BottomRegion = EBS,
) -> pd.DataFrame:
    """Compute the annual modelled cold-pool series for *source* over *region*.

    Works for any source via the loader's grid-agnostic contract: Bering10K is weekly
    + curvilinear; MOM6 NEP is monthly + rectilinear. With ``monthly=False`` the
    summer-week selector picks the time step nearest *target_md*; with ``monthly=True``
    it uses the July monthly mean (so weekly + monthly sources land on identical
    cadence). All sources share one region shelf mask (see :func:`build_shelf_mask`).
    """
    ds = open_bottom_dataset(source)
    lats, lons = region.analysis_lats, region.analysis_lons
    shelf = build_shelf_mask(region)  # shared footprint for all sources → models comparable
    areas = cell_area_km2(lats, lons)
    print(f"{source.id}: shared {region.id.upper()} shelf cells = {int(shelf.sum())} "
          f"(~{areas[shelf].sum():,.0f} km²){' [July monthly mean]' if monthly else ''}")

    rows = []
    for year in range(start, end + 1):
        field = _nearest_summer_field(source, ds, year, target_md, monthly=monthly)
        if field is None:
            continue
        grid = regrid_curvilinear_to_regular(
            field.lat.values, field.lon.values, field.values, lats, lons, fill_nearest=False)
        row = {"year": year, "source": source.id,
               "mean_bottom_temp": round(mean_shelf_bottom_temp(grid, shelf, areas), 4)}
        for thr in THRESHOLDS_C:
            row[_THRESH_COL[thr]] = round(coldpool_area_km2(grid, shelf, areas, thr), 1)
        if region.product_kind == "cold_pool":
            # Derived position indicator (southern extent = p05 latitude of ≤2 °C shelf cells).
            sext = cold_pool_position(grid, shelf, lats, lons, threshold=2.0)
            row["southern_extent_lat"] = None if not np.isfinite(sext) else round(sext, 3)
        rows.append(row)
        print(f"  {year}: ≤2 °C = {row['area_lte2_km2']:,.0f} km²  "
              f"mean BT = {row['mean_bottom_temp']:.2f} °C")
    return pd.DataFrame(rows)


def save_parquet(df: pd.DataFrame, source: BottomSource, monthly: bool = False,
                 region: BottomRegion = EBS) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    suffix = "_monthly" if monthly else ""
    out = DERIVED / f"coldpool_model_{source.id}_{region.id}{suffix}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build the modelled EBS cold-pool series from a regional ocean model.")
    p.add_argument("--source", default="bering10k", choices=sorted(SOURCES), help="Bottom source id")
    p.add_argument("--region", default="sebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--start", type=int, default=1982, help="First year")
    p.add_argument("--end", type=int, default=2024, help="Last year")
    p.add_argument("--monthly", action="store_true",
                   help="Use the July monthly mean (matches MOM6's cadence) for a "
                        "like-for-like model-vs-model comparison.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source = SOURCES[args.source]
    region = get_region(args.region)
    df = build_model_coldpool_series(source, start=args.start, end=args.end,
                                     monthly=args.monthly, region=region)
    if df.empty:
        print("No years produced — check connectivity / year range.")
        return
    save_parquet(df, source, monthly=args.monthly, region=region)


if __name__ == "__main__":
    main()
