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


def open_bottom_dataset(
    source: BottomSource = BERING10K_K20_CORECFS, url: str | None = None
) -> xr.Dataset:
    """Lazily open *source* over OPeNDAP (metadata only; no data transfer yet).

    ``url`` overrides ``source.opendap_url`` — needed for ocean-health variables that live in
    a **separate** per-variable file (MOM6 NEP serves one file per variable).
    """
    u = url or source.opendap_url
    if not u:
        raise ValueError(f"Source {source.id!r} has no OPeNDAP URL configured yet.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return xr.open_dataset(
            u,
            drop_variables=list(source.drop_vars),
            decode_times=True,
        )


def resolve_variable(source: BottomSource, var: str) -> tuple[str, str]:
    """Return ``(variable_name, opendap_url)`` for canonical field *var* on *source*.

    ``var="temp"`` maps to the source's bottom-temperature variable/URL; any other name is
    looked up in ``source.variables`` (ocean-health extras). A variable whose descriptor
    leaves ``opendap_url`` blank shares the source's dataset (Bering10K bundles); otherwise it
    has its own file (MOM6 NEP).
    """
    if var == "temp":
        return source.temp_var, source.opendap_url
    bv = source.variables.get(var)
    if bv is None:
        raise ValueError(
            f"Source {source.id!r} has no {var!r} variable configured "
            f"(available: {['temp', *source.variables]})."
        )
    return bv.var, (bv.opendap_url or source.opendap_url)


def load_bottom_field(
    source: BottomSource = BERING10K_K20_CORECFS,
    var: str = "temp",
    start: date | None = None,
    end: date | None = None,
    ds: xr.Dataset | None = None,
) -> xr.DataArray:
    """Return one bottom field ``(time, y, x)`` with 2-D lat/lon coords, grid-agnostic.

    Generalises :func:`load_bottom_temp` to any canonical field (``"temp"``, ``"salinity"``,
    …). The grid-normalisation (curvilinear vs rectilinear) is identical across a source's
    variables — only the variable name and (for MOM6) the file URL differ.

    Parameters
    ----------
    source : BottomSource
    var : str
        Canonical field name: ``"temp"`` or a key of ``source.variables``.
    start, end : optional date
        Inclusive time selection on the source time coordinate.
    ds : optional open Dataset
        Reuse an already-open dataset for *this variable* (avoids reopening over the network).

    Returns
    -------
    xr.DataArray
        Dims ``(time, y, x)`` with 2-D ``lat``/``lon`` coords over ``(y, x)`` and
        ``source_id`` / ``variable`` attributes. NaN over land.
    """
    varname, url = resolve_variable(source, var)
    ds = ds if ds is not None else open_bottom_dataset(source, url=url)

    da = ds[varname]

    if start is not None or end is not None:
        da = da.sel({source.time_coord: slice(
            None if start is None else str(start),
            None if end is None else str(end),
        )})

    lat = ds[source.lat_coord]
    lon = ds[source.lon_coord]

    # Normalise to (time, y, x) with 2-D lat/lon, regardless of native grid:
    #   * curvilinear sources (Bering10K ROMS) carry 2-D lat/lon over (eta, xi);
    #   * rectilinear sources (MOM6 NEP10k `regrid`) carry 1-D lat/lon along
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
    da.attrs["variable"] = var
    if var == "temp":
        da.attrs.setdefault("units", "Celsius")
    return da


def load_bottom_temp(
    source: BottomSource = BERING10K_K20_CORECFS,
    start: date | None = None,
    end: date | None = None,
    ds: xr.Dataset | None = None,
) -> xr.DataArray:
    """Bottom temperature ``temp(time, y, x)`` — thin wrapper over :func:`load_bottom_field`.

    Kept as the temperature entry point (the cold-pool engine and survey replication call it);
    values are °C, NaN over land.
    """
    return load_bottom_field(source, "temp", start=start, end=end, ds=ds)
