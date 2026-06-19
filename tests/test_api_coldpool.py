"""Cold-pool route tests — reads the on-disk observed-index parquet (no network)."""
from __future__ import annotations

import pytest

COLDPOOL_FIELDS = {
    "year",
    "area_lte2_km2",
    "area_lte1_km2",
    "area_lte0_km2",
    "area_lteminus1_km2",
    "mean_bottom_temp",
    "mean_surface_temp",
}


def test_cold_pool_observed_ok(api_client):
    resp = api_client.get("/v1/cold-pool/observed")
    if resp.status_code == 503:
        pytest.skip("cold-pool parquet not fetched (run mhw-fetch-coldpool)")
    assert resp.status_code == 200
    body = resp.json()
    assert body["region"] == "ebs"
    assert body["records"], "expected at least one survey-year record"
    assert COLDPOOL_FIELDS <= set(body["records"][0])
    # Years are sorted ascending and 2020 (cancelled survey) is absent.
    years = [r["year"] for r in body["records"]]
    assert years == sorted(years)
    assert 2020 not in years


def test_cold_pool_year_filter(api_client):
    resp = api_client.get("/v1/cold-pool/observed", params={"start_year": 2018, "end_year": 2019})
    if resp.status_code == 503:
        pytest.skip("cold-pool parquet not fetched")
    assert resp.status_code == 200
    years = [r["year"] for r in resp.json()["records"]]
    assert years == [2018, 2019]


def test_cold_pool_empty_range_404(api_client):
    resp = api_client.get("/v1/cold-pool/observed", params={"start_year": 3000})
    if resp.status_code == 503:
        pytest.skip("cold-pool parquet not fetched")
    assert resp.status_code == 404
