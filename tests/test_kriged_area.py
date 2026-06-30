"""Tests for the kriged cold-pool AREA pipeline — pure helpers (no network).

The grid/count helpers (make_grid, snap_extent, area_le) are pure NumPy and always run. The
kriging tests need PyKrige (the optional ``[geo]`` extra, which CI deliberately doesn't build),
so they ``skipif`` it's absent. The end-to-end "reproduce AFSC" check is a skip-if-data-missing
integration test (no network: it only runs when the survey-replicate parquet and the trimmed
survey-area geojson are already on disk).
"""
import importlib.util

import numpy as np
import pandas as pd
import pytest

from mhw.bottom.kriged_area import (
    CELL_RES_M,
    KM2_PER_CELL,
    area_le,
    krige_to_grid,
    make_grid,
    snap_extent,
)

# PyKrige lives in the optional [geo] extra; CI installs only [api,dashboard,dev].
needs_pykrige = pytest.mark.skipif(
    importlib.util.find_spec("pykrige") is None, reason="pykrige ([geo] extra) not installed")


# --- make_grid ---------------------------------------------------------------------------
def test_make_grid_dims_and_centres():
    # AFSC SEBS extent → 318×318, first centre offset half a cell in from the corner.
    xc, yc = make_grid((-1625000.0, -35000.0, 379500.0, 1969500.0))
    assert xc.size == 318 and yc.size == 318
    assert xc[0] == pytest.approx(-1625000.0 + CELL_RES_M / 2)   # -1622500
    assert yc[0] == pytest.approx(379500.0 + CELL_RES_M / 2)     # 382000
    assert np.allclose(np.diff(xc), CELL_RES_M)


def test_make_grid_small_known():
    xc, yc = make_grid((0.0, 20000.0, 0.0, 10000.0), res=5000.0)
    assert list(xc) == [2500.0, 7500.0, 12500.0, 17500.0]
    assert list(yc) == [2500.0, 7500.0]


# --- snap_extent -------------------------------------------------------------------------
def test_snap_extent_rounds_outward_to_grid():
    # bounds (minx,miny,maxx,maxy) snap outward to clean multiples of res. Returned as
    # (xmin, xmax, ymin, ymax): mins floor down, maxs ceil up.
    assert snap_extent((1234.0, 2345.0, 6789.0, 9999.0), res=5000.0) == (0.0, 10000.0, 0.0, 10000.0)


def test_snap_extent_pad_adds_cells():
    # one cell of padding on every side.
    assert snap_extent((0.0, 0.0, 5000.0, 5000.0), res=5000.0, pad=1) == (-5000.0, 10000.0, -5000.0, 10000.0)


# --- area_le -----------------------------------------------------------------------------
def test_area_le_counts_only_in_mask_below_threshold():
    field = np.array([[1.0, 3.0], [2.0, np.nan]])
    inside = np.array([[True, True], [True, False]])
    # in-mask cells ≤ 2 °C: 1.0 and 2.0 → 2 cells.
    assert area_le(field, inside, 2.0) == 2 * KM2_PER_CELL
    assert area_le(field, inside, 0.0) == 0.0
    assert area_le(field, inside, 5.0) == 3 * KM2_PER_CELL  # the NaN cell never counts


def test_area_le_ignores_out_of_mask_cold_cells():
    field = np.full((2, 2), -1.0)
    inside = np.array([[True, False], [False, False]])
    assert area_le(field, inside, 0.0) == 1 * KM2_PER_CELL


# --- krige_to_grid -----------------------------------------------------------------------
@needs_pykrige
def test_krige_near_constant_field():
    # Kriging a near-constant signal (~5 °C) returns ~5 everywhere, so the area below 4 is
    # empty and the area below 6 is the whole grid. (A *perfectly* constant field is a
    # degenerate variogram and not a real case.)
    rng = np.random.default_rng(0)
    px = rng.uniform(0, 20000, 40)
    py = rng.uniform(0, 20000, 40)
    z = 5.0 + rng.normal(0, 0.05, 40)
    xc, yc = make_grid((0.0, 20000.0, 0.0, 20000.0))
    field = krige_to_grid(px, py, z, xc, yc)
    assert np.allclose(field, 5.0, atol=0.5)
    inside = np.ones_like(field, dtype=bool)
    assert area_le(field, inside, 4.0) == 0.0
    assert area_le(field, inside, 6.0) == field.size * KM2_PER_CELL


@needs_pykrige
def test_krige_recovers_monotonic_gradient_sign():
    # A west→east warming ramp: the kriged field's west half should be colder than the east.
    xs = np.linspace(0, 100000, 60)
    px = xs.copy()
    py = np.full_like(xs, 50000.0)
    z = xs / 10000.0  # 0 → 10 °C
    xc, yc = make_grid((0.0, 100000.0, 40000.0, 60000.0))
    field = krige_to_grid(px, py, z, xc, yc)
    west = field[:, : field.shape[1] // 2]
    east = field[:, field.shape[1] // 2:]
    assert np.nanmean(west) < np.nanmean(east)


# --- integration: reproduce AFSC (skips unless data already present, no network) ----------
@needs_pykrige
def test_observed_kriged_area_reproduces_afsc_ebs():
    from pathlib import Path

    from mhw.bottom.kriged_area import (
        _SURVEY_AREA_GEOJSON,
        _replicate_path,
        build_kriged_area_series,
    )
    from mhw.bottom.regions import EBS
    from mhw.bottom.sources import BERING10K_K20_CORECFS

    repl = _replicate_path(BERING10K_K20_CORECFS, EBS)
    pub_path = Path("data/raw/coldpool_index_observed_sebs.parquet")
    if not (repl.exists() and _SURVEY_AREA_GEOJSON.exists() and pub_path.exists()):
        pytest.skip("survey-replicate / survey-area / observed index not generated")

    mine = build_kriged_area_series(BERING10K_K20_CORECFS, region=EBS, observed=True)
    mine = mine.set_index("year")["area_lte2_km2"]
    pub = pd.read_parquet(pub_path).set_index("year")["area_lte2_km2"]
    j = pd.DataFrame({"mine": mine, "pub": pub}).dropna()
    pct = (100 * (j["mine"] - j["pub"]) / j["pub"]).abs()
    # The production pipeline must reproduce AFSC's published index closely.
    assert pct.mean() < 2.0
    assert np.corrcoef(j["mine"], j["pub"])[0, 1] > 0.999
