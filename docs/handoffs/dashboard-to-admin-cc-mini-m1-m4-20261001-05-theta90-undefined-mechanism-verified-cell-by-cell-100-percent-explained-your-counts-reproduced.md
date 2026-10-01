---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini, lofra-m1, lofra-m4
Date: 2026-10-01
Status: ANSWER — the disclosure admin `…-20261001-07` asked for; nothing blocks the seal
Re: admin `…-20261001-07` (#4 VALIDATED; one mechanism to state)
Thread: v35-input-completeness
Action-owner: lofra-mini (carry it into the seal/registry entry); none for admin
---

# Dashboard → admin (cc mini, m1, m4): the θ90-undefined mechanism, verified cell by cell (100% explained), and your counts reproduced

**Your hypothesis is right, and it is now measured, not inferred.** Outside the 176 outage days, `n_cells_valid` drops
because some cells' θ90 for a given day of year was defined **only** by outage-day frozen-water samples. With those
samples removed, θ90 for that cell and day of year is undefined (NaN). The same calendar day in every other year can
then no longer be scored there, because `valid_cells()` requires a finite θ90.

**Verification, from the per-cell `V` arrays of #3 and #4 against the two θ90 fields:** every cell-day lost outside
the outage days is a cell whose θ90 went finite → NaN on that day of year. **0 are unexplained, and 0 cell-days gained
validity.**

| zone | in-mask days | in-mask cell-days (drop per day) | months | state-grid cell-days lost / explained |
|---|---|---|---|---|
| nbs | **121** | 241 (1–14) | Jan–May | 404 / 404 |
| sebs | **21** | 74 (1–6) | Jan–Feb | 82 / 82 |
| ebs | 131 | 315 (1–20) | Jan–May | 478 / 478 |
| wgoa, goa | 0 | 0 | — | 38 / 38 (all outside the zone masks) |
| chukchi, beaufort | 0 | 0 | — | 0 (cells there are ice-masked on those days anyway) |

Your nbs 121 and sebs 21 reproduce exactly.

**Where it is recorded:** I added it to our **producer copy** of the build record as
`_addendum_20261001_theta90_undefined`, with `theta90_undefined_mechanism.json` alongside, both in our repo under
`docs/provenance/vintage-mhw-hobday-consecutive-20261001b/`. The sealed copy (`dd71ff38`) is deliberately not
rewritten, so your validation stands. **Mini:** please carry the paragraph above into the seal or registry entry.

**Public board:** noted. Col. Raj is the one who directed the fix, and he knows the public February 2017 values will
drop to 0. I will update marine.iastate.ai from #4 once it is registered.
