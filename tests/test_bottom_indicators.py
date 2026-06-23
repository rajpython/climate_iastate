"""Tests for manager-facing bottom-state indicators — pure functions (no network)."""
import numpy as np

from mhw.bottom.indicators import (
    analog_years,
    anomaly,
    category_color,
    ordinal_rank,
    percentile_rank,
    risk_category,
)


# --- percentile_rank ----------------------------------------------------------------------
def test_percentile_rank_extremes_and_middle():
    series = [10, 20, 30, 40, 50]
    assert percentile_rank(10, series) == 10.0   # smallest → 10th pct (kind="mean")
    assert percentile_rank(30, series) == 50.0    # median → 50th
    assert percentile_rank(50, series) == 90.0    # largest → 90th


def test_percentile_rank_handles_nan_and_empty():
    assert np.isnan(percentile_rank(float("nan"), [1, 2, 3]))
    assert np.isnan(percentile_rank(5, [np.nan, np.nan]))


# --- ordinal_rank -------------------------------------------------------------------------
def test_ordinal_rank_smallest_and_largest():
    series = [100, 200, 300, 400, 500]
    assert ordinal_rank(100, series, smallest=True) == 1     # smallest
    assert ordinal_rank(300, series, smallest=True) == 3
    assert ordinal_rank(500, series, smallest=False) == 1    # largest
    assert ordinal_rank(100, series, smallest=False) == 5


def test_ordinal_rank_value_not_in_series():
    # A new low value ranks 1st-smallest against the population.
    assert ordinal_rank(50, [100, 200, 300], smallest=True) == 1


# --- risk_category ------------------------------------------------------------------------
def test_risk_category_cold_pool_low_is_concern():
    # Default concern_when_low=True: small cold pool (low pct) is the concern.
    assert risk_category(5) == "High concern"
    assert risk_category(15) == "Elevated concern"
    assert risk_category(50) == "Typical"
    assert risk_category(85) == "Favorable"


def test_risk_category_boundaries():
    assert risk_category(9.99) == "High concern"
    assert risk_category(10) == "Elevated concern"
    assert risk_category(19.99) == "Elevated concern"
    assert risk_category(20) == "Typical"
    assert risk_category(80) == "Favorable"


def test_risk_category_concern_when_high_flips():
    # Warm anomaly: a high percentile is the concern.
    assert risk_category(95, concern_when_low=False) == "High concern"
    assert risk_category(50, concern_when_low=False) == "Typical"
    assert risk_category(5, concern_when_low=False) == "Favorable"


def test_category_color_mapping():
    assert category_color("High concern") == "red"
    assert category_color("Favorable") == "green"
    assert category_color("nonsense") == "gray"


# --- anomaly ------------------------------------------------------------------------------
def test_anomaly_sign_and_value():
    baseline = [2.0, 2.0, 2.0, 2.0]   # mean 2.0
    assert anomaly(3.5, baseline) == 1.5
    assert anomaly(1.0, baseline) == -1.0


def test_anomaly_handles_nan():
    assert np.isnan(anomaly(float("nan"), [1, 2, 3]))
    assert np.isnan(anomaly(1.0, [np.nan]))


# --- analog_years -------------------------------------------------------------------------
def test_analog_years_orders_by_similarity():
    years = [2010, 2011, 2012, 2013]
    area = [100, 105, 300, 95]          # 2013 closest to 2010, 2011 next, 2012 far
    mean_bt = [2.0, 2.1, 4.0, 1.9]
    out = analog_years(2010, years, area, mean_bt, k=2)
    assert out == [2013, 2011]
    assert 2010 not in out               # target excluded


def test_analog_years_skips_nonfinite_and_missing_target():
    years = [2010, 2011, 2012]
    area = [100, np.nan, 110]
    mean_bt = [2.0, 2.0, 2.1]
    # 2011 has a NaN component → skipped; only 2012 remains as an analog of 2010.
    assert analog_years(2010, years, area, mean_bt, k=3) == [2012]
    # Unknown target year → empty.
    assert analog_years(1999, years, area, mean_bt) == []
