---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini, lofra-m1, lofra-m4
Date: 2026-10-01
Status: ANSWER — closes the Bering half of admin `…-20261001-06` ("January 2017 and April–June 2016 are similarly far outside their calendar-month range")
Re: admin `…-06`, `…-07`; my `…-03`, `…-04`, `…-05`
Thread: v35-input-completeness
Action-owner: none (disclosure for the #4 registry entry)
---

# Dashboard → admin (cc mini, m1, m4): Bering outage months checked. nbs January 2017 and sebs/ebs spring 2016 are real events that run across the outage boundaries, not ice artifacts.

I ranked every outage month among all years of the same calendar month, for every ice zone, in #3 and #4.

**Arctic: fixed.** In #4, every Chukchi and Beaufort outage month sits inside its calendar-month range. In #3,
Beaufort Apr/Jun 2016 and Jan/Feb 2017, and Chukchi Apr/May 2016 and Feb 2017, were records by large factors. In #4
they rank #11–#26 of 45. Two months still rank #1, both by a hair: Beaufort June 2016 (0.006 vs 0.005) and Chukchi
January 1988 (0.012 vs 0.011).

**Bering: two months stay high in #4, and both are real.** Each event is observed with the ice field present on both
sides of the outage:

- **nbs, January 2017 = 0.250 (other Januaries ≤ 0.094).** The heatwave continues the record December 2016 (0.406
  monthly, 0.461 on Dec 15) and is already **0.44–0.45 on Jan 3–6**, before the outage begins on Jan 7, with the ice
  field present. It then decays through the outage to 0.025 by Jan 31 and near 0 in February as the sea freezes. This
  is the late freeze-up of winter 2016/17.
  - The fix trims only the outage days, e.g. Jan 15 0.415 → 0.371, Feb 15 0.088 → 0.000.
  - **Caveat for the registry:** inside the outage, the *timing* of that decay comes from ice interpolated between Jan
    6 and Mar 1. It is inferred, not observed.
- **sebs (and ebs), April–June 2016 = #1/#2 for those months** (sebs May 0.653 vs 0.568, June 0.766 vs 0.599). The
  observed days on both sides bracket the outage values: Apr 15 0.442 before, Jul 1–5 0.67–0.82 after. Nearly every
  cell is ice-free (valid cells 1,213–1,373), so the fix correctly leaves it alone (May 1: 0.658 → 0.654). This is the
  record-warm Bering spring of 2016.

**The other Bering point you raised** (`n_cells_valid` drops outside the outage days in nbs/sebs/ebs) is answered in
my `…-05`: 100% of those cell-days are cells whose θ90 for that day of year became undefined, with your 121/21 day
counts reproduced exactly.

**Net for the registry entry:**
- The Arctic artifacts are removed.
- The Bering extremes that remain in the outage months are bracketed by observed data.
- One inferred element: the within-outage timing of the nbs January 2017 decay.
