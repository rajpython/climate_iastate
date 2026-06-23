"""Manager-facing descriptive indicators for the bottom-state / cold-pool pages.

These turn a raw annual series (cold-pool area or mean bottom temperature) into the kind of
report-card numbers an AFSC ESR / fisheries manager reads: where does this year sit in the
historical distribution, what category of concern is that, how far from the climatological
norm, and which past years it most resembles.

All functions are **pure** (no network, no Streamlit, no file IO) so they unit-test on small
in-memory frames — mirroring the percentile pattern in :mod:`mhw.states.risk`. Everything here
is **descriptive of observed / historical state** (no prediction); rank on the *observed*
(validated) series and state the baseline period, per the defensibility checklist.

Conventions (stated, not derived — tie to ESR practice where possible):
  * **Anomaly baseline** = ``1991–2020`` (matches the MHW climatology baseline in
    ``config/climatology.yml``). Compute it on the observed annual series.
  * **Risk categories** map a percentile to a manager label. For the cold pool, a *small* value
    is the concern (cold-water specialists lose thermal refuge), so low percentile = concern:
    top 20% **Favorable** · middle **Typical** · bottom 20% **Elevated concern** · bottom 10%
    **High concern**. For a metric where *high* is the concern (e.g. a warm bottom-temperature
    anomaly), pass ``concern_when_low=False`` to flip the scale.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import percentileofscore

# Fixed climatological baseline for anomalies (matches config/climatology.yml).
BASELINE_START = 1991
BASELINE_END = 2020

# Category labels and their report-card colours (green/orange/red mirror risk_gauge.py).
CATEGORY_COLORS: dict[str, str] = {
    "Favorable": "green",
    "Typical": "gray",
    "Elevated concern": "orange",
    "High concern": "red",
}


def _clean(series: Sequence[float]) -> np.ndarray:
    """Return the finite values of a series as a float array (drops NaN/inf)."""
    arr = np.asarray(series, dtype=float)
    return arr[np.isfinite(arr)]


def percentile_rank(value: float, series: Sequence[float]) -> float:
    """Percentile rank (0–100) of ``value`` within the historical ``series``.

    Uses the same ``percentileofscore`` primitive as :mod:`mhw.states.risk`. Returns NaN if
    ``value`` is not finite or the series has no finite values.
    """
    ref = _clean(series)
    if not np.isfinite(value) or ref.size == 0:
        return float("nan")
    return float(percentileofscore(ref, value, kind="mean"))


def ordinal_rank(value: float, series: Sequence[float], smallest: bool = True) -> int:
    """1-based rank of ``value`` within ``series`` — e.g. "5th smallest cold pool".

    ``smallest=True`` counts from the low end (rank 1 = smallest value); ``False`` counts from
    the high end. Ties share the lower rank. ``value`` is included in the population it is
    ranked against (so a value present in the series ranks honestly against its peers).
    """
    ref = _clean(series)
    if not np.isfinite(value) or ref.size == 0:
        return 0
    pop = ref if np.any(np.isclose(ref, value)) else np.append(ref, value)
    if smallest:
        return int(np.sum(pop < value)) + 1
    return int(np.sum(pop > value)) + 1


def risk_category(pct: float, concern_when_low: bool = True) -> str:
    """Map a percentile rank (0–100) to a manager category label.

    ``concern_when_low`` (default) treats a *low* percentile as the concern end (cold-pool
    area). Set ``False`` when a *high* percentile is the concern (e.g. warm anomaly).
    """
    if not np.isfinite(pct):
        return "Typical"
    # Put everything on a "low = concern" scale.
    p = pct if concern_when_low else 100.0 - pct
    if p < 10:
        return "High concern"
    if p < 20:
        return "Elevated concern"
    if p >= 80:
        return "Favorable"
    return "Typical"


def category_color(label: str) -> str:
    """Report-card colour for a category label (defaults to gray)."""
    return CATEGORY_COLORS.get(label, "gray")


def anomaly(value: float, baseline_series: Sequence[float]) -> float:
    """``value`` minus the mean of ``baseline_series`` (the climatological norm).

    Pass the baseline-period slice of the observed series (e.g. years 1991–2020). Returns NaN
    if ``value`` is not finite or the baseline has no finite values.
    """
    base = _clean(baseline_series)
    if not np.isfinite(value) or base.size == 0:
        return float("nan")
    return float(value - base.mean())


def analog_years(
    target_year: int,
    years: Sequence[int],
    *value_columns: Sequence[float],
    k: int = 3,
) -> list[int]:
    """The ``k`` historical years whose conditions most resemble ``target_year``.

    Similarity is Euclidean distance in **z-scored** space across the supplied value columns
    (e.g. cold-pool area and mean bottom temperature), so differently-scaled variables count
    equally. The target year itself is excluded; years with any non-finite component are
    skipped. Returns nearest-first.
    """
    yrs = np.asarray(years)
    if yrs.size == 0 or not value_columns:
        return []
    # z-score each column over the finite population.
    z_cols = []
    for col in value_columns:
        c = np.asarray(col, dtype=float)
        finite = c[np.isfinite(c)]
        sd = finite.std()
        z_cols.append((c - finite.mean()) / sd if sd and sd > 0 else c * 0.0)
    z = np.vstack(z_cols).T  # shape (n_years, n_cols)

    where_target = np.where(yrs == target_year)[0]
    if where_target.size == 0 or not np.all(np.isfinite(z[where_target[0]])):
        return []
    tvec = z[where_target[0]]

    dists: list[tuple[float, int]] = []
    for i, yr in enumerate(yrs):
        if yr == target_year or not np.all(np.isfinite(z[i])):
            continue
        dists.append((float(np.linalg.norm(z[i] - tvec)), int(yr)))
    dists.sort(key=lambda t: (t[0], t[1]))
    return [yr for _, yr in dists[:k]]
