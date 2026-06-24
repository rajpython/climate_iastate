"""Tests for cold-pool position metrics — pure functions (no network)."""
import numpy as np
import pytest

from mhw.bottom.position import cold_pool_position, southern_extent_points


# A 5-row grid (lats 54..58) x 3 cols, all shelf. Rows 0–1 (lats 54,55) are cold (≤2 °C);
# rows 2–4 (56,57,58) are warm. So the ≤2 °C cells span latitudes {54, 55}.
LATS = np.array([54.0, 55.0, 56.0, 57.0, 58.0])
LONS = np.array([-170.0, -169.0, -168.0])
SHELF = np.ones((5, 3), dtype=bool)
GRID = np.array([
    [1.0, 1.0, 1.0],   # 54 N — cold
    [1.5, 1.5, 1.5],   # 55 N — cold
    [3.0, 3.0, 3.0],   # 56 N — warm
    [4.0, 4.0, 4.0],   # 57 N — warm
    [5.0, 5.0, 5.0],   # 58 N — warm
])


def test_p05_latitude_default_is_southern_reach():
    # Selected latitudes are six cells at 54 and six at 55 → 5th percentile sits at the south end.
    lat = cold_pool_position(GRID, SHELF, LATS, LONS, threshold=2.0)
    assert 54.0 <= lat <= 54.2   # near the southernmost cold latitude, but percentile-robust


def test_minimum_latitude_is_absolute_south():
    lat = cold_pool_position(GRID, SHELF, LATS, LONS, threshold=2.0, method="minimum_latitude")
    assert lat == 54.0


def test_centroid_is_mean_of_cold_latitudes():
    lat = cold_pool_position(GRID, SHELF, LATS, LONS, threshold=2.0, method="centroid")
    assert lat == pytest.approx(54.5)   # mean of {54,54,54,55,55,55}


def test_nan_when_no_cold_cells():
    warm = np.full((5, 3), 5.0)
    assert np.isnan(cold_pool_position(warm, SHELF, LATS, LONS, threshold=2.0))


def test_shelf_mask_excludes_offshelf_cold_cells():
    # Make the warm rows cold but off-shelf — they must not pull the extent north or south.
    grid = GRID.copy()
    grid[4, :] = 0.0           # 58 N now cold...
    shelf = SHELF.copy()
    shelf[4, :] = False        # ...but off-shelf, so ignored
    lat = cold_pool_position(grid, shelf, LATS, LONS, threshold=2.0, method="minimum_latitude")
    assert lat == 54.0


def test_robustness_to_single_stray_cell():
    # One stray cold cell far north should move minimum_latitude but barely move p05.
    grid = GRID.copy()
    grid[4, 0] = 1.0           # a lone cold cell at 58 N
    p05 = cold_pool_position(grid, SHELF, LATS, LONS, threshold=2.0, method="p05_latitude")
    mn = cold_pool_position(grid, SHELF, LATS, LONS, threshold=2.0, method="minimum_latitude")
    assert mn == 54.0
    assert p05 <= 55.0         # p05 stays at the southern cluster, ignoring the stray northern cell


def test_unknown_method_raises():
    with pytest.raises(ValueError):
        cold_pool_position(GRID, SHELF, LATS, LONS, method="nope")


def test_documented_stub_raises():
    with pytest.raises(NotImplementedError):
        cold_pool_position(GRID, SHELF, LATS, LONS, method="contour_edge")


# --- southern_extent_points (observed, from survey hauls) ---------------------------------
def test_southern_extent_points_basic():
    # hauls: three cold at 55/56/57, two warm at 58/59 → p05 sits near the southernmost cold haul.
    lats = np.array([55.0, 56.0, 57.0, 58.0, 59.0])
    temps = np.array([1.0, 1.5, 1.8, 3.0, 4.0])
    lat = southern_extent_points(lats, temps, threshold=2.0)
    assert 55.0 <= lat <= 55.3


def test_southern_extent_points_nan_when_no_cold_hauls():
    assert np.isnan(southern_extent_points(np.array([55.0, 56.0]), np.array([3.0, 4.0]), 2.0))


def test_southern_extent_points_ignores_nan_temps():
    lats = np.array([55.0, 56.0, 57.0])
    temps = np.array([np.nan, 1.0, 1.0])
    lat = southern_extent_points(lats, temps, threshold=2.0)
    assert 56.0 <= lat <= 56.1   # the NaN-temp haul at 55 is excluded
