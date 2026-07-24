"""Tests for day-of-year climatology smoothing (canonical Hobday recipe)."""
from __future__ import annotations

import numpy as np

from mhw.climatology.smooth_doy import doy_window, smooth_doy_field


def test_doy_window_centered_and_wraps():
    assert doy_window(10, half_window=5) == list(range(5, 16))
    # near year start: wraps to the end of the year
    assert 366 in doy_window(1, half_window=5)
    assert 362 in doy_window(1, half_window=5)


def test_smooth_constant_unchanged():
    f = np.full((366, 3, 3), 7.0, dtype=np.float32)
    assert np.allclose(smooth_doy_field(f, 31), 7.0)


def test_smooth_conserves_sum_and_window_width():
    g = np.zeros((366, 1, 1), dtype=np.float32)
    g[0, 0, 0] = 31.0
    s = smooth_doy_field(g, 31)[:, 0, 0]
    assert abs(s.sum() - 31.0) < 1e-4          # moving average conserves total
    assert s[0] == 1.0 and s[15] == 1.0        # spike spread evenly over ±15
    assert s[16] == 0.0                        # exactly 31-day-wide window


def test_smooth_wraps_year_boundary():
    g = np.zeros((366, 1, 1), dtype=np.float32)
    g[0, 0, 0] = 31.0
    s = smooth_doy_field(g, 31)[:, 0, 0]
    assert s[365] == 1.0 and s[351] == 1.0     # Dec days pick up the Jan-1 spike
    assert s[350] == 0.0


def test_smooth_is_nan_aware():
    f = np.ones((366, 2, 2), dtype=np.float32)
    f[:, 0, 0] = np.nan                        # a land cell: all-NaN column
    out = smooth_doy_field(f, 31)
    assert np.all(np.isnan(out[:, 0, 0]))      # stays NaN, no warning-driven crash
    assert np.allclose(out[:, 1, 1], 1.0)      # finite cell unaffected


def test_window_one_is_noop():
    f = np.random.default_rng(0).random((366, 2, 2)).astype(np.float32)
    assert np.array_equal(smooth_doy_field(f, 1), f)
