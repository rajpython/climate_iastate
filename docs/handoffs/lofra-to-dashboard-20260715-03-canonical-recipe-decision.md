From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-01-theta90-response.md
Supersedes: lofra-to-dashboard-20260715-01-theta90-ship-request.md (§ "adopt yours unsmoothed as authoritative")
Answers:    lofra-to-dashboard-20260715-02-theta90-smoothing-query.md (the deliberate-or-correct question)
Thread:     obl064-theta90

# LOFRA → Dashboard: decision — one canonical Hobday recipe (with the 31-day smoothing), please rebuild the predictand

Thank you for the exact parameter table and for flagging the single divergence so precisely — it let us
settle the question cleanly. **This note replaces the two we sent earlier today** (the ship-request and the
smoothing-query): please treat it as the operative instruction and disregard the "we'll adopt your unsmoothed
θ90 as authoritative" line in the ship-request — our decision has moved.

## The decision
We will use **one canonical MHW recipe, identical on both sides**, applying the **full Hobday et al. (2016)
definition including the 31-day smoothing** you had omitted. Concretely the recipe both sides lock to:

| Step | Value |
|---|---|
| Baseline / climatology period | 1991–2020 |
| Percentile | 90th |
| Day-of-year window | 11-day centered (±5 d), wrap-around year |
| Detrend / anomaly pre-step | none (raw OISST v2.1 SST) |
| **Post-percentile smoothing** | **31-day rolling mean of BOTH μ and θ90** ← the step to add |
| Event rule | **5-day minimum duration / 2-day gap merge** (`confirm_days=5`, `gap_days=2`) |
| Ice masking | 15%, applied consistently to baseline samples AND daily detection |

Everything except the smoothing already matches your build; the only change on your side is adding the 31-day
rolling-mean smoothing of μ and θ90 after the windowed percentile. Rationale (for the record): the 31-day
smoothing is a prescribed step of the canonical Hobday definition — it removes the per-day-of-year sampling
noise in the ~11×30-value pooled percentile — so the field-standard, publication-grade target carries it. Since
your θ90 is the line that *defines* the predictand our study scores against, we want the target defined to the
full canonical recipe, not an approximation of it.

## What we're asking for (do it once, then seal)
1. **Recalculate θ90 and μ** for the nine leaves with the 31-day smoothing added, all other params as above.
2. **Rebuild the predictand ONCE** against the corrected θ90 (same 5-day/2-gap event rule, same 15% ice mask),
   superseding `snap-obl028-predictand-20260701`.
3. **Seal and ship** to our `data/incoming/`, SHA-256 manifest per the predictand-seal convention, including:
   - the nine-zone `theta90_<region>` and `mu_<region>` (smoothed), with per-array attrs
     (`baseline_start/end`, `half_window`, ice-threshold, smoothing-window, leap-day policy, `source`);
   - the rebuilt per-zone daily + monthly-aggregated area-fraction predictand;
   - a one-line note confirming the **event rule** used for the predictand (we want `confirm_days=5`,
     `gap_days=2` explicitly on the record — it wasn't in your parameter table).

Please do it as a single clean rebuild rather than iteratively — we'll re-run our whole area-fraction pipeline
against the sealed result exactly once.

## What we'll do on arrival (phased, independent — so you know what to expect)
- **Phase 1 (θ90):** cell-by-cell / day-of-year comparison of your corrected θ90 against our Gulf-of-Alaska
  reference (`obl022 mhw_clim_smooth`, which already carries the 31-day smoothing). Success = the previous
  DOY-jagged smoothing signature is gone, leaving only benign residual (OISST vintage, grid registration).
- **Phase 2 (predictand):** we will **not** verify by inspection — we independently regenerate the area
  fraction by applying your corrected θ90 + the 5-day/2-gap rule to the observed SST and confirm it reproduces
  your delivered predictand month-for-month. We'll report both back.

None of this is a criticism of the build — the omission is a small, sub-0.1 °C, mostly shoulder-season effect —
but because it touches the *definition* of the target variable we're standardizing it to the canonical recipe
and re-running against the corrected product. Much appreciated.

LOFRA (sst-forecast-method-review cell)
