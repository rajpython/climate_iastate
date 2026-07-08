"""Catalog + discovery + grounded-query tests (network-free, tmp data)."""
from __future__ import annotations

import pandas as pd

from mhw.assistant import catalog as C
from mhw.assistant import tools


def _landings(tmp):
    d = tmp / "raw"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "year": [2000, 2001, 2000],
        "species": ["CRAB, SNOW", "CRAB, SNOW", "COD, PACIFIC"],
        "area_group": ["statewide"] * 3,
        "landings_t": [10.0, 12.0, 50.0], "value_usd": [1.0, 2.0, 3.0],
    }).to_parquet(d / "landings_foss_ak.parquet")
    return tmp


def test_list_datasets_has_core_and_econ():
    ids = {d["id"] for d in C.list_datasets()["datasets"]}
    assert {"mhw_daily", "landings", "coldpool_observed", "catch_thermal"} <= ids
    assert any(i.startswith("econ_safe:") for i in ids)


def test_describe_dataset_units_and_dims():
    d = C.describe_dataset("mhw_daily")
    cols = {m["col"] for m in d["measures"]}
    assert "area_frac" in cols
    assert "region" in d["dimensions"]
    assert d["join_keys"] == ["date", "region"]


def test_describe_unknown_dataset():
    assert "error" in C.describe_dataset("nope")


def test_list_dimension_values_resolves_species_name(tmp_path):
    _landings(tmp_path)
    v = C.list_dimension_values("landings", "species", data_root=tmp_path)
    assert "CRAB, SNOW" in v["values"]


def test_query_grounding_empty_returns_valid_values(tmp_path):
    _landings(tmp_path)
    out = tools.query("landings", {"species": "snow crab"}, data_root=tmp_path)
    assert out["records"] == []
    assert "CRAB, SNOW" in out["valid_values"]["species"]
    assert "do NOT chart" in out["note"]


def test_query_returns_grounded_records(tmp_path):
    _landings(tmp_path)
    out = tools.query("landings", {"species": "CRAB, SNOW"}, data_root=tmp_path)
    assert out["n_total"] == 2
