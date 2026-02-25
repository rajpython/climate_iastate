"""FastAPI smoke tests using TestClient — no ERDDAP, reads on-disk parquet only."""
from __future__ import annotations

import pytest

DAILY_STATE_FIELDS = {"date", "area_frac", "Ibar", "Dbar", "Cbar", "Obar"}
EVENT_FIELDS = {
    "event_id",
    "start_date",
    "end_date",
    "duration_days",
    "peak_date",
    "peak_area_frac",
    "peak_Ibar",
    "mean_Cbar",
}
REGION_FIELDS = {"region_id", "start_date", "end_date", "n_days"}

EXPECTED_ROWS = 15_706


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------

def test_list_regions(api_client):
    resp = api_client.get("/regions")
    assert resp.status_code == 200
    regions = resp.json()
    assert len(regions) >= 1
    for r in regions:
        assert REGION_FIELDS.issubset(r.keys()), f"Missing fields in region entry: {r}"
        assert isinstance(r["n_days"], int) and r["n_days"] > 0


# ---------------------------------------------------------------------------
# Daily states
# ---------------------------------------------------------------------------

def test_daily_states_goa(api_client):
    resp = api_client.get("/states/region/goa")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS} rows, got {len(data)}"
    # Spot-check first record for required fields
    assert DAILY_STATE_FIELDS.issubset(data[0].keys())


def test_daily_states_date_filter(api_client):
    """2023 is not a leap year → exactly 365 records expected."""
    resp = api_client.get("/states/region/goa?start=2023-01-01&end=2023-12-31")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 365, f"Expected 365 days for 2023, got {len(data)}"


def test_daily_states_unknown_region_404(api_client):
    resp = api_client.get("/states/region/atlantis")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def test_events_goa(api_client):
    resp = api_client.get("/events/goa")
    assert resp.status_code == 200
    events = resp.json()
    for e in events:
        assert EVENT_FIELDS.issubset(e.keys()), f"Missing fields in event: {e}"
        assert e["duration_days"] >= 5, "Events below min_duration=5 should be filtered"


def test_events_min_duration(api_client):
    resp = api_client.get("/events/goa?min_duration=30")
    assert resp.status_code == 200
    events = resp.json()
    for e in events:
        assert e["duration_days"] >= 30, (
            f"Event {e['event_id']} has duration_days={e['duration_days']} < 30"
        )


def test_events_unknown_region_404(api_client):
    resp = api_client.get("/events/atlantis")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Climate indices
# ---------------------------------------------------------------------------

def test_ao_index(api_client):
    """AO endpoint must return 200 (file exists) or 503 (not yet fetched)."""
    resp = api_client.get("/indices/ao")
    assert resp.status_code in (200, 503), (
        f"Unexpected status {resp.status_code} for /indices/ao"
    )
    if resp.status_code == 200:
        body = resp.json()
        assert body["index"] == "ao"
        assert "records" in body
        assert len(body["records"]) > 0


def test_pdo_index(api_client):
    """PDO endpoint must return 200 (file exists) or 503 (not yet fetched)."""
    resp = api_client.get("/indices/pdo")
    assert resp.status_code in (200, 503), (
        f"Unexpected status {resp.status_code} for /indices/pdo"
    )
    if resp.status_code == 200:
        body = resp.json()
        assert body["index"] == "pdo"
        assert "records" in body
        assert len(body["records"]) > 0
