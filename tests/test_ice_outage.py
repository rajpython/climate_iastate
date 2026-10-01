"""mhw.climatology.ice_outage -- pure helpers, network- and disk-free."""
from datetime import date

import numpy as np

from mhw.climatology.ice_outage import (
    SST_OPEN_WATER,
    effective_field,
    interpolated_ice,
    outage_days_for,
    runs,
    substitute,
)
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


def test_interpolation_is_linear_and_blank_counts_as_zero():
    before = np.array([[1.0, np.nan]], np.float32)
    after = np.array([[0.0, 0.8]], np.float32)
    out = interpolated_ice(before, after, 0.25)
    assert np.allclose(out, [[0.75, 0.2]])


def test_warm_water_is_open_whatever_the_interpolation_says():
    before = after = np.array([[0.9, 0.9]], np.float32)
    sst = np.array([[-1.7, SST_OPEN_WATER + 0.5]], np.float32)   # frozen | melted during the outage
    assert effective_field(before, after, 0.5, sst).tolist() == [[np.float32(0.9), 0.0]]


def test_substitute_fills_blank_cells_only_and_only_on_outage_days():
    ice = np.full((2, 1, 2), np.nan, np.float32)
    ice[1, 0, 1] = 0.05                       # an observed value on the outage day is kept
    eff = {date(2017, 2, 2): np.array([[0.9, 0.9]], np.float32)}
    out = substitute(ice, [date(2017, 2, 1), date(2017, 2, 2)], eff)
    assert np.isnan(out[0]).all()             # not an outage day: untouched
    assert out[1].tolist() == [[np.float32(0.9), np.float32(0.05)]]
    assert np.isnan(ice[1, 0, 0])             # input not mutated


def test_the_defect_and_the_fix_through_the_engine_validity_rule():
    """Frozen water with a BLANK ice field is valid under the old reading (the defect); with the
    outage substitution it is masked like any ice-covered cell, while warm open water stays valid."""
    sst = np.array([[-1.7, 4.0]], np.float32)     # ice-covered cell, melted cell
    theta = np.array([[-1.75, 3.0]], np.float32)
    blank = np.full((1, 2), np.nan, np.float32)
    assert valid_cells(sst, blank, theta, apply_ice=True, ice_thresh=0.15).tolist() == [[True, True]]
    icy = np.array([[0.95, 0.95]], np.float32)
    eff = effective_field(icy, icy, 0.5, sst)
    fixed = substitute(blank[None], [date(2017, 2, 1)], {date(2017, 2, 1): eff})[0]
    assert valid_cells(sst, fixed, theta, apply_ice=True, ice_thresh=0.15).tolist() == [[False, True]]
