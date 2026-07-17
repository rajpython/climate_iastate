"""Unit tests for the pinned forecast-scorings reader (occurrence + onset).

Network-free: reads the vendored, SHA-pinned reference CSVs at ``vendor/forecast-scorings-v2/``
(committed), so these assert directly rather than skip. Values are LOFRA's certified v2 numbers.
"""

import math

import pytest

from mhw.forecast import scorings as sc

pytestmark = pytest.mark.skipif(
    not (sc.SCORINGS_DIR / "occurrence_probabilistic_skill_v2.csv").exists(),
    reason="vendored forecast-scorings-v2 reference not present",
)


def test_occurrence_skill_damped_zone_values():
    s = sc.occurrence_skill("egoa", lead=1)
    assert s is not None
    assert math.isclose(s["bss_clim"], 0.5843, abs_tol=1e-3)
    assert math.isclose(s["auc"], 0.9343, abs_tol=1e-3)
    assert s["n"] == 295


def test_occurrence_skill_missing_zone_is_none():
    assert sc.occurrence_skill("not_a_zone", lead=1) is None


def test_occurrence_resolvable_l1_true_l3_negative_false():
    # egoa keeps positive skill through L3; ai_central crosses <=0 by L3 → "watch".
    assert sc.occurrence_resolvable("egoa", lead=1) is True
    assert sc.occurrence_resolvable("ai_central", lead=3) is False


def test_occurrence_reliability_bins_sorted_and_shaped():
    rb = sc.occurrence_reliability("sebs", lead=1)
    assert list(rb.columns) == ["bin", "n", "p_mean", "o_freq"]
    assert len(rb) > 0
    assert list(rb["bin"]) == sorted(rb["bin"])
    # frequencies live in [0, 1]
    assert rb["p_mean"].between(0, 1).all()
    assert rb["o_freq"].between(0, 1).all()


def test_onset_deployed_watch_is_lim_k12_with_persistence_anchor():
    watch = sc.onset_discrimination(lead=1)  # default forecaster = lim_k12
    anchor = sc.onset_discrimination(lead=1, forecaster="persistence")
    assert watch is not None and anchor is not None
    assert math.isclose(watch["onset_auc"], 0.759, abs_tol=1e-3)
    assert math.isclose(watch["sedi"], 0.583, abs_tol=1e-3)
    # The honesty story: the watch discriminates but sits just above persistence, not resolvably past it.
    assert math.isclose(anchor["onset_auc"], 0.665, abs_tol=1e-3)
    assert watch["onset_auc"] > anchor["onset_auc"]
