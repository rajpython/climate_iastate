"""Independent-auditor handback 04 (2026-10-04): CG01, CG02, PC04, PC05. Network-free by construction.

Every remote open is a tripwire: ``xarray.open_dataset`` on an http(s) URL raises AssertionError, so a test
that reaches the PFEG pre-open fails loudly instead of touching the network.
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import mhw.climatology.build_mu_theta as bmt
import mhw.climatology.ice_outage as io_
import mhw.exec_record as er
import mhw.states.aggregates as agg
import mhw.states.update_states as us
from mhw.climatology.build_mu_theta import _load_config
from mhw.utils.grid import GridMismatchError

LAT2 = np.array([60.125, 60.375])
LON2 = np.array([-170.125, -169.875])          # square 2 x 2: a transpose keeps every shape


@pytest.fixture(autouse=True)
def _tripwire(monkeypatch):
    real = xr.open_dataset

    def guarded(obj, *a, **k):
        if isinstance(obj, str) and obj.startswith(("http://", "https://")):
            raise AssertionError(f"NETWORK TRIPWIRE: {obj}")
        return real(obj, *a, **k)
    monkeypatch.setattr(xr, "open_dataset", guarded)
    io_.load_outage_doc.cache_clear()
    io_.outage_brackets.cache_clear()
    io_._BRACKET_GRID.clear()
    er._SEEN.clear()
    yield


def _year(path, start, n, *, transpose_ice=False, ice=np.nan):
    t = pd.date_range(start, periods=n)
    sst = np.full((n, 2, 2), 1.0, dtype=np.float32)
    ic = np.full((n, 2, 2), ice, dtype=np.float32)
    ic[:, 0, 1] = 0.9                           # asymmetric: a transpose moves ice to another cell
    ds = xr.Dataset({"sst": (("time", "lat", "lon"), sst)}, coords={"time": t, "lat": LAT2, "lon": LON2})
    if transpose_ice:
        ds["ice"] = (("time", "lon", "lat"), ic.transpose(0, 2, 1))
    else:
        ds["ice"] = (("time", "lat", "lon"), ic)
    ds.to_netcdf(path)


# --- CG01: dimension order before positional reads ---------------------------------------------
def test_CG01_bracket_ice_transposed_on_a_square_grid_is_rejected(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_beaufort_2016.nc", "2016-12-01", 31, transpose_ice=True)
    _year(raw / "oisst_beaufort_2017.nc", "2017-01-01", 40)
    cfg = tmp_path / "out.json"
    cfg.write_text(json.dumps({"global": {"days": ["2017-01-01"]}}))
    with xr.open_dataset(raw / "oisst_beaufort_2017.nc") as ds, \
            pytest.raises(GridMismatchError, match=r"ice-outage bracket file oisst_beaufort_2016.nc: dims"):
        io_.apply_ice_outages("beaufort", ds, raw_dir=raw, config=cfg)


def test_CG01_control_bracket_aligned_passes(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_beaufort_2016.nc", "2016-12-01", 31)
    _year(raw / "oisst_beaufort_2017.nc", "2017-01-01", 40)
    cfg = tmp_path / "out.json"
    cfg.write_text(json.dumps({"global": {"days": ["2017-01-01"]}}))
    with xr.open_dataset(raw / "oisst_beaufort_2017.nc") as ds:
        out = io_.apply_ice_outages("beaufort", ds, raw_dir=raw, config=cfg)
    assert out.shape == (40, 2, 2)


def test_CG01_engine_raw_ice_transposed_is_rejected(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_sebs_2026.nc", "2026-01-01", 10, transpose_ice=True)
    theta = np.full((366, 2, 2), 5.0, dtype=np.float32)
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(us, "_load_climatology", lambda cfg, r: (theta, theta, LAT2, LON2))
    monkeypatch.setattr(us, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    with pytest.raises(GridMismatchError, match=r"raw ice sebs 2026: dims"):
        us.run_state_engine("sebs", date(2026, 1, 1), date(2026, 1, 10), _load_config(), verbose=False)


def _states(V_transposed=False, present_dims=("time",)):
    t = pd.date_range("2026-01-01", periods=3)
    a = np.ones((3, 2, 2), np.uint8)
    v = np.ones((3, 2, 2), np.uint8)
    v[:, 0, 1] = 0
    ds = xr.Dataset({k: (("time", "lat", "lon"), a.astype(np.float32 if k != "A" else np.uint8))
                     for k in ("A", "I", "D", "C", "O")}, coords={"time": t, "lat": LAT2, "lon": LON2})
    ds["V"] = (("time", "lon", "lat"), v.transpose(0, 2, 1)) if V_transposed else (("time", "lat", "lon"), v)
    if present_dims == ("time",):
        ds["input_present"] = (("time",), np.ones(3, np.uint8))
    else:
        ds["input_present"] = (present_dims, np.ones((3, 2), np.uint8))
    return ds


def test_CG01_aggregate_V_transposed_is_rejected():
    mask = np.ones((2, 2), np.uint8)
    w = np.ones((2, 2), np.float32)
    with pytest.raises(GridMismatchError, match=r"state store variable V: dims"):
        agg.aggregate_region(_states(V_transposed=True), mask, w)


def test_CG01_input_present_on_the_wrong_axis_is_rejected():
    mask = np.ones((2, 2), np.uint8)
    w = np.ones((2, 2), np.float32)
    with pytest.raises(GridMismatchError, match=r"input_present: dims"):
        agg.aggregate_region(_states(present_dims=("time", "lat")), mask, w)


def test_CG01_control_aligned_states_aggregate():
    df = agg.aggregate_region(_states(), np.ones((2, 2), np.uint8), np.ones((2, 2), np.float32))
    assert len(df) == 3 and float(df["valid_frac"].iloc[0]) == 0.75


# --- CG02: canonical, paired DOY 1..366 ---------------------------------------------------------
def _clim(tmp_path, monkeypatch, doy_t, doy_m):
    root = tmp_path / "proj"
    cfg = _load_config()
    paths = cfg["climatology"]["outputs"]["paths"]
    for var, doy in (("theta90", doy_t), ("mu", doy_m)):
        p = root / paths[var].replace(".zarr", "_sebs.zarr")
        p.parent.mkdir(parents=True, exist_ok=True)
        xr.Dataset({var: (("doy", "lat", "lon"), np.zeros((len(doy), 2, 2), np.float32))},
                   coords={"doy": np.asarray(doy), "lat": LAT2, "lon": LON2}).to_zarr(p, consolidated=False)
    monkeypatch.setattr(us, "PROJECT_ROOT", root)
    return cfg


@pytest.mark.parametrize("doy_t, doy_m", [
    (np.arange(2, 368), np.arange(2, 368)),       # shifted, both labelled 2..367
    (np.arange(1, 366), np.arange(1, 366)),       # shortened 1..365
    (np.arange(1, 367), np.arange(2, 368)),       # theta90 canonical, mu shifted (unpaired)
])
def test_CG02_non_canonical_or_unpaired_doy_is_rejected(tmp_path, monkeypatch, doy_t, doy_m):
    cfg = _clim(tmp_path, monkeypatch, doy_t, doy_m)
    with pytest.raises(GridMismatchError, match="canonical 1..366"):
        us._load_climatology(cfg, "sebs")


def test_CG02_control_canonical_doy_loads(tmp_path, monkeypatch):
    cfg = _clim(tmp_path, monkeypatch, np.arange(1, 367), np.arange(1, 367))
    theta, mu, lats, lons = us._load_climatology(cfg, "sebs")
    assert theta.shape == (366, 2, 2)


# --- PC04: certified runs are fresh-output-only -------------------------------------------------
def test_PC04_certified_run_refuses_an_existing_aggregate(tmp_path, monkeypatch):
    monkeypatch.setattr(agg, "AGGREGATES_DIR", tmp_path)
    old = pd.DataFrame({"date": [date(2025, 12, 31)], "area_frac": np.float32([0.123456])})
    old.to_parquet(tmp_path / "region_daily_sebs.parquet", index=False)
    monkeypatch.setenv(er.ENV_VAR, str(tmp_path / "log.jsonl"))
    with pytest.raises(RuntimeError, match="fresh-output-only"):
        agg.certified_fresh_output_preflight("sebs")
    new = pd.DataFrame({"date": [date(2026, 1, 1)], "area_frac": np.float32([0.5])})
    with pytest.raises(RuntimeError, match="fresh-output-only"):
        agg.save_aggregates(new, "sebs")
    assert len(pd.read_parquet(tmp_path / "region_daily_sebs.parquet")) == 1     # untouched


def test_PC04_uncertified_merge_behaviour_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(agg, "AGGREGATES_DIR", tmp_path)
    monkeypatch.delenv(er.ENV_VAR, raising=False)
    pd.DataFrame({"date": [date(2025, 12, 31)], "area_frac": np.float32([0.123456])}).to_parquet(
        tmp_path / "region_daily_sebs.parquet", index=False)
    agg.save_aggregates(pd.DataFrame({"date": [date(2026, 1, 1)], "area_frac": np.float32([0.5])}), "sebs")
    assert len(pd.read_parquet(tmp_path / "region_daily_sebs.parquet")) == 2


# --- PC05: frozen missing inputs refused and recorded BEFORE any remote open ---------------------
def test_PC05_engine_refuses_before_remote_and_records_the_missing_year(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_sebs_2026.nc", "2026-01-01", 10)              # 2025 (warm-up year) absent
    log = tmp_path / "run.jsonl"
    theta = np.full((366, 2, 2), 5.0, dtype=np.float32)
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(us, "_load_climatology", lambda cfg, r: (theta, theta, LAT2, LON2))
    monkeypatch.setattr(us, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    with pytest.raises(RuntimeError, match="Refusing before any remote connection"):
        us.run_state_engine("sebs", date(2025, 12, 20), date(2026, 1, 10), _load_config(), verbose=False)
    _, _, missing = er.read_log(log)
    assert [m["path"].split("/")[-1] for m in missing] == ["oisst_sebs_2025.nc"]


def test_PC05_climatology_refuses_before_remote_and_records_the_missing_year(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_sebs_1991.nc", "1991-01-01", 365)              # 1992 absent
    cfg = _load_config()
    cfg["climatology"]["baseline"] = {"start_year": 1991, "end_year": 1992}
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(bmt, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    with pytest.raises(RuntimeError, match="Refusing before any remote connection"):
        bmt.build_climatology("sebs", cfg)
    _, _, missing = er.read_log(log)
    assert [m["path"].split("/")[-1] for m in missing] == ["oisst_sebs_1992.nc"]


# --- Handback 07 residuals ----------------------------------------------------------------------
def test_H07_fractional_doy_is_rejected_without_truncation(tmp_path, monkeypatch):
    cfg = _clim(tmp_path, monkeypatch, np.arange(1, 367) + 0.5, np.arange(1, 367) + 0.5)   # 1.5..366.5
    with pytest.raises(GridMismatchError, match="canonical 1..366"):
        us._load_climatology(cfg, "sebs")


@pytest.mark.parametrize("doy", [np.arange(1, 367), np.arange(1, 367).astype(np.float64),
                                 np.arange(1, 367).astype(np.int16)])
def test_H07_canonical_doy_in_any_numeric_representation_loads(tmp_path, monkeypatch, doy):
    cfg = _clim(tmp_path, monkeypatch, doy, doy)
    assert us._load_climatology(cfg, "sebs")[0].shape == (366, 2, 2)


def test_H07_no_cache_with_frozen_inputs_refuses_before_remote_engine(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_sebs_2026.nc", "2026-01-01", 10)               # usable cache present
    theta = np.full((366, 2, 2), 5.0, dtype=np.float32)
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(us, "_load_climatology", lambda cfg, r: (theta, theta, LAT2, LON2))
    monkeypatch.setattr(us, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    with pytest.raises(RuntimeError, match=r"--no-cache.*Refusing before any remote connection"):
        us.run_state_engine("sebs", date(2026, 1, 1), date(2026, 1, 10), _load_config(),
                            use_cache=False, verbose=False)


def test_H07_no_cache_with_frozen_inputs_refuses_before_remote_climatology(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _year(raw / "oisst_sebs_1991.nc", "1991-01-01", 365)
    cfg = _load_config()
    cfg["climatology"]["baseline"] = {"start_year": 1991, "end_year": 1991}
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(bmt, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    with pytest.raises(RuntimeError, match=r"--no-cache.*Refusing before any remote connection"):
        bmt.build_climatology("sebs", cfg, use_cache=False)
