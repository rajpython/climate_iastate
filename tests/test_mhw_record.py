"""The board's heatwave record (vintage #7, D1): day rule, month rule, map rule and record equality.

Pure-helper tests run on small in-memory frames (network-free). Tests against the staged record
``data/record/mhw-d1`` skip when it has not been staged (``scripts/stage_d1_record.py``).
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

from mhw import record
from mhw.states.risk import LEVEL_INCOMPLETE, compute_risk_table

ZONES = ["ebs", "sebs", "nbs", "goa", "wgoa", "egoa", "ai", "ai_west", "ai_central", "ai_east",
         "chukchi", "beaufort"]


# ---------------------------------------------------------------------------
# Synthetic frames
# ---------------------------------------------------------------------------
def _frames(area, absent=0.0, sst=0.0, unk_ice=0.0, thr=0.0, ice=0.0, status="partially_scorable",
            start="2016-04-01"):
    n = len(area)
    dates = pd.date_range(start, periods=n, freq="D")
    bc = lambda v: np.broadcast_to(np.asarray(v, dtype=float), n).copy()  # noqa: E731
    agg = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "area_frac": np.asarray(area, "float32"),
                        "Ibar": np.ones(n, "float32"), "Dbar": np.ones(n, "float32"),
                        "Cbar": np.ones(n, "float32"), "Obar": np.zeros(n, "float32")})
    cov = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "share_absent_input": bc(absent),
                        "share_missing_sst": bc(sst), "share_unknown_ice": bc(unk_ice),
                        "share_missing_threshold": bc(thr), "share_observed_masked_ice": bc(ice),
                        "share_scorable": 1 - bc(absent) - bc(sst) - bc(unk_ice) - bc(thr) - bc(ice),
                        "share_unknown_run_or_regional": bc(0.0), "share_unknown_outage": bc(unk_ice),
                        "status": np.broadcast_to(np.asarray(status, dtype=object), n).copy()})
    return agg, cov


# ---------------------------------------------------------------------------
# Day rule
# ---------------------------------------------------------------------------
def test_wholly_unscorable_high_unknown_is_a_gap_never_zero():
    agg, cov = _frames([0.0, 0.0], unk_ice=[1.0, 0.3], status=["wholly_unscorable", "partially_scorable"])
    d = record.classify_days(agg, cov)
    assert d.loc[0, "hatched"] and d.loc[0, "gap"] and np.isnan(d.loc[0, "area_plot"])
    assert d.loc[0, "label"] == record.LABEL_INCOMPLETE
    # partially scorable but > 25 % unknown: hatched, drawn as computed, still not eligible
    assert d.loc[1, "hatched"] and not d.loc[1, "gap"] and not d.loc[1, "eligible"]


def test_ice_covered_wholly_unscorable_low_unknown_is_a_real_zero():
    agg, cov = _frames([0.0], sst=0.01, ice=0.99, status="wholly_unscorable")
    d = record.classify_days(agg, cov)
    assert d.loc[0, "eligible"] and not d.loc[0, "hatched"] and not d.loc[0, "gap"]
    assert d.loc[0, "area_plot"] == 0.0
    assert d.loc[0, "label"] == record.LABEL_ICE


def test_boundary_exactly_quarter_unknown_is_eligible():
    agg, cov = _frames([0.1, 0.1], unk_ice=[0.25, 0.2500001])
    d = record.classify_days(agg, cov)
    assert d["eligible"].tolist() == [True, False]


def test_partial_zero_label_uses_the_zone_floor():
    # floor = min missing SST = 0.02; a zero day at the floor is a plain zero, above it is "assessed area"
    agg, cov = _frames([0.0, 0.0, 0.3], sst=[0.02, 0.02, 0.02], unk_ice=[0.0, 0.1, 0.1])
    d = record.classify_days(agg, cov)
    assert d.attrs["floor"] == pytest.approx(0.02)
    assert d["label"].tolist() == [record.LABEL_NONE, record.LABEL_NONE_ASSESSED, record.LABEL_DETECTED]
    assert d["coverage_reduced"].tolist() == [False, True, True]


def test_absent_input_is_a_gap():
    agg, cov = _frames([np.nan], absent=1.0, status="absent_input")
    d = record.classify_days(agg, cov)
    assert d.loc[0, "gap"] and not d.loc[0, "eligible"] and d.loc[0, "label"] == record.LABEL_NO_INPUT


def test_missing_sidecar_date_refuses():
    agg, cov = _frames([0.1, 0.1])
    with pytest.raises(ValueError):
        record.classify_days(agg, cov.iloc[:1])


# ---------------------------------------------------------------------------
# Month rule (ADDENDUM-02)
# ---------------------------------------------------------------------------
def _month(rejected_idx):
    unk = np.zeros(30)
    unk[list(rejected_idx)] = 0.5
    agg, cov = _frames(np.full(30, 0.2), unk_ice=unk, start="2016-06-01")
    return record.monthly_summary(record.classify_days(agg, cov), area_thresh=0.05).iloc[0]


def test_month_missing_with_eleven_rejected_days():
    m = _month(range(0, 22, 2))          # 11 rejected, none consecutive
    assert m["n_rejected"] == 11 and m["max_consec_rejected"] == 1 and m["missing"]
    assert np.isnan(m["area_mean"]) and np.isnan(m["event_days"])


def test_month_missing_with_five_consecutive_rejected_days():
    m = _month(range(10, 15))
    assert m["n_rejected"] == 5 and m["missing"]


def test_month_kept_with_ten_scattered_rejected_days_mean_over_eligible_only():
    m = _month([0, 2, 4, 6, 9, 12, 15, 18, 21, 24])  # 10 rejected, longest run 1
    assert not m["missing"] and m["n_eligible"] == 20
    assert m["area_mean"] == pytest.approx(0.2, abs=1e-7)   # rejected days never counted as zero
    assert m["event_days"] == 20


def test_reduced_zero_month_flag():
    agg, cov = _frames(np.zeros(30), sst=0.01, unk_ice=np.r_[0.1, np.zeros(29)], start="2016-06-01")
    m = record.monthly_summary(record.classify_days(agg, cov), area_thresh=0.05).iloc[0]
    assert not m["missing"] and m["area_mean"] == 0 and m["has_reduced_zero"]


# ---------------------------------------------------------------------------
# Map rule
# ---------------------------------------------------------------------------
def test_map_shows_only_detected_retained_scorable_cells():
    A = np.array([[1, 1, 1, 0]])
    V = np.array([[1, 0, 1, 1]])
    R = np.array([[1, 1, 0, 1]])
    reason = np.array([[5, 2, 5, 7]])
    inten = np.array([[2.0, 3.0, 4.0, 0.0]])
    vals, cls = record.map_cells("I", inten, A, V, R, reason)
    assert vals[0, 0] == 2.0
    assert np.isnan(vals[0, 1])              # unscorable (observed ice): never coloured
    assert np.isnan(vals[0, 2])              # excluded cell (R = 0): never coloured
    assert cls.tolist() == [[record.CELL_SCORED, record.CELL_ICE, record.CELL_HIDDEN, record.CELL_SCORED]]
    a, _ = record.map_cells("A", A, A, V, R, reason)
    assert np.nansum(a) == 1.0               # A·V·R


def test_map_exceedance_needs_scorable_retained():
    x = np.array([[0.5, 0.5, 0.5]])
    vals, cls = record.map_cells("x", x, np.zeros((1, 3)), np.array([[1, 0, 1]]), np.array([[1, 1, 0]]),
                                 np.array([[5, 3, 5]]))
    assert vals[0, 0] == 0.5 and np.isnan(vals[0, 1]) and np.isnan(vals[0, 2])
    assert cls[0, 1] == record.CELL_UNKNOWN


# ---------------------------------------------------------------------------
# Risk on eligible days only
# ---------------------------------------------------------------------------
def test_risk_skips_ineligible_days():
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=4).date,
                       "area_frac": [0.1, 0.2, 0.0, 0.4], "Ibar": [1, 2, 0, 4.0],
                       "Dbar": [1, 2, 0, 4.0], "Cbar": [1, 2, 0, 4.0]})
    elig = np.array([True, True, False, True])
    r = compute_risk_table(df, eligible=elig)
    assert np.isnan(r.loc[2, "composite_risk"]) and r.loc[2, "risk_level"] == LEVEL_INCOMPLETE
    assert r.loc[3, "area_frac_pct"] == pytest.approx(100.0)   # reference excludes the rejected day


# ---------------------------------------------------------------------------
# The staged record (skips when not staged)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def staged():
    if not (record.agg_dir().exists() and record.coverage_dir().exists()):
        pytest.skip(f"D1 record not staged at {record.record_dir()}")
    return {z: record.load_zone(z) for z in ZONES}


EXPECTED_HATCHED = {"sebs": 171, "nbs": 171, "ebs": 171, "chukchi": 225, "beaufort": 255,
                    "wgoa": 0, "egoa": 0, "ai_east": 0}
EXPECTED_ICE_WHOLLY = {"nbs": 634, "chukchi": 7164, "beaufort": 11170}


def test_record_period_and_rows(staged):
    for z, d in staged.items():
        assert d["date"].min() == pd.Timestamp("1982-01-01"), z
        assert d["date"].max() == pd.Timestamp(record.CERTIFIED_THROUGH), z
        assert len(d) == 16314 and d["date"].is_unique, z


def test_record_hatch_counts(staged):
    for z, n in EXPECTED_HATCHED.items():
        assert int(staged[z]["hatched"].sum()) == n, z


def test_record_ice_covered_wholly_unscorable_counts(staged):
    for z, n in EXPECTED_ICE_WHOLLY.items():
        d = staged[z]
        got = int((d["status"].eq("wholly_unscorable") & d["eligible"]).sum())
        assert got == n, z
        assert (d.loc[d["status"].eq("wholly_unscorable") & d["eligible"], "label"] == record.LABEL_ICE).all(), z


def test_record_no_gap_day_plots_as_zero(staged):
    for z, d in staged.items():
        assert d.loc[d["gap"], "area_plot"].isna().all(), z
        assert not (d["status"].eq("wholly_unscorable") & d["hatched"] & d["area_plot"].notna()).any(), z


def test_record_area_equals_release_products(staged):
    """Board area == release products/daily area_frac (float32), every zone, every date."""
    rel = record.PROJECT_ROOT / "data" / "derived" / "releases" / record.RECORD_ID / "payload" / "products" / "daily"
    if not rel.exists():
        pytest.skip("release products not on disk")
    for z, d in staged.items():
        p = pd.read_csv(rel / f"predictand_daily_{z}.csv")
        assert (pd.to_datetime(p["date"]).to_numpy() == d["date"].to_numpy()).all(), z
        a = d["area_frac"].to_numpy("float32")
        b = p["area_frac"].to_numpy("float32")
        assert np.array_equal(a, b, equal_nan=True), z


def test_record_coverage_partitions_to_one(staged):
    for z, d in staged.items():
        cov = pd.read_csv(record.coverage_path(z))
        total = record.unknown_share(cov) + cov["share_scorable"] + cov["share_observed_masked_ice"]
        assert np.abs(total - 1).max() < 1e-12, z


def test_record_monthly_equals_independent_computation(staged):
    """Board monthly series == a direct computation from coverage_daily + daily areas (frozen rule)."""
    for z in ZONES:
        cov = pd.read_csv(record.coverage_path(z))
        agg = pd.read_parquet(record.agg_path(z))
        U = (cov["share_absent_input"] + cov["share_missing_sst"] + cov["share_unknown_ice"]
             + cov["share_missing_threshold"]).to_numpy()
        rej = U > 0.25
        area = agg["area_frac"].to_numpy("float32")
        months = pd.to_datetime(cov["date"]).dt.to_period("M").to_numpy()
        exp = {}
        for m in pd.unique(months):
            k = months == m
            r = rej[k]
            run = best = 0
            for f in r:
                run = run + 1 if f else 0
                best = max(best, run)
            miss = r.sum() >= 11 or best >= 5
            exp[m] = np.nan if miss else float(area[k][~r].mean())
        got = record.monthly_summary(staged[z], area_thresh=0.05).set_index("month")["area_mean"]
        e = pd.Series(exp)
        assert got.index.equals(e.index), z
        assert np.allclose(got.to_numpy(float), e.to_numpy(float), equal_nan=True, rtol=0, atol=1e-7), z


def test_staged_panel_matches_m4_frozen_hashes():
    d = record.panel2016_dir()
    if not d.exists():
        pytest.skip("2016 panel not staged")
    want = {"sebs_2016_panel_daily.csv": "92b8b13f36c861c42654c44822788fbefa29fa1869b229295057002b44456f72",
            "sebs_2016_panel_history_overlap.csv":
                "db97048e260f3d0877796748eed175793ac2bbad640f175b30c25d621231f913"}
    for name, h in want.items():
        assert hashlib.sha256((d / name).read_bytes()).hexdigest() == h, name
    gap = pd.read_csv(d / "sebs_2016_panel_daily.csv").query("gap_day")
    assert len(gap) == 74
    assert gap["oec_fills_area_frac"].mean() == pytest.approx(0.2467, abs=5e-4)
    assert gap["est_fills_area_frac"].mean() == pytest.approx(0.576, abs=5e-4)
    assert gap["cov_fills_unresolved"].mean() == pytest.approx(0.062, abs=5e-4)
