"""Tests for the Arctic depth-profile helper — pure, network-free."""
import numpy as np

from mhw.bottom.arctic_profile import depth_profile_table


def test_depth_profile_table_area_weighted_bins():
    # 1x4 grid, one cell per bin (depths 5/25/60/150 m), equal area; one bin (10-20, 30-50) empty.
    depth = np.array([[5.0, 25.0, 60.0, 150.0]])
    area = np.array([[1.0, 1.0, 1.0, 1.0]])
    bt = np.array([[8.0, 4.0, 0.0, -1.0]])
    t = depth_profile_table(depth, area, bt).set_index("depth_bin")
    assert t.loc["0–10 m", "mean_bottom_temp"] == 8.0
    assert t.loc["0–10 m", "area_pct"] == 25.0      # 1 of 4 equal-area shelf cells
    assert t.loc["0–10 m", "n_cells"] == 1
    assert np.isnan(t.loc["10–20 m", "mean_bottom_temp"])   # empty bin
    assert t.loc["10–20 m", "area_pct"] == 0.0
    assert t.loc["100–200 m", "mean_bottom_temp"] == -1.0


def test_depth_profile_table_excludes_deep_and_nan():
    # >200 m and NaN-temp cells are off-shelf and must not enter the area total.
    depth = np.array([[5.0, 300.0, 40.0]])
    area = np.array([[1.0, 1.0, 1.0]])
    bt = np.array([[6.0, 5.0, np.nan]])
    t = depth_profile_table(depth, area, bt).set_index("depth_bin")
    assert t.loc["0–10 m", "area_pct"] == 100.0     # only the one valid ≤200 m cell counts
    assert t.loc["0–10 m", "mean_bottom_temp"] == 6.0
