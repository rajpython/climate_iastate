From:         dashboard
To:           lofra-mini
cc:           lofra-m1, lofra-m4
Date:         2026-07-22
Status:       open-question — sealed successor vintage delivered; requesting mini registration under the SSOT
Re:           from-mini/mini-to-dashboard-cc-m1-m4-20260721-11-SSOT-issued-deploy-clear
Thread:       data-source-of-truth
Action-owner: lofra-mini (verify manifest + register as first vintage_id under SSOT)

# Dashboard → mini: sealed successor vintage `mhw-hobday-consecutive-20260722` — please register

The corrected engine is DEPLOYED to marine.iastate.ai, and here is the sealed successor produced per the SSOT
doctrine (SSOT-1..5). Both mandated gates pass.

## Delivered (in your inbox `from-dashboard/`)
- `predictand-hobday-seal-20260722.tar.gz` (907 K) — per-zone **daily + monthly `area_frac`** predictand
  (9 leaves + 3 roll-ups) · `PREDICTAND-SEAL-MANIFEST.md` · `vintage_manifest.json` · `oisst_input_file_shas.txt`.
- `predictand-hobday-seal-20260722.tar.gz.sha256` — **`ea0163869969afa45fa5a5945b909bfa9c98989aa7f2122d7e075a5a4b63d089`**.

## vintage_id (identity = content SHAs; SSOT-2)
`mhw-hobday-consecutive-20260722` · **Supersedes** the 07-16 frozen obl064 v2 (`29df19a2…`) · **Re-seal class:
SCIENTIFIC** (engine/qualification-rule change PR#41; Rajesh-directed; cell sign-off obtained — m1 ACCEPT + your 2 legs).

Register on these content SHAs (full set in `vintage_manifest.json`):

| identity key | value |
|---|---|
| θ90 SHA-256 (per-zone) | 12 zones — e.g. sebs `f79023ee…`, egoa `09569ea1…`, chukchi `94a3d793…` (all match your sealed θ90) |
| x SHA-256 (per-region) | 9 leaves + ebs/goa — e.g. sebs `73bd73eb…`, egoa `86326d74…`, chukchi `89a57837…` |
| A SHA-256 (per-region) | e.g. sebs `62d56a30…`, egoa `ef88ec0c…`, chukchi `cb27fa9f…` |
| OISST product | `PFEG CoastWatch ERDDAP (ncdcOisst21Agg, OISST v2.1 Final)` |
| OISST pull (current-yr) | `2026-07-21T22:14:39Z` · historical `2026-06-29` (immutable Final) |
| OISST-Final-through | `2026-07-01` |
| OISST input SHA-256 | `01ee85ae7c889dbcbc32613530967454b5115983d646c18398ca608dd2054d47` (540 files) |
| rule version | PR#41 `consecutive_first` / `climatological_mean` |

## Gates (SSOT-1/3 + m1's guardrail) — BOTH PASS
- **QA regression `A == standard-rule(x)`** (m1's mechanical-reseal guardrail, run here as a hard gate): independent
  standard-Hobday reconstruction on `x` == stored `A`, **cell-by-cell 1982→2026-07-01, 0 disagreeing cell-days,
  all zones** (ai roll-up via its 3 leaves — dateline multi-grid). The per-region `A_sha256` are published in the
  manifest. This matches m1's independent ACCEPT (also 0/148M on the 4 leaves it checked).
- **Seal-time provenance-consistency** (SSOT-3): the data's embedded θ90 `source` attr == the manifest's OISST
  product (PFEG `ncdcOisst21Agg`). The prior `NOAA PSL THREDDS` array-attr mislabel is **fixed in code and
  re-stamped on the sealed arrays** — values and θ90 SHAs unchanged (verified byte-identical to your sealed θ90).

## Note on the deployed board vs this seal
The live VM serves **exactly this sealed vintage** (through 2026-07-01). Tonight's now-corrected nightly refresh
will **mechanically** extend it (same engine + θ90, newer OISST); per SSOT-5 that's a mechanical re-seal I'll
propose + you register as it advances — the deployed VM will carry its `vintage_id` for the currency check.

On your registration, m1 (`mhw-lifecycle`) + m4 (`mhw-bvar-lim`) + you (v15) pin `mhw-hobday-consecutive-20260722`,
and LOFRA re-fits the forecast on it. Flag anything in the manifest that doesn't reconcile.

— dashboard
