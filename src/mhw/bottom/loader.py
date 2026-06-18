"""Open bottom-temperature sources over OPeNDAP with one return contract.

Mirrors the role of :mod:`mhw.forecast.io` for the surface pipeline: the only
source-specific layer. Given a :class:`~mhw.bottom.sources.BottomSource`, return
the bottom-temperature ``DataArray`` (time, y, x) with its 2-D curvilinear
``lat``/``lon`` coordinates attached — ready for :mod:`mhw.bottom.regrid`.
"""
from __future__ import annotations

import warnings
from datetime import date

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
        Dims ``(time, y, x)``; carries ``lat``/``lon`` (2-D) coords and the
        ``source_id`` attribute. Values are °C; NaN over land.
    """
    ds = ds if ds is not None else open_bottom_dataset(source)

    da = ds[source.temp_var]
    da = da.assign_coords(
        lat=ds[source.lat_coord],
        lon=ds[source.lon_coord],
    )

    if start is not None or end is not None:
        da = da.sel({source.time_coord: slice(
            None if start is None else str(start),
            None if end is None else str(end),
        )})

    # Normalise dim names to (time, y, x) regardless of source convention.
    y_dim, x_dim = ds[source.lat_coord].dims  # e.g. (eta_rho, xi_rho)
    da = da.rename({source.time_coord: "time", y_dim: "y", x_dim: "x"})
    da.attrs["source_id"] = source.id
    da.attrs["source_label"] = source.label
    da.attrs.setdefault("units", "Celsius")
    return da
