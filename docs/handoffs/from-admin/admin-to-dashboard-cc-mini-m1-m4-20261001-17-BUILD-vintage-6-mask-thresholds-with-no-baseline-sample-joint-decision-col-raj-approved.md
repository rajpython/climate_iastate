# admin → dashboard (cc mini, m1, m4): BUILD vintage #6 — mask θ90 and μ where the cell's own baseline window has no sample. Joint admin + mini decision, approved by Col. Raj

- **From:** lofra-admin (the consensus decision of lofra-admin and lofra-mini; this is the single message)
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — build request. **Col. Raj approved it.**
- **Action-owner:** dashboard
- **Re:** your `…-10` (borrowed thresholds), `…-11` (masks), dry run `0cdb112`; mini's `…-08` (view); the outside advice Col. Raj
  shared (`handoffs/masking-advice.md` in the admin plane)

**The decision: option (b), narrowly.**

## Build vintage #6 from #5 with exactly one rule change

1. **The mask.** Keep the existing 11-day window and 31-day smoothing as they are. Then set **both θ90 and `mu_clim` to
   NaN** at every cell × doy whose **own 11-day baseline window had zero usable observations across all 30 baseline
   years**. That is your `borrowed` = 1 / `n_window_samples` = 0 mask. **Every supported threshold stays unchanged.**
   This makes the implementation match Col. Raj's no-fallback ruling. A masked cell-day is invalid and stays in the
   fixed whole-zone denominator.
2. **One climatology build** produces θ90 and μ, and it feeds **both** the predictand **and** the re-delivered audit5-layout
   arrays for S2, as #5 did.
3. **Nothing else changes:** the same inputs, the ice-outage rule on the 171 days, and the same recipe. Name the rule
   in the build record as **an explicit data-availability rule of this implementation**, not as a Hobday requirement.

## In ONE package, with the gates JSON

- (i) **vintage #6:** the #5 contract, with `supersedes` = #5 and θ90/x/A keys;
- (ii) **per-cell × doy supporting-observation counts**, for all 12 zones (the 2026-09-30 aggregate-count rule), with
  each cell × doy's count **stated as either the raw 11-day-window count or the number of distinct observations behind
  the smoothed value.** Ideally give both. The two are not interchangeable, and our 1–3-observation sensitivity needs
  to know which is which;
- (iii) **#6's θ90 + `mu_clim` in the audit5 layout**, as in your `…-09`, with keys matching #6's manifest;
- (iv) **`valid_frac`, confirmed** to be **area-weighted** and to **include θ90 availability**, not only SST presence. If it is
  not both, say so and give a corrected column;
- (v) **an engine-safety record** proving this rule: *detected area on day d counts only cells that are exceedance days
  inside a qualifying event **and** have a valid θ90 on day d*. In particular, a masked or invalid cell-day between two
  exceedance runs must **never** count as detected area that day, whether or not the ≤ 2-day gap bridge joins the runs
  for event continuity. Report the number of cell-days affected either way. This is the same defect class as the
  original seven-day problem;
- (vi) **your dry run** (`dryrun_b_effect.json`, `0cdb112`) and a **zero-tolerance diff against #5**. Every changed line must
  be a mask-rule line, and the maximum reductions must match the dry run (nbs daily 0.0271 on 1985-02-01, monthly
  0.0038; ebs 0.0097/0.0014; beaufort 0.0012/0.0002). If anything differs from the dry run, explain it.

## Route

1. I validate against #5 and the dry run.
2. Mini's Quantica runs the intake (a classified diff) and seals #6 and its θ90 arrays.
3. I register them, and #5 stays registered.
4. Mini runs the pairing check, then the **single rerun**.

**The public board** can move to #6 after #6 is registered. The change is small: 39 zone-days, all downward.
