"""Unit tests for doy_window, compute_mu_theta, and _update_one_day.

All tests use synthetic numpy grids — no ERDDAP, no disk I/O.
"""
from __future__ import annotations

import numpy as np
import pytest

from mhw.climatology.smooth_doy import compute_mu_theta, doy_window
from mhw.states.update_states import (
    StateBuffer,
    _update_one_day,
    active_flag_from_exc,
    finalize_events_grid,
    find_consecutive_runs,
    qualify_mhw_events,
)

# Keyword arguments matching config/climatology.yml defaults
_UPDATE_KWARGS: dict = dict(
    gap_days=2,
    confirm_days=5,
    int_ref="threshold",
    onset_ref="physical_start",
    k_days=3,
    apply_ice=True,
    ice_thresh=0.15,
)


# ---------------------------------------------------------------------------
# doy_window — pure function, 3 tests
# ---------------------------------------------------------------------------

class TestDoyWindow:
    def test_doy1_wraps_back(self):
        """doy_window(1, 5) → 11 items, all in [1,366], includes wrap-around DOY 361–366."""
        result = doy_window(1, 5)
        assert len(result) == 11
        assert all(1 <= d <= 366 for d in result)
        # wrap-around: should include high DOYs near end of year
        assert any(d >= 361 for d in result)

    def test_doy366_wraps_forward(self):
        """doy_window(366, 5) → 11 items, includes DOY 1–5 (forward wrap)."""
        result = doy_window(366, 5)
        assert len(result) == 11
        assert all(1 <= d <= 366 for d in result)
        # wrap-around: should include early DOYs at start of year
        assert any(d <= 5 for d in result)

    def test_doy180_no_wrap(self):
        """doy_window(180, 5) → exactly DOY 175..185, no wrap."""
        result = doy_window(180, 5)
        assert result == list(range(175, 186))
        assert len(result) == 11


# ---------------------------------------------------------------------------
# compute_mu_theta — pure function, 2 tests
# ---------------------------------------------------------------------------

class TestComputeMuTheta:
    def test_known_stack(self):
        """Ones + small noise: mu ≈ nanmean, theta = 90th percentile."""
        rng = np.random.default_rng(42)
        stack = (
            np.ones((30, 4, 5), dtype=np.float32)
            + rng.normal(0, 0.1, (30, 4, 5)).astype(np.float32)
        )
        mu, theta = compute_mu_theta(stack, percentile=90.0)

        assert mu.shape == (4, 5)
        assert theta.shape == (4, 5)
        np.testing.assert_allclose(mu, np.nanmean(stack, axis=0), rtol=1e-5)
        np.testing.assert_allclose(
            theta, np.nanpercentile(stack, 90.0, axis=0), rtol=1e-5
        )

    def test_nan_column_propagates(self):
        """Full-NaN column → NaN output; all-finite columns → finite output."""
        stack = np.ones((10, 2, 2), dtype=np.float32)
        stack[:, 0, 0] = np.nan  # make one column fully NaN

        mu, theta = compute_mu_theta(stack)

        assert np.isnan(mu[0, 0]), "mu of full-NaN column should be NaN"
        assert np.isnan(theta[0, 0]), "theta of full-NaN column should be NaN"
        # remaining cells must be finite
        finite_mu = mu[~np.isnan(mu)]
        assert np.all(np.isfinite(finite_mu))
        finite_theta = theta[~np.isnan(theta)]
        assert np.all(np.isfinite(finite_theta))


# ---------------------------------------------------------------------------
# _update_one_day — core state logic, 7 tests
# ---------------------------------------------------------------------------

class TestUpdateOneDay:
    """Tests use the `tiny_state` fixture (function-scoped → fresh state per test)."""

    @staticmethod
    def _run(sst, ice, state, theta, mu, **extra_kwargs):
        kwargs = {**_UPDATE_KWARGS, **extra_kwargs}
        return _update_one_day(sst, ice, theta, mu, state, **kwargs)

    def test_exceedance_detected(self, tiny_state):
        """1 day sst_above: x > 0, A == 0 (not yet confirmed)."""
        state, theta, mu, sst_above, _, ice_clear, _ = tiny_state
        x, A, D, I, C, O = self._run(sst_above, ice_clear, state, theta, mu)
        assert np.all(x > 0), "exceedance should be positive"
        assert np.all(A == 0), "event not confirmed after only 1 day"

    def test_no_exceedance_below(self, tiny_state):
        """1 day sst_below: x == 0, A == 0."""
        state, theta, mu, _, sst_below, ice_clear, _ = tiny_state
        x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)
        assert np.all(x == 0)
        assert np.all(A == 0)

    def test_confirmation_fires(self, tiny_state):
        """Repeating sst_above for confirm_days → A == 1 on the final call."""
        state, theta, mu, sst_above, _, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        for _ in range(confirm_days):
            x, A, D, I, C, O = self._run(sst_above, ice_clear, state, theta, mu)
        assert np.all(A == 1), "event must be confirmed after 5 consecutive above-threshold days"

    def test_gap_bridged(self, tiny_state):
        """confirm_days above → gap_days below → A still == 1 (gap bridged)."""
        state, theta, mu, sst_above, sst_below, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        gap_days = _UPDATE_KWARGS["gap_days"]

        for _ in range(confirm_days):
            self._run(sst_above, ice_clear, state, theta, mu)

        for _ in range(gap_days):
            x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)

        assert np.all(A == 1), f"A should remain 1 during {gap_days}-day gap"

    def test_gap_closes(self, tiny_state):
        """confirm_days above → gap_days+1 below → A == 0 (gap exceeded)."""
        state, theta, mu, sst_above, sst_below, ice_clear, _ = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]
        gap_days = _UPDATE_KWARGS["gap_days"]

        for _ in range(confirm_days):
            self._run(sst_above, ice_clear, state, theta, mu)

        for _ in range(gap_days + 1):
            x, A, D, I, C, O = self._run(sst_below, ice_clear, state, theta, mu)

        assert np.all(A == 0), "event must close after gap_days+1 sub-threshold days"

    def test_ice_mask_suppresses(self, tiny_state):
        """sst_above but ice_heavy → A == 0, x == 0 (ice mask applied)."""
        state, theta, mu, sst_above, _, _, ice_heavy = tiny_state
        confirm_days = _UPDATE_KWARGS["confirm_days"]

        for _ in range(confirm_days):
            x, A, D, I, C, O = self._run(sst_above, ice_heavy, state, theta, mu)

        assert np.all(x == 0), "ice-covered cells must have zero exceedance"
        assert np.all(A == 0), "ice-covered cells must not confirm"

    def test_nan_sst_no_crash(self, tiny_state):
        """NaN SST: function must not raise; A == 0."""
        state, theta, mu, _, _, ice_clear, _ = tiny_state
        sst_nan = np.full((2, 3), np.nan, dtype=np.float32)
        # Must not raise
        x, A, D, I, C, O = self._run(sst_nan, ice_clear, state, theta, mu)
        assert np.all(A == 0), "NaN SST cells must not produce confirmed events"


# ---------------------------------------------------------------------------
# Hobday-faithful qualification (heatwaveR reference rule) — pure 1-D helpers
# ---------------------------------------------------------------------------

def _b(s: str) -> np.ndarray:
    """Compact bool-series builder: '1' = exceedance day, '0' = below."""
    return np.array([c == "1" for c in s], dtype=bool)


class TestFindConsecutiveRuns:
    def test_empty(self):
        assert find_consecutive_runs(_b("00000")) == []

    def test_single_and_multiple_runs(self):
        # 11100110 → runs at [0,2] and [5,6]
        assert find_consecutive_runs(_b("11100110")) == [(0, 2), (5, 6)]

    def test_edges(self):
        # runs touching both ends
        assert find_consecutive_runs(_b("1")) == [(0, 0)]
        assert find_consecutive_runs(_b("111")) == [(0, 2)]


class TestQualifyMhwEvents:
    def test_five_consecutive_qualifies(self):
        assert qualify_mhw_events(_b("11111")) == [(0, 4)]

    def test_four_consecutive_does_not_qualify(self):
        """A run of 4 is NOT a MHW under Hobday — the core minimum-duration rule."""
        assert qualify_mhw_events(_b("1111")) == []

    def test_bridged_two_exceedance_days_REJECTED(self):
        """THE DEFECT CASE: '1' '0' '0' '1' '0' — the old single-counter rule
        confirmed this (Dtilde reached 5 by counting bridged gap days), but it has
        no 5-consecutive run and MUST NOT qualify under Hobday/heatwaveR."""
        assert qualify_mhw_events(_b("10010")) == []
        assert active_flag_from_exc(_b("10010")).sum() == 0

    def test_merge_across_two_day_gap(self):
        """Two qualifying 5-runs separated by a 2-day gap merge into one event,
        absorbing the gap days."""
        # 11111 00 11111  → one event spanning [0, 11], gap days 5,6 absorbed
        events = qualify_mhw_events(_b("111110011111"))
        assert events == [(0, 11)]
        active = active_flag_from_exc(_b("111110011111"))
        assert active.all()

    def test_gap_of_three_does_not_merge(self):
        """A 3-day gap exceeds max_gap=2 → two separate events, gap days inactive."""
        # 11111 000 11111
        events = qualify_mhw_events(_b("11111000" + "11111"))
        assert events == [(0, 4), (8, 12)]
        active = active_flag_from_exc(_b("11111000" + "11111"))
        assert active[5:8].sum() == 0, "3-day gap must stay inactive"

    def test_isolated_blip_makes_gap_too_large(self):
        """An isolated exceedance blip strictly between two qualifying runs
        (below, blip, below) forces a 3-day gap → the runs do NOT merge, and the
        blip itself is a <5 run so it is never its own event."""
        # 11111 0 1 0 11111 : runs [0,4] and [8,12]; gap = 8-4-1 = 3 > 2
        assert qualify_mhw_events(_b("1111101011111")) == [(0, 4), (8, 12)]

    def test_single_gap_day_merges(self):
        """One below-threshold day between two qualifying runs (gap = 1) merges."""
        # 11111 0 11111 : runs [0,4] and [6,10]; gap = 6-4-1 = 1 <= 2 → merge
        assert qualify_mhw_events(_b("11111011111")) == [(0, 10)]

    def test_short_run_not_between_qualifiers_stays_inactive(self):
        """A 3-day exceedance run standing alone never becomes an event."""
        assert qualify_mhw_events(_b("00011100000")) == []

    def test_max_gap_zero_disables_merging(self):
        events = qualify_mhw_events(_b("111110011111"), max_gap=0)
        assert events == [(0, 4), (7, 11)]

    def test_active_flag_shape_and_values(self):
        exc = _b("0111110011111000")
        active = active_flag_from_exc(exc)
        assert active.shape == exc.shape
        assert active.dtype == bool
        # first event [1,5], 2-day gap [6,7] absorbed, second [8,12] → active [1,12]
        expected = np.zeros(exc.shape, dtype=bool)
        expected[1:13] = True
        np.testing.assert_array_equal(active, expected)


class TestHobdayPaperExamples:
    """The worked examples from Hobday et al. (2016) p.231 — the paper's own
    disambiguation of Table 2. These are the acceptance tests LOFRA-mini cited
    (2026-07-20); pinned here as a regression guard for the qualification rule."""

    @pytest.mark.parametrize("desc,pattern,exp_events,exp_days", [
        # 5 hot, 1 cool, 2 hot -> a 5-day event (trailing sub-5 run discarded)
        ("5hot,1cool,2hot", "11111011", [(0, 4)], 5),
        # converse: 2 hot, 1 cool, 5 hot -> a 5-day event (leading sub-5 discarded)
        ("2hot,1cool,5hot", "11011111", [(3, 7)], 5),
        # 5 hot, 4 cool, 6 hot -> TWO separate events (a 4-day gap is not bridged)
        ("5hot,4cool,6hot", "111110000111111", [(0, 4), (9, 14)], 11),
        # max 2 consecutive -> NOT a marine heatwave
        ("2hot,2cool,1hot", "11001", [], 0),
        # two qualifying runs, 1-day gap -> ONE merged event, gap day absorbed
        ("5hot,1cool,5hot", "11111011111", [(0, 10)], 11),
    ])
    def test_paper_example(self, desc, pattern, exp_events, exp_days):
        exc = np.array([c == "1" for c in pattern], dtype=bool)
        assert qualify_mhw_events(exc, min_duration=5, max_gap=2) == exp_events, desc
        assert int(active_flag_from_exc(exc, min_duration=5, max_gap=2).sum()) == exp_days, desc


class TestFinalizeEventsGrid:
    """The A/D/C/O post-pass used by run_state_engine in consecutive_first mode."""

    @staticmethod
    def _grid(patterns: list[str]):
        """Build (out_x, out_I) of shape (T, 1, n) from '1'/'0' strings.
        x = 1.0 on exceedance days, I = x (flat unit intensity)."""
        T = len(patterns[0])
        n = len(patterns)
        x = np.zeros((T, 1, n), dtype=np.float32)
        for j, p in enumerate(patterns):
            x[:, 0, j] = np.array([c == "1" for c in p], dtype=np.float32)
        return x, x.copy()

    def test_defect_pattern_rejected_merge_accepted(self):
        # cell 0: the old-rule defect '10010...' (must be rejected)
        # cell 1: two 5-runs bridged by a 2-day gap (must be fully active)
        x, I = self._grid(["100100000000", "111110011111"])
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        assert A[:, 0, 0].sum() == 0, "defect pattern must not confirm"
        assert np.all(A[:, 0, 1] == 1), "merged event must be active on all 12 days"

    def test_duration_is_one_based_within_event(self):
        x, I = self._grid(["111110011111"])
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        np.testing.assert_array_equal(
            D[:, 0, 0], np.arange(1, 13, dtype=np.float32)
        )

    def test_cumulative_is_event_running_sum(self):
        """C = Hobday i_cum: running sum of I over the event span (incl. absorbed
        gap days, whose I=0 here), reset between events."""
        x, I = self._grid(["111110011111"])
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        # I = 1 on days 0-4, 0 on gap days 5-6, 1 on days 7-11
        # cumsum over event: 1,2,3,4,5, 5,5, 6,7,8,9,10
        expected = np.array([1,2,3,4,5,5,5,6,7,8,9,10], dtype=np.float32)
        np.testing.assert_array_equal(C[:, 0, 0], expected)

    def test_onset_hobday_start_to_peak(self):
        """Hobday onset = (i_peak - i_start_edge) / ((t_peak - ts) + 0.5),
        i_start_edge = 0.5*(I[ts] + I[ts-1]), placed on the event START day ts."""
        T = 10
        x = np.zeros((T, 1, 1), dtype=np.float32)
        I = np.zeros((T, 1, 1), dtype=np.float32)
        # event on days 1..6 (len 6); intensity ramps 1,2,4,3,2,1 (peak offset 2)
        x[1:7, 0, 0] = 1.0
        I[1:7, 0, 0] = np.array([1, 2, 4, 3, 2, 1], dtype=np.float32)
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        # p=2, i_peak=4, i_start_edge=0.5*(I[1]+I[0])=0.5*(1+0)=0.5
        # O = (4 - 0.5) / (2 + 0.5) = 3.5/2.5 = 1.4  on the START day ts = 1
        assert O[1, 0, 0] == pytest.approx(1.4)
        assert np.count_nonzero(O[:, 0, 0]) == 1
        assert C[6, 0, 0] == pytest.approx(13.0)  # i_cum = 1+2+4+3+2+1

    def test_onset_uses_signed_pre_start_anomaly(self):
        """The day before ts is normally below the seasonal mean (negative relSeas);
        Hobday's i_start_edge must use that signed value, not a 0-clamped one."""
        T = 10
        x = np.zeros((T, 1, 1), dtype=np.float32)
        I = np.zeros((T, 1, 1), dtype=np.float32)
        x[2:8, 0, 0] = 1.0                       # event days 2..7 (len 6)
        I[1, 0, 0] = -1.0                        # day before start: below the mean
        I[2:8, 0, 0] = 2.0                       # flat intensity 2 over the event
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        # p=0, i_peak=2, i_start_edge=0.5*(I[2]+I[1])=0.5*(2+(-1))=0.5
        # O = (2 - 0.5)/(0 + 0.5) = 3.0 on ts=2.  (A 0-clamp would give i_start_edge
        # = 0.5*(2+0)=1.0 → O=2.0, so this asserts the signed value is used.)
        assert O[2, 0, 0] == pytest.approx(3.0)

    def test_onset_truncated_at_series_start_is_zero(self):
        """Event starting at index 0 → onset NA in Hobday → 0 here."""
        x, I = self._grid(["111111000000"])
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        assert O[:, 0, 0].sum() == 0.0

    def test_all_zero_cell_stays_inactive(self):
        x, I = self._grid(["000000000000"])
        A, D, C, O = finalize_events_grid(
            x, I, confirm_days=5, gap_days=2, k_days=3, onset_ref="physical_start",
        )
        assert A.sum() == 0 and D.sum() == 0 and C.sum() == 0 and O.sum() == 0
