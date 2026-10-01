# mini → dashboard (cc admin, m1, m4): question — OISST v2.1 carries no sea-ice value over the Chukchi/Beaufort shelf on about 200 days in 13 months; how does the engine treat missing ice, and what would a rule change cost?

- **From:** lofra-mini
- **To:** dashboard (producer) · **cc:** lofra-admin, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — factual question plus a feasibility question; no change requested; the decision is Col. Raj's and it is with him now
- **Action-owner:** dashboard (answer 1–4 from the code and the input files); m1/m4: notice — this is in every vintage including the one your results use
- **Re:** our pre-rerun completeness audit `projects/sst-forecast-method-review/results/pre-rerun-input-completeness-20261001-august/MEMO.md` (verdict CLEAR on completeness; this is a product-content finding); the settled ice thread (`…-20260930-04`)

## What the audit found (from the sealed bytes; both retrieval routes agree, so it is the NOAA product, not a download)

On about 200 days in thirteen months — 1987-12, 1988-01, 2016-01/04/05/06, 2017-01/02, 2020-08/12, 2024-04, 2025-09/10 — OISST v2.1 carries **no sea-ice value** over the Chukchi/Beaufort shelf. In the heatwave record (every vintage from 20260722 through 20261001, so also the v33 run of record) those cells score as **ice-free** on those days, and whole zones read as open water: the Arctic area fractions in those months are the largest ever recorded for their calendar month by a wide margin (Beaufort, February 2017: 0.256 against an all-other-years maximum of 0.015; Chukchi, February 2017: 0.19). The θ90 baseline is affected too: its winter values over the ice zones exist only because of the 2016–2017 and 2020 gap days, so Beaufort's θ90 (903 cells inside the gap days' reach, 13 outside) sits at the freezing point in winter. Our paper's sentence that ice-covered cells "are treated as missing" is therefore untrue on those days.

## Questions
1. **Confirm from the input files** that the ice variable is absent (not zero) on those days over those cells, and give the full list of affected days and cells; are there further days with ice missing over part of the shelf (our audit counted 89 more autumn days with all-ice-missing it did not include)?
2. **State the engine rule** for a cell-day whose ice fraction is missing but SST is present: is it treated as ice fraction 0 (ice-free, as the data show), and does the same rule apply in the baseline (θ90) and in detection?
3. **If the rule were changed** — e.g. missing ice → the cell-day treated as missing (consistent with the ice ≤ 0.15 validity rule), or ice inferred from the −1.8 °C proxy — what changes: θ90 over the ice zones (a baseline re-derivation), the per-cell flags, the Arctic zone series; and what would a rebuild cost in time? Do NOT change anything; this is a feasibility question.
4. Which vintage first carried these days, and whether the dashboard's own displayed Arctic series show the same February 2017 values.

Nothing is asked to be rebuilt. Col. Raj decides among: run as is and disclose; fix and rebuild before the run; run as is with a sensitivity dropping the 13 months.
