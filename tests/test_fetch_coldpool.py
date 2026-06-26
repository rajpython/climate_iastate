"""Tests for the observed-product fetch helpers — pure (no network)."""
import pandas as pd

from mhw.fetch.coldpool import aggregate_mean_temperature


def _long_goa() -> pd.DataFrame:
    """A tiny by-subarea GOA-style frame (already renamed via the column map)."""
    return pd.DataFrame({
        "year": [1993, 1993, 1996, 1996],
        "subarea": ["Western Gulf of Alaska", "Eastern Gulf of Alaska",
                    "Western Gulf of Alaska", "Eastern Gulf of Alaska"],
        "mean_bottom_temp": [5.0, 7.0, 4.0, 6.0],
        "mean_surface_temp": [10.0, 12.0, 9.0, 11.0],
        "last_update": ["2025-08-26"] * 4,
    })


def test_aggregate_collapses_subareas_to_one_row_per_year():
    out = aggregate_mean_temperature(_long_goa())
    assert list(out["year"]) == [1993, 1996]          # one row per year, sorted
    # region-wide value is the cross-subarea mean (no area weights in the product)
    assert out.loc[out["year"] == 1993, "mean_bottom_temp"].iloc[0] == 6.0
    assert out.loc[out["year"] == 1996, "mean_bottom_temp"].iloc[0] == 5.0


def test_aggregate_keeps_per_subarea_columns():
    out = aggregate_mean_temperature(_long_goa())
    # subarea slug columns are kept for the breakdown overlay
    assert out.loc[out["year"] == 1993, "mean_bottom_temp_western"].iloc[0] == 5.0
    assert out.loc[out["year"] == 1993, "mean_bottom_temp_eastern"].iloc[0] == 7.0
    # surface temp is also collapsed; last_update carried through
    assert out.loc[out["year"] == 1993, "mean_surface_temp"].iloc[0] == 11.0
    assert "last_update" in out.columns
