# SCORINGS MANIFEST — forecast occurrence + onset display references (v2, 2026-07-16)

Pinned reference scorings for the **occurrence-probability** and **SEBS onset-watch** panels. These are
verbatim copies of the certified corrected-predictand (v2) re-run outputs
(`sealed_snapshot = predictand-shim-snap-obl064-v2`; conclusions certified 2026-07-16). Pin these files
and display **our** numbers under the honesty rails below — do not re-derive.

## Files (per-file SHA-256)

| File | SHA-256 | Source (certified v2 re-run) |
|---|---|---|
| `occurrence_probabilistic_skill_v2.csv` | `9227f38ef585aa39666468d7492a5470ad1032f77fa6e312ae6020fc93171560` | `stage-3-baselines/probabilistic_skill.csv` |
| `occurrence_reliability_bins_v2.csv` | `d078832ad6b32e7e1d69bc6de6370a3f967d48b21681c304ca553c8075a5851b` | `stage-3-baselines/reliability_bins.csv` |
| `onset_discrimination_v2.csv` | `2e1bf0b734e1953a369f754f3e76feff0d40e5f1fd0123c29e2b50589741fb9e` | `stage-3-contest/onset_discrimination.csv` |

Keyed by all 9 zones × leads {1,2,3,6} × `stratum` {all, pre2014, post2014}. **Display `stratum = all`**;
pre/post-2014 are retained for QA/context only (the paper's structural-stability check), not for the board.

---

## A. Occurrence-probability panel

**What it is:** P(next-month marine-heatwave area_frac > local train-q90 threshold), one month ahead, from
the **damped-persistence** model — i.e. the occurrence forecast is a read-out of the same persistence model
that drives the magnitude tile, not a separate skillful model.

**Display rule:** `occurrence_probabilistic_skill_v2.csv`, rows `forecaster == 'damped_persistence'`,
`lead == 1`, `stratum == 'all'`, for the **seven damped zones** only (`sebs, wgoa, egoa, nbs, ai_west,
ai_central, ai_east`). chukchi/beaufort have no occurrence panel (climatology-routed); nbs carries the
Arctic ice caveat.

**Metrics to show** (columns in the CSV):
- `bss_clim` — Brier Skill Score vs seasonal climatology (the headline skill number).
- `auc` — discrimination.
- reliability curve — from `occurrence_reliability_bins_v2.csv` (`p_mean` vs `o_freq` per `bin`).
- `n` (effective sample) and `base_rate` for context.

**Resolvability / greying:** occurrence is an **L1 product**. At L1 all seven zones are resolvable and
positive (`bss_clim` egoa 0.58, wgoa 0.59, sebs 0.51, nbs 0.39, ai_east 0.37, ai_west 0.27, ai_central
0.23). If you surface L2/L3 as context, **grey any cell with `bss_clim ≤ 0` as "watch"** rather than a
skill number (mirrors the magnitude ladder) — several zones cross ≤0 by L3.

**Honesty rail — do not imply it beats persistence.** The occurrence forecast *is* the persistence model;
`bss_clim` measures skill over climatology, which is real, but it is not a model beating persistence.

**Panel caption (verbatim):**
> The estimated chance next month's marine-heatwave area exceeds the local 90th-percentile threshold, one
> month ahead, from the damped-persistence model. Skill is measured against seasonal climatology; it is
> resolvable at one month in the productive zones and decays toward climatology beyond, where it is shown
> as "watch" rather than a number.

---

## B. SEBS onset-watch panel

**What it is:** the frozen SEBS LIM path (`lim_k12` → train-only isotonic link → q90 exceedance →
warn-above-climatology). State (`elevated`/`normal`) + threshold come **straight from the v2 manifest's
frozen onset calibration** (`decision_thresholds`, `q90_threshold`, isotonic-link knots,
`zone_readoff_a_sebs`/`const`) — no tuning on the board.

**Display rule:** `onset_discrimination_v2.csv`, rows `zone == 'sebs'`, `forecaster == 'lim_k12'`,
`lead ∈ {1,2}`, `stratum == 'all'`. (Note: this is the **contest** file — the baseline
`onset_discrimination.csv` you named carries only the persistence family, not the deployed LIM watch.)

**Metrics to show:** `onset_auc`, `sedi`, and `pod`/`far` at the calibrated threshold. v2 values:
- L1: AUC 0.759, SEDI 0.583, POD 0.467, FAR 0.682
- L2: AUC 0.685, SEDI 0.503, POD 0.400, FAR 0.806

**Honesty rail — the anchor.** Show the `climatology` and `persistence` rows alongside: persistence's own
onset AUC is 0.665 (L1), just below the watch. The watch discriminates onset but does **not** resolvably
beat persistence — on the corrected predictand the selection-adjusted onset improvement is not
statistically resolvable on the 16 available onsets (its significance moved further from a persistence beat
under the correction). It is an early-warning watch, never a validated forecast advantage.

**Panel caption (verbatim):**
> EXPERIMENTAL — a two-state elevated/normal onset watch. It genuinely discriminates SEBS marine-heatwave
> onset but is not a resolvable skill gain over persistence and is never shown as beating persistence; on
> the corrected predictand its selection-adjusted improvement is not statistically resolvable on the
> available onsets. Read it as an early-warning signal, not a validated forecast advantage.

---

## obl029 field rebuild (un-deferring the watch)
Unchanged under v2. The EOF basis / `field_snapshot` (`snap-obl029-broadfield-20260701`) are byte-identical
to v1, so the vendored `obl029_01/02/04` chain (public OISST v2.1, 1991–2020 baseline, frozen EOF grid) and
its `spec/obl036_*` grid/baseline/mask-hash validation are unchanged. No new gotchas beyond v1;
`load_live_field` will refuse a mismatched grid/baseline as before.
