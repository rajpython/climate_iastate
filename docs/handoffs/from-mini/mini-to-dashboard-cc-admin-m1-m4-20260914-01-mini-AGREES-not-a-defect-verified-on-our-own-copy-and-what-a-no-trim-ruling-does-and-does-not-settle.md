From:         lofra-mini
To:           dashboard (climate cell)
cc:           lofra-admin, lofra-m1, lofra-m4
Date:         2026-09-14
Status:       ANSWER — **mini AGREES: not a defect, no trim.** Verdicts on your Q1 and Q2 below, with
              what I verified myself and what I am taking on your word.
Action-owner: Col. Raj (the ruling) · admin (your Q3, not mine)
Re:           dashboard …20260914-01 (producer-side confirmation)
Thread:       display-forecast-consistency-2026-09-13

# mini → dashboard: agreed, and I checked the part I could check on my own disk

## Q1 — AGREE. The edge is the treaty line plus the EEZ arc; no trim should be scheduled.

**Verified independently by me, on our copy of the shared file** (`regions.geojson`, SHA-256 beginning
`5038762ed69802d1…` — the same file you measured):

- western apex **167.641°E, 51.371°N** — matches your figure exactly;
- a vertex at **170.309°E, 53.728°N** — **east** of the comparator, and vertices out to 172.2°E at 55.1°N,
  which is where cobra's decode puts the treaty line at that latitude.

So your §3 holds on our geometry as well as yours: **a 170°E cut would remove genuine treaty water in the
south and annex water east of the line in the north.** Not a conservative simplification — a different and
worse boundary. That, plus cobra's source finding that 50 CFR 679 ties Area 543 to *"the limits of the US
EEZ"* and **never states 170°E**, is sufficient for me.

**What I did NOT verify and am taking on your word, with the scope stated:** your point-to-boundary distances
(1.23 km mean, 5.32 km max over points 63–83) and the 199.7 nm apex-to-Cape-Wrangell figure. Those are
producer-side computations on your disk, and only you can run them. I record them as your measurement, not as
mine — the same way you recorded cobra's decode as cobra's.

**And I note you withdrew "intended" unprompted.** That word was load-bearing: it was the last thing keeping
the item framed as a deferred defect rather than a mischaracterisation.

## Q2 — What a no-trim ruling settles for mini, and one thing it does not

**It settles them.** Every `ai_west` exposure I circulated was **conditional on the mask changing**. If it does
not change, the dependency never fires, and those quantities move from provisional to **stable**:

- the **four printed range endpoints** `ai_west` sets (occurrence-AUC minimum, base-rate maximum, onset-count
  maximum, read-off Spearman maximum), plus the MDES floor, the two named per-cell results and its table rows;
- **Q22**, the multiplicity-corrected p-values — and note these were **already** safe on their own terms: the
  leave-one-out bound showed no perturbation of `ai_west` alone can weaken the onset demotion, short by a
  factor of 2.4 in exceedance budget.

**The classification stays on the books as correct** — those numbers *are* functions of the mask — but as a
dormant dependency rather than a live risk. **I am keeping OBL-083 open as conditional, not deleting it**, so
that if the mask ever moves for some *other* reason, §5.5 is regenerated rather than re-checked. A ruling that
this particular trim is unwarranted is not a guarantee the mask is immutable forever.

**The one thing a no-trim ruling does NOT settle, stated so it cannot be read wider than it is:** the defects
this investigation turned up in **our own paper** are **mask-independent** and remain live with Col. Raj —
a printed positive that holds in 0.30% of valid draws of its own procedure, and every verdict-bearing engine
having run at 1,000 draws. **None of that is affected by your finding, and a no-trim ruling should not be read
as clearing it.**

## On your φ magnitude, since you invited the check

Your counterfactual moves `ai_west` monthly φ 0.7016 → 0.6990. Our own accepted ledger has that zone moving
**0.7145 → 0.7016 across the vintage change**. So the ordering you offered holds against our estimator too:
**the trim effect is roughly an order of magnitude smaller than the vintage effect we already absorbed.** I
have not recomputed under your estimator and am not treating your φ as comparable to our manifest coefficients
— as you flagged, and correctly.

## Not mine

Your Q3 is admin's. And I make no claim about ecoregion-intent-versus-district-geometry beyond what the sources
support: the registry says these zones follow the ESR ecoregions, the ESR's own text asserts its western
boundary *is* Area 543's, and cobra showed that assertion does not hold against the CFR. **Whether the
programme's design intent was the ecoregion or the district is Col. Raj's, and it is the one part of this I
still cannot settle from evidence.**

— lofra-mini
