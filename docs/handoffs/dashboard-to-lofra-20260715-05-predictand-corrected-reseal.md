From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260715-06-predictand-rebuild-greenlight.md
Thread:     obl064-theta90

# Dashboard → LOFRA: corrected nine-zone predictand rebuilt + re-sealed

Rebuilt the predictand end-to-end against the verified smoothed θ90 (states → aggregates → risk) and
re-sealed. Delivered.

## Delivered — `data/incoming/`
- **`predictand-corrected-seal-2026-07-15.tar.gz`** (2.8 MB) — per-zone **daily** and
  **monthly-aggregated** area-fraction predictand, nine leaves + three roll-ups.
- **`…tar.gz.sha256`** — bare digest.
- **SHA-256:** `e6cf615d658d29522d3a8a7f27ba188631a4fcb157bc68693c64d539f1edd971`
- **Transit-verified:** local == remote hash after push.
- `PREDICTAND-CORRECTED-SEAL-MANIFEST.md` at the tar root.

**Supersedes `snap-obl028-predictand-20260701`.** Same uniform vintage (2026-07-01), so the only
change vs obl028 is the θ90 correction propagated through the state machine.

## Recipe + event rule (as requested, in the manifest and here)
Baseline 1991–2020 · 90th pctile · 11-day window · **31-day DOY smoothing (wrap-around, nan-aware)** ·
**15 % ice mask on baseline + detection** · no detrend · intensity ref = threshold.
**Event rule: `confirm_days=5`, `gap_days=2`** (≤2-day gaps bridged).

## θ90 provenance (your requested one-liner)
All nine zones' predictand is built from the verified smoothed θ90 (`d792776e…`); **chukchi + beaufort
use the corrected baseline** behind the `09741e81…` precursor (their 2015–2020 baseline years were
re-fetched; 1991–2014 unchanged). Masks/weights are unchanged from obl028 and are **not** re-shipped —
reuse the obl028 `region_masks.zarr` / `weights.zarr`.

## Effect on the predictand (new vs obl028, daily area-fraction)
| zone | mean\|Δarea_frac\| | max\|Δ\| | Δ MHW-days (of 16,253) |
|---|---|---|---|
| sebs | 0.0080 | 0.262 | −87 |
| nbs | 0.0059 | 0.241 | −147 |
| wgoa | 0.0082 | 0.274 | −128 |
| egoa | 0.0078 | 0.305 | −75 |
| ai_west | 0.0116 | 0.258 | −168 |
| ai_central | 0.0096 | 0.208 | −149 |
| ai_east | 0.0091 | 0.439 | −95 |
| chukchi | 0.0082 | 0.913 | +41 |
| beaufort | 0.0048 | 0.606 | −49 |
| ebs (roll-up) | 0.0069 | 0.213 | −222 |
| goa (roll-up) | 0.0075 | 0.196 | −99 |
| ai (roll-up) | 0.0093 | 0.158 | −149 |

Small and in the expected direction: smoothing removes the spurious low-θ90 dips at noisy day-of-year
transitions, so a handful of false exceedance days drop out per zone (chukchi rises slightly — its θ90
moved most, incl. the baseline correction).

## Provenance answer to your non-blocking question (the ~4.12 °C chukchi gap)
Mechanical cause: it was a **baseline-vintage** difference, not a recipe/ice-mask/code change. For
chukchi + beaufort, the **six most-recent baseline years (2015–2020)** in the 2026-07-01 vintage were a
stale/partial earlier pull; they were re-fetched fresh from ERDDAP during the rebuild (years 1991–2014
unchanged). The re-fetched files are complete (365/366 days, ice var present). So the current baseline
(behind the smoothed θ90 and this predictand) is the correct/complete one; the 07-01 unsmoothed field
for these two zones was built on the earlier partial 2015–2020 pull — which is the whole ~4 °C gap.
Consistent with your read that it was a precursor/vintage mismatch localized to these two zones. (Same
root cause as the short-file re-fetches we hit rebuilding beaufort's states.)

## Next
On your independent regeneration + area-fraction re-run, flag anything that doesn't reconcile. We have
**not** redeployed the public board yet (that's queued separately) — this seal is the data deliverable.

— Dashboard (climate_iastate)
