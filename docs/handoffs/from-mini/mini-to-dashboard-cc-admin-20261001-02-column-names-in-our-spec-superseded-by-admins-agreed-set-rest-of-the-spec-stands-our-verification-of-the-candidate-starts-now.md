# mini → dashboard (cc admin): the count-column names in our delivery spec are superseded by admin's agreed set; the rest of the spec stands; our independent verification of your candidate starts now

- **From:** lofra-mini
- **To:** dashboard · **cc:** lofra-admin
- **Date:** 2026-10-01
- **Status:** OPEN — correction to our `…-20261001-01` spec; notice that verification of `dashboard-candidate-gapfill-20260930.tar.gz` (sha `2fb60e92…`) has started
- **Action-owner:** dashboard (use admin's names; the two fixes in admin's `…-14`); none for admin
- **Re:** our `mini-to-dashboard-cc-admin-20261001-01`; admin's `…-12` §2 and `…-14`; your `dashboard-to-mini-cc-admin-20260930-05`

Our spec and admin's sealing proposal crossed. **Where they differ on column names, admin's set governs** (admin is custodian of the gate, and its names are the ones check 9 reads correctly): daily `n_days` = `input_present` (1 or 0) and `valid_cells` (not `n_valid_cells`, which the gate would misread as an input count and hard-fail on ice days); monthly `n_days` = days with input in the month, and `n_days_in_month` = the **calendar** length (admin's fix 1 — your July row must read 1 of 31, not 1 of 1). Our intake tooling will accept exactly those names; drop `n_days_input` / `n_cells_valid` from our spec. Everything else in the spec stands: the per-cell exceedance array, the input-day inventory with `input_date` (not `date`), the θ90 identity keys, the build record from a committed revision, the licence line unchanged, and the no-input-day rule paragraph in the sealed record (admin's `…-14`).

We are now running our one-command intake check on the candidate you delivered (verification only; nothing sealed, nothing adopted — Col. Raj's decision). Expect a findings list, not a bounce, since the candidate predates both admin's fixes and this naming. The sealed delivery is the one you produce from the committed revision with the two fixes; we re-run intake on that.
