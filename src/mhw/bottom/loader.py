"""Open bottom-temperature sources over OPeNDAP with one return contract.

Mirrors the role of :mod:`mhw.forecast.io` for the surface pipeline: the only
source-specific layer. Given a :class:`~mhw.bottom.sources.BottomSource`, return
the bottom-temperature ``DataArray`` (time, y, x) with its 2-D curvilinear
``lat``/``lon`` coordinates attached — ready for :mod:`mhw.bottom.regrid`.
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import xarray as xr

from mhw.bottom.sources import BottomSource, BERING10K_K20_CORECFS


def open_bottom_dataset(source: BottomSource = BERING10K_K20_CORECFS) -> xr.Dataset:
    """Lazily open *source* over OPeNDAP (metadata only; no data transfer yet)."""
    if not source.opendap_url:
        raise ValueError(f"Source {source.id!r} has no OPeNDAP URL configured yet.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return xr.open_dataset(
            source.opendap_url,
            drop_variables=list(source.drop_vars),
            decode_times=True,
        )


def load_bottom_temp(
    source: BottomSource = BERING10K_K20_CORECFS,
    start: date | None = None,
    end: date | None = None,
    ds: xr.Dataset | None = None,
) -> xr.DataArray:
    """Return bottom temperature ``temp(time, y, x)`` with 2-D lat/lon coords.

    Parameters
    ----------
    source : BottomSource
    start, end : optional date
        Inclusive time selection on the source time coordinate.
    ds : optional open Dataset
        Reuse an already-open dataset (avoids reopening over the network).

    Returns
    -------
    xr.DataArray
        Dims ``(time, y, x)``; always carries 2-D ``lat``/``lon`` coords over
        ``(y, x)`` and the ``source_id`` attribute. Values are °C; NaN over land.
    """
    ds = ds if ds is not None else open_bottom_dataset(source)

    da = ds[source.temp_var]

    if start is not None or end is not None:
        da = da.sel({source.time_coord: slice(
            None if start is None else str(start),
            None if end is None else str(end),
        )})

    lat = ds[source.lat_coord]
    lon = ds[source.lon_coord]

    # Normalise to (time, y, x) with 2-D lat/lon, regardless of native grid:
    #   * curvilinear sources (Bering10K ROMS) carry 2-D lat/lon over (eta, xi);
    #   * rectilinear sources (CEFI MOM6 NEP `regrid`) carry 1-D lat/lon along
    #     their own dims — broadcast to 2-D so the downstream regrid sees one
    #     uniform contract.
    if lat.ndim == 2:
        y_dim, x_dim = lat.dims
        da = da.rename({source.time_coord: "time", y_dim: "y", x_dim: "x"})
        lat2d, lon2d = np.asarray(lat.values), np.asarray(lon.values)
    elif lat.ndim == 1:
        y_dim, x_dim = lat.dims[0], lon.dims[0]
        da = da.rename({source.time_coord: "time", y_dim: "y", x_dim: "x"})
        lon2d, lat2d = np.meshgrid(np.asarray(lon.values), np.asarray(lat.values))
    else:
        raise ValueError(
            f"{source.lat_coord!r} has ndim={lat.ndim}; expected 1 (rectilinear) "
            "or 2 (curvilinear)."
        )

    da = da.assign_coords(lat=(("y", "x"), lat2d), lon=(("y", "x"), lon2d))
    da.attrs["source_id"] = source.id
    da.attrs["source_label"] = source.label
    da.attrs.setdefault("units", "Celsius")
    return da
