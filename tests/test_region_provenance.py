"""Provenance guardrail for config/regions.geojson.

Ties every zone boundary to a cited source (config/regions_provenance.json) and asserts the
polygon geometry still matches the documented, ESR-sourced value. Any accidental edit that
moves a boundary — the failure mode that nearly triggered a needless reorg — fails CI here.

Pure/offline: reads the two config files only. No network, no derived artifacts.
See docs/region_provenance.md for the narrative and citations.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOJSON = PROJECT_ROOT / "config" / "regions.geojson"
PROVENANCE = PROJECT_ROOT / "config" / "regions_provenance.json"


def _rings(geom: dict) -> list[list[list[float]]]:
    """All linear rings of a Polygon/MultiPolygon as lists of [lon, lat] vertices."""
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    return [ring for poly in geom["coordinates"] for ring in poly]


def _metrics(geom: dict) -> dict[str, float]:
    """Min/max lon (signed and 0-360) and lat over every vertex of a feature."""
    xs = [x for ring in _rings(geom) for x, _ in ring]
    ys = [y for ring in _rings(geom) for _, y in ring]
    xs360 = [x % 360 for x in xs]
    return {
        "lon_min": min(xs), "lon_max": max(xs),
        "lon_min_360": min(xs360), "lon_max_360": max(xs360),
        "lat_min": min(ys), "lat_max": max(ys),
    }


@pytest.fixture(scope="module")
def geojson() -> dict:
    return json.loads(GEOJSON.read_text())


@pytest.fixture(scope="module")
def provenance() -> dict:
    return json.loads(PROVENANCE.read_text())


def test_every_geojson_feature_has_provenance(geojson, provenance):
    """No zone may exist without a cited provenance entry (and vice versa)."""
    geo_ids = {f["properties"]["id"] for f in geojson["features"]}
    prov_ids = set(provenance["features"])
    assert geo_ids == prov_ids, (
        f"geojson vs provenance id mismatch: "
        f"only in geojson={geo_ids - prov_ids}, only in provenance={prov_ids - geo_ids}"
    )


def test_every_provenance_source_is_defined(provenance):
    """Each feature's cited source key must resolve to a real source with ref+url."""
    sources = provenance["sources"]
    for fid, feat in provenance["features"].items():
        for entry in feat["provenance"]:
            key = entry["source"]
            assert key in sources, f"{fid}: undefined source '{key}'"
            assert sources[key].get("ref") and sources[key].get("url"), f"source '{key}' missing ref/url"


def test_rollups_are_unions_of_declared_members(provenance):
    """Roll-up zones must declare their leaf members; every member must be a real leaf."""
    feats = provenance["features"]
    leaves = {fid for fid, f in feats.items() if f["kind"] == "leaf"}
    for fid, feat in feats.items():
        if feat["kind"] == "rollup":
            members = set(feat.get("members", []))
            assert members and members <= leaves, f"{fid}: bad rollup members {members}"


def test_boundaries_match_documented_values(geojson, provenance):
    """The measured polygon extents must still match the ESR-cited boundary values.

    This is the drift alarm: move any divide in regions.geojson and this fails.
    """
    by_id = {f["properties"]["id"]: f["geometry"] for f in geojson["features"]}
    failures: list[str] = []
    for fid, feat in provenance["features"].items():
        checks = feat.get("checks", [])
        if not checks:
            continue
        m = _metrics(by_id[fid])
        for chk in checks:
            metric, want, tol = chk["metric"], chk["value"], chk["tol"]
            got = m[metric]
            if abs(got - want) > tol:
                failures.append(f"{fid}.{metric}: measured {got:.3f}, documented {want} (±{tol})")
    assert not failures, "region boundary drift vs documented provenance:\n  " + "\n  ".join(failures)
