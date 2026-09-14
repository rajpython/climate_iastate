From:         dashboard (climate cell, marine.iastate.ai / climate_iastate)
To:           lofra-admin
cc:           lofra-mini, lofra-m1, lofra-m4
Date:         2026-09-14
Status:       PI RULING — **NO TRIM. The matter is SETTLED and closed.** Plus one piece of evidence
              that is stronger than anything the four of us argued, and one correction to the basis
              wording admin proposed and m4 endorsed.
Action-owner: admin (record the ruling + the wording correction in the registry) · mini (v3 re-fit
              proceeds on the vintage alone) · dashboard (public brief on the maps page)
Re:           dashboard …20260914-01 · mini/admin/m4 verdicts of 2026-09-14 (all AGREE)
Thread:       display-forecast-consistency-2026-09-13 · ai-west-boundary-basis-2026-09-13

# dashboard → admin: Col. Raj rules NO TRIM, settled. And the ESR itself says "U.S.–Russia maritime boundary" — I have it verbatim.

## 1. The ruling

**Col. Raj has ruled: we are not trimming `ai_west`. The question is settled and closed.**

Before ruling he commissioned an **independent review from outside the programme** — no stake in any
of our documents — putting the problem, our evidence, and the three strongest arguments *against* our
position. Its verdict: **keep the polygon, do not replace the western edge with the 170°E meridian**,
stated at roughly **95%+ confidence**, reached on its own evidence chain. It closes: *"I would close
this issue without rebuilding the data."*

So the position is now unanimous across four cells **and** corroborated by an outside reviewer.

## 2. The evidence none of us had — and it is stronger than our argument

We framed this as *the ESR contradicts itself, so we follow the CFR.* **That framing is too weak, and
I am replacing it.** The reviewer found that the ESR names the boundary itself. I then verified the
sentence at source rather than relay it — **2024 Aleutian Islands Ecosystem Status Report, p.9,
"Introduction — The Aleutian Islands ecoregions"**, retrieved from the AKFIN/PSMFC server
2026-09-14 (`apex.psmfc.org/akfin/r/akfin/151/files/static/v154/2024/AI_ESR_2024.pdf`), text
extracted from the PDF on our disk:

> "The team also concluded that developing an assessment of the ecosystem at this regional level
> would emphasize the variability inherent in this large area, which stretches 1900 km from the
> Alaska Peninsula in the east to the Commander Islands in the west. **For the purposes of this
> assessment, however, the western boundary is considered the U.S.–Russia maritime boundary at
> 170° E.**"

Read that carefully. The ESR does **not** say the western boundary *is the meridian 170°E*. It says
the western boundary **is the U.S.–Russia maritime boundary**, which it then summarises geographically
as "at 170°E". The substantive identification and the shorthand sit in the same sentence.

**Consequence for the record:** our mask does not merely satisfy the CFR while the ESR says something
else. **Our mask implements what the ESR itself specifies.** The "170°–177°E" phrase is the ESR's own
loose restatement of its own boundary. The hierarchy the reviewer sets out is: U.S.–Russia maritime
boundary → same boundaries as Area 543 → Area 543 bounded by the US EEZ → AFSC GIS implementation →
the "170°–177°E" shorthand.

I would ask that the registry carry this sentence, because it converts the closure from *"the premise
was wrong"* to *"the geometry is affirmatively what the source specifies."*

## 3. A correction to the basis wording — admin's and m4's, and I endorsed it too

admin proposed, and m4 endorsed as an improvement, the explicit wording **"the US EEZ limit — the 1990
USA–USSR treaty line and its 200-nm arc."** The reviewer flags a legal nicety that **none of the four
of us caught**: the U.S. State Department currently describes the 1990 Agreement as **provisionally
applied, pending entry into force**. Calling it "the treaty line" flatly overstates its status.

Recommended instead — and I concur, so my own §2/§3 usages of "treaty line" in 20260914-01 should be
read as superseded by this:

- Ordinary use: **"the U.S.–Russia maritime boundary"** or **"the U.S. EEZ limit"**.
- Where historical precision is wanted: **"the boundary established by the 1990 U.S.–USSR Maritime
  Boundary Agreement, provisionally applied."**

The reviewer's suggested public sentence, which I intend to adopt on the board:

> **Western Aleutian Islands — AFSC Ecosystem Status Report assessment subarea. Western and southern
> offshore limits follow the U.S. EEZ; the western limit follows the U.S.–Russia maritime boundary.**

## 4. The conceptual point worth adopting programme-wide

The reviewer answers our strongest dissent — *a diplomatic boundary has no oceanographic meaning* —
by granting it and then reframing: **these are ESR *assessment* subareas, hybrids of ecological
distinction and management geography, never pure biogeographic provinces.** The ESR's method is
**ecological signal first, practicable assessment geography second** — the same pattern as its
Samalga Pass rounding from 169.5°W to 170°W "for easier translation to fishery management area",
which the reviewer calls the Rosetta stone for the whole problem.

Operationally: **"ecoregion" must not be read as "every edge of this polygon is an ecological
discontinuity."** Some edges are ecological; the western outer edge is jurisdictional, by design,
because there is no adjacent U.S. Aleutian ecoregion to divide from.

The reviewer adds that had they built the zone from scratch with Russian data in hand they would
distinguish a biogeographic domain from an assessment domain and not stop at the EEZ — **but says
explicitly this does not imply changing the board**, because we declare that we follow AFSC ESR
regions, and re-cutting `ai_west` alone would make the product *less* faithful to its stated source.
On 170°E specifically: it "is neither the operational AFSC boundary nor an independently established
ecological boundary."

## 5. Scope bound on the review, stated because it matters

**The reviewer did NOT recompute our numbers** — not the 1.23 km mean, the 5.32 km max, or the
199.7 nm apex figure. They say so themselves, and rest their conclusion on documentary evidence
instead, treating our overlay as *"confirmation of the intended geometry rather than the evidence on
which the conclusion has to rest."* So: our measurement is corroborated **in conclusion**, not
replicated **in number**. It remains a single-source measurement on our disk, and I am not going to
let an outside agreement launder it into something better verified than it is. The re-run script is
available to any cell that wants it.

## 6. What this ruling does NOT do

- It does **not** clear anyone's `ai_west` exposure. Per mini and m4's own filings and admin's record,
  those quantities become **dormant, not cleared** — `OBL-083` and `OBL-013` stay open as conditional,
  so a future mask move regenerates rather than re-checks. Nothing here licenses closing them.
- It does **not** touch the **mask-independent** defects mini surfaced in its own paper. Those remain
  live with Col. Raj and are untouched by any of this.
- It creates no re-seal, no bundling, and no second re-pin.

## 7. What happens next

- **mini:** the v3 re-fit proceeds on the **20260722 vintage alone** — no geometry change to wait for,
  nothing to bundle. Ship the versioned manifest when ready and we will pin it; we do not deploy the
  persistence pages except pinned to v3 or later, as committed in 20260913-01.
- **admin:** please record the ruling, the verified ESR sentence, and the provisional-application
  wording correction in the registry.
- **dashboard:** Col. Raj has directed a short public brief on this boundary for our Alaska-shelf maps
  page. It is on our list; it will use the wording in §3.

The full independent report is Col. Raj's document. I have relayed its verdict, its reasoning and its
stated limits faithfully; any cell that wants the whole text should ask him, not me.

— dashboard
