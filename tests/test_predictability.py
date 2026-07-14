"""Tests for the Climate Drivers cross-correlation helpers — pure, no network.

Exercises the driver-leads lagged cross-correlation and its supporting monthly-mean /
deseasonalize transforms on small in-memory frames with a known injected lag.
"""
import numpy as np
import pandas as pd

from dashboard.components.predictability_panel import (
    best_lag_table,
    deseasonalize,
    lagged_cross_correlation,
    monthly_onset_counts,
    to_monthly_mean,
)


def _months(n: int, start: str = "2000-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="MS")


def test_lagged_cross_correlation_recovers_injected_lead():
    # Target is the driver shifted 3 months LATER, i.e. the driver leads the target by 3.
    n = 60
    dates = _months(n)
    rng = np.random.default_rng(0)
    driver = rng.normal(size=n)
    lead = 3
    target = np.full(n, np.nan)
    target[lead:] = driver[:-lead]                    # target[t] = driver[t-3]

    drivers = pd.DataFrame({"date": dates, "x": driver})
    targets = pd.DataFrame({"date": dates, "y": target})

    grid = lagged_cross_correlation(drivers, targets, max_lag=6)
    best = best_lag_table(grid)

    row = best[(best["driver"] == "x") & (best["target"] == "y")].iloc[0]
    assert int(row["lag"]) == lead          # strongest correlation is at the true lead
    assert row["r"] > 0.99                  # and it is a near-perfect correlation


def test_lag_zero_when_contemporaneous():
    n = 48
    dates = _months(n)
    rng = np.random.default_rng(1)
    x = rng.normal(size=n)
    drivers = pd.DataFrame({"date": dates, "x": x})
    targets = pd.DataFrame({"date": dates, "y": x * 2.0})   # same-month linear relation

    best = best_lag_table(lagged_cross_correlation(drivers, targets, max_lag=6))
    assert int(best.iloc[0]["lag"]) == 0
    assert best.iloc[0]["r"] > 0.99


def test_short_overlap_yields_nan_r():
    # Only 5 overlapping months but min_overlap defaults to 12 → r is NaN, not a spurious 1.0.
    dates = _months(5)
    drivers = pd.DataFrame({"date": dates, "x": np.arange(5.0)})
    targets = pd.DataFrame({"date": dates, "y": np.arange(5.0)})
    grid = lagged_cross_correlation(drivers, targets, max_lag=2)
    assert grid["r"].isna().all()
    assert best_lag_table(grid).empty


def test_to_monthly_mean_collapses_daily():
    daily = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=60, freq="D"),   # Jan 31 + Feb 29 (leap)
        "v": np.r_[np.zeros(31), np.ones(29)],          # Jan=0, Feb=1
    })
    out = to_monthly_mean(daily, "v")
    assert list(out["date"]) == list(pd.to_datetime(["2020-01-01", "2020-02-01"]))
    assert out["v"].tolist() == [0.0, 1.0]


def test_monthly_onset_counts_counts_rising_edges():
    # Daily area fraction: one event in Jan (rising edge on Jan 5), a separate event
    # spanning into Feb (rising edge on Jan 20). Feb has no *new* onset — the event
    # merely continues — so Feb's onset count is 0.
    dates = pd.date_range("2020-01-01", "2020-02-29", freq="D")
    area = np.zeros(len(dates))
    idx = {d.strftime("%Y-%m-%d"): i for i, d in enumerate(dates)}
    area[idx["2020-01-05"]:idx["2020-01-08"]] = 0.5          # event 1 (onset Jan 5)
    area[idx["2020-01-20"]:idx["2020-02-10"]] = 0.5          # event 2 (onset Jan 20, runs into Feb)
    df = pd.DataFrame({"date": dates, "area_frac": area})

    out = monthly_onset_counts(df, threshold=0.1)
    assert list(out["date"]) == list(pd.to_datetime(["2020-01-01", "2020-02-01"]))
    assert out["Onset events"].tolist() == [2, 0]


def test_monthly_onset_counts_empty_frame():
    empty = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "area_frac": pd.Series(dtype=float)})
    out = monthly_onset_counts(empty)
    assert out.empty
    assert list(out.columns) == ["date", "Onset events"]


def test_deseasonalize_removes_month_climatology():
    # Two years with a pure seasonal cycle (value == month number) → anomalies all zero.
    dates = _months(24)
    df = pd.DataFrame({"date": dates, "v": np.tile(np.arange(1, 13, dtype=float), 2)})
    out = deseasonalize(df, "v")
    assert np.allclose(out["v"].to_numpy(), 0.0)
