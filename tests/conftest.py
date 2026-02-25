"""Shared fixtures for MHW test suite.

No ERDDAP or network calls — all fixtures use either:
  (a) synthetic numpy grids, or
  (b) existing on-disk parquet/zarr files.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parents[1]
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"


# ---------------------------------------------------------------------------
# Session-scoped: config + on-disk parquet
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def cfg():
    """Load config/climatology.yml."""
    with open(PROJECT_ROOT / "config" / "climatology.yml") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def goa_agg():
    """Load GOA regional daily aggregate parquet (skipped in CI — file absent)."""
    path = DATA_DERIVED / "aggregates_region" / "region_daily_goa.parquet"
    if not path.exists():
        pytest.skip(f"Data file not found (run mhw-backfill first): {path}")
    return pd.read_parquet(path)


@pytest.fixture(scope="session")
def goa_risk():
    """Load GOA risk parquet (skipped in CI — file absent)."""
    path = DATA_DERIVED / "risk" / "risk_goa.parquet"
    if not path.exists():
        pytest.skip(f"Data file not found (run mhw-compute-risk first): {path}")
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# Function-scoped: synthetic 2×3 grid for state engine unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny_state(cfg):
    """2×3 synthetic grid; returns (state, theta, mu, sst_above, sst_below, ice_clear, ice_heavy).

    theta=10.0, mu=8.0
    sst_above=11.5  (> theta, exceedance 1.5 °C)
    sst_below=9.0   (< theta, no exceedance)
    ice_clear=zeros (no ice)
    ice_heavy=ones  (100 % ice — above any ice_thresh)
    """
    from mhw.states.update_states import StateBuffer

    confirm_days = cfg["mhw_definition"]["confirm_days"]
    state = StateBuffer(n_lat=2, n_lon=3, confirm_days=confirm_days)

    theta     = np.full((2, 3), 10.0, dtype=np.float32)
    mu        = np.full((2, 3),  8.0, dtype=np.float32)
    sst_above = np.full((2, 3), 11.5, dtype=np.float32)
    sst_below = np.full((2, 3),  9.0, dtype=np.float32)
    ice_clear = np.zeros((2, 3), dtype=np.float32)
    ice_heavy = np.ones((2, 3),  dtype=np.float32)

    return state, theta, mu, sst_above, sst_below, ice_clear, ice_heavy


# ---------------------------------------------------------------------------
# FastAPI TestClient — reads on-disk parquet, no ERDDAP
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient backed by on-disk parquet files (skipped in CI — data absent)."""
    if not (DATA_DERIVED / "aggregates_region" / "region_daily_goa.parquet").exists():
        pytest.skip("Parquet data files not found — skipping API smoke tests")
    try:
        from fastapi.testclient import TestClient
        from api.main import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Could not import API app: {exc}")
    return TestClient(app)
