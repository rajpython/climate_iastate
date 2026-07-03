"""Survey-CTD bottom O₂/pH fetcher — pure-helper tests (network-free).

The download/open is network; the parsing (fill masking, per-station reduction, regional
aggregation) is pure and tested here on small in-memory datasets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from mhw.fetch.survey_ctd import (
    _mask_fill,
    _O2_VALID,
    _PH_VALID,
    regional_annual_means,
    station_frame,
)


def _ds(o2, ph, lat, lon, station, with_o2=True, with_ph=True):
    """Build a gapctd-shaped dataset (dim `index`) with optional O₂/pH variables."""
    n = len(lat)
    data = {
        "latitude": (("index",), np.asarray(lat, float)),
        "longitude": (("index",), np.asarray(lon, float)),
        "stationid": (("index",), np.asarray(station, object)),
    }
    if with_o2:
        data["sea_floor_dissolved_oxygen"] = (("index",), np.asarray(o2, float))
    if with_ph:
        data["sea_floor_ph_reported_on_total_scale"] = (("index",), np.asarray(ph, float))
    return xr.Dataset(data, coords={"index": np.arange(n)})


def test_mask_fill_removes_fills_and_out_of_range():
    a = np.array([7.0, 9.97e36, -1.0, 20.0, 5.0])   # valid, fill, negative, too-high, valid
    out = _mask_fill(a, *_O2_VALID)
    assert np.isfinite(out).tolist() == [True, False, False, False, True]
    np.testing.assert_allclose(out[[0, 4]], [7.0, 5.0])


def test_ph_plausibility_filter_drops_sensor_drift():
    a = np.array([7.9, 6.2, 11.2, 8.0])             # good, drift-low, drift-high, good
    out = _mask_fill(a, *_PH_VALID)
    assert np.isfinite(out).tolist() == [True, False, False, True]


def test_station_frame_averages_up_down_profiles():
    # Station 'A' appears twice (down+up) with O₂ 7.0 and 7.4 → mean 7.2; 'B' once.
    ds = _ds(o2=[7.0, 7.4, 6.0], ph=[8.0, 8.0, 7.9],
             lat=[57.0, 57.0, 58.0], lon=[-170.0, -170.0, -171.0],
             station=["A", "A", "B"])
    f = station_frame(ds, 2023)
    assert set(f["stationid"]) == {"A", "B"}
    a = f.loc[f["stationid"] == "A"].iloc[0]
    assert a["o2_mll"] == pytest.approx(7.2)
    assert (f["year"] == 2023).all()


def test_station_frame_missing_o2_variable_is_nan_not_error():
    # A survey year that predates O₂/pH processing (2021/2022 EBS) lacks the variables.
    ds = _ds(o2=None, ph=None, lat=[57.0, 58.0], lon=[-170.0, -171.0],
             station=["A", "B"], with_o2=False, with_ph=False)
    f = station_frame(ds, 2022)
    assert len(f) == 2
    assert f["o2_mll"].isna().all() and f["ph"].isna().all()


def test_regional_annual_means_intensive_mean_and_counts():
    stations = pd.DataFrame({
        "year": [2023, 2023, 2024],
        "stationid": ["A", "B", "C"],
        "latitude": [57.0, 58.0, 57.5], "longitude": [-170.0, -171.0, -170.5],
        "o2_mll": [7.0, 8.0, np.nan],       # 2023 mean = 7.5; 2024 has no valid O₂
        "ph": [7.9, np.nan, 8.0],           # 2023 mean = 7.9 (one valid); 2024 = 8.0
        "sal": [32.0, 33.0, 33.5],          # 2023 mean = 32.5; 2024 = 33.5
    })
    out = regional_annual_means(stations).set_index("year")
    assert out.loc[2023, "mean_bottom_oxygen"] == pytest.approx(7.5)
    assert out.loc[2023, "n_stations_o2"] == 2
    assert np.isnan(out.loc[2024, "mean_bottom_oxygen"])   # no valid O₂ that year
    assert out.loc[2024, "n_stations_o2"] == 0
    assert out.loc[2024, "mean_bottom_ph"] == pytest.approx(8.0)
    assert out.loc[2023, "mean_bottom_salinity"] == pytest.approx(32.5)
    assert out.loc[2024, "n_stations_salinity"] == 1
