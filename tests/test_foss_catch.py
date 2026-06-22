"""Tests for the FOSS catch × bottom-state adapter — pure join/summary (no network)."""
import numpy as np
import pandas as pd

from mhw.fetch.foss_catch import join_catch_to_hauls, cold_pool_summary


def _hauls():
    # 4 hauls, one region/year; two cold (≤2 °C), two warm.
    return pd.DataFrame({
        "year": [2023, 2023, 2023, 2023],
        "region": ["EBS"] * 4,
        "hauljoin": [1, 2, 3, 4],
        "latitude": [57.0, 58.0, 59.0, 60.0],
        "longitude": [-163.0, -164.0, -165.0, -166.0],
        "depth_m": [60, 70, 80, 90],
        "bottom_temperature_c": [1.0, 1.5, 4.0, 5.0],  # hauls 1,2 in cold pool
    })


def _catch():
    # Species caught only in the two cold hauls (1, 2). Hauls 3,4 = absence.
    return pd.DataFrame({
        "hauljoin": [1, 2],
        "species_code": [68580, 68580],
        "cpue_kgkm2": [400.0, 300.0],
        "cpue_nokm2": [4000.0, 3000.0],
    })


def test_join_zero_fills_absences():
    df = join_catch_to_hauls(_hauls(), _catch(), 68580, "snow crab")
    # every haul survives the left join — absences are kept, not dropped
    assert len(df) == 4
    assert set(df["hauljoin"]) == {1, 2, 3, 4}
    # warm hauls (3, 4) get CPUE 0, not NaN
    warm = df[df["hauljoin"].isin([3, 4])]
    assert (warm["cpue_kgkm2"] == 0.0).all()
    assert (warm["cpue_nokm2"] == 0.0).all()
    assert (df["species_code"] == 68580).all()
    assert (df["common_name"] == "snow crab").all()


def test_join_missing_species_all_zero():
    empty = pd.DataFrame(columns=["hauljoin", "cpue_kgkm2", "cpue_nokm2"])
    df = join_catch_to_hauls(_hauls(), empty, 99999, "nothing")
    assert len(df) == 4
    assert (df["cpue_kgkm2"] == 0.0).all()


def test_cold_pool_summary_shares():
    df = join_catch_to_hauls(_hauls(), _catch(), 68580, "snow crab")
    s = cold_pool_summary(df, threshold=2.0).iloc[0]
    assert s["n_hauls"] == 4
    assert s["frac_hauls_in_band"] == 0.5            # 2 of 4 hauls ≤2 °C
    # all 700 kg/km² of biomass is inside the cold pool
    assert s["frac_biomass_in_band"] == 1.0
    assert s["mean_cpue_in_band"] == 350.0           # (400+300)/2
    assert s["mean_cpue_out_band"] == 0.0
    # colder hauls hold more crab -> negative BT/CPUE correlation
    assert s["corr_bt_cpue"] < 0


def test_cold_pool_summary_excludes_missing_bt():
    h = _hauls()
    h.loc[2, "bottom_temperature_c"] = np.nan       # haul 3 has no bottom temp
    df = join_catch_to_hauls(h, _catch(), 68580, "snow crab")
    s = cold_pool_summary(df).iloc[0]
    assert s["n_hauls"] == 3                          # the NaN-BT haul is dropped
