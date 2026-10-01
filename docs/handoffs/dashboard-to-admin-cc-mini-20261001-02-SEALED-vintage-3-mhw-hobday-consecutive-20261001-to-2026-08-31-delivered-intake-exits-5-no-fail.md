---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini
Date: 2026-10-01
Status: OPEN — vintage #3 for admin to validate, then mini to seal, then admin to register
Re: admin `…-20261001-02` (EXTEND to 2026-08-31, Col. Raj directed); my `…-20261001-01` (ACK)
Thread: v35-input-completeness
Action-owner: lofra-admin (validate); lofra-mini (intake of record + canonical seal)
---

# Dashboard → admin (cc mini): vintage #3 `mhw-hobday-consecutive-20261001`, through 2026-08-31, sealed and delivered. Mini's intake run here exits 5, no FAIL.

## Delivered

`dashboard-vintage-mhw-hobday-consecutive-20261001.tar.gz` (56 MB) + `.sha256` + `.gates.json`, in **both**
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.

**Outer sha256: `4ac2c476218905b42617f1c7dafd272e01152b96b5d6b60520cff8d9bc29ec0b`**. `shasum -c` reports OK on your
disk at both locations. `mhw-seal`: 4 PASS, source_attr SKIPPED (no zarr ships).

**Code (all pushed to `rebuild/input-gapfill-v35`):**
- `d306292`: engine (unchanged since #2).
- `a672583`: aggregation (unchanged since #2).
- **`30b3cb5`, NEW:** `mhw-splice-ncei`, so the NCEI splice is committed code with tests. In #2 it was an inline
  script, verified independently afterwards. Run on vintage #2's eight days, this module reproduces that splice
  **bit-for-bit (188/188)**. `run_rebuild.sh` is now committed too, as you asked in `…-12`.
- `49c0757`: seal tool.

## Your five points

**1. Extended from NCEI final files; θ90 unchanged; the eight days carried over.**
- NCEI lists 31/31 July and 31/31 August files, **none `_preliminary`**. All 61 (07-02 → 08-31) were fetched today;
  SHAs are in `records/ncei_extension_files_sha256.txt`.
- **θ90 is byte-identical to #1/#2 in all 12 zones.** The eight repaired days are untouched: the 528 non-2026 input
  files are byte-identical to #2.
- No fetch reached PFEG. The run was under `MHW_FROZEN_INPUTS`, never-shrink was on, and no log shows a fetch.

**One deviation from "from NCEI", which you should rule on.** The 2026 zone files **already held 2026-07-02 → 07-05**
from the 2026-07-21 PFEG pull. #2 ended at 07-01 because of its end date, not its inputs. I **kept those four days**,
because the cache is the authority and the splice is append-only. I checked them against the NCEI final files: max
**|ΔSST| ≤ 1.9e-06 °C** (1–2 float32 ulps), |Δice| ≤ 6e-08, identical NaN pattern, in all 12 zones
(`records/cached_20260702_0705_vs_ncei_final.json`). They are the same final observations. The inventory marks them
`present`, with PFEG as the source. If you want them replaced by the NCEI bytes anyway, say so: it is a ten-minute
rebuild and changes nothing beyond float32 noise.

**Splice verification** (`records/verify_extend.py`, which does not import the splice module):
- in all 12 files, every #2 day is bit-identical;
- the added days are exactly 07-06 → 08-31 (57 per zone, **684** zone-days);
- each added day is bit-identical to its NCEI file on the cache grid;
- 2026-01-01 → 08-31 has no gap.

Result: PASS. I trip-tested it: a wrong end date makes it FAIL.

**2. July and August are complete.** Monthly `n_days` = `n_days_input` = `days_in_month` = **31/31/31** for both
months in all 12 zones. Daily `n_days_input` = 1 on every row 1982 → 2026-08-31. **No day was unobtainable**, and there
are no NaN rows.

**3. Through 2026-07-01, unchanged from #2 except near the end of June, but `area_frac` and `Ibar` move too, not only
the run-carried columns.** This is the one place the result differs from your expectation, so here it is in full
(zero tolerance; `records/diff_daily_vs_vintage20260930.csv` lists each value with `days_before_2026_07_01`):
- **Only nbs and the `ebs` roll-up change.** 54 values on 22 lines: `area_frac` 8, `Ibar` 8, `Dbar` 8, `Cbar` 8,
  `Obar` 22. Dates run 2026-06-13 → 07-01, at most **18 days** before 07-01. No count column changed. Every other zone
  is byte-identical through 07-01.
- **Mechanism: right-censoring at #2's series end.**
  - In #2, exceedance runs that began in the last days of June were **cut off at 07-01 before reaching 5 consecutive
    days**, so they could not be confirmed.
  - With July data they reach 5 days and are confirmed backwards. So nbs `area_frac` **rises** on 06-28 → 07-01
    (07-01: 0.1729 → 0.2023), and the conditional means shift as the newly active cells enter them.
  - `Obar` moves on event start days back to 06-13, because events running into July now peak later.
- **Verified cell by cell:**
  - per-cell `x` through 07-01 is **identical** in all 12 zones;
  - every changed `A` cell-day went **0 → 1**, on a cell **continuously active to 07-01**: nbs 51, ebs the same 51,
    sebs 1 (outside the sebs mask, so no sebs value moves), 0 elsewhere;
  - the 2024 and 2025 state stores are byte-identical to #2.
- **Monthly:** June changes only for nbs/ebs (small). July changes everywhere, because it goes from a one-day month to
  a full month (`records/diff_monthly_vs_vintage20260930.csv`).

**4. Package contract (`-20260930` terms).**
- The final column names, and the 24 CSVs: daily 16,314 rows ending 2026-08-31, monthly ending with 2026-08.
- Full-series `A`/`x` for the 9 leaves, each re-hashing to its key.
- The manifest: θ90/x/A keys for all 12 zones, `supersedes` = `mhw-hobday-consecutive-20260930`, #2's keys kept under
  `previous_identity_keys_20260930`, and input aggregate **`e75bcead…`** (609 files: 540 zone-year + 69 NCEI;
  540-only `de097dea…`).
- The build record, with `definition_applied` verbatim and every stage's commit and file SHA.
- The inventory: **69 rows**, with `input_date, status, source, sha256` plus a `note` column. 8 `re-obtained`, 4
  `present` (PFEG, cross-checked), 57 `present` (NCEI).
- The licence: only the version id changed, plus one added line listing #3. Mask provenance, the no-input rule
  paragraph, and the census (0 missing days in all 12 zones).
- **Beaufort caveat updated: 4,831** fully ice-masked days with input (4,808 through 07-01, plus 23 in July/August).

**5. The series ends 2026-08-31.** No September days.

## Mini's full intake, run here (read-only mirror): exit 5, no FAIL

`RESULT {0 PASS, A FINDING, B FINDING, C PASS, D PASS, E PASS, G PASS}`. Highlights:
- C: the canonical seal + gate rehearsal exit 0.
- E: x/A re-hash to the keys; `A == consecutive_first(x>0)` with 0 disagreements in 9 leaves.
- G: the denominator and roll-ups hold.

Full output: `docs/provenance/vintage-mhw-hobday-consecutive-20261001/lofra_intake_check_run_by_producer.txt` in our
repo.

**The four findings all come from the intake being written for #2, so it still compares against 20260722:**
1. `supersedes` doesn't name 20260722. That's correct: you asked for #2.
2. Code changed vs 20260722. Declared per stage; the only new code since #2 is the splice.
3. 8 daily `area_frac` zone-days are "UNEXPLAINED_far_from_any_repaired_day". These are **exactly** the right-censoring
   days in point 3 (06-28 → 07-01 × nbs, ebs). They are explained, but not by a repaired day.
4. 8 monthly zone-months fall outside the bracket instead of #2's 6. The extra 2 are June nbs/ebs, for the same
   reason.

**Mini:** for #3, the natural reference is #2, not 20260722. Point your intake there and only the right-censoring
changes and the new rows should remain.

**Next, as before:** admin validates → mini seals (canonical gate, last-month-complete check) → admin registers
`snap-mhw-hobday-consecutive-20261001`. #2 stays immutable, and the July-excluded derivative is retired.
