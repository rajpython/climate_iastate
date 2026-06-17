"""Short-term marine-heatwave forecasting (statistical baselines).

Design principle — **variable- and source-agnostic**.
The engine forecasts *an anomaly field* against *a θ₉₀ threshold field* and emits
exceedance probabilities. Today the anomaly is OISST SST − μ; tomorrow it can be
MOM6 bottom-temperature anomaly, or an NMME/PSL seasonal ensemble, with no change
to the math in `baselines`, `exceedance`, or `regional`. Only the data adapters
(`io`) change per source.

Pipeline
--------
    anomaly_now  = SST − μ                      (per grid cell)
    anomaly_fc   = baseline forecast at horizon h  (persistence / damped / AR1)
    P(MHW, h)    = P(anomaly_fc > θ₉₀ − μ)       (Gaussian exceedance)
    regional     = area-weighted aggregation of the cell-probability field

See docs/forecast_extension/sst-forecast-mvp-plan.md for the full plan.
"""
from __future__ import annotations

from mhw.forecast.baselines import (
    ar1_forecast,
    damped_persistence,
    fit_ar1,
    persistence,
)
from mhw.forecast.exceedance import exceedance_probability
from mhw.forecast.regional import expected_area_fraction, regional_probability

__all__ = [
    "persistence",
    "damped_persistence",
    "ar1_forecast",
    "fit_ar1",
    "exceedance_probability",
    "regional_probability",
    "expected_area_fraction",
]
