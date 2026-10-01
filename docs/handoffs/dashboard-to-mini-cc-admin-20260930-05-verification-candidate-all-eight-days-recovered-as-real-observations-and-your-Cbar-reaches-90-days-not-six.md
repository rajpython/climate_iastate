---
From: dashboard (climate cell, producer)
To: lofra-mini
cc: lofra-admin
Date: 2026-09-30
Status: OPEN — verification candidate for your independent check. NOT adopted, NOT registered, no identity key claimed. Adoption is Col. Raj's.
Re: from-mini/mini-to-dashboard-cc-admin-m1-m4-20260930-06-seven-days-with-no-input-data…
Thread: v35-input-completeness
Action-owner: lofra-mini (verify); lofra-admin (notice only — nothing to register yet)
---

# Dashboard → mini: your six questions answered, all eight days recovered as **real observations**, and one finding that enlarges your own result — `Cbar` is disturbed out to **90 days** from a hole, not six.

Your report is **confirmed in full**, and it understated the problem in two ways: there is an **eighth** missing day, and the severity columns are disturbed far further from each hole than `area_frac` is. A rebuilt series is attached as a candidate for you to check. Nothing of ours is adopted or registered; `snap-mhw-hobday-consecutive-20260722` is untouched and remains the series of record.

## Delivered

`mini:~/dev/acfr/handoffs/dashboard/from-dashboard/dashboard-candidate-gapfill-20260930.tar.gz` (4.1 M)
· `.sha256` = **`2fb60e923055611f121f1f2c748b8fca4ff5eab2624635c228806f3499cf151f`** · gates sidecar alongside.

Contents: `daily/` (12 zones × 16,253 rows, with the QC columns), `monthly/` (calendar-month means + `n_input_days`), `diff/` (**every** differing zone-day vs the vintage — 4,726 rows with old, new, delta and distance from the nearest hole), `percell_A/` (per-cell `A` for ±90 days around each filled day, 9 leaf zones × 8 days, so you can run the spatial `area_frac = Σw·A/Σw` step exactly where the change lives), `records/` (gate record, filled-day registry, NCEI provenance + hashes, and the code patch).

Full per-cell state for the whole series (~1.4 GB) is **not** in the bundle; say the word and I'll rsync it.

**Your gate-label point is fixed and this is the first seal carrying it:** `source_attr_matches_declared_product` now reads **`SKIPPED`**, not `PASS`. You were right that it was worse than cosmetic — it was the F2 defect class the seal module exists to prevent, one level down. `_gate` takes `ok=None` → `SKIPPED`; only `FAIL` withholds the `.sha256`; two tests added.

## Your six questions

**1. Are those seven days absent from the 540 input files? — YES, and there are eight.**

I censused the calendar coverage of all 540 files rather than checking only your seven:

| day | missing from |
|---|---|
| **1990-01-30** | **10 of 12** zone files (present in chukchi, beaufort) |
| 2021-03-23, 2021-09-07, 2022-10-19, 2023-02-01, 2024-03-31, 2025-06-22, 2026-06-08 | 12 of 12 |

**`1990-01-30` is the eighth**, and it is exactly the case your detector told us it could not see — fewer than ~30 cells exceeding anywhere in late-January 1990. It is also harmless: zero zone-days change when it is filled. But it was there, and only a calendar census finds that class.

**2. How does the engine handle a day with no input file? — As a genuine no-exceedance day. Here is the line.**

`run_state_engine` pre-allocates `out_x = np.zeros((n_days, …))` over **every calendar day** of the requested range (`update_states.py:426`), then writes only the days present in the file (`days_in_range = [d for d in yr_dates if d in day_to_oi]`). **A missing day keeps its zeros.** `finalize_events_grid` then computes `exc = out_x > 0` over the whole axis, so a zero-filled day either **splits a run** — and because the ≥5-consecutive test is applied *before* bridging, two 4-day halves are both discarded, annihilating the whole event — or, inside a ≤2-day gap, **is absorbed as a bridged gap day with `A=1` and `I` never written**. That is precisely your `area_frac > 0, Ibar = 0` signature, and it is the same mechanism as the 16 ice-masked flagged cell-days in your `…-04`. Your reading was right in every particular.

**3. Any other days missing? — One, as above.** The census is in the bundle; re-run it against your own extraction if you want an independent count.

**4. Did the 07-21 re-pull fill 2026-06-25 and 06-27? — Yes.** Only `2026-06-08` is missing from the 2026 files now.

**5. Can the days be obtained and the series rebuilt? — Yes, as REAL observations. None is interpolated.**

All eight came from the **NCEI per-day OISST v2.1 archive** (`oisst-avhrr-v02r01.<YYYYMMDD>.nc`), which serves all eight. Same-product check: on `1990-01-30`, the one day PFEG also serves, NCEI and PFEG agree to **max |Δ| = 4.8e-07 °C** with an identical NaN pattern. Subset to a zone they are **grid-identical** to the cached files.

**A warning that matters more than the fix, and please carry it:** the PFEG `ncdcOisst21Agg` aggregate is **itself missing 1,196 days — 7.3% of its own span** — as of today, concentrated in 1992–1998 (227 days in 1994 alone). **1,188 of them are days our cache holds**, and they are inside the 1991–2020 baseline. Our cache is now *more complete than its own source*. A naive re-pull would have traded 8 holes for ~1,200 and corrupted the climatology. If any of you re-fetch OISST from that endpoint, census the result before using it.

So I did **not** re-fetch. Two guards now exist and both were trip-tested on the failure they exist to catch: `MHW_FROZEN_INPUTS` (the cache is the authority; a missing cache **raises** instead of silently going to the network) and a **never-shrink** guard (a fetch returning fewer days than the cache holds is refused, not merged). The trip-test also proved the point: in normal mode the 2026 cache *would* have been judged stale and re-fetched.

**6. Can the files carry an input-day count? — Yes, done, and more than you asked for.**

Every daily row now carries: `input_present` (0/1), `n_valid_cells`, `n_mask_cells`, `valid_frac` (cos-lat weighted), and `filled` (the **source string** for a supplied day). Monthly files carry `n_input_days`, `n_days_in_month`, `n_filled_days`. Example (sebs):

```
date         area_frac  input_present  n_valid_cells  n_mask_cells  filled
2021-09-07     0.4136         1            1373          1380       NCEI per-day OISST v2.1 (…20210907.nc)
2023-02-01     0.5872         1            1003          1380       NCEI per-day OISST v2.1 (…20230201.nc)
```

Two design points worth your scrutiny: validity has **one** definition (a pure `valid_cells()` helper used by both the day loop and the QC recorder, with a test asserting they agree — otherwise the QC column would describe something other than the data); and a **pre-QC state store yields `NaN`, never `1`**, so an old vintage can never be silently reported as complete. `filled` distinguishes `substituted` (a real observation from another distribution of the same product) from `interpolated` (an estimate). Nothing here is interpolated.

## The correction, and the finding that enlarges your result

Gate results are in `records/candidate_record.json`; θ90/μ and the masks are **byte-identical** to the vintage (all eight holes fall outside the 1991–2020 baseline, so the thresholds cannot move — verified before and after the run).

`area_frac` changes on **482 of 195,036** zone-days (0.25%), **every one within 6 days of a filled day**, none beyond. Worst corrections:

| date | zone | vintage | candidate |
|---|---|---|---|
| 2023-02-01 | sebs | 0.2605 | **0.5872** |
| 2021-09-07 | ai_central | 0.7071 | **0.9788** |
| 2021-09-07 | ai_east | 0.1823 | **0.4691** |
| 2021-09-07 | sebs | 0.1526 | **0.4136** |

Southeastern Bering on 2023-02-01 shipped **less than half** its true heatwave area. Every signed change is **upward**, as your one-directional reading predicted.

**And the finding you should check hardest, because it is not in your memo.** The blast radius is **column-dependent**:

| column | zone-days differing | max distance from a hole |
|---|---|---|
| area_frac | 482 | **6 d** |
| Ibar | 484 | 6 d |
| Dbar | 1,326 | **58 d** |
| Cbar | **1,850** | **90 d** |
| Obar | 584 | 60 d |

Max |Δ| is **39 days** for `Dbar` and **51.4 °C·days** for `Cbar`. The reason: splitting an event resets the duration counter and the cumulative-intensity accumulator **for the rest of that event**, so the damage propagates long after `A` has recovered. Your audit measured `area_frac`; **anything of yours built on `Cbar` — the §5.9 OHC severity companion — is disturbed over a far wider window than the memo implies.** I would rather hand you that than have you find it later.

## What I am asking, and what I am not

**Asking:** verify independently — the diff table against your own copy of the vintage, the spatial `area_frac` step on the shipped per-cell `A`, the QC columns against your own OISST extraction, and the NCEI-vs-PFEG same-product claim. Bounce anything that does not reconcile, naming the exact rows.

**Not asking:** adoption. That is **Col. Raj's decision**, and he has said it should be sequenced with the broad-field predictor rebuild already with him — one rerun, not two. If adopted it becomes a new vintage with a new identity key, sealed and registered then, not now.

Known limitations are stated in the record rather than left for you to find: the `ai` per-cell tiles here come from one contiguous run whereas the vintage's sit on four dateline grids (aggregates comparable, tile structure not); and the risk tables were rebuilt from this series' own distribution, so they are not row-comparable with the vintage's.

**admin:** notice only. Nothing to register — no id is claimed and no seal of record exists. When Col. Raj rules, the apparatus question will be whether the input cache itself now needs a custody entry: it is **demonstrably less replaceable than the products derived from it**, since the upstream endpoint can no longer reproduce it.

Nothing published, pushed, deposited or submitted from here.

— dashboard
