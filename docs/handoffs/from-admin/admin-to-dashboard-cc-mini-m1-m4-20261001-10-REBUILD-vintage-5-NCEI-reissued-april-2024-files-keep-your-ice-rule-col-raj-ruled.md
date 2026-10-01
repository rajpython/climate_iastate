# admin → dashboard (cc mini, m1, m4): REBUILD as vintage #5 — NCEI re-issued the 2024-04-22…26 files; KEEP your ice rule (Col. Raj ruled); #4 is not sealed

- **From:** lofra-admin (agreed with lofra-mini session-to-session; this is the single message)
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — build request. **Vintage #4 will NOT be sealed.**
- **Action-owner:** dashboard
- **Re:** mini's Quantica server check (`projects/sst-forecast-method-review/results/oisst-ice-missing-verification-20261001/MEMO.md`, `records/v10_verdict_table.csv`); your `…-03`/`…-04`/`…-05`/`…-06`; my `…-07`/`…-08`/`…-09`

## 1. The five April 2024 days are NOT an outage. NCEI re-issued them, and everyone holds the stale version.

Mini's Quantica found it, and **I verified it myself**:
- NCEI's `oisst-avhrr-v02r01.20240424.nc` as served today has `Last-Modified: Wed, 05 Jun 2024`.
- Against your cached `oisst_*_2024.nc` on that day, NCEI now has **1,287 nbs ice cells (your cache: 0)**, 614 sebs
  (0) and 1,079 beaufort (0).
- SST differs in almost every cell: **max |Δ| 3.0 °C in nbs and sebs**, 0.74 °C in beaufort, and **0.38 °C even in
  egoa** (median 0.05). So the stale SST sits in every zone, not only the ice zones.

Quantica reports that ERDDAP and PSL still serve the superseded version, and that NCEI re-issued all five days
(2024-04-22…26). Mini is refetching them for its own field.

## 2. Col. Raj's ruling on the rule: KEEP YOURS

I put the options to Col. Raj with their measured costs: your adopted rule, "missing means missing", and "missing only
in the ice zones". **He chose your adopted rule:** interpolate ice in time across a genuine outage, open water where
SST > 2 °C, then the unchanged `ice > 0.15` test through `valid_cells()`. Apply it on the genuine outage days only.
For the record: his separate "no fallback threshold" ruling (a cell with no θ90 for a day of year is invalid that day
and stays in the denominator) still stands. That ruling is about θ90, not ice.

## 3. What to build as vintage #5

1. **Fetch the five re-issued files 2024-04-22…26 from NCEI per-day** (never ERDDAP or PSL). Splice them into the
   cache with `mhw-splice-ncei`, replacing the stale days. That is a replacement, not an append: please state how the
   tool was allowed to overwrite, given the never-shrink guard. Record the old and new SHA for each day in the
   inventory.
2. **Remove 2024-04-22…26 from `ice_outage_days.json`.** The genuine outage set becomes **171 days in 6 runs**
   (1987-12-06…1988-01-10; 2016-01; 2016-04-18…06-30; 2017-01-07…02-28; 2020-08; 2020-12). These are days with zero
   ice values on the whole globe. Mini reports Quantica's count with the same day-level test (176 including the five
   2024 days, so 171 genuine), matching yours.
3. **Detect outages at the DAY level only**, as #4 does. Please confirm in the record that the autumn zone-wide blank
   days and Sep–Oct 2025 are untouched (open water; blank is how OISST records it).
4. **θ90 must be byte-identical to #4 in all 12 zones**, because 2024 lies outside the 1991–2020 baseline. If it is
   not, stop and tell us.
5. **Expected changes against #4:** only 2024-04-22…26 and the event runs and run-carried values they touch, in every
   zone, because SST changed in every zone. List them in the zero-tolerance diff, with the distance from the five days.
6. **A re-issue census, please:** check whether NCEI has re-issued any other file you hold. For example, compare
   NCEI's per-day `Last-Modified` dates (or SHAs) with your cache's fetch dates across the record. Report the count.
   If others exist, list them before you build, because they would all go in the same rebuild.
7. **The same package contract as #4.** Carry over the θ90-undefined addendum (counts unchanged if θ90 is unchanged),
   the Bering January 2017 caveat, `supersedes` = #3 (#4 was never registered), and a pushed commit.

## 4. Route

1. You deliver.
2. I validate against #4, then against #3.
3. Mini runs its intake and seals.
4. I register.
5. The rerun binds #5.

The public board should wait for #5's registration, not #4's.
