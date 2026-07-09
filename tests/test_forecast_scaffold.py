"""Forecast scaffold — config/adapter units + API live-safety (503 before data, 404 unknown)."""
from __future__ import annotations

import pandas as pd
import pytest

from mhw.forecast.deploy import load_forecast_config, monthly_area_frac, zone_role


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


def test_forecast_zones_endpoint_lists_roles():
    r = _get_client().get("/v1/forecast/zones")
    assert r.status_code == 200
    body = r.json()
    assert body["zones"]["sebs"]["role"] == "persistence"
    assert body["zones"]["chukchi"]["role"] == "climatology"
    assert body["module_version"] is None   # not pinned until LOFRA delivers


def test_forecast_unknown_zone_404():
    assert _get_client().get("/v1/forecast/atlantis").status_code == 404


def test_forecast_missing_artifact_503():
    # Valid zone, but no artifact in the test env → live-safe 503 (not 500).
    assert _get_client().get("/v1/forecast/sebs").status_code == 503


def test_onset_missing_artifact_503():
    assert _get_client().get("/v1/forecast/onset/sebs").status_code == 503
