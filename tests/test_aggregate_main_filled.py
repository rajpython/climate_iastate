"""O2 (package-07 observation): mhw-aggregate's main must carry the filled-days provenance label, as backfill does."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr

import mhw.states.aggregates as agg


def _states():
    t = pd.date_range("2026-06-07", periods=3)
    lat, lon = np.array([60.125, 60.375]), np.array([-170.125, -169.875])
    one = np.ones((3, 2, 2), np.float32)
    ds = xr.Dataset({k: (("time", "lat", "lon"), one.astype(np.uint8 if k in ("A", "V") else np.float32))
                     for k in ("A", "I", "D", "C", "O", "V")}, coords={"time": t, "lat": lat, "lon": lon})
    ds["input_present"] = (("time",), np.ones(3, np.uint8))
    return ds


def test_mhw_aggregate_main_writes_the_filled_label(monkeypatch):
    captured = {}

    def fake_save(df, region):
        captured["df"] = df
        return agg.AGGREGATES_DIR / f"region_daily_{region}.parquet"
    monkeypatch.setattr(agg, "_load_states", lambda r, s, e: _states())
    monkeypatch.setattr(agg, "_load_mask_weights", lambda r, la, lo: (np.ones((2, 2), np.uint8), np.ones((2, 2), np.float32)))
    monkeypatch.setattr(agg, "load_filled_days", lambda: {"2026-06-08": "NCEI per-day OISST v2.1 (test)"})
    monkeypatch.setattr(agg, "save_aggregates", fake_save)
    monkeypatch.setattr(agg, "certified_fresh_output_preflight", lambda r: None)
    monkeypatch.setattr(sys, "argv", ["mhw-aggregate", "--region", "sebs", "--start", "2026-06-07", "--end", "2026-06-09"])
    agg.main()
    df = captured["df"]
    labels = dict(zip(pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"), df["filled"]))
    assert labels["2026-06-08"] == "NCEI per-day OISST v2.1 (test)"
    assert labels["2026-06-07"] in ("", None) or pd.isna(labels["2026-06-07"])
