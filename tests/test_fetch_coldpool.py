"""Tests for the observed-product fetch helpers — pure (no network)."""
import pandas as pd
import pytest

from mhw.fetch.coldpool import aggregate_mean_temperature

# ESR subarea areas used for weighting (10⁹ m²): WGOA 606.578, EGOA 366.884.
_WW, _WE = 606.578, 366.884


def _wmean(a, b):  # area-weighted mean of (WGOA value a, EGOA value b)
    return (a * _WW + b * _WE) / (_WW + _WE)


def _long_goa() -> pd.DataFrame:
    """A tiny by-subarea GOA-style frame (already renamed via the column map)."""
    return pd.DataFrame({
        "year": [1993, 1993, 1996, 1996],
        # Categorical mirrors pyreadr reading R factors (a past bug: .map().sum() failed on it).
        "subarea": pd.Categorical(["Western Gulf of Alaska", "Eastern Gulf of Alaska",
                                   "Western Gulf of Alaska", "Eastern Gulf of Alaska"]),
        "mean_bottom_temp": [5.0, 7.0, 4.0, 6.0],
        "mean_surface_temp": [10.0, 12.0, 9.0, 11.0],
        "last_update": ["2025-08-26"] * 4,
    })


def test_aggregate_collapses_subareas_to_one_row_per_year():
    out = aggregate_mean_temperature(_long_goa())
    assert list(out["year"]) == [1993, 1996]          # one row per year, sorted
    # region-wide value is the ESR-area-weighted cross-subarea mean
    assert out.loc[out["year"] == 1993, "mean_bottom_temp"].iloc[0] == pytest.approx(_wmean(5.0, 7.0), abs=1e-4)
    assert out.loc[out["year"] == 1996, "mean_bottom_temp"].iloc[0] == pytest.approx(_wmean(4.0, 6.0), abs=1e-4)


def test_aggregate_keeps_per_subarea_columns():
    out = aggregate_mean_temperature(_long_goa())
    # subarea slug columns are kept for the breakdown overlay
    assert out.loc[out["year"] == 1993, "mean_bottom_temp_western"].iloc[0] == 5.0
    assert out.loc[out["year"] == 1993, "mean_bottom_temp_eastern"].iloc[0] == 7.0
    # surface temp is also collapsed (area-weighted); last_update carried through
    assert out.loc[out["year"] == 1993, "mean_surface_temp"].iloc[0] == pytest.approx(_wmean(10.0, 12.0), abs=1e-4)
    assert "last_update" in out.columns
