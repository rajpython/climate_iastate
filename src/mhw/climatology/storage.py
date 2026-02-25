"""Zarr read/write helpers for climatology arrays (mu, theta90).

Arrays are stored as xr.Dataset → to_zarr.
Chunking: (doy_chunk=1, lat_chunk=min(180, n_lat), lon_chunk=min(360, n_lon))
This optimises for fast single-DOY lookup during daily MHW detection.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import xarray as xr


def save_climatology(
    mu: np.ndarray,
    theta90: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    out_paths: dict,
    chunking: dict,
    attrs: dict | None = None,
) -> None:
    """Persist mu and theta90 as separate Zarr stores.

    Parameters
    ----------
    mu, theta90 : (366, n_lat, n_lon) float32 arrays
    lats, lons  : 1-D coordinate arrays
    out_paths   : {'mu': path_str, 'theta90': path_str}
    chunking    : {'doy_chunk': int, 'lat_chunk': int, 'lon_chunk': int}
    attrs       : optional dict of metadata attributes
    """
    n_lat, n_lon = len(lats), len(lons)
    doy_c = chunking["doy_chunk"]
    lat_c = min(chunking["lat_chunk"], n_lat)
    lon_c = min(chunking["lon_chunk"], n_lon)
    doys = np.arange(1, 367, dtype=np.int32)

    for name, arr in (("mu", mu), ("theta90", theta90)):
        da = xr.DataArray(
            arr,
            dims=["doy", "lat", "lon"],
            coords={"doy": doys, "lat": lats, "lon": lons},
            name=name,
            attrs=attrs or {},
        ).chunk({"doy": doy_c, "lat": lat_c, "lon": lon_c})

        path = Path(out_paths[name])
        path.parent.mkdir(parents=True, exist_ok=True)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            xr.Dataset({name: da}).to_zarr(path, mode="w", consolidated=False)

        print(f"  Saved {name} → {path}")


def load_climatology(mu_path: str | Path, theta90_path: str | Path) -> tuple[xr.DataArray, xr.DataArray]:
    """Load mu and theta90 from their Zarr stores.

    Returns
    -------
    (mu_da, theta90_da) as xr.DataArrays with dims (doy, lat, lon)
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mu = xr.open_zarr(mu_path, consolidated=False)["mu"]
        theta90 = xr.open_zarr(theta90_path, consolidated=False)["theta90"]
    return mu, theta90


def load_doy(path: str | Path, var_name: str, doy: int) -> xr.DataArray:
    """Load a single DOY slice from a climatology Zarr store.

    Efficient for daily refresh: loads only the (lat, lon) slice for *doy*.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        da = xr.open_zarr(path, consolidated=False)[var_name]
    return da.sel(doy=doy).load()
