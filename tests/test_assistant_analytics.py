"""Analytics tests — aggregate, join, correlation/regression, rank, summary (tmp data)."""
from __future__ import annotations

import pandas as pd

from mhw.assistant import analytics


def _two_datasets(tmp):
    """landings_t = i (annual) and mhw_daily area_frac = 2*i (annual mean), years 2000–2010."""
    yrs = list(range(2000, 2011))
    r = tmp / "raw"
    r.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "year": yrs, "species": ["CRAB, SNOW"] * len(yrs), "area_group": ["statewide"] * len(yrs),
        "landings_t": [float(i) for i in range(len(yrs))],
        "value_usd": [float(i * 10) for i in range(len(yrs))],
    }).to_parquet(r / "landings_foss_ak.parquet")
    a = tmp / "derived" / "aggregates_region"
    a.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"date": pd.Timestamp(y, 7, 1), "area_frac": 2.0 * i,
         "Ibar": 0.0, "Dbar": 0.0, "Cbar": 0.0, "Obar": 0.0}
        for i, y in enumerate(yrs)
    ]).to_parquet(a / "region_daily_sebs.parquet")
    return tmp


def test_aggregate_by_year(tmp_path):
    _two_datasets(tmp_path)
    a = analytics.aggregate("landings", "year", "landings_t", "sum", data_root=tmp_path)
    assert a["n"] == 11


def test_correlate_recovers_known_r_and_slope(tmp_path):
    _two_datasets(tmp_path)
    c = analytics.correlate("mhw_daily", "area_frac", "landings", "landings_t",
                            on=["year"], data_root=tmp_path)
    assert c["n"] == 11
    assert abs(c["pearson_r"] - 1.0) < 1e-6        # 2i vs i → perfectly correlated
    assert abs(c["slope"] - 0.5) < 1e-6            # landings_t = 0.5 * area_frac
    assert c["fit_line"]["x"] and c["fit_line"]["y"]


def test_correlate_too_few_points(tmp_path):
    r = tmp_path / "raw"
    r.mkdir(parents=True)
    pd.DataFrame({"year": [2000], "species": ["X"], "area_group": ["s"],
                  "landings_t": [1.0], "value_usd": [1.0]}).to_parquet(r / "landings_foss_ak.parquet")
    c = analytics.correlate("landings", "landings_t", "landings", "value_usd",
                            on=["year"], data_root=tmp_path)
    assert "error" in c


def test_join_series(tmp_path):
    _two_datasets(tmp_path)
    j = analytics.join_series("mhw_daily", "area_frac", "landings", "landings_t",
                              on=["year"], data_root=tmp_path)
    assert j["n"] == 11
    assert set(j["records"][0]) == {"year", "a", "b"}


def test_rank_top_n(tmp_path):
    _two_datasets(tmp_path)
    r = analytics.rank("landings", "landings_t", "year", top_n=3, agg="sum", data_root=tmp_path)
    assert len(r["records"]) == 3


def test_summary_stats_trend(tmp_path):
    _two_datasets(tmp_path)
    s = analytics.summary_stats("mhw_daily", "area_frac", data_root=tmp_path)
    assert s["n"] == 11
    assert s["trend_per_year"] > 0


def test_aggregate_empty_is_explicit(tmp_path):
    _two_datasets(tmp_path)
    a = analytics.aggregate("landings", "year", "landings_t", "sum",
                            filters={"species": "nonexistent"}, data_root=tmp_path)
    assert a["records"] == []
    assert "do NOT chart" in a["note"]
