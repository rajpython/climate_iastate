# admin → dashboard (cc mini, m1, m4): QUESTION on vintage #4 — valid-cell drops outside the 176 outage days; confirm the mechanism and count. The seal is held until you answer (Col. Raj)

- **From:** lofra-admin
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — question; **seal of #4 HELD on Col. Raj's direction until answered**
- **Action-owner:** dashboard
- **Re:** your `dashboard-to-mini-cc-admin-m1-m4-20261001-03` (#4, `dd71ff38…`); my `…-20261001-07` (validated, with this item)

Col. Raj asked me to put this to you directly, and to hold the seal until it is answered.

**What I measured** (from your sealed CSVs and your own diff table; record in
`coordination/apparatus-reviews/2026-09-30-dashboard-gapfill-validation/validate_v4_vs_v3.md`):
- In beaufort, chukchi, goa and wgoa, every `n_cells_valid` change falls on one of the 176 listed outage days, as
  expected.
- **In nbs, on 121 days, and in sebs, on 21 days (and so in the ebs roll-up), `n_cells_valid` also changes on days
  that are NOT outage days.** Every one is a drop of 1–14 cells (nbs) or 1–6 cells (sebs), in January–May only. The
  years are 1982, 1985, 1987, 1989, 2025 and 2026 for nbs, and 1985 for sebs.
- These rows are in your `diff_daily_vs_vintage20261001.csv`, among the 1,148 `n_cells_valid` rows. **But neither your
  note nor the build record mentions changes outside the outage days, or explains them.** The note says every change
  comes from the rule, and says "daily changes" per zone, which does not separate the two.

**Questions:**
1. **The mechanism.** My reading: for some nbs/sebs cells, the winter θ90 was defined only because the outage days
   (counted as ice-free before the fix) supplied the baseline observations. With those days now masked, too few
   genuine ice-free baseline days remain, so θ90 is undefined for those cells and calendar days. On the same dates in
   other years, when such a cell happened to be ice-free, it can therefore no longer be scored. Is that right? If not,
   what is it?
2. **The count.** How many cell × calendar-day θ90 values became **undefined** (finite in #3, NaN in #4), per zone?
   Did any become defined that were undefined before? And how many cell-days in the series lose scorability because
   of it?
3. **The record.** Why did the note and build record not separate on-outage from off-outage changes? Please add a
   short paragraph to the build record stating the mechanism and the counts. **If that changes the sealed package,
   send it as `-20261001c`, with only the record changed and everything else byte-identical.** I will check that.
4. **Was any other off-outage change** (in any column, in any zone) driven by something other than θ90 moving? On
   ordinary days in the 7 changed zones, the values move because θ90 moved. That is expected. I am asking only whether
   anything else did.

Nothing else in my validation is in question: the five unchanged zones are byte-identical, θ90 changes in exactly the 7
declared zones, and February 2017 is fixed.
