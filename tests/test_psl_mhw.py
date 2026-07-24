"""Network-free tests for the NOAA PSL marine-heatwave replication layer.

Exercises the pure helpers: the conditional-download decision, the 0–360
polygon wrap + fractional rasterization (the Aleutian-strip regression guard),
the NaN-aware zonal mean, the observed-MHW flag, and the SEDI transform. The
artifact-dependent bits (the built cubes/parquets) are only checked when they
exist, mirroring tests/test_aggregates.py.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Polygon, box

from mhw.fetch.psl_mhw import need_download
from mhw.forecast.psl_mhw import mhw_flags, sedi_from_counts, zonal_mean_cube
from mhw.regions.nmme_masks import fractional_mask, poly_to_360

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DERIVED = PROJECT_ROOT / "data" / "derived" / "psl_mhw"


# --------------------------------------------------------------------------- #
# Conditional download
# --------------------------------------------------------------------------- #

def test_need_download_when_no_local():
    assert need_download({"last_modified": "x", "length": 1}, {}) is True


def test_need_download_false_when_last_modified_matches():
    r = {"last_modified": "Mon, 14 Jul 2026 17:08:00 GMT", "length": 100}
    assert need_download(r, dict(r)) is False


def test_need_download_true_when_last_modified_changes():
    r = {"last_modified": "Mon, 14 Jul 2026 17:08:00 GMT", "length": 100}
    local = {"last_modified": "Sun, 01 Jun 2026 00:00:00 GMT", "length": 100}
    assert need_download(r, local) is True


def test_need_download_falls_back_to_length():
    r = {"last_modified": None, "length": 200}
    assert need_download(r, {"last_modified": None, "length": 100}) is True
    assert need_download(r, {"last_modified": None, "length": 200}) is False


# --------------------------------------------------------------------------- #
# Geometry: 0–360 wrap + fractional coverage
# --------------------------------------------------------------------------- #

def test_poly_to_360_wraps_negative_lons():
    # A box straddling the dateline (−175 .. 175 is the *long* way; the short way
    # crosses 180). After the wrap every vertex is in [0, 360).
    poly = box(-175.0, 50.0, 175.0, 55.0)
    wrapped = poly_to_360(poly)
    xs = np.array(wrapped.exterior.coords)[:, 0]
    assert xs.min() >= 0.0 and xs.max() < 360.0


def test_poly_to_360_makes_dateline_zone_contiguous():
    # Two halves split at ±180 become adjacent at 180 after the wrap and dissolve
    # into one polygon spanning ~178 .. 182.
    west = Polygon([(178, 50), (180, 50), (180, 55), (178, 55)])
    east = Polygon([(-180, 50), (-178, 50), (-178, 55), (-180, 55)])
    merged = poly_to_360(west.union(east))
    minx, _, maxx, _ = merged.bounds
    assert minx <= 178.5 and maxx >= 181.5
    assert merged.geom_type == "Polygon"   # not MultiPolygon


def test_fractional_mask_half_cell():
    lats = np.array([50.0, 51.0])
    lons = np.array([200.0, 201.0])
    # Polygon covers the western half of the cell centred at (200, 50).
    poly = box(199.5, 49.5, 200.0, 50.5)
    cov = fractional_mask(poly, lats, lons)
    assert cov[0, 0] == pytest.approx(0.5, abs=1e-4)
    assert cov[1, 1] == pytest.approx(0.0)


def test_fractional_mask_thin_strip_survives():
    # A strip far narrower than a 1° cell (the Aleutian case): a binary centre
    # test would drop it; fractional coverage keeps a small positive weight.
    lats = np.array([52.0])
    lons = np.array([180.0])
    strip = box(179.5, 51.9, 180.5, 52.1)   # 0.2° tall, spans the cell in lon
    cov = fractional_mask(strip, lats, lons)
    assert 0.0 < cov[0, 0] < 0.5
    assert cov[0, 0] == pytest.approx(0.2, abs=1e-4)


# --------------------------------------------------------------------------- #
# NaN-aware zonal mean
# --------------------------------------------------------------------------- #

def test_zonal_mean_is_weighted_mean():
    prob = np.array([[0.0, 1.0], [1.0, 1.0]])
    weight = np.array([[1.0, 1.0], [1.0, 1.0]])
    assert zonal_mean_cube(prob, weight) == pytest.approx(0.75)


def test_zonal_mean_excludes_nan_cells():
    # A NaN (land) cell must be dropped and the weights renormalized — NOT
    # counted as probability zero (that would bias a coastal zone low).
    prob = np.array([[np.nan, 1.0], [1.0, 1.0]])
    weight = np.ones((2, 2))
    assert zonal_mean_cube(prob, weight) == pytest.approx(1.0)


def test_zonal_mean_leading_dims():
    cube = np.stack([np.full((2, 2), 0.2), np.full((2, 2), 0.8)])   # (2, 2, 2)
    out = zonal_mean_cube(cube, np.ones((2, 2)))
    assert out.shape == (2,)
    assert np.allclose(out, [0.2, 0.8])


def test_zonal_mean_all_nan_is_nan():
    assert np.isnan(zonal_mean_cube(np.full((2, 2), np.nan), np.ones((2, 2))))


# --------------------------------------------------------------------------- #
# Observed MHW flag
# --------------------------------------------------------------------------- #

def test_mhw_flags_thresholds_by_calendar_month():
    anom = np.array([[[2.0]], [[0.1]]])           # (time=2, 1, 1)
    q90 = np.zeros((12, 1, 1))
    q90[0] = 1.0                                  # January threshold
    q90[5] = 1.0                                  # June threshold
    flags = mhw_flags(anom, q90, months=np.array([1, 6]))
    assert flags[0, 0, 0] == 1.0                  # 2.0 > Jan q90 1.0
    assert flags[1, 0, 0] == 0.0                  # 0.1 < Jun q90 1.0


def test_mhw_flags_nan_anom_is_nan():
    anom = np.array([[[np.nan]]])
    q90 = np.zeros((12, 1, 1))
    assert np.isnan(mhw_flags(anom, q90, months=np.array([1]))[0, 0, 0])


# --------------------------------------------------------------------------- #
# SEDI
# --------------------------------------------------------------------------- #

def test_sedi_perfect_forecast_is_one():
    # All hits and correct negatives, no misses/false alarms → H=1, F=0. The
    # limit of SEDI as F→0, H→1 is 1; with a tiny guard it approaches 1.
    val = sedi_from_counts(np.array(99.0), np.array(1.0), np.array(1.0), np.array(99.0))
    assert val == pytest.approx(1.0, abs=0.15)


def test_sedi_no_skill_near_zero():
    # Independent forecast: H == F → numerator 0 → SEDI 0.
    val = sedi_from_counts(np.array(10.0), np.array(10.0), np.array(10.0), np.array(10.0))
    assert val == pytest.approx(0.0, abs=1e-9)


def test_sedi_degenerate_rate_is_nan():
    # H == 1 (no misses) → guarded to NaN.
    assert np.isnan(sedi_from_counts(np.array(5.0), np.array(1.0), np.array(0.0), np.array(5.0)))


# --------------------------------------------------------------------------- #
# Built artifacts (only when present — skip otherwise)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("flavor", ["trend", "detrend"])
def test_zone_series_schema(flavor):
    p = DERIVED / f"zone_series_{flavor}.parquet"
    if not p.exists():
        pytest.skip(f"{p.name} not built (run mhw-build-psl-mhw)")
    import pandas as pd
    df = pd.read_parquet(p)
    assert {"zone", "init_time", "lead_months", "prob", "flavor"} <= set(df.columns)
    finite = df["prob"].dropna()
    assert ((finite >= 0.0) & (finite <= 1.0)).all()
