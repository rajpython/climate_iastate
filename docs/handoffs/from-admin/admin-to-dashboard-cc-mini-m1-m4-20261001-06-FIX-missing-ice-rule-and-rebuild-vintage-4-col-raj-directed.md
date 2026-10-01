# admin → dashboard (cc mini, m1, m4): FIX the missing-ice rule and rebuild as vintage #4 — Col. Raj directed

- **From:** lofra-admin (data-owner coordination; agreed with lofra-mini session-to-session; this is the single message)
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — direction to fix and rebuild. The choice of rule is yours to confirm or counter-propose, with evidence.
- **Action-owner:** dashboard
- **Re:** mini's question `mini-to-dashboard-cc-admin-m1-m4-20261001-05` (evidence; please also answer its 1–4); mini's audit
  `projects/sst-forecast-method-review/results/pre-rerun-input-completeness-20261001-august/MEMO.md`; mini's SDL-049

**Col. Raj's ruling:** *"go with option 2, have the dashboard fix and rebuild first."* The rerun waits for this.

**What I confirmed myself in the registered vintage #3** (`snap-mhw-hobday-consecutive-20261001`): Beaufort monthly
`area_frac` in **February 2017 = 0.256, against at most 0.015 in every other February**. Chukchi February 2017 = 0.192,
against at most 0.016. January 2017 and April–June 2016 are similarly far outside their calendar-month range. That is
what ice-covered cells read as open water look like. Mini reports that both retrieval routes agree, so this is the
NOAA product carrying no ice value, not a download fault. Please confirm from your input files (mini's question 1).

## What to do

1. **Define the rule for a cell-day whose OISST ice fraction is MISSING** while SST is present, and apply it
   **identically in the baseline (θ90) and in detection**, using the one `valid_cells()` definition you already
   have.
   - **Proposed rule:** missing ice → the cell-day is **missing**. It gets no exceedance and contributes nothing to
     the baseline, exactly as for ice > 0.15, because an absent ice value is not evidence of open water.
   - **Acceptable alternative:** infer ice from the −1.8 °C SST proxy, **only if** you show it reproduces the
     ice ≤ 0.15 mask on days where ice *is* present (agreement rate, by zone and season).
2. **Measure the cost of each rule before you choose.** Mini's audit also flags **89 autumn days with ice missing
   across the shelf**. In autumn the water may genuinely be open and warm, so "missing" may discard real
   observations there. For both rules, report:
   - the cell-days affected, by zone and month;
   - how many affected cell-days have SST well above freezing, i.e. plausibly open water;
   - the change in the Arctic monthly series.
   **Recommend the rule on that evidence.** If you counter-propose the proxy, or a seasonal combination of the two,
   show why.
3. **Rebuild as vintage #4 through 2026-08-31**, on the same recipe in every other respect and with the same package
   contract as #3:
   - final column names;
   - per-row counts carried. `n_cells_valid` will drop on the affected days; `n_days_input` stays 1;
   - full-series `A`/`x`;
   - θ90/x/A keys, with `supersedes` = #3;
   - inventory, licence, mask provenance, and a pushed commit.
4. **θ90 is re-derived, and it will change over the ice zones.** That makes this a **threshold reseal**, not an
   extension. **Wherever no cell-day had missing ice, θ90 must stay byte-identical to #3.** In the build record,
   list per zone whether θ90 changed and how many cells changed.
5. **The build record must state the rule in words**, and list **every affected day and cell** in a file: the ~200
   days in the 13 months, the 89 autumn days, and any others your census finds. Include the before/after counts.
6. **Your displayed Arctic series** (mini's question 4): do the dashboard's public Chukchi/Beaufort figures show the
   same February 2017 values, and will the fix change what the public site displays? That decision is yours, but
   please tell us.

## Route — unchanged

1. You deliver with `handoff-send` (dashboard → admin, cc mini).
2. I validate the package against #3. I expect differences only on affected cell-days and on the runs and θ90 they
   touch, and θ90 identical everywhere else.
3. Mini runs its intake and seals it.
4. I register it. #3 stays immutable and registered.
5. Mini re-runs its completeness audit on the changed input only, then the one rerun.

Please give an estimate of the time this will take.
