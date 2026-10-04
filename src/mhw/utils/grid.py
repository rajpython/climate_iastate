"""Exact coordinate assertions at array joins.

Two arrays joined cell-by-cell must sit on the SAME grid: same length, same order, same values.
A shape check alone passes a grid that is shifted by one cell or reversed, and a
``.sel(method="nearest")`` silently snaps a shifted grid onto the wrong cells. Both joins this
module guards (raw SST/ice <-> theta90/mu in the state engine; region mask <-> area weight <->
state grid in the aggregation) passed on the vintage-#6 grids. These checks are prevention
(dashboard audit follow-up, 2026-10-04), not the fix for an observed misalignment.

Equality is exact (``np.array_equal`` after promoting both sides to float64): every grid here
derives from the same OISST 0.25 deg axis, so any difference is a real misalignment, not round-off.
"""
from __future__ import annotations

import numpy as np


class GridMismatchError(ValueError):
    """Two arrays about to be joined cell-by-cell are not on the same coordinates."""


def _describe(a: np.ndarray, b: np.ndarray) -> str:
    if a.shape != b.shape:
        return f"length {a.size} vs {b.size}"
    d = np.abs(a - b)
    i = int(np.nanargmax(d))
    return f"max |delta| {float(d[i]):.6g} at index {i} ({a[i]!r} vs {b[i]!r})"


def assert_same_axis(a, b, name: str, where: str) -> None:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    if a.shape != b.shape or not np.array_equal(a, b):
        raise GridMismatchError(f"{where}: {name} axes differ ({_describe(a, b)})")


def assert_same_grid(lat_a, lon_a, lat_b, lon_b, where: str) -> None:
    """Raise GridMismatchError unless (lat_a, lon_a) equals (lat_b, lon_b) exactly, in order, and
    both satisfy the axis contract (unique, strictly increasing): equal-but-duplicated axes fail."""
    for v, n in ((lat_a, "lat"), (lon_a, "lon"), (lat_b, "lat"), (lon_b, "lon")):
        assert_axis_contract(v, n, where)
    assert_same_axis(lat_a, lat_b, "lat", where)
    assert_same_axis(lon_a, lon_b, "lon", where)


def assert_axis_contract(values, name: str, where: str) -> None:
    """A coordinate axis must be 1-D, finite, unique and strictly increasing (the pipeline's order)."""
    v = np.asarray(values, dtype=np.float64)
    if v.ndim != 1 or v.size == 0:
        raise GridMismatchError(f"{where}: {name} must be a non-empty 1-D axis (shape {v.shape})")
    if not np.all(np.isfinite(v)):
        raise GridMismatchError(f"{where}: {name} has non-finite values")
    d = np.diff(v)
    if np.any(d == 0):
        i = int(np.flatnonzero(d == 0)[0])
        raise GridMismatchError(f"{where}: {name} has duplicate coordinates ({v[i]!r} at {i} and {i + 1})")
    if np.any(d < 0):
        i = int(np.flatnonzero(d < 0)[0])
        raise GridMismatchError(f"{where}: {name} is not strictly increasing ({v[i]!r} then {v[i + 1]!r})")


def assert_grid_contract(da, where: str, trailing_dims=("lat", "lon")) -> None:
    """A DataArray joined cell-by-cell must end in the named dims (in order) on contract-valid axes."""
    dims = tuple(da.dims)
    if dims[-len(trailing_dims):] != tuple(trailing_dims):
        raise GridMismatchError(f"{where}: dims {dims} do not end in {tuple(trailing_dims)}")
    for d in trailing_dims:
        assert_axis_contract(da[d].values, d, where)
