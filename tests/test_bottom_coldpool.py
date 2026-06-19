"""Tests for the modelled cold-pool derivation — pure helpers (no network)."""
import numpy as np

from mhw.bottom.coldpool import (
    cell_area_km2,
    coldpool_area_km2,
    mean_shelf_bottom_temp,
)


def test_cell_area_shrinks_with_latitude():
    lats = np.array([50.0, 60.0, 70.0])
    lons = np.array([-179.0, -178.0])
    areas = cell_area_km2(lats, lons)
    assert areas.shape == (3, 2)
    # cos-lat weighting: higher latitude -> smaller cell.
    assert areas[0, 0] > areas[1, 0] > areas[2, 0]
    # constant across longitude within a row.
    assert np.allclose(areas[:, 0], areas[:, 1])


def test_coldpool_area_respects_shelf_and_threshold():
    # 2x2 grid; one deep (off-shelf) cell is cold but must be excluded.
    temp = np.array([[1.0, 3.0], [-0.5, 1.5]])
    shelf = np.array([[True, True], [False, True]])  # bottom-left is deep basin
    areas = np.array([[100.0, 100.0], [100.0, 100.0]])
    # ≤2 °C on shelf: (0,0)=1.0 yes, (0,1)=3.0 no, (1,0) excluded, (1,1)=1.5 yes -> 200
    assert coldpool_area_km2(temp, shelf, areas, 2.0) == 200.0
    # ≤0 °C on shelf: only the excluded deep cell qualifies -> 0
    assert coldpool_area_km2(temp, shelf, areas, 0.0) == 0.0


def test_coldpool_area_ignores_nan():
    temp = np.array([[np.nan, 1.0]])
    shelf = np.array([[True, True]])
    areas = np.array([[100.0, 100.0]])
    assert coldpool_area_km2(temp, shelf, areas, 2.0) == 100.0


def test_mean_shelf_bottom_temp_area_weighted():
    temp = np.array([[0.0, 4.0]])
    shelf = np.array([[True, True]])
    areas = np.array([[300.0, 100.0]])  # weight the cold cell 3x
    # (0*300 + 4*100) / 400 = 1.0
    assert mean_shelf_bottom_temp(temp, shelf, areas) == 1.0


def test_mean_shelf_bottom_temp_empty_is_nan():
    temp = np.array([[1.0]])
    shelf = np.array([[False]])
    areas = np.array([[100.0]])
    assert np.isnan(mean_shelf_bottom_temp(temp, shelf, areas))
