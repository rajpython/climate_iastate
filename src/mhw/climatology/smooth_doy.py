"""DOY window logic and percentile statistics for climatology build.

All functions are pure (no I/O).
"""
from __future__ import annotations

import numpy as np


def doy_window(doy: int, half_window: int = 5, n_doys: int = 366) -> list[int]:
    """Return DOY values (1..n_doys) within half_window of doy, wrapping around year.

    Parameters
    ----------
    doy        : target day-of-year (1..n_doys)
    half_window: number of days each side (default 5 → 11-day window)
    n_doys     : number of DOYs in the cycle (default 366)

    Returns
    -------
    Sorted list of DOY integers (1-based), length = 2*half_window + 1
    """
    doys = []
    for offset in range(-half_window, half_window + 1):
        d = ((doy - 1 + offset) % n_doys) + 1
        doys.append(d)
    return sorted(set(doys))


def compute_mu_theta(
    stack: np.ndarray,
    percentile: float = 90.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute nanmean and nanpercentile over axis=0 of *stack*.

    Parameters
    ----------
    stack      : (n_samples, n_lat, n_lon) float array, may contain NaN
    percentile : threshold percentile (default 90)

    Returns
    -------
    (mu, theta) each of shape (n_lat, n_lon), dtype float32
    """
    mu = np.nanmean(stack, axis=0).astype(np.float32)
    theta = np.nanpercentile(stack, percentile, axis=0).astype(np.float32)
    return mu, theta
