"""Forecast verification — rolling-origin backtest and skill scores.

A forecast is only worth shipping if it beats the cheap reference baselines. The
two references every lead must beat:

* **climatology** — the unconditional MHW frequency for that day-of-year.
* **persistence** — "tomorrow looks like today".

Headline metric is the Brier score (mean squared error of the probability
forecast vs the {0,1} MHW outcome), summarised as a Brier Skill Score relative to
climatology. Reliability (calibration) diagrams come later.
"""
from __future__ import annotations

import numpy as np


def brier_score(prob: np.ndarray, outcome: np.ndarray) -> float:
    """Mean squared error between forecast probability and {0,1} outcome."""
    p = np.asarray(prob, dtype="float64")
    o = np.asarray(outcome, dtype="float64")
    return float(np.nanmean((p - o) ** 2))


def brier_skill_score(
    prob: np.ndarray, outcome: np.ndarray, reference_prob: np.ndarray
) -> float:
    """Brier skill of *prob* vs a *reference_prob* (e.g. climatology).

    Returns 1.0 for a perfect forecast, 0.0 for no skill over the reference, and
    negative when the forecast is worse than the reference.
    """
    bs = brier_score(prob, outcome)
    bs_ref = brier_score(reference_prob, outcome)
    if bs_ref <= 0:
        return float("nan")
    return 1.0 - bs / bs_ref


# TODO (MVP): rolling-origin harness.
#   for as_of in test_dates:
#       fit AR(1) on history strictly before as_of   (no leakage)
#       forecast leads {14, 30} days
#       record (prob, observed MHW outcome) per cell and regionally
#   then report Brier / BSS vs climatology and persistence, per region and lead.
def rolling_origin_backtest(*args, **kwargs):  # noqa: D401
    """Placeholder — see TODO above."""
    raise NotImplementedError("MVP: implement leakage-free rolling-origin loop")
