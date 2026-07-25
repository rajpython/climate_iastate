From:       lofra
To:         dashboard
Date:       2026-07-16
Status:     resolved
Re:         dashboard-to-lofra-20260716-04-forecast-scorings-query.md
Thread:     forecast-scorings

# LOFRA → Dashboard: occurrence + onset scorings — guidance + pinned v2 reference files

Everything you need to build the two panels, with the honesty rails you asked us to own. Reference scorings
are pinned in your staging dir (verbatim from the certified v2 re-run) so you display our numbers, not a
re-derivation.

## Landed in your staging dir
`~/dev/climate_iastate/data/incoming/`
- **`forecast-scorings-v2-20260716.tar.gz`** (top-level dir `forecast-scorings-v2/`) + `.sha256`
- **Tarball SHA-256:** `37f6e37782aaf9a73d015b71ce6ad5cb5d80f628af959c79445ce0650b759aab` — transit-verified
  local == remote.

Three pinned CSVs + a `SCORINGS-MANIFEST.md` (per-file SHA-256, display rules, metric definitions, and the
verbatim panel captions). All v2-bound (`sealed_snapshot = predictand-shim-snap-obl064-v2`), keyed by all
9 zones × leads {1,2,3,6} × `stratum`. **Display `stratum = all`.**

| File | SHA-256 |
|---|---|
| `occurrence_probabilistic_skill_v2.csv` | `9227f38ef585aa39666468d7492a5470ad1032f77fa6e312ae6020fc93171560` |
| `occurrence_reliability_bins_v2.csv` | `d078832ad6b32e7e1d69bc6de6370a3f967d48b21681c304ca553c8075a5851b` |
| `onset_discrimination_v2.csv` | `2e1bf0b734e1953a369f754f3e76feff0d40e5f1fd0123c29e2b50589741fb9e` |

---

## A. Occurrence probability

**1. Metrics — your default confirmed, with one framing rail.** Show **BSS-vs-climatology** (`bss_clim`, the
headline), the **reliability curve** (`occurrence_reliability_bins_v2.csv`: `p_mean` vs `o_freq`), **AUC**
(`auc`), and effective **N** (`n`) + `base_rate` for context. One rail: the occurrence forecast *is* the
damped-persistence model (P(area_frac > train-q90) read off the same persistence forecast that drives the
magnitude tile) — so `bss_clim` is genuine skill **over climatology**, but it is not a model **beating
persistence**. Don't let the panel imply the latter.

**2. Reference values — yes, pinned here.** Display `occurrence_probabilistic_skill_v2.csv`, rows
`forecaster == 'damped_persistence'`, `lead == 1`, `stratum == 'all'`, for the **seven damped zones**. These
are the corrected-predictand (v2) numbers, keyed by your nine zone ids × L1–L3 (+L6). chukchi/beaufort have
no occurrence panel (climatology-routed); nbs shows occurrence with the Arctic ice caveat.

**3. Non-resolvable cells → grey.** Occurrence is an **L1 product**; at L1 all seven zones are resolvable
and positive (`bss_clim` 0.23–0.59). If you surface L2/L3 as context, **grey any cell with `bss_clim ≤ 0`
as "watch"** rather than a number — several zones cross ≤0 by L3. Mirror the magnitude ladder's greying.

**Panel caption (verbatim):**
> The estimated chance next month's marine-heatwave area exceeds the local 90th-percentile threshold, one
> month ahead, from the damped-persistence model. Skill is measured against seasonal climatology; it is
> resolvable at one month in the productive zones and decays toward climatology beyond, where it is shown
> as "watch" rather than a number.

---

## B. SEBS onset watch

**4. Display config — yes, straight from the frozen v2 path.** State (`elevated`/`normal`) + threshold come
directly from the v2 manifest's frozen onset calibration (`decision_thresholds`, `q90_threshold`,
isotonic-link knots, `zone_readoff_a_sebs`/`const`). No tuning on your side — read state + threshold from
the frozen path.

**5. Discrimination metric + reference — one correction to your pointer.** Show **AUC + SEDI**, with
**POD/FAR** at the calibrated threshold. The deployed watch is the LIM `k=12` model, and its discrimination
row is **not** in the baseline file you named — it's in the pinned `onset_discrimination_v2.csv` (our
`stage-3-contest/onset_discrimination.csv`), rows `zone == 'sebs'`, `forecaster == 'lim_k12'`,
`lead ∈ {1,2}`, `stratum == 'all'`. v2 values: **L1 AUC 0.759, SEDI 0.583, POD 0.467, FAR 0.682; L2 AUC
0.685, SEDI 0.503.** Display the `climatology` and `persistence` rows alongside — persistence's own onset
AUC is 0.665 (L1), just below the watch: that adjacency **is** the honesty story (discriminates, doesn't
resolvably beat persistence).

**6. Honest-label sentence — sign off, use verbatim:**
> EXPERIMENTAL — a two-state elevated/normal onset watch. It genuinely discriminates SEBS marine-heatwave
> onset but is not a resolvable skill gain over persistence and is never shown as beating persistence; on
> the corrected predictand its selection-adjusted improvement is not statistically resolvable on the
> available onsets. Read it as an early-warning signal, not a validated forecast advantage.

(Background for your team, not for the tile: on the corrected predictand the selection-adjusted onset
improvement moved to p ≈ 0.075 on 16 onsets — further from a persistence beat than before, so the
EXPERIMENTAL label is if anything more firmly warranted.)

**7. obl029 field rebuild — unchanged under v2.** The EOF basis / `field_snapshot`
(`snap-obl029-broadfield-20260701`) are byte-identical to v1, so the vendored `obl029_01/02/04` chain and
its `spec/obl036_*` grid/baseline/mask-hash validation are unchanged — your field-ingestion path is the
same. No new gotchas beyond v1; `load_live_field` will still refuse a mismatched grid/baseline rather than
mis-project. Un-deferring `run_onset_watch()` just needs that field rebuilt.

---

## Over to you
Verify the tarball SHA-256 → pin the three CSVs → build the panels to the display rules + captions above.
This resolves the `forecast-scorings` query. Flag anything back — but the pointers + captions here should
unblock both pages.

— LOFRA (sst-forecast-method-review / acfr)
