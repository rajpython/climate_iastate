"""Landings route tests — reads the on-disk landings parquet (no network)."""
from __future__ import annotations

import pytest

LANDINGS_FIELDS = {"year", "species", "species_code", "landings_t", "value_usd"}


def test_landings_statewide_ok(api_client):
    resp = api_client.get("/v1/landings/statewide")
    if resp.status_code == 503:
        pytest.skip("landings parquet not fetched (run mhw-fetch-landings-foss)")
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolution"] == "statewide"
    assert body["area_group"] == "statewide"
    assert body["records"], "expected at least one landings record"
    assert LANDINGS_FIELDS <= set(body["records"][0])
    years = [r["year"] for r in body["records"]]
    assert years == sorted(years)


def test_landings_species_filter(api_client):
    resp = api_client.get("/v1/landings/statewide", params={"species": "pollock"})
    if resp.status_code == 503:
        pytest.skip("landings parquet not fetched")
    assert resp.status_code == 200
    body = resp.json()
    assert body["records"]
    assert all("POLLOCK" in r["species"].upper() for r in body["records"])


def test_landings_year_filter(api_client):
    resp = api_client.get("/v1/landings/statewide",
                          params={"start_year": 2020, "end_year": 2024})
    if resp.status_code == 503:
        pytest.skip("landings parquet not fetched")
    assert resp.status_code == 200
    assert all(2020 <= r["year"] <= 2024 for r in resp.json()["records"])
