"""Loader contract tests — both native grids normalise to (time, y, x) + 2-D lat/lon.

Uses synthetic in-memory datasets passed via ``ds=`` so no network/OPeNDAP is hit.
Covers the two real source shapes:
  * Bering10K ROMS — curvilinear, 2-D ``lat_rho``/``lon_rho`` over (eta_rho, xi_rho);
  * CEFI MOM6 NEP `regrid` — rectilinear, 1-D ``lat``/``lon`` along their own dims.
"""
import numpy as np
import pytest
import xarray as xr

from mhw.bottom.loader import load_bottom_temp
from mhw.bottom.regrid import regrid_curvilinear_to_regular
from mhw.bottom.sources import BERING10K_K20_CORECFS, MOM6_NEP


def _curvilinear_ds(eta=3, xi=4, nt=2):
    """Bering10K-shaped: temp(ocean_time, eta_rho, xi_rho) + 2-D lat_rho/lon_rho."""
    lat2d = 50.0 + np.arange(eta * xi, dtype="float64").reshape(eta, xi)
    lon2d = -180.0 + np.arange(eta * xi, dtype="float64").reshape(eta, xi)
    time = np.array(["2020-01-15", "2020-02-15"], dtype="datetime64[ns]")[:nt]
    data = np.random.default_rng(0).random((nt, eta, xi))
    return xr.Dataset(
        {
            "temp": (("ocean_time", "eta_rho", "xi_rho"), data),
            "lat_rho": (("eta_rho", "xi_rho"), lat2d),
            "lon_rho": (("eta_rho", "xi_rho"), lon2d),
        },
        coords={"ocean_time": time},
    )


def _rectilinear_ds(ny=5, nx=4, nt=2):
    """MOM6 NEP regrid-shaped: btm_temp(time, lat, lon) + 1-D lat/lon."""
    lat = np.linspace(50.0, 60.0, ny)
    lon = np.linspace(-180.0, -160.0, nx)
    time = np.array(["2020-01-15", "2020-02-15"], dtype="datetime64[ns]")[:nt]
    data = np.random.default_rng(1).random((nt, ny, nx))
    return xr.Dataset(
        {"btm_temp": (("time", "lat", "lon"), data)},
        coords={"time": time, "lat": lat, "lon": lon},
    )


def test_curvilinear_normalises_to_time_y_x():
    ds = _curvilinear_ds()
    da = load_bottom_temp(BERING10K_K20_CORECFS, ds=ds)

    assert da.dims == ("time", "y", "x")
    assert da.lat.dims == ("y", "x") and da.lon.dims == ("y", "x")
    assert da.shape == (2, 3, 4)
    # 2-D lat/lon preserved verbatim from the source.
    np.testing.assert_allclose(da.lat.values, ds["lat_rho"].values)
    np.testing.assert_allclose(da.lon.values, ds["lon_rho"].values)
    assert da.attrs["source_id"] == "bering10k"


def test_rectilinear_broadcasts_to_2d_latlon():
    ds = _rectilinear_ds()
    da = load_bottom_temp(MOM6_NEP, ds=ds)

    assert da.dims == ("time", "y", "x")
    assert da.lat.dims == ("y", "x") and da.lon.dims == ("y", "x")
    assert da.shape == (2, 5, 4)
    # 1-D lat/lon broadcast to a 2-D mesh: lat varies down y, lon across x.
    assert np.allclose(da.lat.values[:, 0], da.lat.values[:, -1])  # const across x
    assert np.allclose(da.lon.values[0, :], da.lon.values[-1, :])  # const down y
    np.testing.assert_allclose(da.lat.values[:, 0], ds["lat"].values)
    np.testing.assert_allclose(da.lon.values[0, :], ds["lon"].values)
    assert da.attrs["source_id"] == "mom6_nep"


def test_time_selection_applies_before_normalise():
    ds = _rectilinear_ds()
    da = load_bottom_temp(MOM6_NEP, ds=ds, start="2020-02-01", end="2020-02-28")
    assert da.sizes["time"] == 1
    assert str(da["time"].values[0])[:7] == "2020-02"


@pytest.mark.parametrize(
    "source, make_ds",
    [(BERING10K_K20_CORECFS, _curvilinear_ds), (MOM6_NEP, _rectilinear_ds)],
)
def test_loader_output_feeds_regrid_for_both_grids(source, make_ds):
    """The uniform (time,y,x)+2-D lat/lon contract drops straight into regrid."""
    da = load_bottom_temp(source, ds=make_ds())
    field0 = da.isel(time=0)
    tgt_lats = np.arange(50.0, 60.0, 0.25)
    tgt_lons = np.arange(-180.0, -160.0, 0.25)
    out = regrid_curvilinear_to_regular(
        da.lat.values, da.lon.values, field0.values, tgt_lats, tgt_lons,
        fill_nearest=False,
    )
    assert out.shape == (tgt_lats.size, tgt_lons.size)
    assert np.isfinite(out).any()  # at least some target cells received source data
