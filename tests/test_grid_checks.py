"""Exact coordinate assertions at the two pipeline joins (prevention; network-free).

Join 1: raw SST/ice <-> theta90/mu in the state engine.  Join 2: region mask <-> area weights <->
state grid in the aggregation. Matching grids pass with unchanged results; reordered or shifted
grids (same shape, so a shape check alone passes them) must raise.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import mhw.states.aggregates as agg
import mhw.states.update_states as us
from mhw.climatology.build_mu_theta import _load_config
from mhw.utils.grid import GridMismatchError, assert_same_grid

LAT = np.array([60.125, 60.375])
LON = np.array([-170.125, -169.875, -169.625])


# --- the helper --------------------------------------------------------------------------
def test_identical_grids_pass_including_dtype_promotion():
    assert_same_grid(LAT, LON, LAT.astype(np.float32), LON.astype(np.float32), where="t")


@pytest.mark.parametrize("lat, lon", [
    (LAT, LON[::-1]),                      # reversed
    (LAT + 0.25, LON),                     # shifted by one cell
    (LAT, LON + 1e-4),                     # sub-cell offset
    (LAT, LON[:2]),                        # different length
])
def test_mismatched_grids_raise(lat, lon):
    with pytest.raises(GridMismatchError):
        assert_same_grid(LAT, LON, lat, lon, where="t")


# --- join 1: the state engine -------------------------------------------------------------
def _sst_ds(lat, lon, n=8):
    t = pd.date_range("2026-01-01", periods=n)
    sst = np.full((n, len(lat), len(lon)), 9.0, dtype=np.float32)
    sst[:, 0, 0] = np.arange(n, dtype=np.float32)        # one distinctive cell
    ice = np.full_like(sst, np.nan)
    return xr.Dataset({"sst": (("time", "lat", "lon"), sst), "ice": (("time", "lat", "lon"), ice)},
                      coords={"time": t, "lat": lat, "lon": lon})


def _run_engine(monkeypatch, sst_lat, sst_lon):
    theta = np.full((366, len(LAT), len(LON)), 5.0, dtype=np.float32)
    mu = np.full_like(theta, 3.0)
    monkeypatch.setattr(us, "_load_climatology", lambda cfg, r: (theta, mu, LAT, LON))
    monkeypatch.setattr(us, "_load_region_bbox", lambda r: {})
    monkeypatch.setattr(us, "year_cache_stale", lambda *a, **k: False)
    monkeypatch.setattr(us, "fetch_year", lambda *a, **k: _sst_ds(sst_lat, sst_lon))
    monkeypatch.setattr(us, "apply_ice_outages", lambda r, ds: ds["ice"].values)
    ds, _ = us.run_state_engine("sebs", date(2026, 1, 1), date(2026, 1, 8), _load_config(),
                                verbose=False)
    return ds


def test_engine_aligned_grid_runs(monkeypatch):
    ds = _run_engine(monkeypatch, LAT, LON)
    assert int(ds["A"].values[:, 1, 1].sum()) == 8      # 9 > 5 every day -> in event once confirmed


@pytest.mark.parametrize("lat, lon", [(LAT, LON[::-1]), (LAT[::-1], LON), (LAT, LON + 0.25)])
def test_engine_reordered_or_shifted_sst_grid_raises(monkeypatch, lat, lon):
    with pytest.raises(GridMismatchError, match=r"raw (sst|SST) sebs 2026"):
        _run_engine(monkeypatch, lat, lon)


# --- join 2: the aggregation --------------------------------------------------------------
def _stores(tmp_path, monkeypatch, w_lon=None):
    big_lat = np.arange(59.875, 61.0, 0.25)
    big_lon = np.arange(-170.625, -169.0, 0.25)
    m = xr.Dataset({"sebs": (("lat", "lon"), np.ones((big_lat.size, big_lon.size), np.uint8))},
                   coords={"lat": big_lat, "lon": big_lon})
    wl = big_lon if w_lon is None else w_lon
    w = xr.Dataset({"weights": (("lat", "lon"), np.cos(np.deg2rad(big_lat))[:, None] * np.ones(wl.size))},
                   coords={"lat": big_lat, "lon": wl})
    m.to_zarr(tmp_path / "m.zarr", consolidated=False)
    w.to_zarr(tmp_path / "w.zarr", consolidated=False)
    monkeypatch.setattr(agg, "MASKS_PATH", tmp_path / "m.zarr")
    monkeypatch.setattr(agg, "WEIGHTS_PATH", tmp_path / "w.zarr")


def test_mask_weights_on_the_state_grid_are_unchanged(tmp_path, monkeypatch):
    _stores(tmp_path, monkeypatch)
    mask, w = agg._load_mask_weights("sebs", LAT, LON)
    assert mask.shape == (2, 3) and mask.all()
    np.testing.assert_array_equal(w, np.cos(np.deg2rad(LAT))[:, None].astype(np.float32) * np.ones((1, 3), np.float32))


def test_state_grid_off_the_mask_grid_raises_instead_of_snapping(tmp_path, monkeypatch):
    _stores(tmp_path, monkeypatch)
    with pytest.raises(GridMismatchError, match="region mask vs state grid"):
        agg._load_mask_weights("sebs", LAT, LON + 0.1)       # "nearest" would silently snap this


def test_mask_and_weight_stores_on_different_grids_raise(tmp_path, monkeypatch):
    _stores(tmp_path, monkeypatch, w_lon=np.arange(-170.625, -169.0, 0.25) + 0.25)
    with pytest.raises(GridMismatchError, match="region mask store vs area-weight store"):
        agg._load_mask_weights("sebs", LAT, LON)


# --- contract details: duplicates, dims, a planted mismatch in one used cell -----------------
def test_duplicate_coordinates_fail_even_when_both_sides_are_equal():
    dup = np.array([-170.125, -170.125, -169.625])
    with pytest.raises(GridMismatchError, match="duplicate"):
        assert_same_grid(LAT, dup, LAT, dup, where="t")


def test_planted_mismatch_in_one_used_cell_is_located():
    planted = LON.copy()
    planted[1] += 0.25 / 1000
    with pytest.raises(GridMismatchError, match=r"lon axes differ .* at index 1"):
        assert_same_grid(LAT, LON, LAT, planted, where="t")


def test_engine_duplicate_lat_rejected_before_any_state_is_written(monkeypatch):
    with pytest.raises(GridMismatchError, match="duplicate"):
        _run_engine(monkeypatch, np.array([60.125, 60.125]), LON)


def test_wrong_dimension_order_is_rejected():
    from mhw.utils.grid import assert_grid_contract
    da = _sst_ds(LAT, LON)["sst"].transpose("time", "lon", "lat")
    with pytest.raises(GridMismatchError, match="do not end in"):
        assert_grid_contract(da, "t", ("time", "lat", "lon"))


def test_climatology_baseline_years_must_share_one_grid(tmp_path, monkeypatch):
    """Join 0: every baseline year is stacked cell-by-cell onto the first year's grid."""
    import mhw.climatology.build_mu_theta as bmt
    cfg = _load_config()
    cfg["climatology"]["baseline"] = {"start_year": 1991, "end_year": 1992}
    grids = {1991: (LAT, LON), 1992: (LAT, LON + 0.25)}       # same shape, shifted
    monkeypatch.setattr(bmt, "_load_region_bbox", lambda r: {})
    monkeypatch.setattr(bmt, "fetch_year", lambda r, y, *a, **k: _sst_ds(*grids[y], n=365).assign_coords(
        time=pd.date_range(f"{y}-01-01", periods=365)))
    monkeypatch.setattr(bmt, "apply_ice_outages", lambda r, ds: ds["ice"].values)
    with pytest.raises(GridMismatchError, match="baseline year 1992 vs 1991"):
        bmt.build_climatology("sebs", cfg)


def test_ice_outage_brackets_on_a_different_grid_are_rejected(tmp_path):
    """Join 1b: bracket ice (read from neighbouring files) is applied cell-by-cell to the zone-year."""
    import json

    import mhw.climatology.ice_outage as io_
    io_.load_outage_doc.cache_clear()
    io_.outage_brackets.cache_clear()
    raw = tmp_path / "raw"
    raw.mkdir()
    _sst_ds(LAT, LON + 0.25, n=31).assign_coords(time=pd.date_range("2016-12-01", periods=31)) \
        .to_netcdf(raw / "oisst_beaufort_2016.nc")
    yr = _sst_ds(LAT, LON, n=40).assign_coords(time=pd.date_range("2017-01-01", periods=40))
    yr.to_netcdf(raw / "oisst_beaufort_2017.nc")
    cfg = tmp_path / "outages.json"
    cfg.write_text(json.dumps({"global": {"days": ["2017-01-01"]}}))
    with pytest.raises(GridMismatchError, match="ice-outage bracket"):
        io_.apply_ice_outages("beaufort", yr, raw_dir=raw, config=cfg)
