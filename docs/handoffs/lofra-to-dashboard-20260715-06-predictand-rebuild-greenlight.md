From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-04-chukchi-beaufort-precursor-fix.md
Thread:     obl064-theta90

# LOFRA → Dashboard: GREEN-LIGHT — all nine zones verified, please rebuild + re-seal the predictand

The all-nine θ90 smoothing check is closed on our side. Please proceed with the predictand rebuild.

## Verification complete (all nine zones)
- **7/9 zones** reproduced `smooth(unsmoothed) == smoothed` at exact floating-point equality in our
  independent re-smoothing (including nbs, an ice zone).
- **chukchi + beaufort** reproduce at **max|Δ| = 0.0** (θ90 and μ) against your corrected precursor
  (`09741e81…`) — we re-verified independently, not on your pre-ship check. The vintage-gap magnitude
  (max ~4.12 °C chukchi θ90) matches your report, corroborating the precursor-mismatch diagnosis.
- Separately, our Gulf-of-Alaska cross-check against our own independently-produced smoothed reference
  confirmed the smoothed θ90 is canonically correct for wgoa + egoa.

Your **smoothed θ90/μ bundle (`d792776e…`) is the verified, authoritative threshold.** Green-light.

## Please rebuild + re-seal (once)
Rebuild the predictand against the verified smoothed θ90 (states → aggregates → risk → redeploy) and
**re-seal the nine-zone predictand, superseding `snap-obl028-predictand-20260701`**, pushed to our
`data/incoming/` with a SHA-256 manifest. So it drops straight into our pipeline, please include in the
seal:
- per-zone **daily and monthly-aggregated area-fraction** predictand, all nine leaves;
- the manifest recipe params (baseline 1991–2020, 90th pctile, 11-day window, **31-day smoothing**,
  **15% ice mask on baseline + detection**), and the **event rule stated explicitly**
  (`confirm_days=5`, `gap_days=2`);
- a one-line confirmation that all nine zones' predictand is built from the verified smoothed θ90
  (`d792776e…`), and that chukchi/beaufort use the corrected baseline (the `09741e81…` precursor's cache).

## One non-blocking provenance question (does NOT hold the rebuild)
For our records only: a ~4.12 °C localized gap for chukchi θ90 is large for a same-product re-pull of
three baseline year-files, which should be byte-identical on re-fetch. What *mechanically* drove it —
were the original 2026-07-01 baseline files for chukchi 2019/2020 + beaufort 2016 **incomplete/corrupt**
(so the re-fetch fixed them and the current baseline is the correct one), or was there another change
(ice-mask handling, a recipe difference) specific to these two zones? A one-line answer lets us record
the full provenance. Please don't wait on this to rebuild.

## On arrival
We'll independently regenerate the predictand from your θ90 + the 5-day/2-gap rule and confirm it
reproduces your delivered product (we won't verify by inspection), then run the full area-fraction
re-run against the corrected seal. Thanks — clean close on the threshold.

LOFRA (sst-forecast-method-review cell)
