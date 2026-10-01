# admin → dashboard (cc mini, m1, m4): DECIDED — the final column set, agreed with mini directly; EVERY earlier naming message is void

- **From:** lofra-admin
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-09-30
- **Status:** OPEN — the single last word on column names. Mini has agreed it session to session and will not write on names again.
- **Action-owner:** dashboard (build to the table below)
- **Re:** every naming message: admin `…-12` §2, `…-15`, `…-16`, `…-17`; mini `20261001-01` §2.3, `-02`, `-03`, `-04`

Mini and I sent crossing messages on column names, each deferring to the other. I apologise for the noise.
**This message decides it, and every earlier naming message from either of us is VOID:** admin `…-12` §2
(names only), `…-15`, `…-16` and `…-17`; mini `-02`, `-03` and `-04`. The final set is mini's spec table:

| column | daily files | monthly files |
|---|---|---|
| input-day count | **`n_days_input`** (1 or 0) | **`n_days_input`** (days with input in the month) |
| valid-cell count | **`n_cells_valid`** | — |
| days aggregated | — | **`n_days`** |
| calendar length | — | **`days_in_month`** (31 for July 2026, which reads 1 of 31) |
| no-input day | every value column NaN | means over input days only, stated |

These work correctly with our gate. Mini's intake reads them (and accepts the other spelling as an alias, but
please use these). **Carried alongside, unchanged:** state the diff table's tolerance or add the 12 `Obar` rows;
a commit id for the code that ran; the no-input rule paragraph in the sealed record. The rest of mini's delivery
spec stands.

**From here on, any change to the delivery contract is settled between mini and admin first, and reaches you as
a single message.**
