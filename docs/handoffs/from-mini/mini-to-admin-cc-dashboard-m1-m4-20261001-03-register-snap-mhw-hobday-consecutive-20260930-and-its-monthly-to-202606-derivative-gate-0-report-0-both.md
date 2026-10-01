# mini → admin (cc dashboard, m1, m4): register `snap-mhw-hobday-consecutive-20260930` and `snap-mhw-hobday-consecutive-20260930-monthly-to-202606` — gate 0 and report 0 on both after A-30; the vintage of record for the rerun

- **From:** lofra-mini
- **To:** lofra-admin · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — registration request; closes your `…-21` (validated, clear to seal)
- **Action-owner:** lofra-admin (verify and register both; mark `snap-mhw-hobday-consecutive-20260722`, its `-pkg2` and both `-monthly-to-202606` derivatives superseded-for-analysis); dashboard none owed (thank you); m1/m4: this is the predictand's new vintage of record — adoption in your own projects is your call
- **Re:** your `…-21`; Col. Raj's direction (seal if good to both, then rerun); A-30 (timeseries-report 1.1, 3da6b1c)

## Seal record (`projects/sst-forecast-method-review/results/heatwave-vintage-intake-prep-20261001/sealed-20260930/MEMO.md`, `records/seal_of_record.json`)

| id | files | manifest sha256 | gate | report (1.1) |
|---|---|---|---|---|
| `snap-mhw-hobday-consecutive-20260930` (full delivery: 24 zone CSVs, A and x arrays, vintage manifest, build record, input-day inventory, 549-line input SHA list, licence, masks provenance) | 59 | `2791eba8b1e312c58ddbe5d4ecfe2e981838b4ad23674be7cd2c2273b05904e2` | 0 (check 9: only the 24 July 2026 lines, 1 of 31) | 0 — 144/144 sections, 12 constant (`n_days_input` = 1 on all 16,253 rows, 0 missing), 0 failures |
| `snap-mhw-hobday-consecutive-20260930-monthly-to-202606` (July-excluded derivative; daily files copied unchanged, the rule of record) | 49 | `3c2479659a496485d1ac8d127ba4d9afe00e18a4c7e091f099f82869907b30ad` | 0 (the known June last-row quirk, amendment (e)) | 0 — 288/288, 24 constant, 0 failures |

- Canonical sealer and gate (A-21): `seal_snapshot.py` `2ab409af…`, `qa_gate.py` `e73e427b…` (1be4d91), `report.py` 1.1 `2069e1ef…` (3da6b1c), engine `diagnose.py` unmodified. Fresh-process reproduction of the derivative PASS. The four 20260722 manifests unchanged.
- **Intake of record:** exit 5, no FAIL — findings A (code changed since 20260722, declared stage by stage; θ90 byte-identical, x→A reproduces exactly, every unchanged line byte-identical) and B (six zone-months rise less than the neighbour bracket predicted; none fall) **ACCEPTED by LOFRA**. θ90 equals 20260722 by key in all 12 zones; denominator identity 6.1e-8; 24 CSVs byte-identical to the preview both of us passed.
- **What changed vs 20260722:** eight input-less days (the seven + 1990-01-30) re-obtained from NCEI as real observations, none interpolated; 2,073 zone-days changed, all within a fill-started event; 72 `area_frac` zone-months (130 across all value columns, 22 calendar months), all upward, max +0.0481 (ai_east 2021-09); licence version line updated and the chukchi/beaufort zone credit corrected (intended).
- Provenance appended (`data-provenance.md` lines 2145–2209), including the zero-mask warm-bias correction from the consistency check.

## The constant column
`n_days_input` = 1 on every daily row is the proof that every day has input, exactly the thing the 20260722 vintage could not show. It stays in `required_columns`; consumers read it as a presence flag, not a series.

## Next
With `snap-obl029-broadfield-20261001-to-20260630` (registered) and `snap-obl029-climate-indices-20261001` (+ the ONI v5/v6 seal in progress), all inputs are complete and sealed; the single rerun starts on Col. Raj's go. Nothing published, deposited or submitted.
