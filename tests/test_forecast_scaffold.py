"""Forecast wiring — config/adapter units, the frozen→artifact mapping, and API live-safety.

The forecast module is vendored + pinned (config/forecast.yml module_version), so the zones
endpoint reports the pin and per-zone endpoints serve artifacts when present. Artifacts live under
the gitignored ``data/derived/forecast/`` — the end-to-end producer test skips when the (also
gitignored) ``region_daily_*`` inputs or the vendored module are absent, per the house pattern.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from mhw.forecast import deploy
from mhw.forecast.deploy import (
    AGG_DIR,
    FORECAST_COLUMNS,
    VENDOR_DIR,
    _forecast_rows,
    load_forecast_config,
    monthly_area_frac,
    run_forecast,
    zone_role,
)


def test_monthly_area_frac_reduces_daily_to_month_starts():
    dates = pd.date_range("2020-01-01", "2020-02-29", freq="D")
    df = pd.DataFrame({"date": dates, "area_frac": [0.5] * len(dates)})
    m = monthly_area_frac(df)
    assert list(m["date"].dt.month) == [1, 2]
    assert (m["area_frac"] == 0.5).all()


def test_monthly_area_frac_requires_columns():
    with pytest.raises(ValueError):
        monthly_area_frac(pd.DataFrame({"foo": [1]}))


def test_zone_roles_match_settled_split():
    cfg = load_forecast_config()
    persistence = {z for z, m in cfg["zones"].items() if m["role"] == "persistence"}
    climatology = {z for z, m in cfg["zones"].items() if m["role"] == "climatology"}
    assert persistence == {"sebs", "wgoa", "egoa", "nbs", "ai_west", "ai_central", "ai_east"}
    assert climatology == {"chukchi", "beaufort"}
    # NBS: persistence zone, but ice caveat + no LIM reading.
    assert cfg["zones"]["nbs"]["ice_caveat"] is True
    assert cfg["zones"]["nbs"]["lim_reading"] is False
    assert zone_role("sebs", cfg) == "persistence"


# --- frozen result → artifact mapping (pure; no manifest / no IO) ----------

def _fake_out(model: str, l1_occurrence: float | None) -> dict:
    """A minimal ``forecast_frozen``-shaped result over leads 1–3."""
    leads = {}
    for h, point, var in ((1, 0.9, 0.01), (2, -0.05, 0.02), (3, 0.03, 0.03)):
        entry = {"target_date": f"2026-{7 + h:02d}-01", "point_area_frac": point,
                 "predictive_variance": var, "predictive_variance_kind": "test"}
        if h == 1 and l1_occurrence is not None:
            entry["occurrence_prob_q90"] = l1_occurrence
        leads[h] = entry
    return {"zone": "z", "model": model, "coefficient_vintage": "2026-04-01",
            "origin_date": "2026-07-01", "leads": leads}


def test_forecast_rows_damped_maps_and_clips():
    cfg = load_forecast_config()
    df = _forecast_rows(_fake_out("damped_persistence", 0.3), cfg)
    assert list(df.columns) == FORECAST_COLUMNS + ["target_date"]
    assert list(df["lead"]) == ["L1", "L2", "L3"]
    assert list(df["confidence"]) == ["headline", "banded", "watch"]
    # points/bands are display-clipped to [0, 1] and the band brackets the point.
    assert (df["point"].between(0, 1)).all()
    assert (df["band_lo"] <= df["point"]).all() and (df["point"] <= df["band_hi"]).all()
    assert df.loc[df["lead"] == "L2", "point"].iloc[0] == 0.0        # -0.05 clipped
    # L1-only occurrence probability.
    assert df.loc[df["lead"] == "L1", "l1_prob"].iloc[0] == pytest.approx(0.3)
    assert math.isnan(df.loc[df["lead"] == "L2", "l1_prob"].iloc[0])


def test_forecast_rows_climatology_has_no_occurrence():
    cfg = load_forecast_config()
    df = _forecast_rows(_fake_out("climatology", None), cfg)
    assert (df["method"] == "climatology").all()
    assert df["l1_prob"].isna().all()


# --- end-to-end producer (skips when gitignored inputs are absent) ---------

def _inputs_present(zone: str) -> bool:
    return VENDOR_DIR.exists() and (AGG_DIR / f"region_daily_{zone}.parquet").exists()


def test_run_forecast_writes_pinned_artifact(tmp_path, monkeypatch):
    if not _inputs_present("chukchi"):
        pytest.skip("vendored module or region_daily inputs not generated")
    monkeypatch.setattr(deploy, "FORECAST_DIR", tmp_path)
    path = run_forecast("chukchi")
    assert path.parent == tmp_path
    df, meta = deploy.read_forecast_artifact("chukchi")
    assert list(df.columns[:len(FORECAST_COLUMNS)]) == FORECAST_COLUMNS
    assert meta["module_version"] == load_forecast_config()["module_version"]
    assert meta["coefficient_vintage"]  # provenance embedded


def test_run_onset_watch_writes_two_state_artifact(tmp_path, monkeypatch):
    from mhw.forecast.deploy import _onset_field_path
    cfg = load_forecast_config()
    if not (VENDOR_DIR.exists() and _onset_field_path(cfg).exists()
            and (AGG_DIR / "region_daily_sebs.parquet").exists()):
        pytest.skip("vendored module, obl029 onset field, or sebs inputs not generated")
    monkeypatch.setattr(deploy, "FORECAST_DIR", tmp_path)
    path = deploy.run_onset_watch(cfg)
    assert path.parent == tmp_path
    df, meta = deploy.read_onset_artifact()
    # a two-state elevated/normal watch (never a probability) with a numeric decision threshold
    assert set(df["state"]).issubset({"elevated", "normal"})
    assert df["threshold"].notna().all()
    assert meta["coefficient_vintage"]  # SEBS onset vintage embedded


# --- API live-safety -------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from api.main import app
        _client = TestClient(app)
    return _client


def test_forecast_zones_endpoint_reports_pin():
    r = _get_client().get("/v1/forecast/zones")
    assert r.status_code == 200
    body = r.json()
    assert body["zones"]["sebs"]["role"] == "persistence"
    assert body["zones"]["chukchi"]["role"] == "climatology"
    assert body["module_version"] == load_forecast_config()["module_version"]


def test_forecast_unknown_zone_404():
    assert _get_client().get("/v1/forecast/atlantis").status_code == 404


def test_forecast_missing_artifact_503(tmp_path, monkeypatch):
    # Point the artifact lookup at an empty dir → live-safe 503 (not 500), even once data exists.
    monkeypatch.setattr(deploy, "FORECAST_DIR", tmp_path)
    assert _get_client().get("/v1/forecast/sebs").status_code == 503


def test_forecast_served_when_present(tmp_path, monkeypatch):
    if not _inputs_present("sebs"):
        pytest.skip("vendored module or region_daily inputs not generated")
    monkeypatch.setattr(deploy, "FORECAST_DIR", tmp_path)
    run_forecast("sebs")
    r = _get_client().get("/v1/forecast/sebs")
    assert r.status_code == 200
    body = r.json()
    assert body["module_version"] == load_forecast_config()["module_version"]
    assert len(body["records"]) == 3


def test_onset_route_live_safe():
    # Live-safe both ways: 503 when the onset artifact has not been produced, 200 (two-state
    # elevated/normal records) once it has. The artifact is gitignored, so either is valid here.
    r = _get_client().get("/v1/forecast/onset/sebs")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        recs = r.json()["records"]
        assert recs and all(x["state"] in ("elevated", "normal") for x in recs)
