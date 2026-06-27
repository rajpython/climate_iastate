"""Tests for the daily-then-time open-water helper — pure, network-free."""
import numpy as np

from mhw.bottom.surface import daily_then_time_mean


def test_daily_then_time_mean_per_timestep_mask():
    # 3 days, 1x2 grid. Day1: only cell0 open (cell1 iced) → 5. Day2: only cell0 open → 6.
    # Day3: both iced → day dropped. Surface = mean(5,6) = 5.5; ~1 open cell/day.
    sst = np.array([[[5.0, 8.0]], [[6.0, 9.0]], [[7.0, 10.0]]])   # (time, lat, lon)
    ice = np.array([[[0.0, 1.0]], [[0.0, 0.9]], [[0.5, 1.0]]])
    shelf = np.array([[True, True]])
    areas = np.array([[1.0, 1.0]])
    mean, n = daily_then_time_mean(sst, sst, ice, shelf, areas, ice_max=0.15)
    assert mean == 5.5 and n == 1


def test_daily_then_time_mean_field_distinct_from_sst():
    # field (e.g. model bottom) averaged over the open-water mask derived from sst/ice.
    # Day1: cell1 iced → field over open = 2. Day2: both open → mean(3,3)=3. → mean(2,3)=2.5.
    field = np.array([[[2.0, 2.0]], [[3.0, 3.0]]])
    sst = np.array([[[5.0, 8.0]], [[6.0, 9.0]]])
    ice = np.array([[[0.0, 1.0]], [[0.0, 0.0]]])
    shelf = np.array([[True, True]])
    areas = np.array([[1.0, 1.0]])
    mean, _ = daily_then_time_mean(field, sst, ice, shelf, areas, ice_max=0.15)
    assert mean == 2.5


def test_daily_then_time_mean_all_ice_is_nan():
    sst = np.array([[[-1.8]]])
    ice = np.array([[[1.0]]])
    mean, n = daily_then_time_mean(sst, sst, ice, np.array([[True]]), np.array([[1.0]]))
    assert np.isnan(mean) and n == 0
