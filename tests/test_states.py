"""Unit tests for doy_window, compute_mu_theta, and _update_one_day.

All tests use synthetic numpy grids — no ERDDAP, no disk I/O.
"""
from __future__ import annotations

import numpy as np
import pytest

from mhw.climatology.smooth_doy import compute_mu_theta, doy_window
from mhw.states.update_states import StateBuffer, _update_one_day

# Keyword arguments matching config/climatology.yml defaults
_UPDATE_KWARGS: dict = dict(
    gap_days=2,
    confirm_days=5,
    int_ref="threshold",
    onset_ref="physical_start",
    k_days=3,
    apply_ice=True,
    ice_thresh=0.15,
)


# ---------------------------------------------------------------------------
# doy_window — pure function, 3 tests
# ---------------------------------------------------------------------------

class TestDoyWindow:
    def test_doy1_wraps_back(self):
        """doy_window(1, 5) → 11 items, all in [1,366], includes wrap-around DOY 361–366."""
        result = doy_window(1, 5)
        assert len(result) == 11
        assert all(1 <= d <= 366 for d in result)
        # wrap-around: should include high DOYs near end of year
        assert any(d >= 361 for d in result)

    def test_doy366_wraps_forward(self):
        """doy_window(366, 5) → 11 items, includes DOY 1–5 (forward wrap)."""
        result = doy_window(366, 5)
        assert len(result) == 11
        assert all(1 <= d <= 366 for d in result)
        # wrap-around: should include early DOYs at start of year
        assert any(d <= 5 for d in result)

    def test_doy180_no_wrap(self):
        """doy_window(180, 5) → exactly DOY 175..185, no wrap."""
        result = doy_window(180, 5)
        assert result == list(range(175, 186))
        assert len(result) == 11


# ---------------------------------------------------------------------------
# compute_mu_theta — pure function, 2 tests
# ---------------------------------------------------------------------------

class TestComputeMuTheta:
    def test_known_stack(self):
        """Ones + small noise: mu ≈ nanmean, theta = 90th percentile."""
        rng = np.random.default_rng(42)
        stack = (
            np.ones((30, 4, 5), dtype=np.float32)
            + rng.normal(0, 0.1, (30, 4, 5)).astype(np.float32)
        )
        mu, theta = compute_mu_theta(stack, percentile=90.0)

        assert mu.shape == (4, 5)
        assert theta.shape == (4, 5)
        np.testing.assert_allclose(mu, np.nanmean(stack, axis=0), rtol=1e-5)
        np.testing.assert_allclose(
            theta, np.nanpercentile(stack, 90.0, axis=0), rtol=1e-5
        )

    def test_nan_column_propagates(self):
        """Full-NaN column → NaN output; all-finite columns → finite output."""
        stack = np.ones((10, 2, 2), dtype=np.float32)
        stack[:, 0, 0] = np.nan  # make one column fully NaN

        mu, theta = compute_mu_theta(stack)

        assert np.isnan(mu[0, 0]), "mu of full-NaN column should be NaN"
        assert np.isnan(theta[0, 0]), "theta of full-NaN column should be NaN"
        # remaining cells must be finite
        finite_mu = mu[~np.isnan(mu)]
        assert np.all(np.isfinite(finite_mu))
        finite_theta = theta[~np.isnan(theta)]
        assert np.all(np.isfinite(finite_theta))


# ---------------------------------------------------------------------------
# _update_one_day — core state logic, 7 tests
# ---------------------------------------------------------------------------

class TestUpdateOneDay:
    """Tests use the `tiny_state` fixture (function-scoped → fresh state per test)."""

    @staticmethod
    def _run(sst, ice, state, theta, mu, **extra_kwargs):
        kwargs = {**_UPDATE_KWARGS, **extra_kwargs}
        return _update_one_day(sst, ice, theta, mu, state, **kwargs)

    def test_exceedance_detected(self, tiny_state):
        """1 day sst_above: x > 0, A == 0 (not yet confirmed)."""
        state, theta, mu, sst_above, _, ice_clear, _ = tiny_state
        x, A, D, I, C, O = self._run(sst_above, ice_clear, state, theta, mu)
        assert np.all(x > 0), "exceedance should be positive"
        assert np.all(A == 0), "event not confirmed after only 1 day"

    def test_no_exceedance_below(self, tiny_state):
        """1 day sst_below: x == 0, A == 0."""
        state, theta, mu, _, sst_below, ice_clear, _ = tiny_state
        x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)
        assert np.all(x == 0)
        assert np.all(A == 0)

    def test_confirmation_fires(self, tiny_state):
        """Repeating sst_above for confirm_days → A == 1 on the final call."""
        state, theta, mu, sst_above, _, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        for _ in range(confirm_days):
            x, A, D, I, C, O = self._run(sst_above, ice_clear, state, theta, mu)
        assert np.all(A == 1), "event must be confirmed after 5 consecutive above-threshold days"

    def test_gap_bridged(self, tiny_state):
        """confirm_days above → gap_days below → A still == 1 (gap bridged)."""
        state, theta, mu, sst_above, sst_below, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        gap_days = _UPDATE_KWARGS["gap_days"]

        for _ in range(confirm_days):
            self._run(sst_above, ice_clear, state, theta, mu)

        for _ in range(gap_days):
            x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)

        assert np.all(A == 1), f"A should remain 1 during {gap_days}-day gap"

    def test_gap_closes(self, tiny_state):
        """confirm_days above → gap_days+1 below → A == 0 (gap exceeded)."""
        state, theta, mu, sst_above, sst_below, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        gap_days = _UPDATE_KWARGS["gap_days"]

        for _ in range(confirm_days):
            self._run(sst_above, ice_clear, state, theta, mu)

        for _ in range(gap_days + 1):
            x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)

        assert np.all(A == 0), "event must close after gap_days+1 sub-threshold days"

    def test_ice_mask_suppresses(self, tiny_state):
        """sst_above but ice_heavy → A == 0, x == 0 (ice mask applied)."""
        state, theta, mu, sst_above, _, _, ice_heavy = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]

        for _ in range(confirm_days):
            x, A, D, I, C, O = self._run(sst_above, ice_heavy, state, theta, mu)

        assert np.all(x == 0), "ice-covered cells must have zero exceedance"
        assert np.all(A == 0), "ice-covered cells must not confirm"

    def test_nan_sst_no_crash(self, tiny_state):
        """NaN SST: function must not raise; A == 0."""
        state, theta, mu, _, _, ice_clear, _ = tiny_state
        sst_nan = np.full((2, 3), np.nan, dtype=np.float32)
        # Must not raise
        x, A, D, I, C, O = self._run(sst_nan, ice_clear, state, theta, mu)
        assert np.all(A == 0), "NaN SST cells must not produce confirmed events"
