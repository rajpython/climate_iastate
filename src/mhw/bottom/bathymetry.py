"""Region shelf-depth grid from a standalone global bathymetry (model-agnostic mask source).

The shelf mask (depth ≤ ``region.shelf_max_depth_m``, optionally > ``shelf_min_depth_m``) was
originally derived from Bering10K's internal ``z_w`` bathymetry, which only exists where
Bering10K covers (the Bering). This module derives the same per-cell depth from a standalone
global bathymetry (ETOPO 2022, NOAA NCEI) so the mask can be built for ANY region — GOA, AI,
the Arctic — and so every model shares an identical, model-neutral footprint.

Method (see docs/bathymetry_mask_plan.md): fetch ETOPO over the region's bounds (longitude on
ETOPO's native 0–360°), then **bin to the region's 0.25° analysis grid as the mean ocean depth
per cell** (a 0.25° cell is "shelf" if its mean ETOPO depth ≤ the threshold). Land (elevation
≥ 0) is excluded; the result is positive metres below sea level, NaN where a cell has no ocean.

CLI: mhw-build-bathymetry --region ebs
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr

from mhw.bottom.regions import BOTTOM_REGIONS, EBS, BottomRegion, get_region
from mhw.bottom.sources import ETOPO_2022, BathySource

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

_FETCH_STRIDE_DEG = 0.02   # ~5× downsample of 15-arcsec ETOPO → ~140 samples per 0.25° cell


# ---------------------------------------------------------------------------
# Pure helper (network-free, unit-testable): bin fine depths to the analysis grid
# ---------------------------------------------------------------------------

def bin_depth_to_grid(pt_lat: np.ndarray, pt_lon360: np.ndarray, pt_depth: np.ndarray,
                      lats: np.ndarray, lon360: np.ndarray, res: float = 0.25) -> np.ndarray:
    """Mean ocean depth per analysis cell from scattered bathymetry points.

    ``pt_*`` are 1-D fine bathymetry samples (lat, lon on 0–360, depth = positive m; non-ocean
    samples already dropped). ``lats``/``lon360`` are the region's analysis-grid coordinates
    (lon on 0–360, ascending). Each cell spans ``[coord, coord+res)``. Returns depth grid
    ``[n_lat, n_lon]``; cells with no ocean sample are NaN.
    """
    from scipy.stats import binned_statistic_2d

    if pt_depth.size == 0:                       # no ocean samples → all-NaN grid
        return np.full((len(lats), len(lon360)), np.nan)
    lat_edges = np.append(lats, lats[-1] + res)
    lon_edges = np.append(lon360, lon360[-1] + res)
    stat, _, _, _ = binned_statistic_2d(
        pt_lat, pt_lon360, pt_depth, statistic="mean", bins=[lat_edges, lon_edges])
    return stat


# ---------------------------------------------------------------------------
# Fetch + regrid + cache
# ---------------------------------------------------------------------------

def _ordered_slice(coord: xr.DataArray, lo: float, hi: float) -> slice:
    """slice(lo, hi) respecting the coordinate's stored direction (asc or desc)."""
    return slice(lo, hi) if float(coord.values[0]) <= float(coord.values[-1]) else slice(hi, lo)


def depth_grid_for(lats: np.ndarray, lons: np.ndarray, res: float = 0.25,
                   source: BathySource = ETOPO_2022,
                   stride_deg: float = _FETCH_STRIDE_DEG) -> np.ndarray:
    """Fetch ETOPO over an arbitrary regular grid and bin to it (mean ocean depth, m).

    Works for any (lats, lons) — a region's analysis grid *or* the OISST region grid (used by
    the bottom-vs-surface diagnostic). Returns depth ``[len(lats), len(lons)]``, NaN over land.
    """
    lats = np.sort(np.asarray(lats, dtype="float64"))
    lon360 = np.sort(np.asarray(lons, dtype="float64") % 360.0)
    ds = xr.open_dataset(source.opendap_url)
    lat_c, lon_c = ds[source.lat_coord], ds[source.lon_coord]
    res_native = abs(float(lat_c.values[1]) - float(lat_c.values[0]))
    step = max(1, int(round(stride_deg / res_native)))
    sub = ds[source.var].sel({
        source.lat_coord: _ordered_slice(lat_c, float(lats.min()), float(lats.max()) + res),
        source.lon_coord: _ordered_slice(lon_c, float(lon360.min()), float(lon360.max()) + res),
    }).isel({source.lat_coord: slice(None, None, step),
             source.lon_coord: slice(None, None, step)}).load()
    lon_mesh, lat_mesh = np.meshgrid(sub[source.lon_coord].values, sub[source.lat_coord].values)
    depth = np.where(sub.values < 0, -sub.values.astype("float64"), np.nan)   # ocean depth; land→NaN
    flat_lat, flat_lon, flat_d = lat_mesh.ravel(), lon_mesh.ravel(), depth.ravel()
    ok = np.isfinite(flat_d)
    return bin_depth_to_grid(flat_lat[ok], flat_lon[ok], flat_d[ok], lats, lon360, res=res)


def fetch_region_depth(region: BottomRegion, source: BathySource = ETOPO_2022,
                       stride_deg: float = _FETCH_STRIDE_DEG) -> np.ndarray:
    """Fetch ETOPO over *region* and bin to its 0.25° analysis grid (mean ocean depth, m)."""
    grid = depth_grid_for(region.analysis_lats, region.analysis_lons, region.grid_res,
                          source, stride_deg)
    print(f"{source.id}: {region.id.upper()} depth grid {grid.shape}, "
          f"{int(np.isfinite(grid).sum())} ocean cells "
          f"(≤{region.shelf_max_depth_m:.0f} m: {int(np.nansum(grid <= region.shelf_max_depth_m))})")
    return grid


def _depth_cache(region: BottomRegion) -> Path:
    return DERIVED / f"{region.id}_depth.npz"


def build_region_depth(region: BottomRegion = EBS, force: bool = False,
                       source: BathySource = ETOPO_2022) -> np.ndarray:
    """Return *region*'s ETOPO depth grid on its 0.25° grid, building + caching if needed."""
    cache = _depth_cache(region)
    if cache.exists() and not force:
        return np.load(cache)["depth"]
    grid = fetch_region_depth(region, source)
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.savez(cache, depth=grid, lats=region.analysis_lats, lons=region.analysis_lons)
    return grid


def shelf_mask_from_bathymetry(region: BottomRegion = EBS, force: bool = False) -> np.ndarray:
    """Boolean shelf mask on *region*'s 0.25° grid from the standalone bathymetry.

    Same rule as the Bering10K-derived mask — depth ≤ ``shelf_max_depth_m`` (and >
    ``shelf_min_depth_m`` for slope/deep bands) — but with a model-neutral depth source.
    """
    depth = build_region_depth(region, force=force)
    mask = np.isfinite(depth) & (depth <= region.shelf_max_depth_m)
    if region.shelf_min_depth_m > 0:
        mask &= depth > region.shelf_min_depth_m
    return mask


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a region's shelf-depth grid from ETOPO 2022.")
    p.add_argument("--region", default="ebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--force", action="store_true", help="Rebuild even if cached")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    region = get_region(args.region)
    build_region_depth(region, force=args.force)
    print(f"  Saved → {_depth_cache(region)}")


if __name__ == "__main__":
    main()
