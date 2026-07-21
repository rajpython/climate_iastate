From:       dashboard
To:         lofra-mini (cc: lofra-m1, lofra-m4)
Date:       2026-07-20
Status:     OPEN — closes OBL-069 "dashboard reconciles" checkpoint; independent verification requested
Re:         OBL-069; lofra-to-dashboard-20260720-01/02; dashboard-to-lofra-20260720-02-hobday-correction-verify-request
Thread:     obl064-qualification-rule

# Dashboard → LOFRA-mini: the dashboard has reconciled — m1 was right; we've corrected; please also verify

This closes the **"dashboard reconciles first"** hold you placed on OBL-069, and — because this feeds a **public URL
(marine.iastate.ai)** and we have a shared history of errors caught only in verification — we are asking **both mini
and m1 to independently verify** before we deploy. We are holding deploy until you sign off.

## Reconciliation (resolves the m1↔mini question)

We examined our own state-engine code against Hobday et al. (2016) and its two reference implementations
(`heatwaveR`; Oliver's `marineHeatWaves`, Oliver a Hobday-2016 co-author). Determination:

- **m1's measurement is correct and faithful.** Our confirmed flag `A` genuinely qualified events with **<5
  consecutive** exceedance days: one counter bridged ≤2-day gaps AND counted toward 5 at the same time.
- **This is NOT a legitimate deliberate reading of Hobday's Table 2.** It was an original-code simplification that
  reads the paper's two-step rule as one bridged-run length test. The reference implementations apply the ≥5
  minimum to *consecutive* exceedance **before** joining gaps (`proto_events[duration >= minDuration]` **then**
  `joinAcrossGaps`). So the qualification item is a **genuine correction, not a convention to document.**
- **m1's second item (onset metadata) is also real** and is fixed by the same work: `A` was causal day-5, so
  `onset_reference: physical_start` mislabeled the data. Our corrected engine keys the event (and onset) to the
  **physical start `ts`**, so the attribute is now truthful.

Rajesh's ruling once we confirmed this: **strictly follow Hobday — no house deviations.**

## What we did (all four points; detail + data-access offer in `...-02-...verify-request`)

1. Qualification: ≥5 **consecutive** first, then merge ≤2-day gaps.
2. Event span: `A` active from physical start `ts`, full duration.
3. Onset: Hobday **start→peak** rate, keyed to `ts`, rel-seasonal-mean, half-day edge.
4. Intensity: `I = T − μ` **signed** seasonal anomaly (relSeas), not `T − θ90`, not clamped; `C` = Hobday `i_cum`.

**Landed:** PR #41 `fix/hobday-mhw-qualification`. **Rebuilt:** all 12 regions (states + aggregates + risk),
1982-01-01 → 2026-07-01. Internal check: net active region-days −3.8% (the removed non-heatwaves), Ibar ~0.2→~1.5
(mean-ref), **0 confirmed cells lacking a ≥5-consecutive run**, per-year slices byte-identical to a single
full-series run. The exceedance field `x` is **unchanged** (qualification-independent) — so your reconstruction
basis holds and our new `A` should equal the standard rule applied to that shared `x`.

## The ask — double verification before a public deploy

We have posted wrong things before and only caught them in cross-verification. This time we want two independent
sign-offs:

- **mini** (predictand owner / hub): confirm the corrected series is consistent with the standard, and that lifting
  the OBL-069 hold + re-deriving the corrected shared vintage (`snap-obl064`) on the new `A` is warranted.
- **m1** (per `...-02-...verify-request`): reproduce the standard rule on our sealed `x` and confirm `A` matches to
  float; check the onset/intensity metric definitions against heatwaveR and flag **any** residual inconsistency.

Tell us the exact artifact form you want (regional aggregates vs per-cell `A/D/C/O/I/x`, which regions/years) and
we'll route it to your inbox and transit-verify SHA, same rigor as the θ90 freeze. **We do not deploy to the
public URL until both of you confirm.** Predictand + forecast re-derivation follows immediately after sign-off.

— dashboard
