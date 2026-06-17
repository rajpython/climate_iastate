"""Aggregate a cell-probability field to regional forecast products.

The cell-level exceedance map is the primary product (a spatial MHW-probability
map is far more informative for an ecosystem report card than a scalar). These
helpers derive the regional summaries that answer "what fraction of the region is
likely to be in a heatwave" — reusing the same area weights and region masks as
the monitoring aggregates (`mhw.regions.weights`, `mhw.regions.masks`).
"""
from __future__ import annotations

import numpy as np


def _masked_weights(mask: np.ndarray, weights: np.ndarray) -> np.ndarray:
    w = np.asarray(weights, dtype="float64") * (np.asarray(mask) > 0)
    total = w.sum()
    if total <= 0:
        raise ValueError("Region mask/weights sum to zero — empty region?")
    return w / total


def regional_probability(
    prob_grid: np.ndarray, mask: np.ndarray, weights: np.ndarray
) -> float:
    """Area-weighted mean cell probability over the region.

    Interpretable as the *expected fraction of region area* in MHW at the lead —
    equivalently the area-weighted regional MHW probability.
    """
    w = _masked_weights(mask, weights)
    p = np.asarray(prob_grid, dtype="float64")
    return float(np.nansum(p * w))


def expected_area_fraction(
    prob_grid: np.ndarray, mask: np.ndarray, weights: np.ndarray
) -> float:
    """Alias of :func:`regional_probability`, named for the area-fraction framing.

    This is the forecast analogue of the monitored ``area_frac`` in
    ``data/derived/aggregates_region/`` — directly comparable for backtesting.
    """
    return regional_probability(prob_grid, mask, weights)


# NOTE (TODO, post-MVP): P(area_frac > threshold) — e.g. P(>5% of region in MHW),
# matching config `regional_events.area_frac_threshold` — needs the joint spatial
# distribution, not just marginal cell probabilities (cells are strongly
# correlated). Options: (a) Monte-Carlo from a spatially-correlated anomaly
# forecast, (b) calibrate a logistic map from expected_area_fraction to the
# observed exceedance frequency in the backtest. Defer until the marginal-map MVP
# is validated.
