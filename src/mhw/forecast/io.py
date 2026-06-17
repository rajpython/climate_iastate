"""Data adapters for the forecast engine (the only source-specific layer).

For the SST MVP these wrap assets that already exist on disk — nothing new needs
ingesting:

* μ and θ₉₀  — per-region zarr in ``data/derived/climatology/`` (see
  ``mhw.states.update_states._load_climatology`` which returns
  ``(theta90, mu, lats, lons)``).
* daily SST  — OISST year cache fetched by ``mhw.climatology.build_mu_theta``
  (``fetch_year`` / ``_year_cache_path``).
* mask + weights — ``mhw.regions.masks`` / ``mhw.regions.weights``.

When the bottom-temperature increment arrives, a sibling adapter loads MOM6
bottom-temp + ``theta90_bottom`` with the *same* return contract, and the rest of
the engine is unchanged. Keep these signatures stable.

TODO (MVP wiring): implement the bodies below against the loaders named above.
They are stubbed so the package imports cleanly and the contract is explicit.
"""
from __future__ import annotations

from datetime import date

import numpy as np


def load_climatology(region_id: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(theta90, mu, lats, lons)`` for *region_id*.

    Thin wrapper over ``mhw.states.update_states._load_climatology`` so the
    forecast package does not reach into ``states`` internals directly.
    """
    raise NotImplementedError("MVP wiring: delegate to states._load_climatology")


def load_anomaly_history(
    region_id: str, start: date, end: date
) -> np.ndarray:
    """Return the de-seasonalised anomaly cube ``(time, lat, lon) = SST − μ``.

    Used by :func:`mhw.forecast.baselines.fit_ar1` to estimate per-cell φ and
    σ_eps over a training window (suggest the full backfill, ice-masked exactly
    as in monitoring so the statistics are consistent).
    """
    raise NotImplementedError("MVP wiring: SST cache − mu, ice-masked")


def load_current_anomaly(region_id: str, as_of: date) -> np.ndarray:
    """Return the most recent anomaly field ``SST(as_of) − μ(doy)``."""
    raise NotImplementedError("MVP wiring: latest SST − mu for as_of")
