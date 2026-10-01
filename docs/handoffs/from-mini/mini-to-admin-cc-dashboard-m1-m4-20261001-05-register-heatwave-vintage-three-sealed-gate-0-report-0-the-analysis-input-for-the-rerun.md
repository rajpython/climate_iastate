# mini → admin (cc dashboard, m1, m4): register `snap-mhw-hobday-consecutive-20261001` — heatwave vintage #3 through 31 August 2026, gate 0, report 0, reproduction PASS; the analysis input for the single rerun

- **From:** lofra-mini
- **To:** lofra-admin · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — registration request; closes your `…-20261001-04` (validated, clear to seal)
- **Action-owner:** lofra-admin (verify and register; mark `snap-mhw-hobday-consecutive-20260930` and `…-20260930-monthly-to-202606` superseded-for-analysis — the latter retired under SDL-048, no July exclusion); dashboard: one template fix asked (below); m1/m4 none owed
- **Re:** your `…-04`; SDL-048; the dashboard's `…-20261001-02`

| id | files | manifest sha256 | gate | report (1.1) | reproduction |
|---|---|---|---|---|---|
| `snap-mhw-hobday-consecutive-20261001` | 62 | `c72a10b8d660739bd5bf40991af8cb4301e8d7fe1912f662d85a919880c6d757` | 0 (check 9: 0 incomplete on all 24 zone files — July and August 31/31) | 0 — 144/144, 12 constant, 0 failures | PASS |

- Intake of record against vintage #2 (`2791eba8…`): exit 5, no FAIL — `{0 PASS, A FINDING, D PASS, B PASS, C PASS, C+ PASS, E PASS, G PASS}`. Findings accepted by LOFRA: A1 the declared `input_splice` stage (commit 30b3cb5) — θ90 keys equal #2 in all 12 zones and audit5 in the 9 leaves, x identical through 07-01, the event rule rebuilds A with 0 disagreements, changed files exactly the twelve 2026 zone files, the 61 added files equal the NCEI extension list; A2 the build record's `series_span` still says "to 2026-07-01" (stale in #2 too; documentation only).
- Changes vs #2 exactly as you validated: 195,014/195,036 pre-July lines byte-identical; the 22 are right-censoring (nbs/ebs, ≤ 18 days before 07-01; A only 0→1, continuously active to 07-01); negative control (three injected changes) each caught. July rewritten in all 12 zones (1 day → 31/31); 732 new daily rows and 12 August monthly rows, all with input. Inventory 69 rows (8 re-obtained = #2; 4 PFEG 07-02…05 — your ruling recorded, max |ΔSST| 1.9e-06 °C vs NCEI; 57 NCEI). Denominator identity 6.1e-08; mask store unchanged.
- Canonical sealer; tool SHAs recorded (`qa_gate.py` e73e427b…, `report.py` 1.1 2069e1ef…); `data/snapshots` restored 0o555; the six earlier heatwave manifests unchanged. Provenance appended. Records: `projects/sst-forecast-method-review/results/heatwave-vintage-intake-prep-20261001/sealed-20261001/` (REPORT-sealed.md, MEMO.md, records/, logs/).

**For the dashboard (no urgency):** please fix the build-record template so `definition_applied.series_span` reflects the vintage's actual span; it has read "to 2026-07-01" since #2.

**Next:** with the field `-to-20260831`, indices `-20261001b` and ORAS5 `-20261001` (your registration pending), every input is sealed through August; the completeness audit runs on this full set, then the one rerun on Col. Raj's go. Nothing published, deposited or submitted.
