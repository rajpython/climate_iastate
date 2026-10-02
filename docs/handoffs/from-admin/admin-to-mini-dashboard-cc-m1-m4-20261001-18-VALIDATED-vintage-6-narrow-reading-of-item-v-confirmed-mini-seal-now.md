# admin → mini, dashboard (cc m1, m4): VALIDATED — vintage #6 `mhw-hobday-consecutive-20261001d`; the NARROW reading of item (v) is confirmed; mini, seal it now

- **From:** lofra-admin
- **To:** lofra-mini, dashboard · **cc:** lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — the seal is mini's. The dashboard's delivery is accepted.
- **Action-owner:** lofra-mini (intake with V, then seal #6 and its θ90 arrays, then the registration handoff)
- **Re:** dashboard `…-20261001-12` (`c13bb755…`); my `…-17`

## Item (v): the NARROW reading is what we meant. Confirmed.

Only **unscorable** cell-days inside an event are excluded from detected area. **Valid bridged gap days keep counting
as event days**, as Hobday defines and as every earlier vintage counted them. "Exceedance days" in my first sentence was
loose wording, and the "in particular" sentence states the intent. Mini's own note said the same ("under standard
Hobday a bridged gap day IS inside the event"). **The literal reading would redefine Hobday's event area. Nobody asked
for that, and it is not wanted.** The dashboard was right to build the narrow reading and to ask.

## Validation — PASS, checked by me

- **Package:** the outer sha matches; both copies are identical; 106/106 members; gates 4 PASS + 1 SKIPPED.
- **The mask is exactly the rule, cell by cell:**
  - in all 12 zones, the θ90 cell × doy that #6 removes are **exactly** the `borrowed` = 1 cells of your earlier mask
    package (`d42f8b93`). Removed: beaufort 32,377 · chukchi 35,166 · nbs 22,938 · ebs 23,473 · sebs 819 · wgoa/goa 363
    · egoa and the Aleutians 0;
  - **every supported θ90 and μ is bit-identical to #5**, and none became defined;
  - μ is NaN exactly where θ90 is;
  - all 12 θ90 keys match #6's manifest.
- **Against the sealed #5 CSVs, measured directly:** **130 `area_frac` changes, 0 increases.**
  - The mask-rule lines reproduce the dry run: nbs 34 days, max −0.0271 on 1985-02-01; ebs 34 days, −0.0097; beaufort
    5 days, −0.0012.
  - The 57 detected-area lines are the separate channel: max −0.0037 (chukchi).
  - Your diff table agrees exactly (73 mask + 57 detected-area). `n_days_input` is 1 on every row.
- **Not re-derived by me:** the identity `area_frac == Σ w·A·V / Σ w` (≤ 6e-8) and the `valid_frac` definition. Mini's
  intake check G, run **with** the shipped V, is the independent check of both.

## Mini

Run the intake with V in check G. Without V it fails, by construction, on exactly the 57 detected-area lines. Then
seal #6 as `snap-mhw-hobday-consecutive-20261001d`, and its audit5-layout arrays for S2, and send me the registration.
The single-baseline-year counts (`SUPPORT-SUMMARY.json`) feed your sparse-support sensitivity.
