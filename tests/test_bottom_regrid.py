"""Offline tests for the source-agnostic bottom-state regrid (no network)."""
from __future__ import annotations

import numpy as np

from mhw.bottom.regrid import (
    alaska_target_grid,
    normalize_lon,
    oisst_grid,
    regrid_curvilinear_to_regular,
)


def test_normalize_lon_wraps_dateline():
    # 215.1°E -> -144.9; 156.4 stays; -144.9 stays.
    out = normalize_lon(np.array([215.1, 156.4, -144.9, 360.0]))
    np.testing.assert_allclose(out, [-144.9, 156.4, -144.9, 0.0], atol=1e-9)
    assert np.all((out >= -180.0) & (out < 180.0))


def test_oisst_grid_shape():
    lats, lons = oisst_grid()
    assert lats.size == 720 and lons.size == 1440
    assert np.isclose(lats[0], -89.875) and np.isclose(lons[0], -179.875)


def test_alaska_target_grid_within_bounds():
    lats, lons = alaska_target_grid((46.0, 78.0), (-205.0, -155.0))
    assert lats.min() >= 46.0 and lats.max() <= 78.0
    assert lons.max() <= -155.0
    # spacing preserved at 0.25
    assert np.allclose(np.diff(lats), 0.25)


def test_block_average_means_sources_in_cell():
    # Target: two cells centred at lon 0.0 and 0.25, lat 0.0.
    tgt_lats = np.array([0.0])
    tgt_lons = np.array([0.0, 0.25])
    # Two source points in cell0 (values 2 and 4 -> mean 3), one in cell1 (10).
    src_lat = np.array([0.01, -0.01, 0.0])
    src_lon = np.array([-0.05, 0.05, 0.24])
    field = np.array([2.0, 4.0, 10.0])
    out = regrid_curvilinear_to_regular(
        src_lat, src_lon, field, tgt_lats, tgt_lons, fill_nearest=False
    )
    np.testing.assert_allclose(out, [[3.0, 10.0]])


def test_nans_ignored_and_empty_cell_is_nan():
    tgt_lats = np.array([0.0])
    tgt_lons = np.array([0.0, 0.25])
    src_lat = np.array([0.0, 0.0])
    src_lon = np.array([0.0, 0.0])      # both in cell0; none in cell1
    field = np.array([5.0, np.nan])     # NaN ignored -> cell0 mean = 5
    out = regrid_curvilinear_to_regular(
        src_lat, src_lon, field, tgt_lats, tgt_lons, fill_nearest=False
    )
    assert np.isclose(out[0, 0], 5.0)
    assert np.isnan(out[0, 1])


def test_nearest_fill_within_distance():
    tgt_lats = np.array([0.0])
    tgt_lons = np.array([0.0, 0.25])
    src_lat = np.array([0.0])
    src_lon = np.array([0.0])           # only cell0 has data
    field = np.array([7.0])
    # cell1 centre is 0.25° away -> within default 0.30° fill radius.
    out = regrid_curvilinear_to_regular(
        src_lat, src_lon, field, tgt_lats, tgt_lons,
        fill_nearest=True, fill_max_deg=0.30,
    )
    assert np.isclose(out[0, 1], 7.0)
    # but not when the radius is too small.
    out2 = regrid_curvilinear_to_regular(
        src_lat, src_lon, field, tgt_lats, tgt_lons,
        fill_nearest=True, fill_max_deg=0.10,
    )
    assert np.isnan(out2[0, 1])
