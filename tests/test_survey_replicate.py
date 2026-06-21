"""Tests for survey-replicated skill metrics — pure functions (no network)."""
import numpy as np
import pandas as pd

from mhw.bottom.survey_replicate import annual_means, haul_skill


def _df():
    # 2 years, simple values; model = obs + known offset to check bias.
    return pd.DataFrame({
        "year": [2000, 2000, 2001, 2001],
        "stationid": ["A", "B", "A", "B"],
        "obs_bottom_temp": [1.0, 3.0, 2.0, 4.0],
        "model_bottom_temp": [1.5, 3.5, 2.5, 4.5],  # uniform +0.5 bias
    })


def test_haul_skill_bias_rmse_corr():
    s = haul_skill(_df())
    assert s["n_hauls"] == 4
    assert s["bias_c"] == 0.5           # uniform +0.5 offset
    assert s["rmse_c"] == 0.5           # constant error -> RMSE == |bias|
    assert s["corr"] == 1.0             # perfectly correlated (offset only)
    assert s["year_min"] == 2000 and s["year_max"] == 2001


def test_annual_means_per_year():
    a = annual_means(_df()).set_index("year")
    assert a.loc[2000, "n_hauls"] == 2
    assert a.loc[2000, "obs_mean_bottom_temp"] == 2.0      # (1+3)/2
    assert a.loc[2000, "model_mean_bottom_temp"] == 2.5    # (1.5+3.5)/2
    assert a.loc[2000, "bias_c"] == 0.5


def test_haul_skill_handles_scatter():
    df = pd.DataFrame({
        "year": [2000, 2000],
        "stationid": ["A", "B"],
        "obs_bottom_temp": [0.0, 2.0],
        "model_bottom_temp": [1.0, 1.0],  # mean matches (bias 0) but scatter present
    })
    s = haul_skill(df)
    assert s["bias_c"] == 0.0
    assert s["rmse_c"] == 1.0  # sqrt(((1)^2+(1)^2)/2)
