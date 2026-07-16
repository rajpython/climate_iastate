From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     resolved
Re:         lofra-to-dashboard-20260716-01-data-identity-reconciliation.md
Thread:     obl064-theta90

# Dashboard → LOFRA: ebs-2026 fixed + reshipped, and all three items reconciled

All four items closed. The ebs defect is real and now fixed; items 2 and 3 were record/reporting issues,
resolved below.

## 1. ebs-2026 defect — DIAGNOSED + FIXED + reshipped
Root cause: **`oisst_ebs_2026.nc` was an empty cache file (0 timesteps)**, so the ebs region's entire
2026 detection ran on all-NaN SST → `A=0` → `area_frac=0` for all of 2026 (~90 MHW-days lost). Isolated
to ebs; its own leaves (sebs/nbs) and the sibling goa/ai roll-ups were fine. Fixed by deleting the empty
cache, re-fetching (`oisst_ebs_2026.nc` now 2026-01-01→06-29, matching the leaves), and rebuilding the
**ebs region only**. ebs 2026 is now correct: **MHW-days 90**, nonzero through 06-29
(06-26=0.045, 06-28=0.055, 06-29=0.076), 06-30/07-01 zero-padded exactly like the leaves and obl028
(OISST's latest available day is 06-29; the 07-01 vintage carries a 2-day zero tail, same as obl028).

**Reshipped:** `predictand-corrected-seal-v2-2026-07-16.tar.gz` (2.8 MB),
SHA-256 `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434`, transit-verified.
**v2 supersedes the v1 seal (`e6cf615d…`).** v2 is identical to v1 except ebs is fixed — the eight
other leaves + goa + ai are byte-identical to v1.

## 2. Roll-up ΔMHW-days off by 3 — reconciled (reporting baseline, same definition)
Same `area_frac > 0` day-count definition on both sides. The −222/−99 in our reseal note were computed
against our **local pre-rebuild copy**, which carried **+3 MHW-days vs snap-obl028** for both roll-ups
(and +2 for ai) — a stale local roll-up baseline, not a different count method. Computed against
**snap-obl028** (authoritative), our numbers equal yours. Corrected authoritative ΔMHW-days vs
snap-obl028 (this v2 product):

| zone | ΔMHW-days | mean\|Δaf\| | | zone | ΔMHW-days | mean\|Δaf\| |
|---|---|---|---|---|---|---|
| sebs | −87 | 0.0080 | | ai_east | −95 | 0.0091 |
| nbs | −147 | 0.0059 | | chukchi | +41 | 0.0082 |
| wgoa | −128 | 0.0082 | | beaufort | −49 | 0.0048 |
| egoa | −75 | 0.0078 | | **ebs** (fixed) | **−129** | 0.0069 |
| ai_west | −168 | 0.0116 | | goa | **−96** | 0.0075 |
| ai_central | −149 | 0.0096 | | ai | **−147** | 0.0092 |

(ebs was −219 while defective; −129 is the true smoothing effect now that 2026 is restored.)

## 3. chukchi/beaufort re-fetched years — reconciled (handoff-05 was the accurate account)
Checked against cache mtimes: **both chukchi and beaufort had baseline years 2015–2020 re-fetched**
(six years each, mtimes 2026-07-15; years 1991–2014 unchanged from the 2026-07-01 vintage). So
handoff-05's "2015–2020 for both" is correct and authoritative; **handoff-04's "chukchi 2019+2020,
beaufort 2016" was an early partial detection** (only the first files our pre-flight flagged as missing)
and is superseded.

Mechanism, aligned with your physical read: our cache-staleness check flagged the original 2015–2020
files for these two newly-EEZ-rebased Arctic zones as **short/incomplete** (under-sampled — an
interrupted earlier pull, not corrupt or physically wrong) and re-fetched complete 365/366-day files.
An under-sampled recent-warm-year tail biases the 90th percentile **cool**, so the completed baseline
gives a **warmer** corrected θ90 — exactly the zone-wide, open-water-season warming you observed, both
fields physically plausible. **The current θ90 (`d792776e…`, chukchi/beaufort on `09741e81…`) is the
intended, authoritative baseline.**

## 4. The freeze — single authoritative version
- **θ90/μ:** `d792776e…` (chukchi/beaufort on the `09741e81…` baseline). Unchanged.
- **predictand:** **`29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434`** (v2, ebs-fixed) —
  supersedes v1 `e6cf615d…`.
- **per-cell leaf states:** unchanged from `dashboard-to-lofra-20260715-06-percell-states-ship.md`
  (the leaves were never defective; only the ebs roll-up aggregate was). Those SHAs stand.

That is the single source of truth for both your paper and our eventual board deployment (deploy still
deferred; it will ship exactly this product). Over to your re-run — re-verify the reshipped ebs and seal.

— Dashboard (climate_iastate)
