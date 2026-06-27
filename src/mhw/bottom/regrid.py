"""Regrid a curvilinear ocean-model field onto the regular OISST 0.25° grid.

Regional ocean models (Bering10K ROMS ~10 km curvilinear; MOM6 NEP10k) are
incompatible as-is with the regular 0.25° lat/lon grid the rest of the pipeline
assumes (cos-lat weights, rasterised region masks, climatology zarr). This module
remaps onto that grid using **only numpy + scipy** — no conda / xesmf / esmpy
(the repo is pyenv/pip).

Method: **block average** — each target 0.25° cell takes the mean of all source
cells whose centres fall in it (the right operator for coarsening ~10 km → 25 km).
Target cells with no source centre but inside the model footprint are optionally
filled by nearest source cell (scipy cKDTree, bounded distance).
"""
from __future__ import annotations

import numpy as np


def oisst_grid() -> tuple[np.ndarray, np.ndarray]:
    """Return (lats, lons) for the global OISST 0.25° grid, [-180, 180) lons.

    Canonical fixed grid — mirrors :func:`mhw.regions.masks.oisst_grid` but is
    defined here to keep the bottom package free of the masks module's heavier
    (shapely) dependencies. The OISST grid is a fixed standard; these must match.
    """
    lats = np.arange(-89.875, 90.0, 0.25, dtype=np.float64)   # 720 points
    lons = np.arange(-179.875, 180.0, 0.25, dtype=np.float64)  # 1440 points
    return lats, lons


def normalize_lon(lon: np.ndarray) -> np.ndarray:
    """Wrap longitudes to the OISST [-180, 180) convention."""
    return (np.asarray(lon, dtype="float64") + 180.0) % 360.0 - 180.0


def alaska_target_grid(
    lat_bounds: tuple[float, float] = (46.0, 78.0),
    lon_bounds: tuple[float, float] = (-205.0, -155.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Return the OISST-0.25° (lats, lons) subset covering the Alaska domain.

    Longitudes are returned in the OISST [-180, 180) convention; the default
    ``lon_bounds`` are expressed in that frame (the Bering straddles the dateline,
    so the western shelf near 180°E appears as ~+179 — handled by the caller via
    :func:`normalize_lon` before binning).
    """
    lats, lons = oisst_grid()
    lat_sel = lats[(lats >= lat_bounds[0]) & (lats <= lat_bounds[1])]
    lon_sel = lons[(lons >= lon_bounds[0]) & (lons <= lon_bounds[1])]
    return lat_sel, lon_sel


def regrid_curvilinear_to_regular(
    src_lat: np.ndarray,
    src_lon: np.ndarray,
    field: np.ndarray,
    tgt_lats: np.ndarray,
    tgt_lons: np.ndarray,
    fill_nearest: bool = True,
    fill_max_deg: float = 0.30,
) -> np.ndarray:
    """Block-average *field* (on a curvilinear grid) onto a regular target grid.

    Parameters
    ----------
    src_lat, src_lon : arrays, same shape as *field*
        Source cell-centre coordinates (any longitude convention; wrapped here).
    field : array
        Source values; NaNs (land/ice mask) are ignored.
    tgt_lats, tgt_lons : 1-D arrays
        Regular target grid centres (monotonic, constant spacing), OISST frame.
    fill_nearest : bool
        Fill empty in-footprint target cells with the nearest source cell.
    fill_max_deg : float
        Max distance (degrees) for nearest-fill, so we do not paint beyond the
        model footprint.

    Returns
    -------
    array (len(tgt_lats), len(tgt_lons))
        Regridded field; NaN where no source data is within range.
    """
    tgt_lons = np.asarray(tgt_lons, dtype="float64")
    # Longitude frame must match the target grid. The Alaska regions are in the OISST
    # [-180,180) frame, EXCEPT the Aleutians, whose box straddles the dateline and is defined
    # on 0–360 (e.g. 170..195). Pick the frame from the target so a dateline-spanning region
    # stays contiguous; behaviour is unchanged for every [-180,180) region.
    src_lon_arr = np.asarray(src_lon).ravel()
    if float(tgt_lons.max()) > 180.0:
        slon = src_lon_arr % 360.0
    else:
        slon = normalize_lon(src_lon_arr)
    slat = np.asarray(src_lat, dtype="float64").ravel()
    sval = np.asarray(field, dtype="float64").ravel()

    good = np.isfinite(sval) & np.isfinite(slat) & np.isfinite(slon)
    slat, slon, sval = slat[good], slon[good], sval[good]

    tgt_lats = np.asarray(tgt_lats, dtype="float64")  # tgt_lons already coerced above
    nlat, nlon = tgt_lats.size, tgt_lons.size
    # Cell spacing from the regular grid; fall back to OISST 0.25° for a 1-cell axis.
    dlat = float(tgt_lats[1] - tgt_lats[0]) if nlat > 1 else 0.25
    dlon = float(tgt_lons[1] - tgt_lons[0]) if nlon > 1 else 0.25

    # Nearest target-cell index for each source centre.
    ii = np.round((slat - tgt_lats[0]) / dlat).astype(np.int64)
    jj = np.round((slon - tgt_lons[0]) / dlon).astype(np.int64)
    inb = (ii >= 0) & (ii < nlat) & (jj >= 0) & (jj < nlon)
    ii, jj, vv = ii[inb], jj[inb], sval[inb]

    flat = ii * nlon + jj
    sums = np.bincount(flat, weights=vv, minlength=nlat * nlon)
    cnts = np.bincount(flat, minlength=nlat * nlon).astype("float64")
    out = np.full(nlat * nlon, np.nan, dtype="float64")
    nz = cnts > 0
    out[nz] = sums[nz] / cnts[nz]
    out = out.reshape(nlat, nlon)

    if fill_nearest and (~nz).any():
        out = _nearest_fill(out, slat, slon, sval, tgt_lats, tgt_lons, fill_max_deg)
    return out


def _nearest_fill(
    out: np.ndarray,
    slat: np.ndarray,
    slon: np.ndarray,
    sval: np.ndarray,
    tgt_lats: np.ndarray,
    tgt_lons: np.ndarray,
    max_deg: float,
) -> np.ndarray:
    """Fill NaN target cells from the nearest source point within *max_deg*."""
    from scipy.spatial import cKDTree

    empty = np.isnan(out)
    if not empty.any():
        return out
    lon2d, lat2d = np.meshgrid(tgt_lons, tgt_lats)
    tree = cKDTree(np.column_stack([slon, slat]))
    q = np.column_stack([lon2d[empty], lat2d[empty]])
    dist, idx = tree.query(q, distance_upper_bound=max_deg)
    hit = np.isfinite(dist)
    filled = out.copy()
    vals = np.full(q.shape[0], np.nan)
    vals[hit] = sval[idx[hit]]
    filled[empty] = vals
    return filled
