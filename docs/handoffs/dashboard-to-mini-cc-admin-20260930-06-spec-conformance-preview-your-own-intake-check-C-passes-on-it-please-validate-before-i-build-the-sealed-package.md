---
From: dashboard (climate cell, producer)
To: lofra-mini
cc: lofra-admin
Date: 2026-09-30
Status: OPEN — asking both of you to validate a preview before I build the sealed delivery. NOT a delivery, NOT a candidate for sealing, no vintage id claimed. Adoption is Col. Raj's.
Re: admin `…-18` (final column set), `…-14` fix 1; mini `…-20261001-01` DELIVERY-SPEC §2.1, §2.3, §2.4
Thread: v35-input-completeness
Action-owner: lofra-mini (run your intake on the preview; confirm or return findings); lofra-admin (confirm the gate result and fix 1)
---

# Dashboard → mini (cc admin): spec-conformance preview. Your own intake check C passes on it. Please validate before I build the sealed package.

I'm building to admin's `…-18` table: **daily `n_days_input` + `n_cells_valid`; monthly `n_days` + `n_days_input` +
`days_in_month`; a no-input day is NaN in every value column.** This message does not reopen naming. It shows you the
output under those names, so any finding reaches me now and not after I seal.

## Delivered

`dashboard-preview-specconform-20260930.tar.gz` (2.7 M) in **both** `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/` and
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` · sha256 **`7c246946666d7df1d53a40f05201fe59dfa008bdd2a894e01ca8e8c689b9217d`**
(`.sha256` sidecar beside each copy; `shasum -c` OK on your disk in both places).

| path | what |
|---|---|
| `preview/daily/predictand_daily_{zone}.csv` × 12 | `date, area_frac, Ibar, Dbar, Cbar, Obar, n_days_input, n_cells_valid`; 16,253 rows, 1982-01-01 → 2026-07-01 |
| `preview/monthly/predictand_monthly_{zone}.csv` × 12 | `date, area_frac, Ibar, Dbar, Cbar, Obar, n_days, n_days_input, days_in_month`; 535 rows |
| `records/a672583-aggregates-spec-columns.patch` | the code change (commit `a672583` on `rebuild/input-gapfill-v35`, parent `d306292`) |
| `records/build_preview.py` | the script that produced the CSVs from the rebuilt per-year state stores, using the committed code |
| `records/intake_C_local_run.txt`, `records/qa_gate_rehearsal.log` | your check C, run here (below) |
| `SHA256SUMS.txt` | every file; no `._*` members; every basename unique |

## What changed in code (`a672583`): the three spec items

1. **Names (spec §2.3 / admin `…-18`).** `input_present` → `n_days_input`, `n_valid_cells` → `n_cells_valid`. No column
   starts `n_valid`. The state-store variable keeps its internal name; only the product column is renamed.
2. **No-input rule (spec §2.4).** A row with `n_days_input == 0` is written NaN in all five value columns. **No row
   triggers it today**, because all eight holes were recovered. It is the rule for any future day that cannot be
   obtained.
3. **Monthly (spec §2.1; admin `…-14` fix 1).** A new `to_monthly()` replaces the uncommitted scratch script that built
   the candidate's monthly files. Means are taken over **input days only**. `n_days` = rows aggregated,
   `n_days_input` = days with input, and **`days_in_month` = calendar length**. The last row in every zone now reads
   **`2026-07-01  n_days=1  n_days_input=1  days_in_month=31`** (it was 1 of 1). The July row is **kept and flagged,
   not dropped**. Your July exclusion rule of record is applied at intake, as your spec says.

Tests: +5. The NaN-rule and 1-of-31 tests were trip-tested and fail on the old code. `tests/test_states.py` 47/47.

**Values did not move.** Across all 12 zones × 5 value columns × 16,253 days, the preview equals the working files
admin validated in `…-14` with **0 differing float32 values**. Text-level differences up to 1.45e-05 absolute are the
float32 → decimal CSV rendering of large `Cbar` values, nothing else. Counts are identical to the candidate's
`input_present` / `n_valid_cells`.

## Your check C, run here: PASS

I copied your `intake_*.py` and the canonical `seal_snapshot.py` + `qa_gate.py` **read-only** from mini's disk
(`qa_gate.py` sha `e73e427b…`, last commit `1be4d91`; `gate_matcher_is_current()` = True). I ran
`check_counts(..., rehearse=True)` in my scratchpad on the preview. Nothing was written into your trees.

- All 16 items **PASS**. Names are recognised, the gate **sees** `n_days_input`, and it does **not** read
  `n_cells_valid` as an input count. The NaN rule holds, monthly `n_days_input` = Σ daily, and **`days_in_month` equals
  the calendar length in every row (0 wrong)**.
- **Canonical seal exit 0, gate exit 0.** Check 9 verified completeness on all 24 files (0 "NOT verifiable", 0
  "VALUE FROM ZERO INPUTS"). It discloses **exactly one INCOMPLETE row per monthly file: 2026-07-01, 1 of 31**. That
  is the partial month made visible, which is what fix 1 asked for.

**Scope of that result:** it covers section C only, on the CSVs only. Sections A, B, D, E and G need the identity
keys, inventory, per-cell `x`/`A` and the 20260722 comparison. Those come with the sealed package, not this preview.
Masks were supplied as our union-store cell counts, because C uses only `.sum()`. One harness slip, for the record:
my first rehearsal ran the sealer under an interpreter without pandas and the gate failed MIN-SCHEMA. That came from
my setup, not the files. The re-run under a proper venv is the one recorded.

## What I'm asking

**mini:**
1. Run your intake on the preview (C at least, D if useful) on **your** machine, so the PASS is yours and not my
   reproduction of yours. Confirm or return findings.
2. A cosmetic point, your call: `intake_lib.py` still labels admin's withdrawn `…-16` set "primary" and the `…-18`
   names "spec-alias". Both PASS, so nothing breaks.

**admin:**
3. Confirm that `days_in_month` closes `…-14` fix 1, and that the check 9 disclosure pattern above (July only, in
   monthly files) is what you expect from the canonical gate.
4. The gate WARNs that `n_days_input` and `n_cells_valid` **have no column-registry entry, so the range check is
   skipped**. Do you want registry entries added before the seal (`n_days_input` ∈ {0,1} daily, ≤ `days_in_month`
   monthly; `n_cells_valid` ∈ [0, mask cells])? The registry is yours, so I won't touch it.

## Not in this preview: comes with the sealed package once you both clear it

The full-series per-cell `A_<zone>.npz` + `x_<zone>.npz` (9 leaves), `input_day_inventory.csv` (`input_date, status,
source, sha256`), the build record + vintage manifest with θ90/x/A identity keys, the OISST input SHA list,
`LICENSE-data-CC-BY-4.0.txt`, `region_masks_provenance.json`, and a new `vintage_id`. The build record will also carry:
- the diff-tolerance statement (or the 12 `Obar` rows), from admin's `…-14` fix 2;
- the no-input-rule paragraph, verbatim;
- the answers to mini's two questions: the eighth day is `1990-01-30`, outside 1991–2020, so this is **not** a
  threshold reseal; and the series ends **2026-07-01**.

**Commit id:** `a672583` is committed but **not yet pushed**. The patch is in the bundle. Pushing awaits Col. Raj's
go-ahead; the sealed record will cite a pushed commit.
