"""Vintage #6 rules: support counts, the data-availability mask, and detected area (network-free)."""
import numpy as np
import pandas as pd
import xarray as xr

from mhw.climatology.smooth_doy import mask_unsupported, smooth_doy_field, support_counts


def _one_obs(doy_obs=192, n_years=3):
    """A single cell, ice-covered (invalid) every day of every year except ONE day in year 0."""
    doy = np.tile(np.arange(1, 367), n_years)
    year = np.repeat(np.arange(n_years), 366)
    valid = np.zeros((doy.size, 1, 1), bool)
    valid[doy_obs - 1, 0, 0] = True                 # year 0, doy_obs
    return valid, doy, year


def test_support_counts_raw_window_vs_distinct_support():
    valid, doy, year = _one_obs(192)
    n_raw, n_obs, n_years = support_counts(valid, doy, year, half_window=5, post_window=31)
    assert n_raw[192 - 1 - 5, 0, 0] == 1 and n_raw[192 - 1 + 5, 0, 0] == 1
    assert n_raw[192 - 1 - 6, 0, 0] == 0                       # outside the 11-day window
    assert n_obs[172 - 1, 0, 0] == 1 and n_years[172 - 1, 0, 0] == 1   # 20 days away still feeds the smoothed value
    assert n_obs[171 - 1, 0, 0] == 0                           # 21 days away does not


def test_the_7_01_case_june_threshold_masked_july_unchanged():
    """One July observation must not create a June threshold; supported values stay bit-identical."""
    valid, doy, year = _one_obs(192)
    raw = np.full((366, 1, 1), np.nan, np.float32)
    n_raw, _, _ = support_counts(valid, doy, year)
    raw[n_raw > 0] = 7.01                                       # the raw percentile exists only where the window has data
    smoothed = smooth_doy_field(raw, 31)
    assert np.isfinite(smoothed[172 - 1, 0, 0])                 # the defect: smoothing created a June value
    masked = mask_unsupported(smoothed, n_raw)
    assert np.isnan(masked[172 - 1, 0, 0])                      # rule: no observation in its own window -> none
    supported = n_raw > 0
    assert np.array_equal(masked[supported], smoothed[supported])


def test_detected_area_excludes_unscorable_event_days():
    from mhw.states.aggregates import aggregate_region
    T = 3
    A = np.ones((T, 1, 2), np.uint8)                            # both cells in an event all 3 days
    V = np.ones((T, 1, 2), np.uint8)
    V[1, 0, 1] = 0                                              # cell 2 unscorable on day 2 (a bridged gap day)
    f = np.ones((T, 1, 2), np.float32)
    ds = xr.Dataset({"A": (("time", "lat", "lon"), A), "I": (("time", "lat", "lon"), f),
                     "D": (("time", "lat", "lon"), f), "C": (("time", "lat", "lon"), f),
                     "O": (("time", "lat", "lon"), f), "V": (("time", "lat", "lon"), V),
                     "input_present": (("time",), np.ones(T, np.uint8))},
                    coords={"time": pd.date_range("2025-01-01", periods=T), "lat": [70.0], "lon": [-160.0, -159.75]})
    df = aggregate_region(ds, np.ones((1, 2), np.uint8), np.ones((1, 2), np.float32))
    assert df.area_frac.tolist() == [1.0, 0.5, 1.0]
    assert df.n_cells_event_unscorable.tolist() == [0, 1, 0]
