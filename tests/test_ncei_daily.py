"""Pure helpers of mhw.fetch.ncei_daily -- network-free, on tiny in-memory grids."""
from datetime import date

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from mhw.fetch.ncei_daily import ncei_url, parse_ncei_name, splice, subset_day


def _global_day(day: str, value: float) -> xr.Dataset:
    """A miniature NCEI-shaped day: (time, zlev, lat, lon) on a 0-360 grid."""
    lat = np.array([59.875, 60.125], dtype=np.float32)
    lon = np.array([179.875, 180.125, 190.125], dtype=np.float32)
    shp = (1, 1, 2, 3)
    sst = np.full(shp, value, np.float32)
    sst[0, 0, 0, 2] = np.nan                     # one land/ice cell
    return xr.Dataset(
        {"sst": (("time", "zlev", "lat", "lon"), sst),
         "ice": (("time", "zlev", "lat", "lon"), np.zeros(shp, np.float32)),
         "anom": (("time", "zlev", "lat", "lon"), np.zeros(shp, np.float32))},
        coords={"time": [pd.Timestamp(day) + pd.Timedelta(hours=12)], "zlev": [0.0],
                "lat": lat, "lon": lon})


def _cache(days, lon=(179.875, -179.875, -169.875)):
    t = pd.DatetimeIndex(days) + pd.Timedelta(hours=12)
    z = np.zeros((len(t), 2, 3), np.float32)
    return xr.Dataset({"sst": (("time", "lat", "lon"), z), "ice": (("time", "lat", "lon"), z)},
                      coords={"time": t, "lat": np.array([59.875, 60.125], np.float32),
                              "lon": np.array(lon, np.float32)},
                      attrs={"source": "cache"})


def test_url_and_name_roundtrip():
    d = date(2026, 8, 31)
    assert ncei_url(d).endswith("/202608/oisst-avhrr-v02r01.20260831.nc")
    assert parse_ncei_name("oisst-avhrr-v02r01.20260831.nc") == (d, False)
    assert parse_ncei_name("oisst-avhrr-v02r01.20260831_preliminary.nc") == (d, True)
    with pytest.raises(ValueError):
        parse_ncei_name("oisst_sebs_2026.nc")


def test_subset_day_lands_on_the_cache_grid_across_the_dateline():
    c = _cache(["2026-07-01"])                   # cache lon in [-180, 180)
    sub = subset_day(_global_day("2026-07-02", 5.0), c.lat.values, c.lon.values)
    assert set(sub.data_vars) == {"sst", "ice"}
    assert np.array_equal(sub.lon.values, c.lon.values)
    assert sub.sst.shape == (1, 2, 3)
    assert np.isnan(sub.sst.values[0, 0, 2])     # NaN pattern carried, not filled


def test_subset_day_rejects_a_foreign_grid():
    c = _cache(["2026-07-01"], lon=(179.875, -179.875, -150.0))
    with pytest.raises(KeyError):
        subset_day(_global_day("2026-07-02", 5.0), c.lat.values, c.lon.values)


def test_splice_appends_sorted_and_never_shrinks():
    c = _cache(["2026-06-30", "2026-07-01"])
    days = [subset_day(_global_day(d, 7.0), c.lat.values, c.lon.values)
            for d in ("2026-07-03", "2026-07-02")]
    out = splice(c, days)
    assert len(out.time) == 4
    assert pd.DatetimeIndex(out.time.values).is_monotonic_increasing
    assert np.array_equal(out.sst.isel(time=slice(0, 2)).values, c.sst.values)  # originals untouched
    assert out.attrs["source"] == "cache"


def test_splice_refuses_a_day_the_cache_already_holds():
    c = _cache(["2026-07-01", "2026-07-02"])
    with pytest.raises(ValueError, match="already holds"):
        splice(c, [subset_day(_global_day("2026-07-02", 9.0), c.lat.values, c.lon.values)])
