"""mhw.exec_record -- execution records bind the bytes a build opened (dashboard audit D01).

Network-free. Includes the D01 negative control: a build that opens a file with the SAME name as
a declared input but DIFFERENT (extended) bytes must be caught, not certified.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import mhw.climatology.build_mu_theta as bmt
import mhw.climatology.ice_outage as io_
import mhw.exec_record as er


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    er._SEEN.clear()
    io_.load_outage_doc.cache_clear()
    io_.outage_brackets.cache_clear()
    getattr(io_, "_BRACKET_GRID", {}).clear()
    yield
    er._SEEN.clear()


def _zone_year(path, start, n_days, *, seed=0):
    """A tiny zone-year OISST-shaped file: sst + ice on a 2 x 3 grid."""
    t = pd.date_range(start, periods=n_days)
    rng = np.random.default_rng(seed)
    sst = rng.normal(5, 1, (n_days, 2, 3)).astype(np.float32)
    ice = np.full((n_days, 2, 3), np.nan, dtype=np.float32)
    ds = xr.Dataset({"sst": (("time", "lat", "lon"), sst), "ice": (("time", "lat", "lon"), ice)},
                    coords={"time": t, "lat": [60.125, 60.375], "lon": [-170.125, -169.875, -169.625]})
    ds.to_netcdf(path)
    return path


def _log_rows(log):
    return [json.loads(x) for x in log.read_text().splitlines() if x.strip()]


def test_record_open_is_a_noop_without_the_variable(tmp_path, monkeypatch):
    monkeypatch.delenv(er.ENV_VAR, raising=False)
    f = tmp_path / "a.nc"
    f.write_bytes(b"x")
    er.record_open(f, "raw_sst_ice")          # must not raise or write anywhere
    assert list(tmp_path.iterdir()) == [f]


def test_fetch_year_records_the_bytes_it_opens(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    f = _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 10)
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    bmt.fetch_year("sebs", 2026, {}, None).close()
    rows = _log_rows(log)
    assert [(r["role"], r["basename"]) for r in rows] == [("raw_sst_ice", "oisst_sebs_2026.nc")]
    assert rows[0]["sha256"] == er.sha256_file(f)


def test_D01_negative_control_same_name_extended_bytes_is_caught(tmp_path, monkeypatch):
    """Declared list = the 243-day original; the build opens a 273-day file of the same name."""
    (tmp_path / "orig").mkdir()
    orig = _zone_year(tmp_path / "orig" / "oisst_sebs_2026.nc", "2026-01-01", 243)
    declared = tmp_path / "declared.txt"
    declared.write_text(f"# declared\noisst_sebs_2026.nc:{er.sha256_file(orig)}\n")

    raw = tmp_path / "raw"
    raw.mkdir()
    # Same name, same first 243 days (same seed -> identical overlap values), 30 more days appended.
    ext = _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 273)
    with xr.open_dataset(orig) as a, xr.open_dataset(ext) as b:
        assert np.array_equal(a["sst"].values, b["sst"].values[:243])   # overlap identical, like D01

    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    bmt.fetch_year("sebs", 2026, {}, None).close()

    out = tmp_path / "rec"
    rc = er.finalize(log, out, declared)
    rec = json.loads((out / "executed_inputs.json").read_text())
    assert rc == 3
    assert rec["declared_comparison"]["changed_same_name_different_bytes"] == ["oisst_sebs_2026.nc"]
    assert not rec["declared_comparison"]["ok"]
    listed = er.parse_shas_list((out / "oisst_input_file_shas_executed.txt").read_text())
    assert listed == {"oisst_sebs_2026.nc": er.sha256_file(ext)}   # the record names what was opened


def test_positive_control_unchanged_input_passes(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    f = _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 243)
    declared = tmp_path / "declared.txt"
    declared.write_text(f"oisst_sebs_2026.nc:{er.sha256_file(f)}\n")
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    bmt.fetch_year("sebs", 2026, {}, None).close()
    assert er.finalize(log, tmp_path / "rec", declared) == 0


def test_dynamically_resolved_bracket_files_are_recorded(tmp_path, monkeypatch):
    """The ice-outage rule opens files the caller never named (days either side of an outage)."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _zone_year(raw / "oisst_beaufort_2016.nc", "2016-12-01", 31)
    _zone_year(raw / "oisst_beaufort_2017.nc", "2017-01-01", 59)
    cfg = tmp_path / "outages.json"
    cfg.write_text(json.dumps({"global": {"days": ["2017-01-01", "2017-01-02"]}}))
    log = tmp_path / "run.jsonl"
    monkeypatch.setenv(er.ENV_VAR, str(log))
    with xr.open_dataset(raw / "oisst_beaufort_2017.nc") as ds:
        io_.apply_ice_outages("beaufort", ds, raw_dir=raw, config=cfg)
    got = {(r["role"], r["basename"]) for r in _log_rows(log)}
    assert ("raw_ice_bracket", "oisst_beaufort_2016.nc") in got     # resolved at run time
    assert ("raw_ice_bracket", "oisst_beaufort_2017.nc") in got
    assert ("config", "outages.json") in got


def test_a_path_seen_with_two_hashes_is_a_conflict(tmp_path):
    log = tmp_path / "run.jsonl"
    rows = [dict(role="raw_sst_ice", path="/x/oisst_a_2026.nc", basename="oisst_a_2026.nc", sha256=s)
            for s in ("1" * 64, "2" * 64)]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert er.finalize(log, tmp_path / "rec") == 3


def test_directory_hash_follows_content(tmp_path):
    d = tmp_path / "store.zarr"
    (d / "v").mkdir(parents=True)
    (d / "v" / "0").write_bytes(b"abc")
    h1 = er.sha256_path(d)
    assert h1 == er.aggregate_sha([f"v/0:{er.sha256_file(d / 'v' / '0')}"])
    (d / "v" / "0").write_bytes(b"abd")
    assert er.sha256_path(d) != h1


def test_wrap_refuses_an_empty_record(tmp_path):
    rc = er.main(["wrap", "--out", str(tmp_path / "rec"), "--", sys.executable, "-c", "pass"])
    assert rc == 4
    assert not (tmp_path / "rec" / "executed_inputs.json").exists()


def test_wrap_records_a_child_process(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 5)
    code = ("import mhw.climatology.build_mu_theta as b, pathlib; "
            f"b.DATA_RAW = pathlib.Path({str(raw)!r}); b.fetch_year('sebs', 2026, {{}}, None).close()")
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    rc = er.main(["wrap", "--out", str(tmp_path / "rec"), "--", sys.executable, "-c", code])
    assert rc == 0
    rec = json.loads((tmp_path / "rec" / "executed_inputs.json").read_text())
    assert rec["oisst_inputs"]["n_files"] == 1
    assert rec["environment"]["env"]["MHW_FROZEN_INPUTS"] == "1"


def test_compare_to_declared_by_name_and_bytes():
    cmp = er.compare_to_declared({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9", "d": "4"})
    assert cmp["changed_same_name_different_bytes"] == ["b"]
    assert cmp["executed_not_declared"] == ["c"] and cmp["declared_not_executed"] == ["d"]
    assert cmp["n_same_name_same_bytes"] == 1 and not cmp["ok"]



def test_mutation_between_open_and_finalize_fails_the_record(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    f = _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 10)
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    bmt.fetch_year("sebs", 2026, {}, None).close()
    _zone_year(f, "2026-01-01", 11, seed=1)            # rewritten after it was opened
    rc = er.finalize(log, tmp_path / "rec")
    rec = json.loads((tmp_path / "rec" / "executed_inputs.json").read_text())
    assert rc == 3
    assert [m["path"] for m in rec["mutated_after_open"]] == [str(f.resolve())]


def test_missing_frozen_input_is_recorded_and_fatal(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    with pytest.raises(RuntimeError, match="Refusing to fetch"):
        bmt.fetch_year("sebs", 2026, {}, None)
    _, _, missing = er.read_log(log)
    assert [(m["role"], Path(m["path"]).name) for m in missing] == [("raw_sst_ice", "oisst_sebs_2026.nc")]


def test_engine_records_available_vs_processed_days(tmp_path, monkeypatch):
    """Intended calendar restriction: a 273-day file run to 08-31 records 243 processed days."""
    import mhw.states.update_states as us
    from mhw.climatology.build_mu_theta import _load_config

    raw = tmp_path / "raw"
    raw.mkdir()
    _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 273)
    lat, lon = np.array([60.125, 60.375]), np.array([-170.125, -169.875, -169.625])
    theta = np.full((366, 2, 3), 99.0, dtype=np.float32)
    log = tmp_path / "run.jsonl"
    monkeypatch.setattr(bmt, "DATA_RAW", raw)
    monkeypatch.setattr(us, "_load_climatology", lambda cfg, r: (theta, theta, lat, lon))
    monkeypatch.setattr(us, "_load_region_bbox", lambda r: {})
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    monkeypatch.setenv(er.ENV_VAR, str(log))
    us.run_state_engine("sebs", date(2026, 1, 1), date(2026, 8, 31), _load_config(), verbose=False)
    er.finalize(log, tmp_path / "rec")
    rec = json.loads((tmp_path / "rec" / "executed_inputs.json").read_text())
    (row,) = [r for r in rec["opened"] if r["basename"] == "oisst_sebs_2026.nc"]
    assert row["use"][0]["available"] == ["2026-01-01", "2026-09-30", 273]
    assert row["use"][0]["processed"] == ["2026-01-01", "2026-08-31", 243]


def test_executed_code_is_bound_by_module_hash(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    _zone_year(raw / "oisst_sebs_2026.nc", "2026-01-01", 5)
    code = ("import mhw.climatology.build_mu_theta as b, pathlib; "
            f"b.DATA_RAW = pathlib.Path({str(raw)!r}); b.fetch_year('sebs', 2026, {{}}, None).close()")
    monkeypatch.setenv("MHW_FROZEN_INPUTS", "1")
    assert er.main(["wrap", "--out", str(tmp_path / "rec"), "--", sys.executable, "-c", code]) == 0
    rec = json.loads((tmp_path / "rec" / "executed_inputs.json").read_text())
    files = rec["executed_code"]["files"]
    assert files["mhw/exec_record.py"] == [er.sha256_file(Path(er.__file__))]
    assert "mhw/climatology/build_mu_theta.py" in files and rec["executed_code"]["n_module_files"] >= 3
