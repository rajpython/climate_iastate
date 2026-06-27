"""Tests for the bathymetry depth-binning helper — pure, network-free."""
import numpy as np

from mhw.bottom.bathymetry import bin_depth_to_grid


def test_bin_depth_to_grid_means_per_cell():
    # 2x2 analysis grid; cells span [coord, coord+0.25). lon on 0–360.
    lats = np.array([54.0, 54.25])
    lon360 = np.array([190.0, 190.25])
    pt_lat = np.array([54.10, 54.20, 54.30, 54.10])
    pt_lon = np.array([190.10, 190.10, 190.30, 190.30])
    pt_dep = np.array([50.0, 70.0, 100.0, 30.0])
    grid = bin_depth_to_grid(pt_lat, pt_lon, pt_dep, lats, lon360, res=0.25)
    assert grid.shape == (2, 2)
    assert grid[0, 0] == 60.0        # mean of 50 & 70 in cell (54.0, 190.0)
    assert grid[0, 1] == 30.0        # single point in cell (54.0, 190.25)
    assert grid[1, 1] == 100.0       # single point in cell (54.25, 190.25)
    assert np.isnan(grid[1, 0])      # no points in cell (54.25, 190.0)


def test_bin_depth_to_grid_empty_is_nan():
    lats = np.array([60.0])
    lon360 = np.array([200.0])
    grid = bin_depth_to_grid(np.array([]), np.array([]), np.array([]), lats, lon360)
    assert grid.shape == (1, 1)
    assert np.isnan(grid[0, 0])
