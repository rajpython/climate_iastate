"""Sanity tests for the forecast pure-math layer (no I/O)."""
from __future__ import annotations

import numpy as np

from mhw.forecast.baselines import (
    ar1_forecast,
    damped_persistence,
    fit_ar1,
    persistence,
)
from mhw.forecast.exceedance import exceedance_probability
from mhw.forecast.regional import expected_area_fraction, regional_probability


def test_persistence_is_identity():
    a = np.array([0.5, -1.0, 2.0])
    assert np.allclose(persistence(a, horizon=14), a)


def test_damped_persistence_relaxes_to_zero():
    a = np.array([2.0])
    near = damped_persistence(a, phi=0.9, horizon=1)
    far = damped_persistence(a, phi=0.9, horizon=60)
    assert near[0] < a[0]
    assert abs(far[0]) < abs(near[0])
    assert abs(far[0]) < 0.05


def test_ar1_variance_saturates():
    a = np.array([2.0])
    _, s_short = ar1_forecast(a, phi=0.9, sigma_eps=1.0, horizon=1)
    _, s_long = ar1_forecast(a, phi=0.9, sigma_eps=1.0, horizon=500)
    stationary = np.sqrt(1.0 ** 2 / (1 - 0.9 ** 2))
    assert s_short[0] < s_long[0]
    assert np.isclose(s_long[0], stationary, rtol=1e-3)


def test_fit_ar1_recovers_known_phi():
    rng = np.random.default_rng(0)
    phi_true, n = 0.8, 20000
    a = np.zeros(n)
    for t in range(1, n):
        a[t] = phi_true * a[t - 1] + rng.normal(0, 1.0)
    phi, sigma = fit_ar1(a[:, None], time_axis=0)
    assert np.isclose(phi[0], phi_true, atol=0.02)
    assert np.isclose(sigma[0], 1.0, atol=0.05)


def test_exceedance_probability_at_threshold_is_half():
    p = exceedance_probability(forecast_mean=1.0, forecast_std=1.0, threshold=1.0)
    assert np.isclose(p, 0.5)


def test_exceedance_monotonic_in_mean():
    lo = exceedance_probability(0.0, 1.0, 1.0)
    hi = exceedance_probability(2.0, 1.0, 1.0)
    assert hi > lo


def test_regional_probability_is_weighted_mean():
    prob = np.array([[1.0, 0.0], [0.0, 0.0]])
    mask = np.array([[1, 1], [1, 1]])
    weights = np.array([[3.0, 1.0], [0.0, 0.0]])  # only top row has area
    # weighted mean = (1*3 + 0*1) / 4 = 0.75
    assert np.isclose(regional_probability(prob, mask, weights), 0.75)
    assert np.isclose(expected_area_fraction(prob, mask, weights), 0.75)
