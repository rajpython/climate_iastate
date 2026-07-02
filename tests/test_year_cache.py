"""Tests for year_cache_stale — the single source of truth for OISST yearly
cache re-fetch decisions (fetch_year and the state engine's up-front
remote-connection check both delegate to it).

All tests are network-free: tiny synthetic NetCDF caches in tmp_path, with
`today` passed explicitly so the New-Year rules are exercised deterministically.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.climatology.build_mu_theta import year_cache_stale


def _write_cache(
    path: Path,
    start: str,
    end: str,
    *,
    drop_ice: bool = False,
    mtime: date | None = None,
) -> Path:
    """Write a minimal oisst-style yearly cache covering [start, end]."""
    times = pd.date_range(start, end, freq="D")
    n = len(times)
    data = np.zeros((n, 2, 2), dtype=np.float32)
    ds = xr.Dataset(
        {"sst": (["time", "lat", "lon"], data)},
        coords={"time": times, "lat": [55.0, 55.25], "lon": [-150.0, -149.75]},
    )
    if not drop_ice:
        ds["ice"] = (["time", "lat", "lon"], data)
    ds.to_netcdf(path)
    if mtime is not None:
        ts = datetime(mtime.year, mtime.month, mtime.day, 12).timestamp()
        os.utime(path, (ts, ts))
    return path


def test_missing_file_is_stale(tmp_path):
    assert year_cache_stale(tmp_path / "nope.nc", 2025, today=date(2026, 7, 1))


def test_corrupt_file_is_stale(tmp_path):
    p = tmp_path / "bad.nc"
    p.write_bytes(b"not a netcdf file")
    assert year_cache_stale(p, 2025, today=date(2026, 7, 1))


def test_missing_ice_var_is_stale(tmp_path):
    p = _write_cache(tmp_path / "c.nc", "2024-01-01", "2024-12-31", drop_ice=True)
    assert year_cache_stale(p, 2024, today=date(2026, 7, 1))


def test_old_year_complete_is_fresh(tmp_path):
    p = _write_cache(tmp_path / "c.nc", "2024-01-01", "2024-12-31")
    assert not year_cache_stale(p, 2024, today=date(2026, 7, 1))


def test_old_year_short_is_stale(tmp_path):
    # < 360 days for a past year -> truncated fetch, must re-pull
    p = _write_cache(tmp_path / "c.nc", "2024-01-01", "2024-11-01")
    assert year_cache_stale(p, 2024, today=date(2026, 7, 1))


def test_current_year_fresh_within_lag(tmp_path):
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-06-30")
    assert not year_cache_stale(p, 2026, today=date(2026, 7, 1))


def test_current_year_lagging_is_stale(tmp_path):
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-06-25")
    assert year_cache_stale(p, 2026, today=date(2026, 7, 1))


# --- New-Year settling-window rules (prior year only) -----------------------

def test_prior_year_tail_hole_is_stale_in_january(tmp_path):
    # Year turned with the Dec 30-31 tail unpublished: cache ends Dec 29.
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-12-29",
                     mtime=date(2026, 12, 31))
    assert year_cache_stale(p, 2026, today=date(2027, 1, 2))


def test_prior_year_complete_but_preliminary_fresh_before_finalize(tmp_path):
    # Complete through Dec 31, fetched Jan 2; before Jan 15 nothing to gain.
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-12-31",
                     mtime=date(2027, 1, 2))
    assert not year_cache_stale(p, 2026, today=date(2027, 1, 10))


def test_prior_year_refetches_once_after_finalize(tmp_path):
    # Fetched Jan 2 (December still preliminary); after Jan 15 -> re-pull once.
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-12-31",
                     mtime=date(2027, 1, 2))
    assert year_cache_stale(p, 2026, today=date(2027, 1, 20))


def test_prior_year_already_refetched_after_finalize_is_fresh(tmp_path):
    # Re-pulled on Jan 16 (mtime past the finalize point) -> settled for good.
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-12-31",
                     mtime=date(2027, 1, 16))
    assert not year_cache_stale(p, 2026, today=date(2027, 1, 20))


def test_prior_year_window_closes_mid_march(tmp_path):
    # After the settling window the prior year is treated as any past year:
    # a >=360-day cache is accepted as-is (no surprise re-fetches later on).
    p = _write_cache(tmp_path / "c.nc", "2026-01-01", "2026-12-29",
                     mtime=date(2026, 12, 31))
    assert not year_cache_stale(p, 2026, today=date(2027, 4, 1))
