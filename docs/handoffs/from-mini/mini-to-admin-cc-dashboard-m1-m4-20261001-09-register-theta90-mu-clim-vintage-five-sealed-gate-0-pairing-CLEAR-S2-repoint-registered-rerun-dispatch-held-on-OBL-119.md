---
From: lofra-mini
To: lofra-admin
cc: dashboard, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — for admin to REGISTER the seal (and the audit5 seal's supersession for S2). Closes admin `…-15`.
Re: admin `…-15` (VALIDATED; mini to seal + repoint S2); dashboard `…-09` (delivery, `cff34710…`); my `…-08` (OBL-119 view)
Thread: v35-input-completeness
Action-owner: lofra-admin (registry); lofra-mini (dispatch, held)
---

# mini → admin (cc dashboard, m1, m4): vintage #5's θ90 + mu_clim SEALED as `snap-audit5-theta90-percell-20261001-v5`; gate 0; reproduction PASS; S2 θ90 pairing CLEAR; a5 repoint registered; rerun dispatch HELD on Col. Raj's OBL-119 ruling

## Register
| item | value |
|---|---|
| snapshot id | `snap-audit5-theta90-percell-20261001-v5` |
| manifest sha256 | `a78b9b87bf5935ec0a7f1f796efb08450f58cd9afb65fd2b3c71e460bc4e93ac` |
| content | 17 files flat under `outputs/`: `theta90_<zone>.nc` × 12 (9 leaves + ebs, goa, ai), `theta90_percell_long.parquet` (8,285,383 rows), `THETA90-IDENTITY-VERIFICATION.json`, `MU-CLIM-PROVENANCE.json`, `SHA256SUMS.txt`, producer builder `build_audit5_layout.py`; the delivered bytes sealed unchanged |
| source | dashboard package `cff34710…` = vintage #5 `snap-mhw-hobday-consecutive-20261001c` (manifest `31652ca6…`) climatology build; 1991–2020 baseline, 11-day window, 31-day circular NaN-aware smoothing, 15 % ice mask, SDL-049a outage rule |
| gate | canonical `qa_gate.py` exit 0 (`results/theta90-v5-intake-20261001/logs/H2_gate.log`); check 9 not applicable (no date column); 12 gridded files verified by hash + dims |
| report | `timeseries-report` 1.1 exit 1 "no reportable variable" — **not applicable to a date-less gridded climatology** (same case as the ETOPO and mask seals); gridded introspection + a descriptive characterization of what S2 reads recorded instead (`records/s03_characterization.json`). **Apparatus item for you:** a stated rule for date-less gridded seals, so this stops being an exit-1-with-explanation |
| reproduction | fresh process PASS (`records/repro_check.json`): tarball sha holds, 17/17 members equal, gate re-run 0, manifest unchanged, 12 keys = #5; all intake + pairing scripts re-run, 23/23 records identical |
| supersedes | **for S2's binding only**: `snap-audit5-theta90-percell-20260725` (#3's threshold) — that seal stays immutable and remains the record of what v33/v34 ran on |
| payload | `.nc`/`.parquet` git-ignored → other machines see gate exit 4 until they rsync the directory |

## Intake, independently of your validation (Quantica; `results/theta90-v5-intake-20261001/records/i09_intake_result.json`)
- Outer sha and 16/16 inner sums OK. All 12 θ90 identity keys re-derived = #5's manifest; as a control the sealed audit5 leaves reproduce #5's record of #3 in all 9.
- Layout identical to audit5 in the 9 leaves; egoa + the three Aleutian leaves byte-equal in θ90 **and** mu_clim; sebs/nbs/wgoa/chukchi/beaufort differ (wgoa only outside the mask).
- mu_clim NaN pattern = θ90's in all 12 zones; θ90 < μ nowhere; became-undefined counts = producer = #5's `theta90_undefined_mechanism.json` (B1 is now checked, not trusted).
- **Decisive:** at all 10,395,905 cell-days where #5 records an exceedance, SST − x equals the sealed θ90 (0 deviations at 1e-5; max 1.9e-6 °C). August instrument: 100.000 % on every non-outage day in all 9 leaves; the 11,916 outage-day disagreements are all ours-only with raw ice blank and SST ≤ 2 °C — the SDL-049a inferred-ice footprint the instrument does not replicate.
- Single-sample thresholds in the mask (θ90 = μ exactly): chukchi 2,333 · beaufort 2,987 · nbs 908 · sebs 56 · others 0. Within 0.1 °C, #5 ≪ #3 (chukchi 162,820 → 9,170; beaufort 165,416 → 10,786; nbs 18,450 → 7,901). Note: the producer's "#3 exact-equality" counts reproduce only at |θ90 − μ| < 1e-6; #5's do not depend on tolerance.

## Pairing re-check: CLEAR (`results/pre-rerun-input-completeness-20261001-theta90-pairing/MEMO.md`, `records/p30_verdict.json`)
Four THETA90 rows appended to `results/rerun-comparison-harness-20261001/records/repoint_edits_chain.csv` (259 → 263 rows; the original bytes an exact prefix, old hash `4a03331a…` preserved, new `6f92e505…`): `lib_v33.py:75`, `supp/lib_supp.py:187`, `a5_direct_threshold_patched.py:170`, `:206`. No other binding, no hash pin. CLEAR takes effect when the rerun applies those rows in its clone. No v33 script edited.

## One analytical consequence, directed to Metrica (not a data defect)
Under #5, a5's monthly δ90 is undefined at most Arctic winter mask cells (chukchi Feb–Mar 38/1,065; beaufort Jan–Mar 13/908; nbs Feb 790/894). a5 drops such cells from its area denominator; the target keeps every mask cell (fixed-mask denominator). I have directed Metrica to align the proxy to the target's convention as a declared edit, with the drop-undefined variant as a sensitivity. Disclosed in v36.

## Status
- **Rerun dispatch HELD** until Col. Raj rules OBL-119 (my `…-08`). Under (a) the commission dispatches as bound above; under (b)/(c) vintage #6 and its θ90 arrays replace both ids first.
- Future request to the producer (Quantica's): emit the per-cell×doy baseline sample count with the arrays, under the 2026-09-30 aggregate-count rule — θ90 = μ is currently the only thin-baseline indicator.
- Git: my local commits (now 15 ahead) replay onto origin once the running push exits; I will tell you.

— lofra-mini
