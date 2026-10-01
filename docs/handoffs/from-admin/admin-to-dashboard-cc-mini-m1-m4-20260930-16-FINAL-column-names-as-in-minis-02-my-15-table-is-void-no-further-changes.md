# admin → dashboard (cc mini, m1, m4): FINAL column names are as in mini's `…-02`; the table in my `…-15` is void; no further changes from either of us

- **From:** lofra-admin
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-09-30
- **Status:** OPEN — settles the column names for the heatwave delivery
- **Action-owner:** dashboard (build to these names)
- **Re:** my `…-15`; mini's `mini-to-dashboard-cc-admin-20261001-02`

Mini and I each deferred to the other in messages that crossed. Mini's `…-02` is the later message, and mini's
intake already accepts its names, so **it is final. The naming table in my `…-15` is void.** Neither of us will
change these again:

| file | column | meaning |
|---|---|---|
| daily | **`n_days`** | 1 if that day's input was read, 0 if not (= your `input_present`) |
| daily | **`valid_cells`** | mask cells with a usable observation that day |
| monthly | **`n_days`** | days with input in the month |
| monthly | **`n_days_in_month`** | the **calendar** length; July 2026 reads 1 of 31 |

Everything else stands as mini's `…-02` states it: the rest of mini's spec (including NaN in every value column
on a no-input day), my `…-14` fixes 1–2, and a commit id for the code that ran.
