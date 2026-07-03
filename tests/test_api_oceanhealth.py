"""Ocean-health route tests — reads on-disk parquet (no network); skips when unbuilt."""
from __future__ import annotations

import pytest


def test_ocean_health_observed_ok(api_client):
    resp = api_client.get("/v1/ocean-health/observed",
                          params={"variable": "salinity", "region": "sebs"})
    if resp.status_code == 503:
        pytest.skip("observed salinity not fetched (run mhw-fetch-coldpool --region sebs)")
    assert resp.status_code == 200
    body = resp.json()
    assert body["variable"] == "salinity" and body["region"] == "sebs"
    assert body["units"] == "psu" and body["kind"] == "observed"
    assert body["records"], "expected at least one survey-year record"
    years = [r["year"] for r in body["records"]]
    assert years == sorted(years)
    # Salinity sensors begin ~2008, so nothing earlier should appear.
    assert min(years) >= 2008


def test_ocean_health_modelled_ok(api_client):
    resp = api_client.get("/v1/ocean-health/modelled",
                          params={"variable": "salinity", "source": "mom6_nep", "region": "sebs"})
    if resp.status_code == 503:
        pytest.skip("modelled salinity not built (run mhw-build-ocean-health)")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "modelled" and body["units"] == "psu"
    assert body["records"]


def test_ocean_health_unknown_variable_404(api_client):
    # Variable validation happens before any data load, so this 404s with or without parquet.
    resp = api_client.get("/v1/ocean-health/observed", params={"variable": "unobtanium"})
    assert resp.status_code == 404


def test_ocean_health_unknown_region_404(api_client):
    resp = api_client.get("/v1/ocean-health/observed",
                          params={"variable": "salinity", "region": "atlantis"})
    assert resp.status_code == 404


def test_ocean_health_unknown_source_404(api_client):
    resp = api_client.get("/v1/ocean-health/modelled",
                          params={"variable": "salinity", "source": "nope", "region": "sebs"})
    assert resp.status_code == 404


def test_ocean_health_observed_goa_no_salinity_503(api_client):
    # GOA has no packaged bottom salinity — must fail cleanly (503), never silently empty.
    resp = api_client.get("/v1/ocean-health/observed",
                          params={"variable": "salinity", "region": "goa"})
    assert resp.status_code == 503
