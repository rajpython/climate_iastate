"""mhw.fetch.ncei_update -- planner + an end-to-end run on tiny files (no network: listing is injected)."""
from datetime import date

import numpy as np
import pandas as pd
import xarray as xr

from mhw.fetch.ncei_update import load_prelim, parse_listing, plan_updates, run, window_days

LAT = np.array([59.875, 60.125], np.float32)
LON_NCEI = np.array([189.875, 190.125], np.float32)
LON_CACHE = np.array([-170.125, -169.875], np.float32)


def _ncei(path, day, value, prelim=False):
    t = [pd.Timestamp(day) + pd.Timedelta(hours=12)]
    a = np.full((1, 1, 2, 2), value, np.float32)
    ds = xr.Dataset({"sst": (("time", "zlev", "lat", "lon"), a), "ice": (("time", "zlev", "lat", "lon"), np.full_like(a, np.nan))},
                    coords={"time": t, "zlev": [0.0], "lat": LAT, "lon": LON_NCEI})
    name = f"oisst-avhrr-v02r01.{pd.Timestamp(day):%Y%m%d}{'_preliminary' if prelim else ''}.nc"
    ds.to_netcdf(path / name)
    return name


def _cache(path, zone, days, value=1.0):
    t = pd.DatetimeIndex(days) + pd.Timedelta(hours=12)
    z = np.full((len(t), 2, 2), value, np.float32)
    xr.Dataset({"sst": (("time", "lat", "lon"), z), "ice": (("time", "lat", "lon"), np.full_like(z, np.nan))},
               coords={"time": t, "lat": LAT, "lon": LON_CACHE}).to_netcdf(path / f"oisst_{zone}_{t[0].year}.nc")


def test_parse_listing_separates_final_and_preliminary():
    html = ('<a href="oisst-avhrr-v02r01.20260916.nc">x</a> <a href="oisst-avhrr-v02r01.20260917_preliminary.nc">y</a>')
    out = parse_listing(html)
    assert out[date(2026, 9, 16)] == {"final": "oisst-avhrr-v02r01.20260916.nc"}
    assert out[date(2026, 9, 17)] == {"preliminary": "oisst-avhrr-v02r01.20260917_preliminary.nc"}


def test_plan_never_touches_a_held_final_and_upgrades_only_preliminary():
    a, b, c, d = (date(2026, 9, x) for x in (1, 2, 3, 4))
    av = {a: {"final": "fa"}, b: {"final": "fb"}, c: {"preliminary": "pc"}}
    plan = plan_updates([a, b, c, d], held={a, b}, prelim_held={b}, available=av)
    assert plan == [(b, "replace_with_final", "fb"), (c, "append_preliminary", "pc")]   # a untouched, d unlisted


def test_window_covers_the_year_and_the_lookback_across_new_year():
    w = window_days(date(2027, 1, 10), 60)
    assert w[0] == date(2026, 11, 11) and w[-1] == date(2027, 1, 9)


def test_end_to_end_prelim_then_final_then_new_year(tmp_path):
    raw, ncei = tmp_path / "raw", tmp_path / "ncei"
    raw.mkdir()
    ncei.mkdir()
    _cache(raw, "nbs", ["2026-12-29", "2026-12-30"], value=1.0)
    listing = {"202611": {}, "202612": {date(2026, 12, 31): {"preliminary": _ncei(ncei, "2026-12-31", 2.0, prelim=True)}},
               "202701": {}}
    run(date(2027, 1, 1), 60, ncei, raw, listing=lambda ym: listing.get(ym, {}))
    with xr.open_dataset(raw / "oisst_nbs_2026.nc") as ds:
        assert len(ds.time) == 3 and float(ds.sst.values[-1].max()) == 2.0
    assert load_prelim(raw) == {date(2026, 12, 31)}
    # next night: final for 12-31 and a preliminary 2027-01-01 (new year file on the previous year's grid)
    listing["202612"] = {date(2026, 12, 31): {"final": _ncei(ncei, "2026-12-31", 3.0)}}
    listing["202701"] = {date(2027, 1, 1): {"preliminary": _ncei(ncei, "2027-01-01", 4.0, prelim=True)}}
    run(date(2027, 1, 2), 60, ncei, raw, listing=lambda ym: listing.get(ym, {}))
    with xr.open_dataset(raw / "oisst_nbs_2026.nc") as ds:
        assert len(ds.time) == 3 and float(ds.sst.values[-1].max()) == 3.0
        assert float(ds.sst.values[0].max()) == 1.0                    # held final day untouched
    with xr.open_dataset(raw / "oisst_nbs_2027.nc") as ds:
        assert len(ds.time) == 1 and np.array_equal(ds.lon.values, LON_CACHE)
    assert load_prelim(raw) == {date(2027, 1, 1)}
