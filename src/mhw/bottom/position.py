"""Cold-pool spatial-position indicators (derived; eastern Bering Sea).

The cold-pool area/temperature indicators say *how much* cold habitat exists; this module says
*where* it is. The default v1 indicator is the **southern extent**: the 5th-percentile latitude
of shelf cells at or below the threshold (≤ 2 °C) — the cold pool's southern reach, robust to
isolated cold cells and interpolation artefacts (unlike the absolute southernmost cell).

This is a **derived position metric, not an official AFSC ESR indicator** (ESRs convey position
through maps). The definition is deliberately **swappable** via ``method`` so it can be revised
to an AFSC convention later without touching the build column, KPIs, charts, or documentation —
only this module changes.

Pure / network-free, unit-tested on small grids; mirrors the helpers in :mod:`mhw.bottom.coldpool`.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

DEFAULT_METHOD = "p05_latitude"
SOUTHERN_PERCENTILE = 5.0   # the "southern reach" percentile for the default method


def _selected_latitudes(temp_grid, shelf, lats, threshold: float) -> np.ndarray:
    """Latitudes of shelf cells with finite bottom temperature ≤ ``threshold``."""
    grid = np.asarray(temp_grid, dtype=float)
    mask = np.asarray(shelf, dtype=bool)
    lat1d = np.asarray(lats, dtype=float)
    lat2d = np.broadcast_to(lat1d[:, None], grid.shape)
    sel = mask & np.isfinite(grid) & (grid <= threshold)
    return lat2d[sel]


def _p05_latitude(temp_grid, shelf, lats, lons, threshold) -> float:
    """Default: the 5th-percentile latitude of ≤ threshold shelf cells (southern reach)."""
    v = _selected_latitudes(temp_grid, shelf, lats, threshold)
    return float(np.percentile(v, SOUTHERN_PERCENTILE)) if v.size else float("nan")


def _minimum_latitude(temp_grid, shelf, lats, lons, threshold) -> float:
    """The absolute southernmost ≤ threshold shelf cell (sensitive to outliers; not default)."""
    v = _selected_latitudes(temp_grid, shelf, lats, threshold)
    return float(v.min()) if v.size else float("nan")


def _centroid_latitude(temp_grid, shelf, lats, lons, threshold) -> float:
    """Mean latitude of ≤ threshold shelf cells (centre of mass, not the southern boundary)."""
    v = _selected_latitudes(temp_grid, shelf, lats, threshold)
    return float(v.mean()) if v.size else float("nan")


def _not_implemented(name: str) -> Callable:
    def _fn(temp_grid, shelf, lats, lons, threshold) -> float:
        raise NotImplementedError(
            f"cold-pool position method {name!r} is documented but not wired in v1"
        )
    return _fn


# Method registry — the single place the definition lives. Only ``p05_latitude`` is wired in v1;
# minimum/centroid are available for comparison/tests; the rest are documented stubs.
_METHODS: dict[str, Callable] = {
    "p05_latitude": _p05_latitude,
    "minimum_latitude": _minimum_latitude,
    "centroid": _centroid_latitude,
    "reference_meridian": _not_implemented("reference_meridian"),
    "contour_edge": _not_implemented("contour_edge"),
}


def cold_pool_position(
    temp_grid,
    shelf,
    lats,
    lons=None,
    threshold: float = 2.0,
    method: str = DEFAULT_METHOD,
) -> float:
    """Latitude (°N) describing cold-pool position on a regular grid.

    Parameters
    ----------
    temp_grid : 2-D array (nlat, nlon) of bottom temperature (°C); NaN where invalid.
    shelf     : 2-D boolean mask of valid shelf cells (same shape as ``temp_grid``).
    lats      : 1-D latitudes (length nlat) for the grid rows.
    lons      : 1-D longitudes (length nlon); required only by ``reference_meridian``.
    threshold : cold-pool temperature threshold (default ≤ 2 °C).
    method    : definition selector (default ``"p05_latitude"`` — the southern extent).

    Returns the latitude, or NaN if no shelf cell meets the threshold.
    """
    if method not in _METHODS:
        raise ValueError(f"unknown method {method!r}; known: {sorted(_METHODS)}")
    return _METHODS[method](temp_grid, shelf, lats, lons, threshold)
