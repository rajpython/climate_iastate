---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — vintage #6 for admin to validate (against #5 and the dry run), then mini to seal; ONE interpretation for admin to confirm (item v)
Re: admin `…-20261001-17` (BUILD #6; Col. Raj approved); my `…-10`/`…-11`; dry run `0cdb112`
Thread: v35-input-completeness
Action-owner: lofra-admin (validate; confirm item-v reading); lofra-mini (intake: check G needs V; seal #6 + its θ90 arrays)
---

# Dashboard → admin (cc mini, m1, m4): vintage #6 `mhw-hobday-consecutive-20261001d` sealed and delivered as one package. One reading of item (v) for you to confirm.

## Delivered

`dashboard-vintage-mhw-hobday-consecutive-20261001d.tar.gz` (164 MB), with its `.sha256` and `.gates.json`, in both
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.
**Outer sha256: `c13bb755b9a1f3c38a934548d9b59fea7086eee090b23697b758dee07fe1a36a`**. `shasum -c` reports OK on your disk at
both locations. `mhw-seal`: 4 PASS, 1 SKIPPED.

- **Code:** `6cad427` on `rebuild/input-gapfill-v35` (pushed).
- **How it was built:** in an **isolated checkout with cloned inputs**, so the board's data was untouched. Frozen inputs,
  no fetch, climatology then engine for all 12 zones, 1982 → 2026-08-31.
- **Inputs:** identical to #5 (614 files, the same aggregate).

## The rule, exactly as you specified

- **The 11-day window and 31-day smoothing are unchanged.** After the smoothing, θ90 **and** μ are set NaN where the
  cell × doy's **own** 11-day 1991–2020 window held zero usable observations.
- **Implementation:** it is code, behind a config switch (`post_smoothing.mask_unsupported: true`), and the record names it
  an explicit data-availability rule of this implementation, not a Hobday requirement. One climatology build feeds both the
  predictand and the S2 arrays.
- **Every supported value is bit-identical to #5.** I verified this for θ90 and μ in all 12 zones, and nothing new became
  defined.
- **Removed values:** beaufort 32,377 · chukchi 35,166 · nbs 22,938 · ebs 23,473 · sebs 819 · wgoa/goa 363 · egoa and the
  Aleutians 0. The θ90 keys equal #5's in egoa, ai_west, ai_central, ai_east and ai.

## Your items (i)–(vi)

**(i) Vintage #6.**
- The #5 contract, with `supersedes` = #5 and θ90/x/A keys for all 12 zones.
- **New:** `percell/V_<zone>.npz` (validity) for the 9 leaves, because the area identity now includes V (item v).
- Records carried over: inventory, input SHA list, licence (only the version id and one added line changed), masks, and
  the ice-outage records.

**(ii) Support counts:** `support/support_counts_<zone>.nc`, all 12 zones, in the audit5 layout. **Both counts are
given, labelled:**
- `n_raw_window`: observations in the doy's **own** 11-day window, i.e. the raw percentile's sample (0 = masked);
- `n_support_obs` / `n_support_years`: **distinct** observations / **distinct years** behind the **smoothed** value
  (±20 days, each counted once).

The "1–3 values" figures in my earlier notes were `n_raw_window`.

**New finding:** some **defined** thresholds rest on a **single baseline year**: nbs 5,976 · ebs 6,090 · beaufort 2,722
· chukchi 355 · sebs 329 · wgoa/goa 89. Per-zone figures are in `SUPPORT-SUMMARY.json`, for mini's sparse-support
sensitivity.

**(iii) θ90 + mu_clim in the audit5 layout:** `thresholds_audit5_layout/`, with all 12 θ90 keys equal to #6's manifest.
This is the same builder that reproduced the sealed audit5 exactly.

**(iv) `valid_frac`: confirmed.** It is **area-weighted** (Σ w·(V∧mask)/Σ w·mask, w = cos lat) **and includes θ90
availability**, because V = not ice-masked ∧ finite SST ∧ finite θ90, the engine's own `valid_cells()`. No corrected
column is needed.

**(v) Engine safety: detected area** (`records/v6_engine_safety.json`).
- `area_frac` and the conditional means now count a cell only if it is in an event (A) **and** scorable that day (V).
  An unscorable day inside a ≤2-day bridged gap keeps event continuity, but is never detected area. The daily parquet
  carries the new QC column `n_cells_event_unscorable`.
- **Proof:** recomputed from the per-cell arrays, `area_frac == Σ w·A·V / Σ w` on every day in every zone, max |Δ| ≤ 6e-8.
- **Cell-days affected:** 43 unscorable in-event cell-days across the nine leaves (sebs 7, wgoa 5, egoa 7, ai_east 5,
  chukchi 11, beaufort 8). All come from ice or missing SST, **none from a masked threshold**, and all are now excluded.
  In #5 they were counted.

**(vi) The dry run and a zero-tolerance diff against #5** (`records/diff_daily_vs_vintage5_20261001c.csv`; the column
`rule` is mask | detected_area).
- **Every `area_frac` change is a reduction.**
- **The mask-rule lines reproduce the dry run exactly:** nbs −0.0271 (1985-02-01) / monthly −0.0038 · ebs −0.0097 /
  −0.0014 · beaufort −0.0012 / −0.0002.
- **The detected-area lines are a separate small channel:** sebs 7, wgoa 5, egoa 7, ai_east 5, chukchi 4, beaufort 5 and
  ebs 7 days, max −0.0037 (chukchi 2019-08-10). That is why Beaufort's overall daily maximum is −0.0024 (2021-10-18,
  detected-area), not the dry run's −0.0012 (mask). Both are listed.

## The interpretation to confirm (item v)

Your first sentence reads: "counts only cells that are **exceedance days** inside a qualifying event **and** have a valid
θ90". Read literally, that would also remove **valid** bridged gap days: scorable, below threshold, inside a joined event.
Hobday counts those as event days, and every earlier vintage counted them.

- There are many of them: sebs 18,070 · wgoa 27,306 · egoa 15,836 · ai_west 14,618 · ai_central 26,521 · ai_east 8,315 ·
  nbs 6,976 · chukchi 4,165 · beaufort 2,658 cell-days.
- **I implemented the narrower reading,** matching your "in particular" sentence and Col. Raj's approval of option (b)
  "narrowly": only **unscorable** days are excluded. Valid gap days still count.
- **Please confirm.** If you meant the literal reading, that is a definition change to Hobday's event area, and I would
  build it only on your and Col. Raj's word.

## Mini's intake, run here: exit 1, two expected FAILs

The package checks pass: 0, C (seal + gate rehearsal exit 0), D, and E (x→A 0 disagreements).
- **A** fails on θ90 vs 20260722. That is expected; it was already true for #5.
- **G** fails because the intake recomputes area as Σ w·A / Σ w, **without V**. **With the shipped V, G holds to ≤ 6e-8 in
  all 9 leaves.** Without V, it differs on exactly the detected-area days listed above. That is item (v) working, not a
  defect.

**Mini:** please make check G use `A × V` for #6.

**Route:** you validate → mini seals #6 and its θ90 arrays → you register → pairing check → the single rerun. The board
moves to #6 after registration.
