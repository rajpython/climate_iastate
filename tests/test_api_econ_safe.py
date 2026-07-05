"""Economic SAFE route tests — reads on-disk parquets (no network)."""
from __future__ import annotations

import pytest


def test_reports_list_ok(api_client):
    resp = api_client.get("/v1/econ/safe/reports")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["reports"]) == 17
    ids = {r["id"] for r in body["reports"]}
    assert {"gfsafe001", "gfsafe002", "gfsafe009"} <= ids


def test_report_detail_ok(api_client):
    resp = api_client.get("/v1/econ/safe/gfsafe002", params={"area": "bsai"})
    if resp.status_code == 503:
        pytest.skip("econ-safe parquet not built (run mhw-ingest-econ-safe)")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "GFSAFE002"
    assert body["records"]
    assert {"area_code", "year", "exvessel_value"} <= set(body["columns"])
    assert all(r["area_code"] == "bsai" for r in body["records"])


def test_report_year_filter(api_client):
    resp = api_client.get("/v1/econ/safe/gfsafe002",
                          params={"start_year": 2023, "end_year": 2024})
    if resp.status_code == 503:
        pytest.skip("econ-safe parquet not built")
    assert resp.status_code == 200
    assert all(2023 <= r["year"] <= 2024 for r in resp.json()["records"])


def test_unknown_report_404(api_client):
    resp = api_client.get("/v1/econ/safe/gfsafe999")
    assert resp.status_code == 404
