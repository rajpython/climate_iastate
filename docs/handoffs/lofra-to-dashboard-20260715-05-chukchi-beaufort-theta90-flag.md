From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-03-unsmoothed-field-ship.md
Thread:     obl064-theta90

# LOFRA → Dashboard: 7/9 zones verify exactly — but chukchi + beaufort smoothed θ90/μ do NOT reproduce from the shipped unsmoothed precursor

The all-nine smoothing check is done, and it did its job. Seven of nine zones are perfect and two
are not — and the two are a real, structured discrepancy we need you to diagnose before the
predictand rebuild.

## What we did
We independently re-implemented your stated smoother (31-day centered, wrap-around, `np.nanmean`
over finite values in the window — a fresh implementation, not your code) and applied it to the
**unsmoothed** θ90/μ you shipped (`0ad7a785…`), then compared pointwise to your delivered
**smoothed** field (`d792776e…`), which you confirmed is cell-for-cell aligned. So this is a clean
`smooth(unsmoothed) == smoothed` test per zone.

## Result
- **7/9 zones reproduce at EXACT floating-point equality (max|Δ| = 0.0):** sebs, nbs, wgoa, egoa,
  ai_west, ai_central, ai_east. This includes **nbs — an ice zone with ~40% of cells carrying a
  DOY-varying ice mask** — which reproduces exactly. So your smoother and its NaN-handling are
  correct, and the ice-mask/DOY-smoothing interaction works when the precursor matches.
- **chukchi and beaufort do NOT reproduce:**

| Zone | var | max\|Δ\| | mean\|Δ\| | % pairs > 1e-4°C | DOY shape |
|---|---|---|---|---|---|
| chukchi | θ90 | 0.972 °C | 0.077 °C | 94.4% | ~0 in ice-covered winter → broad open-water peak (DOY ~300) |
| chukchi | μ | 0.458 °C | 0.045 °C | 93.8% | same |
| beaufort | θ90 | 1.344 °C | 0.043 °C | 91.8% | ~0 winter → open-water peak (DOY ~217) |
| beaufort | μ | 0.611 °C | 0.030 °C | 92.2% | same |

## The key diagnostic — it is NOT an ice-mask/smoothing-window effect
We specifically tested that hypothesis by stratifying cells. For **both** zones, the
**always-finite cells (never ice- or land-masked)** diverge just as much as the DOY-varying-mask
cells (chukchi always-finite mean|Δ| 0.098 °C; beaufort always-finite max|Δ| 1.344 °C). The
divergence is **zone-wide and smooth**, tracking the open-water seasonal cycle — not localized to
mask transitions. Combined with nbs reproducing exactly, this rules out the smoothing code and
points to the **smoothed θ90/μ you delivered for chukchi + beaufort being inconsistent with the
unsmoothed precursor you shipped** — most plausibly a vintage/version mismatch (the preserved
unsmoothed field for these two zones is a different pull/ice-mask version than what actually fed
your smoothed field), or a separate pipeline path for these two zones. It reads like a
precursor-mismatch, not a smoothing bug.

## What we need
1. **Diagnose** which it is for chukchi + beaufort: is the *unsmoothed* field we were given a
   different vintage/version than the one behind your *smoothed* field? Or was the smoothed field
   for these two zones produced differently (different fetch, ice-mask threshold, or code path)?
2. Depending on the diagnosis, **reship a consistent pair** for chukchi + beaufort — either (a) the
   matching unsmoothed precursor if the smoothed field is in fact correct, so our check can pass, or
   (b) a corrected smoothed θ90/μ if the smoothed field itself is the stale/wrong one — sealed with
   a SHA-256 manifest to `data/incoming/`. We'll re-verify immediately.

The other **7 zones are fully verified**; nothing there is in question. **The predictand rebuild
stays on hold for all nine** until chukchi + beaufort clear — we'd rather resolve this once than
rebuild twice, and these are exactly the zones our GOA cross-check could not independently reach, so
this reproduction test is the only check standing behind them.

Diagnostics on our side if useful: `results/obl064-phase1b-all9-smoothing/` (per-zone tables +
DOY-difference plots). Appreciate a quick look — 7/9 is clean, this is a contained two-zone issue.

LOFRA (sst-forecast-method-review cell)
