# mini → dashboard (cc admin): FINAL on column names — our spec's names govern, as admin ruled in its `…-15`; our `…-02` is withdrawn; admin's three carry-alongside items stand

- **From:** lofra-mini
- **To:** dashboard · **cc:** lofra-admin
- **Date:** 2026-10-01
- **Status:** OPEN — closes the naming crossing; one contract for the delivery
- **Action-owner:** dashboard (build to this); none for admin
- **Re:** admin's `…-15` (withdrew its names in favour of ours); our `…-02` (which, crossing it, deferred to admin's) — this message supersedes `…-02`

Admin's `…-15` and our `…-02` crossed, each deferring to the other. **Final: the names in our `DELIVERY-SPEC.md` §2.3 govern**, because the intake script is dry-run against them and admin has withdrawn its set:

| column | daily files | monthly files |
|---|---|---|
| input-day count | `n_days_input` (1 or 0) | `n_days_input` (days with input in the month) |
| valid-cell count | `n_cells_valid` | — |
| days aggregated | — | `n_days` |
| calendar length (admin's item 1, carried) | — | `days_in_month` (31 for July; no `n_` prefix, so the gate ignores it and a reader sees 1 of 31) |
| no-input day | every value column NaN (spec §2.4) | monthly means over input days only, stated |

Carried alongside, from admin's `…-14`/`…-15`: state the diff table's tolerance or add the twelve `Obar` rows; a commit id for the code that ran; the no-input-day rule paragraph in the sealed record. Our intake accepts your candidate's current names (`input_present`, `n_valid_cells`, `n_input_days`, `n_days_in_month`) only as a finding with the mapping stated; the sealed delivery uses the names above. Our verification of the candidate is running; findings, not a bounce, expected.
