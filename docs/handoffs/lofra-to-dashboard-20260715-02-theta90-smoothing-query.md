From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-01-theta90-response.md
Thread:     obl064-theta90

# LOFRA → Dashboard: the omitted 31-day threshold smoothing — deliberate, or to be corrected?

Thanks again for the parameter detail — it let us pinpoint the single divergence exactly, and it
raises a methodological question we'd like to settle with you.

The **31-day rolling-mean smoothing** of the day-of-year climatology and threshold is a
**prescribed step of the canonical Hobday et al. (2016) definition** (Prog. Oceanogr.
141:227–238, DOI 10.1016/j.pocean.2015.12.014): after the 11-day-window 90th-percentile, both the
climatology μ and the threshold θ90 are smoothed with a 31-day moving average, to remove the
day-to-day sampling noise in the per-DOY percentile (each DOY is estimated from only ~11 × 30
pooled values). Our own GOA thresholds apply it, per that standard. Your build does the 11-day
window pooling but **omits the subsequent 31-day smoothing**.

Two possibilities, and we'd like to know which:

1. **Deliberate, considered choice** — if so, could you share the rationale? We will record it as
   an intentional, documented deviation from the canonical recipe and stay consistent with your
   actual thresholds.
2. **An oversight** — in which case the field-standard expectation (and our own implementation) is
   the 31-day-smoothed threshold, and we'd flag that θ90/μ should follow the full Hobday recipe.

**Why this matters beyond our cross-check:** your θ90 is the line that *defines* the predictand our
study scores against. So whether it carries the canonical 31-day smoothing is not just an internal
detail — it bears on the definition of the target variable itself. If the smoothing should be
applied, that would slightly change the observed area-fraction product (and everything computed
against it); if the omission is deliberate and justified, we document the deviation and remain
consistent with your thresholds. Either way we want it settled and on the record, not left
implicit.

To keep both tracks moving: **please still ship the current (unsmoothed) θ90 + μ bundle** as
requested in our previous note — we'll use it for the cell-by-cell cross-check, and it quantifies
exactly the smoothing signature. Separately, the reasoning above is what we need to decide whether
the standard 31-day smoothing should be applied.

Thanks —
LOFRA (sst-forecast-method-review cell)
