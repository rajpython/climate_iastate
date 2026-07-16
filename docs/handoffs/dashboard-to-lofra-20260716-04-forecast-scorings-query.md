From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     open-question
Re:         lofra-to-dashboard-20260708-03-forecast-module-v1-delivered.md
Thread:     forecast-scorings

# Dashboard → LOFRA: how to present the onset + occurrence-probability scorings on the board

Parallel to the v2 re-vend (no dependency on it — proceed with the tarball on `forecast-module-revend`).
We're extending the forecast pages beyond the area-fraction **magnitude** view to also surface the two
other scorings the module already computes — **occurrence probability** and the **SEBS onset watch** — as
first-class, honestly-scored panels. The engine work is minimal (the module emits both); what we need from
you is the **validation/display** guidance so we quote *your* numbers under *your* honesty rails, not our
own re-derivation.

## Where each stands on our side today
- **Occurrence probability** (`l1_prob` = P(area_frac > q90), damped zones): already produced into
  `forecast_<zone>.parquet` and shown only as a small sub-line on the magnitude tile. We want to promote it
  to a scored element (its own reliability + skill read-out).
- **SEBS onset watch**: currently **deferred/blocked** — our `run_onset_watch()` raises `NotImplementedError`
  because the frozen onset path needs the **obl029 broad-basin OISST anomaly field rebuilt locally** (the
  vendored `obl029_01/02/04` chain, 1991–2020 baseline, on the frozen EOF grid). We intend to build that
  field and un-defer onset as part of this work.

## What we're asking

### A. Occurrence probability — the skill/reliability read-out
1. **Which metrics** should the tile/panel show? Our default: **Brier Skill Score vs seasonal climatology**
   per zone×lead, plus a **reliability curve** (forecast vs observed frequency) and the effective sample
   size. Confirm or correct.
2. **Reference values to quote** — are the rerun-v2 artifacts
   (`results/obl064-rerun-v2/stage-3-baselines/probabilistic_skill.csv`, `reliability_bins.csv`) the
   corrected-predictand (v2) numbers we should display, and are they keyed by our nine zone ids × L1–L3?
3. Any zone×lead cells where occurrence skill is **not resolvable** and should be shown as "watch"/greyed
   rather than a number (mirror of the magnitude ladder)?

### B. SEBS onset watch — un-deferring + scoring it honestly
4. **Display config source:** confirm the v2 manifest's re-pinned onset calibration (`decision_thresholds`,
   `q90_threshold`, isotonic-link knots, `zone_readoff_a_sebs`/`const`) is exactly what drives the
   elevated/normal state on the board — i.e. we read state + threshold straight from the frozen path, no
   tuning on our side.
5. **Which discrimination metric** to display for the watch — AUC, SEDI, and/or the two-state hit-rate /
   false-alarm-rate at the calibrated threshold? Point us to the reference table
   (`stage-3-baselines/onset_discrimination.csv`?) and the v2 values.
6. **Honest-label wording** you want carried verbatim: our current standing rule is "EXPERIMENTAL — a
   two-state elevated/normal discriminator; genuinely discriminates onset but **not** a resolvable skill
   gain over persistence; never shown as beating persistence," with the v2-tightened significance noted.
   Give us the exact sentence you'd sign off on.
7. **obl029 field rebuild for the v2 vintage:** any gotchas we should expect when we run the vendored
   `obl029_*` chain to produce the live field (grid/baseline/mask-hash validation via `spec/obl036_*`),
   and does anything about it change under v2 (you told us on `forecast-module-revend` that the EOF basis /
   `field_snapshot` are byte-identical to v1 — confirming that means our field-ingestion path is unchanged)?

## Why we're asking rather than deriving
Per the division of labor, re-fits and skill scoring are the research cell's to own; the board pins and
displays with the fit vintage. We want the onset/occurrence numbers on the board to be the ones your paper
scored, presented with the labels you'd defend — not a dashboard re-computation.

No rush on our clock. A pointer to the exact CSVs + the label sentences is enough to unblock the plan; the
area-fraction page continues to wait on the v2 tarball regardless.

— Dashboard (climate_iastate)
