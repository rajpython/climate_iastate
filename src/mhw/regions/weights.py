"""Compute cos(lat) area weights for the OISST 0.25° grid.

w_g = cos(latitude_radians)

These weights are used for all regional aggregation (Section 7 of mhw_README.md).
"""
from __future__ import annotations

import numpy as np
import xarray as xr


def build_weights(lats: np.ndarray, lons: np.ndarray) -> xr.DataArray:
    """Return a 2D cos(lat) weight DataArray on the OISST grid.

    Parameters
    ----------
    lats : 1-D array of latitude centre-points (degrees, -90..90)
    lons : 1-D array of longitude centre-points (degrees, -180..180)

    Returns
    -------
    xr.DataArray of shape (len(lats), len(lons)), dims ["lat", "lon"]
    """
    w_1d = np.cos(np.deg2rad(lats)).astype(np.float32)
    w_2d = np.broadcast_to(w_1d[:, np.newaxis], (len(lats), len(lons))).copy()
    return xr.DataArray(
        w_2d,
        dims=["lat", "lon"],
        coords={"lat": lats, "lon": lons},
        name="weights",
        attrs={"method": "cos_lat", "units": "dimensionless"},
    )
