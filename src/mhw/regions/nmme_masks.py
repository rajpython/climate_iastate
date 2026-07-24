"""Fractional ESR-zone masks and cos(lat) weights on the NMME 1° (0–360) grid.

Companion to :mod:`mhw.regions.masks` for the NOAA PSL marine-heatwave forecast
product (config/psl_mhw.yml), which lives on a 1° global grid with longitudes
0–360. Two deliberate differences from the OISST 0.25° builder:

* **Fractional coverage, not a binary centre test.** At 1° the narrow Aleutian
  ESR strips would lose most (or all) of their cells to a centre-in-polygon
  test; instead each cell stores the fraction of its area inside the zone.
* **Land-only exclusion.** The PSL mask classes are 0=ocean, 1=land, 2=ice; the
  Chukchi, Beaufort and NBS zones are *entirely* class-2 (seasonal ice) yet the
  published probability field is defined there, so ice cells keep their weight
  and the per-zone ice fraction is recorded as ``ice_frac`` for a UI caveat.

Weight = cos(lat) × coverage × (not land). The artifact is static — it depends
only on the polygons, the grid and the land mask — and is rebuilt by
``mhw-build-psl-mhw`` only when missing or when regions.geojson is newer.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import shapely
import xarray as xr
from shapely.geometry import shape
from shapely.ops import unary_union

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GEOJSON_PATH = PROJECT_ROOT / "config" / "regions.geojson"


# ---------------------------------------------------------------------------
# Grid & land mask (from the PSL mask file, so axes match the source exactly)
# ---------------------------------------------------------------------------

def nmme_grid_from_mask(mask_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (lats, lons) read from the PSL land/sea/ice mask file."""
    with xr.open_dataset(mask_path) as ds:
        return ds["lat"].values.astype("float64"), ds["lon"].values.astype("float64")


def load_land_flags(mask_path: Path, land_value: int = 1) -> np.ndarray:
    """Boolean (lat, lon): True where the PSL mask says land."""
    with xr.open_dataset(mask_path) as ds:
        return ds["mask"].values == land_value


def load_ice_flags(mask_path: Path, ice_value: int = 2) -> np.ndarray:
    """Boolean (lat, lon): True where the PSL mask says permanent/seasonal ice."""
    with xr.open_dataset(mask_path) as ds:
        return ds["mask"].values == ice_value


# ---------------------------------------------------------------------------
# Geometry helpers (pure — unit-testable)
# ---------------------------------------------------------------------------

def poly_to_360(geometry: dict | shapely.Geometry) -> shapely.Geometry:
    """Rebuild a GeoJSON/shapely geometry with every longitude wrapped to [0, 360).

    Dateline-straddling zones are stored in regions.geojson as MultiPolygons
    split at ±180 (e.g. ai_central); after the wrap the halves become adjacent
    at 180 and ``unary_union`` dissolves the shared edge so the zone is one
    contiguous polygon in the 0–360 frame.
    """
    geom = shape(geometry) if isinstance(geometry, dict) else geometry
    wrapped = shapely.transform(
        geom, lambda coords: np.column_stack([coords[:, 0] % 360.0, coords[:, 1]])
    )
    return unary_union(wrapped)


def fractional_mask(
    poly: shapely.Geometry,
    lats: np.ndarray,
    lons: np.ndarray,
    resolution_deg: float = 1.0,
) -> np.ndarray:
    """Fraction of each grid cell's area inside *poly* — float32 (lat, lon) in [0, 1].

    Cells are ``resolution°`` boxes centred on the coordinate values (the NMME
    grid centres sit on integer degrees). Only cells whose box intersects the
    polygon bounds are tested, and the intersection is vectorised with
    shapely 2.x array ops. Areas are plain lon/lat degree² on both sides of the
    ratio, so the fraction needs no spherical correction.
    """
    half = resolution_deg / 2.0
    cover = np.zeros((lats.size, lons.size), dtype="float32")

    lon_min, lat_min, lon_max, lat_max = poly.bounds
    ii = np.nonzero((lats > lat_min - half) & (lats < lat_max + half))[0]
    jj = np.nonzero((lons > lon_min - half) & (lons < lon_max + half))[0]
    if ii.size == 0 or jj.size == 0:
        return cover

    jj_2d, ii_2d = np.meshgrid(jj, ii)
    cells = shapely.box(
        lons[jj_2d].ravel() - half,
        lats[ii_2d].ravel() - half,
        lons[jj_2d].ravel() + half,
        lats[ii_2d].ravel() + half,
    )
    frac = shapely.area(shapely.intersection(poly, cells)) / (resolution_deg**2)
    cover[ii_2d.ravel(), jj_2d.ravel()] = frac.astype("float32")
    return cover


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_zone_masks(
    zone_ids: list[str],
    mask_path: Path,
    geojson_path: Path = GEOJSON_PATH,
    window: dict | None = None,
) -> xr.Dataset:
    """Coverage + weights for the ESR zones on the NMME grid.

    Returns a Dataset with dims (zone, lat, lon):
      coverage — fraction of the cell inside the zone polygon
      weight   — cos(lat) × coverage × (not land); the zonal-mean weights
    and per-zone attrs-style variables:
      ice_frac — fraction of the zone's weight sitting on PSL ice-class cells
                 (Chukchi/Beaufort/NBS ≈ 1.0 — surface as a UI caveat)
      n_cells  — number of cells with weight > 0 (near-empty zones are visible)
    Subset to *window* ({lat_min, lat_max, lon_min, lon_max}, 0–360) when given.
    """
    lats, lons = nmme_grid_from_mask(mask_path)
    land = load_land_flags(mask_path)
    ice = load_ice_flags(mask_path)

    with open(geojson_path) as f:
        features = {feat["properties"]["id"]: feat for feat in json.load(f)["features"]}

    coslat = np.cos(np.deg2rad(lats))[:, None]

    coverage = np.zeros((len(zone_ids), lats.size, lons.size), dtype="float32")
    weight = np.zeros_like(coverage)
    ice_frac = np.zeros(len(zone_ids), dtype="float64")
    n_cells = np.zeros(len(zone_ids), dtype="int64")

    for k, zid in enumerate(zone_ids):
        feat = features[zid]
        poly = poly_to_360(feat["geometry"])
        cov = fractional_mask(poly, lats, lons)
        w = coslat * cov * (~land)
        total = w.sum()
        if total <= 0:
            raise ValueError(
                f"Zone {zid!r} rasterized to zero weight on the NMME 1° grid — "
                "check the polygon/grid alignment before trusting any zonal series."
            )
        coverage[k] = cov
        weight[k] = w
        ice_frac[k] = float((w * ice).sum() / total)
        n_cells[k] = int((w > 0).sum())
        print(f"  {zid:12s}: {n_cells[k]:4d} cells, ice_frac={ice_frac[k]:.2f}")

    ds = xr.Dataset(
        {
            "coverage": (("zone", "lat", "lon"), coverage),
            "weight": (("zone", "lat", "lon"), weight),
            "ice_frac": (("zone",), ice_frac),
            "n_cells": (("zone",), n_cells),
        },
        coords={"zone": zone_ids, "lat": lats, "lon": lons},
        attrs={
            "description": "Fractional ESR-zone masks/weights on the NMME 1° 0–360 grid",
            "weight_method": "cos_lat * coverage_fraction * (PSL mask != land)",
            "ice_note": "PSL ice-class cells keep their weight; ice_frac carries the caveat",
        },
    )
    if window:
        ds = ds.sel(
            lat=slice(window["lat_min"], window["lat_max"]),
            lon=slice(window["lon_min"], window["lon_max"]),
        )
    return ds
