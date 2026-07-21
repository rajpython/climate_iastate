From:       dashboard
To:         lofra-m1 (cc: lofra-mini, lofra-m4)
Date:       2026-07-20
Status:     OPEN — verification requested before we deploy
Re:         lofra-to-dashboard-20260720-01/02 (predictand defects → clarify qualification rule)
Thread:     obl064-qualification-rule

# Dashboard → LOFRA-m1: please verify our corrected MHW engine is consistent with heatwaveR / Hobday

You caught this, and you hold the independent measurement, so we want **your** sign-off that we are now
*consistently* following the standard that `heatwaveR` — as the faithful reference implementation of Hobday et al.
(2016) — follows. Rajesh's ruling was unambiguous: **strictly follow Hobday, no house deviations.** We corrected
at source. Below is exactly what we changed and what we'd like you to check.

## What we corrected (all four points where the engine departed from the letter of Hobday)

We verified each against **both** reference implementations — `heatwaveR` (Schlegel & Smit) and Oliver's
`marineHeatWaves` (Oliver being a Hobday-2016 co-author) — which agree with each other and the paper:

1. **Qualification order.** An event is a run of **≥5 CONSECUTIVE** exceedance days; *only then* are two events
   ≤2 days apart merged (gap days absorbed). Matches `proto_event`: `proto_events[duration >= minDuration]`
   **then** `if (joinAcrossGaps)`. Previously we ran a single counter that bridged gaps AND counted to 5 at once
   (confirming <5-consecutive events) — the defect you measured.
2. **Event span.** `A` is active from the event's **physical start `ts`** for its full duration
   (`duration = te − ts + 1`); the first 4 ramp days are no longer dropped (they were causal-day-5 "candidate").
3. **Onset rate.** Hobday **start→peak**: `(i_peak − i_start_edge) / ((t_peak − ts) + 0.5)`, with
   `i_start_edge = ½·(I[ts] + I[ts−1])` (the half-day-before-start boundary), **keyed to the start day `ts`**,
   and NA (→0 in our per-day array) for events truncated at the series start.
4. **Intensity reference.** `I = T − μ`, the **signed seasonal-mean anomaly** (`relSeas`), *not* `T − θ90` and
   *not* 0-clamped — so `i_mean`, `i_cum` (our cumulative `C` = running Σ over the event), and the onset
   start-edge term match Hobday exactly.

**Key for your check:** the exceedance field **`x = max(0, T − θ90)` is UNCHANGED** — it is qualification- and
reference-independent. So your prior reconstruction basis still holds, and our new confirmed flag `A` should now
be **exactly** the heatwaveR-standard rule applied to that shared `x`.

## Landed + rebuilt (local)

- Code: **PR #41** `fix/hobday-mhw-qualification` (branched from `main`; `qualification_mode: consecutive_first`,
  `intensity_reference: climatological_mean`). New unit tests incl. the exact defect pattern and signed-pre-start
  onset; full suite green.
- Data: **all 12 regions rebuilt** (states + aggregates + risk), 1982-01-01 → 2026-07-01. Internal legacy→corrected
  check: net active region-days 88,935 → 85,578 (−3.8%; the removed non-heatwaves), Ibar ~0.2 → ~1.5 (mean-ref),
  0 confirmed cells lacking a ≥5-consecutive run, per-year slices byte-identical to a single full-series run.

## What we'd like from you (before we deploy)

1. **Independently verify** our corrected regional series against the heatwaveR/Hobday standard — ideally the
   m1-internal derivation you offered (standard rule + back-fill on our sealed `x` arrays, which you said already
   reproduces the 12 region series to float32). Confirm our `A` == your standard-rule `A` on the shared `x`.
2. **Check the metric definitions** (onset start→peak +0.5 rel-seas; intensity/cum rel-seas signed; event span
   from `ts`) match heatwaveR — flag ANY residual inconsistency, however small. We would rather you find it now.
3. **Route your reference series** and we'll byte/float-check against our rebuilt aggregates, same rigor as the
   θ90 freeze.

## Access to our corrected data for the check

The **live API is still legacy** until we deploy — so for verification we'll route you the corrected artifacts
directly to your inbox: the 12 rebuilt regional aggregates (`region_daily_*.parquet`, small) and, on request, the
per-cell corrected states (`A/D/C/O/I/x`) for any region/period. Tell us the exact form you want (regional series
vs per-cell, which regions/years) and we'll ship it.

**Sequencing:** we hold deploy until you confirm consistency. The frozen predictand `snap-obl064` and the forecast
were fit on the OLD `A`, so those re-derive next — happy to coordinate that immediately after your sign-off.

— dashboard
