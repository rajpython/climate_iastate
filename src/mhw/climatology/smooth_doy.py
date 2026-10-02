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


def support_counts(valid: np.ndarray, doy: np.ndarray, year: np.ndarray, half_window: int = 5,
                   post_window: int = 31, n_doys: int = 366) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """How many baseline observations stand behind each (doy, cell) threshold.

    valid : (n_days, n_lat, n_lon) bool -- a usable baseline observation (finite SST, not ice-masked)
    doy   : (n_days,) 1..366 ; year : (n_days,)

    Returns (n_raw_window, n_support_obs, n_support_years), each (n_doys, n_lat, n_lon) int32:
      n_raw_window    -- observations in the doy's OWN 11-day window (what the raw percentile is computed from)
      n_support_obs   -- DISTINCT observations behind the SMOOTHED value: the post-smoothing window reaches
                         +-(post_window//2) raw days, each reaching +-half_window, so every observation within
                         +-(half_window + post_window//2) days of the doy feeds it, each counted once
      n_support_years -- distinct baseline years among those observations (observations in one year are not
                         independent; this is the better reliability count)
    """
    reach = half_window + post_window // 2
    shape = (n_doys,) + valid.shape[1:]
    per_doy = np.zeros(shape, np.int32)
    np.add.at(per_doy, doy - 1, valid.astype(np.int32))
    def circ_sum(a, h):
        return sum(np.roll(a, k, axis=0) for k in range(-h, h + 1))
    n_raw = circ_sum(per_doy, half_window)
    n_obs = circ_sum(per_doy, reach)
    n_years = np.zeros(shape, np.int32)
    for y in np.unique(year):
        sel = year == y
        pres = np.zeros(shape, np.int32)
        np.add.at(pres, doy[sel] - 1, valid[sel].astype(np.int32))
        n_years += (circ_sum((pres > 0).astype(np.int32), reach) > 0).astype(np.int32)
    return n_raw.astype(np.int32), n_obs.astype(np.int32), n_years


def mask_unsupported(field: np.ndarray, n_raw_window: np.ndarray) -> np.ndarray:
    """Data-availability rule (vintage #6): NaN wherever the doy's own window held zero observations.

    Applied AFTER the unchanged 31-day smoothing, so every supported value is untouched; only values the
    NaN-aware smoothing would otherwise create from neighbouring days (up to 20 days away) are removed.
    """
    out = np.array(field, copy=True)
    out[n_raw_window == 0] = np.nan
    return out
