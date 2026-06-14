"""Statistical baseline forecasts for an anomaly field.

All functions are array-shape-agnostic: the anomaly input may be a scalar, a 1-D
regional series, or a 2-D/3-D grid (lat, lon[, ...]). Per-cell AR(1) parameters
are fit independently across the leading *time* axis.

References
----------
Damped persistence and AR(1) are the standard low-cost MHW-forecast baselines
(cf. Jacox et al. 2022, *Global seasonal forecasts of marine heatwaves*). Skill
beyond these baselines is what any future dynamical/seasonal product must beat.
"""
from __future__ import annotations

import numpy as np


def persistence(anomaly_now: np.ndarray, horizon: int) -> np.ndarray:
    """Plain persistence: the forecast mean equals the current anomaly.

    Parameters
    ----------
    anomaly_now : array
        Current anomaly field (any shape).
    horizon : int
        Forecast lead in days (unused for the mean; kept for a uniform signature).

    Returns
    -------
    array
        Forecast-mean anomaly, same shape as *anomaly_now*.
    """
    return np.asarray(anomaly_now, dtype="float64")


def damped_persistence(
    anomaly_now: np.ndarray, phi: np.ndarray, horizon: int
) -> np.ndarray:
    """Damped persistence: anomaly relaxes toward 0 (climatology) at rate ``phi``.

        mean(h) = phi**h * anomaly_now

    Parameters
    ----------
    anomaly_now : array
        Current anomaly field.
    phi : array or float
        Lag-1 autocorrelation, broadcastable to *anomaly_now*. ``0 < phi < 1``.
    horizon : int
        Forecast lead in days.
    """
    phi = np.asarray(phi, dtype="float64")
    return (phi ** horizon) * np.asarray(anomaly_now, dtype="float64")


def ar1_forecast(
    anomaly_now: np.ndarray,
    phi: np.ndarray,
    sigma_eps: np.ndarray,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    """AR(1) forecast mean and predictive standard deviation at a lead.

        mean(h) = phi**h * anomaly_now
        var(h)  = sigma_eps**2 * (1 - phi**(2h)) / (1 - phi**2)

    As ``h -> inf`` the variance approaches the stationary variance
    ``sigma_eps**2 / (1 - phi**2)``, i.e. forecast uncertainty saturates at the
    climatological spread — the correct long-lead behaviour.

    Returns
    -------
    (mean, std) : tuple of arrays
        Forecast-mean anomaly and predictive standard deviation.
    """
    phi = np.asarray(phi, dtype="float64")
    sigma_eps = np.asarray(sigma_eps, dtype="float64")
    mean = (phi ** horizon) * np.asarray(anomaly_now, dtype="float64")
    # Guard phi -> 1 (random walk): fall back to var = h * sigma_eps**2.
    denom = 1.0 - phi ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        var_stationary = sigma_eps ** 2 * (1.0 - phi ** (2 * horizon)) / denom
    var_rw = horizon * sigma_eps ** 2
    var = np.where(denom > 1e-8, var_stationary, var_rw)
    # Broadcast std to the anomaly/mean shape (var may be scalar when phi/sigma are).
    std = np.sqrt(np.clip(var, 0.0, None)) + np.zeros_like(mean)
    return mean, std


def fit_ar1(
    anomaly_history: np.ndarray, time_axis: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Fit per-cell AR(1) parameters along *time_axis*.

        phi       = Σ a_t·a_{t-1} / Σ a_{t-1}²        (lag-1 regression, no intercept)
        sigma_eps = std( a_t − phi·a_{t-1} )           (innovation std)

    The anomaly history should already be de-seasonalised (SST − μ), so the mean
    is ~0 and a no-intercept AR(1) is appropriate.

    Parameters
    ----------
    anomaly_history : array
        Anomaly field with a leading (or *time_axis*) time dimension, e.g.
        ``(time, lat, lon)``.
    time_axis : int
        Axis holding the time dimension.

    Returns
    -------
    (phi, sigma_eps) : tuple of arrays
        Per-cell AR(1) coefficient and innovation std (time axis removed).
    """
    a = np.moveaxis(np.asarray(anomaly_history, dtype="float64"), time_axis, 0)
    a_prev = a[:-1]
    a_next = a[1:]
    num = np.nansum(a_next * a_prev, axis=0)
    den = np.nansum(a_prev * a_prev, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        phi = np.where(den > 0, num / den, 0.0)
    phi = np.clip(phi, 0.0, 0.999)  # keep stationary, non-negative persistence
    resid = a_next - phi * a_prev
    sigma_eps = np.nanstd(resid, axis=0)
    return phi, sigma_eps
