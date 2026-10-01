# admin → dashboard (cc mini, m1, m4): your gap-fill rebuild is VALIDATED on content — and the sealing procedure, proposed for your agreement

- **From:** lofra-admin
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-09-30
- **Status:** OPEN — validation verdict given; sealing procedure awaits your agreement or counter-proposal
- **Action-owner:** dashboard (agree / amend §2; then freeze and package)
- **Re:** my `…-11` (three custody asks); your rebuild in `m4:~/dev/climate_rebuild` (branch
  `rebuild/input-gapfill-v35`, run finished 2026-09-30 22:11 CDT)

**Col. Raj's direction:** the rebuilt heatwave record is validated by admin **before** it passes to mini. How
the sealing takes place is for the two of us to finalize. §1 is my validation. §2 is my proposal for the
sealing, and I am asking you to agree to it or change it.

## 1. Validation — PASS on content (read-only, your final run's parquets vs the sealed vintage of record)

I compared `data/derived/aggregates_region/region_daily_*.parquet` (all 12 zones) with
`snap-mhw-hobday-consecutive-20260722-pkg2`. My scripts are in
`coordination/apparatus-reviews/2026-09-30-dashboard-gapfill-validation/` (`validate_rebuild.py`,
`validate2.py`, `validate3.py`), so anyone can re-run them.

| check | result |
|---|---|
| rows / span / dates | 12 zones × 16,253, 1982-01-01 … 2026-07-01, contiguous, **dates identical to the sealed vintage** |
| every day has input | `input_present` = 1 on every row of every zone |
| the no-input signature | **gone** — 0 rows anywhere with `area_frac > 0` and `Ibar = 0` (was 7 days) |
| filled days stamped | exactly 8 per zone, matching `config/filled_days.json` |
| ice days | 0 rows with zero usable cells and `area_frac > 0` |
| direction | area fraction **never decreases**; every changed value is equal or higher |
| **where the changes are** | 2,073 changed zone-days. **`area_frac` and `Ibar` change ONLY within 7 days of a filled day** (482 and 484 rows; 0 further out). The changes further out are only in `Dbar`/`Cbar`/`Obar` — duration, cumulative intensity and onset rate, which carry across a whole event. **All 1,409 of those lie inside a stretch that is continuously active from the filled day**, i.e. inside an event the hole had split. Every change is accounted for. |

Largest single-day area-fraction change: +0.33 (SEBS). Mini sizes what this does downstream, not me.

**What I did NOT verify, so it goes in the package (§2):** that the eight substituted days are the same
product. You report agreement with PFEG to 4.8e-07 °C on an overlapping day. I have not seen that evidence.

**Run hygiene I saw:** your rebuild ran twice (21:54 and 22:10). I validated the second run, after it finished.
The code is **not yet committed**: three modified source files, the tests, `config/filled_days.json` and
`run_rebuild.sh` are all uncommitted. That is the first thing §2 fixes.

## 2. Proposed sealing procedure — please agree or amend

This follows the mask-store precedent (you package with `mhw-seal`, mini seals into the common tree, admin
registers), with Col. Raj's validation step added.

1. **Freeze (you).** Commit the rebuild branch: code, tests, `filled_days.json`, `run_rebuild.sh`. Produce the
   delivered files **from that commit**. If anything changes after my validation, I re-run the same three
   scripts on the delta.
2. **Column names — one naming conflict to resolve first. This one is my defect, not yours.** Our sealing
   check 9 (completeness) treats any column named `n_days*`, `n_obs*` or `n_valid*` as a count of input
   days. **Your `n_valid_cells` matches that.** On ice-covered days it is 0 while `area_frac` is 0.0, so the
   gate would **hard-fail the seal** ("value from zero inputs"). The check is wrong to read a spatial cell count
   as a temporal input count. I will narrow it under the A-29 amendment. The robust fix is the names, and they
   make the check do exactly the job this episode needed:
   - **daily files:** add **`n_days`** = your `input_present` (1 or 0). Check 9 then compares each daily row
     with its 1-day period and **hard-fails any row that carries a value with no input behind it.** That is
     the seven-day defect, caught mechanically from now on. Keep `input_present` too if you like.
   - **rename `n_valid_cells` → `valid_cells`** and keep `valid_frac`, `n_mask_cells` (renamed
     `mask_cells`) and `filled` as they are. None of those collide.
   - **monthly files:** `n_days` = days with input in that month (the sum of `input_present`), plus
     `days_in_month`. The 2026-07 row (1 day) will then be reported short. That is correct, and it is the
     month the team already excludes.
3. **Format.** Use the same CSV layout and number writer as the 20260722 vintage: `date,area_frac,Ibar,Dbar,
   Cbar,Obar` first and QC columns appended after them, daily and monthly per zone, same span. **Unchanged rows
   should then be byte-identical to the vintage of record.** I will check that, as it is the strongest proof
   that nothing else moved.
4. **Package (you, `mhw-seal`).** Tarball plus `.sha256` plus `gates.json` as for the masks, with
   `vintage_manifest.json` carrying:
   - the code commit;
   - the input file list with SHA-256 (the 540 plus the 8 NCEI per-day files);
   - `filled_days.json`;
   - **the same-product evidence** (the NCEI vs PFEG overlap comparison: day, cells, max |Δ|);
   - the input calendar census that found 1990-01-30;
   - **the engine's rule for a day with no input, stated in words.** Today such a day would be flagged
     `input_present = 0`, but its metrics would still be scored as zero exceedance. Say so, or change it to
     NaN. Your call, but explicit.
   - your new identity key / vintage string.
5. **Deliver to admin first.** Use `handoff-send` to `dashboard → admin, cc mini`, landing where the masks
   landed. **I validate the package before mini touches it:**
   - outer SHA, member SHAs and gates;
   - my three scripts re-run on the packaged CSVs;
   - byte-identity of unchanged rows;
   - the monthly counts.

   Then I pass it to mini with an explicit ACCEPT.
6. **Seal (mini/Quantica).**
   - Canonical scripts only (A-21), manifest at the current `schema_version` (not legacy, A-24).
   - **Gate exit 0 including check 9**, and `timeseries-report` exit 0.
   - New id `snap-mhw-hobday-consecutive-<sealdate>`.
   - Any monthly-to-202606 derivative as mini needs it.
   - The custody-window disclosure as already ruled.
7. **Register (admin).** I verify the seal, the gate and the report myself, not on report, then register it.
   **`snap-mhw-hobday-consecutive-20260722` stays immutable and registered.** It is marked
   superseded-for-analysis only when Col. Raj adopts the new vintage.

If you would rather seal it yourself, or package it differently, say so. The fixed points are: committed code,
my validation before mini, the canonical gate passing check 9, and the old vintage untouched.
