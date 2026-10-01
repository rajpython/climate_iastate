"""mhw.climatology.ice_outage -- pure helpers, network- and disk-free."""
from datetime import date

import numpy as np

from mhw.climatology.ice_outage import bracket_ice, outage_days_for, runs, substitute
from mhw.states.update_states import valid_cells

DOC = {"global": {"days": ["2017-02-01", "2017-02-02", "2017-02-04"]},
       "regional": [{"days": ["2024-04-22"], "zones": ["beaufort"]}]}


def test_outage_days_global_plus_regional_scope():
    assert date(2024, 4, 22) in outage_days_for(DOC, "beaufort")
    assert date(2024, 4, 22) not in outage_days_for(DOC, "egoa")
    assert date(2017, 2, 1) in outage_days_for(DOC, "egoa")


def test_runs_groups_consecutive_days():
    r = runs(outage_days_for(DOC, "egoa"))
    assert r == [(date(2017, 2, 1), date(2017, 2, 2)), (date(2017, 2, 4), date(2017, 2, 4))]


def test_bracket_ice_takes_the_larger_side_and_blank_is_zero():
    before = np.array([[0.9, np.nan, np.nan, 0.10]], np.float32)
    after = np.array([[np.nan, 0.8, np.nan, 0.12]], np.float32)
    assert bracket_ice(before, after).tolist() == [[np.float32(0.9), np.float32(0.8), 0.0, np.float32(0.12)]]


def test_substitute_fills_blank_cells_only_and_only_on_outage_days():
    ice = np.full((2, 1, 2), np.nan, np.float32)
    ice[1, 0, 1] = 0.05                       # an observed value on the outage day is kept
    eff = {date(2017, 2, 2): np.array([[0.9, 0.9]], np.float32)}
    out = substitute(ice, [date(2017, 2, 1), date(2017, 2, 2)], eff)
    assert np.isnan(out[0]).all()             # not an outage day: untouched
    assert out[1].tolist() == [[np.float32(0.9), np.float32(0.05)]]
    assert np.isnan(ice[1, 0, 0])             # input not mutated


def test_the_defect_and_the_fix_through_the_engine_validity_rule():
    """Frozen water with a BLANK ice field is valid under the old reading (the defect);
    with the bracket substitution it is masked like any ice-covered cell."""
    sst = np.array([[-1.7, 4.0]], np.float32)     # ice-covered cell, open-water cell
    theta = np.array([[-1.75, 3.0]], np.float32)
    blank = np.full((1, 2), np.nan, np.float32)
    assert valid_cells(sst, blank, theta, apply_ice=True, ice_thresh=0.15).tolist() == [[True, True]]
    eff = bracket_ice(np.array([[0.95, np.nan]], np.float32), np.array([[0.97, np.nan]], np.float32))
    fixed = substitute(blank[None], [date(2017, 2, 1)], {date(2017, 2, 1): eff})[0]
    assert valid_cells(sst, fixed, theta, apply_ice=True, ice_thresh=0.15).tolist() == [[False, True]]
