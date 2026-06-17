"""Gaussian exceedance probability — anomaly forecast → MHW probability.

Given a forecast distribution for the anomaly (mean, std) and the MHW threshold
expressed as an anomaly above the climatological mean (``theta90 - mu``), the
probability that a cell is in a marine heatwave at the forecast lead is

    P(MHW) = P(anomaly_fc > thr) = 1 - Φ((thr - mean) / std) = Φ((mean - thr) / std)

This is the Jacox et al. (2022) construction: a continuous forecast field is
mapped to an exceedance probability against the same θ₉₀ threshold the monitoring
engine already uses, so forecast and nowcast are on a consistent footing.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def exceedance_probability(
    forecast_mean: np.ndarray,
    forecast_std: np.ndarray,
    threshold: np.ndarray,
) -> np.ndarray:
    """Probability the forecast anomaly exceeds *threshold*.

    Parameters
    ----------
    forecast_mean : array
        Forecast-mean anomaly (e.g. from :func:`baselines.damped_persistence`).
    forecast_std : array
        Predictive standard deviation. Where ``std == 0`` the result degenerates
        to a hard 0/1 step at the threshold.
    threshold : array
        MHW threshold in anomaly space, ``theta90 - mu``. Broadcastable to the
        forecast fields.

    Returns
    -------
    array
        Exceedance probability in [0, 1].
    """
    mean = np.asarray(forecast_mean, dtype="float64")
    std = np.asarray(forecast_std, dtype="float64")
    thr = np.asarray(threshold, dtype="float64")

    z = np.where(std > 0, (mean - thr) / np.where(std > 0, std, 1.0), 0.0)
    prob = norm.cdf(z)
    # Degenerate (std == 0): deterministic step.
    prob = np.where(std > 0, prob, (mean > thr).astype("float64"))
    return np.clip(prob, 0.0, 1.0)
