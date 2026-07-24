"""DOY window logic and percentile statistics for climatology build.

All functions are pure (no I/O).
"""
from __future__ import annotations

import warnings

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


def smooth_doy_field(field: np.ndarray, window_days: int = 31) -> np.ndarray:
    """Circular centered moving average along the day-of-year axis (axis 0).

    This is the second smoothing step of the canonical Hobday et al. (2016) MHW
    definition: after the 11-day-window percentile, the seasonally-varying
    climatology mu(d) and threshold theta90(d) are each smoothed with a 31-day
    moving average to remove the day-to-day sampling noise left in the per-DOY
    percentile (each DOY is estimated from only ~11 x N_baseline pooled values).

    Wrap-around at the year boundary (Dec <-> Jan) and NaN-aware: land/masked
    cells stay NaN; a DOY whose window has some finite days averages over those.

    Parameters
    ----------
    field       : (n_doy, n_lat, n_lon) float array (n_doy usually 366), may hold NaN
    window_days : centered window length in days (default 31, Hobday-canonical)

    Returns
    -------
    Smoothed array, same shape and dtype as *field*.
    """
    if window_days <= 1:
        return field
    n = field.shape[0]
    half = window_days // 2
    padded = np.concatenate([field[n - half:], field, field[:half]], axis=0)
    out = np.empty_like(field)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN slices -> NaN (land)
        for d in range(n):
            out[d] = np.nanmean(padded[d:d + window_days], axis=0)
    return out.astype(field.dtype)
