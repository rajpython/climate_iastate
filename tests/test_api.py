"""FastAPI smoke tests using TestClient — no ERDDAP, reads on-disk parquet only."""
from __future__ import annotations

import pandas as pd
import pytest

DAILY_STATE_FIELDS = {
    "date",
    "area_frac",
    "mean_intensity",
    "mean_duration",
    "cumul_intensity",
    "onset_rate",
}
EVENT_FIELDS = {
    "event_id",
    "start_date",
    "end_date",
    "duration_days",
    "peak_date",
    "peak_area_frac",
    "peak_intensity",
    "mean_cumul_intensity",
}
REGION_FIELDS = {"region_id", "start_date", "end_date", "n_days"}

BACKFILL_START = pd.Timestamp("1982-01-01")


def _expected_rows_from_dates(data) -> int:
    """One row per day from BACKFILL_START to the latest date in the response."""
    latest = max(pd.to_datetime(d["date"]) for d in data)
    return (latest - BACKFILL_START).days + 1


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
    resp = api_client.get("/v1/regions")
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
    resp = api_client.get("/v1/regions/goa/states")
    assert resp.status_code == 200
    data = resp.json()
    expected = _expected_rows_from_dates(data)
    assert len(data) == expected, f"Expected {expected} rows, got {len(data)}"
    # Spot-check first record for required fields
    assert DAILY_STATE_FIELDS.issubset(data[0].keys())


def test_daily_states_date_filter(api_client):
    """2023 is not a leap year → exactly 365 records expected."""
    resp = api_client.get("/v1/regions/goa/states?start=2023-01-01&end=2023-12-31")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 365, f"Expected 365 days for 2023, got {len(data)}"


def test_daily_states_unknown_region_404(api_client):
    resp = api_client.get("/v1/regions/atlantis/states")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def test_events_goa(api_client):
    resp = api_client.get("/v1/regions/goa/events")
    assert resp.status_code == 200
    events = resp.json()
    for e in events:
        assert EVENT_FIELDS.issubset(e.keys()), f"Missing fields in event: {e}"
        assert e["duration_days"] >= 5, "Events below min_duration=5 should be filtered"


def test_events_min_duration(api_client):
    resp = api_client.get("/v1/regions/goa/events?min_duration=30")
    assert resp.status_code == 200
    events = resp.json()
    for e in events:
        assert e["duration_days"] >= 30, (
            f"Event {e['event_id']} has duration_days={e['duration_days']} < 30"
        )


def test_events_unknown_region_404(api_client):
    resp = api_client.get("/v1/regions/atlantis/events")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Climate indices
# ---------------------------------------------------------------------------

def test_ao_index(api_client):
    """AO endpoint must return 200 (file exists) or 503 (not yet fetched)."""
    resp = api_client.get("/v1/indices/ao")
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
    resp = api_client.get("/v1/indices/pdo")
    assert resp.status_code in (200, 503), (
        f"Unexpected status {resp.status_code} for /indices/pdo"
    )
    if resp.status_code == 200:
        body = resp.json()
        assert body["index"] == "pdo"
        assert "records" in body
        assert len(body["records"]) > 0
