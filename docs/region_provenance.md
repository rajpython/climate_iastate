# Region boundary provenance — `config/regions.geojson`

Authoritative, cited provenance for the 12 zone polygons that drive the masks, aggregation, and
live maps. Machine-checkable boundary values live in `config/regions_provenance.json` and are
enforced by `tests/test_region_provenance.py` (any boundary drift fails CI). Companion:
`docs/arctic_region_provenance.md` (Chukchi/Beaufort in full).

> **Written 2026-07-22, rewritten 2026-07-23** to close a provenance gap that let a *correct*
> boundary (the AI Central↔East divide) be mistaken for a defect and nearly triggered a costly
> geometry reorg. Every internal divide has now been verified verbatim against its primary NOAA
> source.

## Doctrine — which reference is authoritative

**This is an ESR ecosystem board. The authoritative boundary reference is the AFSC Ecosystem
Status Report (ESR) ecoregions — NOT the fishery-management statistical/survey areas.**

NOAA publishes two *different, overlapping* Alaska zonations:

- **ESR ecoregions** — physics/biogeography-driven (oceanographic passes, fronts, water-mass
  breaks). This is what an ecosystem board mirrors.
- **Fishery-management / survey areas** — NMFS statistical areas (e.g. AI districts 541/542/543)
  for apportioning TAC. A *management* construct.

They **disagree by design**. The canonical case is the Aleutians: the ESR splits Central↔Eastern
at **Samalga Pass ≈ 170°W** (a first-order biogeographic break), while management splits
Central↔Eastern at **177°W**. Our polygons follow the **ESR** (170°W) and are therefore correct;
the earlier "reconcile to 177°W" note measured against the wrong reference and is **retracted**
below.

## Structure — 12 features = 9 leaves + 3 roll-ups
- **9 leaf zones** (partition, no overlap): `sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east,
  chukchi, beaufort`.
- **3 roll-ups** (unions): `ebs = sebs ∪ nbs`, `goa = wgoa ∪ egoa`,
  `ai = ai_west ∪ ai_central ∪ ai_east`.

Two structural facts: (1) **outer edges follow the real coast/shelf** (2,000–9,900 vertices per
polygon; only ocean OISST 0.25° cells inside the polygon feed a zone); (2) **internal divides are
straight meridians/parallels** — correct, because the ESR ecoregion boundaries are themselves
administrative meridians (approximating the underlying oceanographic break).

## The boundaries — measured vs cited ESR source

Every internal divide, verified verbatim against the primary ESR document. Values are enforced by
the test suite.

| Divide / edge | In geojson | ESR ecoregion basis (verbatim) | Source |
|---|---|---|---|
| **SEBS ↔ NBS** | **60°N** | "The southeastern and northern Bering Sea (divided at **60°N**) have different oceanographic and zoogeographic characteristics." | Siddon 2023 EBS ESR *In Brief*, p.2 |
| **WGOA ↔ EGOA** | **147°W** | "the western and eastern GOA ecosystems (divided at **147°W**)" | Ferriss & Zador 2022 GOA ESR, p.8 |
| **AI West ↔ Central** | **177°E** | "The Western Aleutian Islands ecoregion spans **170° to 177°E**." (= NMFS mgmt area 543) | Zador & Ortiz 2018 AI ESR, p.8 |
| **AI Central ↔ East** | **170°W** | "The Central Aleutian Islands ecoregion spans 177°E to **170°W**. … the eastern boundary … occurs at **Samalga Pass, which is at 169.5°W**, but for easier translation … **170°W was a close approximation**." | 2018 AI ESR, p.9 |
| **AI East ↔ WGOA seam** | **164°W** | "The Eastern Aleutian Islands ecoregion spans 170°W to **False Pass at 164°W**." | 2018 AI ESR, p.9 |
| **EGOA east extent** | **~130°W** | Dixon Entrance / SE Alaska (coastline-traced) | GOA ESR |
| **NBS north extent** | **~65.83°N** | Bering Strait (coastline-traced; ~0.17° polygon gap to Chukchi) | Arctic doc |
| **Chukchi ↔ Beaufort** | **156.47°W** | Point Barrow (156°28′W; IHO S-23 / NOAA Coast Pilot 9) | `arctic_region_provenance.md` (NPFMC Arctic Mgmt Area, MRGID 8463) |
| **Beaufort east extent** | **141°W** | US–Canada maritime boundary | Arctic doc |

## Retractions (previously flagged "reconcile" — both were wrong references)

- **AI Central↔East (170°W).** *Not* a defect. It is the ESR ecoregion break at Samalga Pass.
  The fishery-management district break at 177°W (NMFS areas 541/542/543, BSAI FMP Amendment 28)
  is a **different, intentional** zonation and must not be used to "correct" the ESR polygons.
- **WGOA↔EGOA (147°W, once doubted as maybe 144°W).** Confirmed **147°W** verbatim in the GOA
  ESR. No change.

## Open items

1. **`ai_west` western edge — the one real geometry discrepancy.** The polygon runs to
   **167.64°E**, ~2.4° west of the ESR's nominal western boundary (US–Russia border at **170°E**,
   2018 AI ESR p.8). This is an unprovenanced hand-drawn box edge and it is **not cosmetic**: ~71
   mask cells (~9% of `ai_west`) lie west of 170°E, out toward Stalemate Bank / the US–Russia
   maritime line. Fixing it (trim → 170°E) changes the `ai_west` mask and therefore the sealed
   forecast zone — **rebuild + LOFRA re-seal/re-fit cost**. Recommendation: keep documented as a
   known over-extension; bundle any trim with the next planned LOFRA re-seal (revisit sooner only
   if those cells are confirmed non-US water).
2. **Observed AI bottom-temp binning ≠ ESR ecoregions.** `ai_mean_temperature.rda` is packaged by
   the AFSC **survey areas** (Western/Central/Eastern = 543/542/541, split at 177°W), while our
   pages are **ESR ecoregions** (`ai_central` = 542+541). So on `ai_central`/`ai_east` the
   *observed* line is a survey-area sub-slice of the ESR zone — a labeling caveat, not a boundary
   error. Label observed AI panels as "AFSC survey-area index."
3. **Seam hygiene.** NBS (65.83°N) ↔ Chukchi (66.0°N) leave a ~0.17° polygon gap at Bering Strait
   (0 ocean cells unassigned at OISST resolution — see arctic doc). `sebs` reaches 60.75°N along
   the coast; the SEBS↔NBS partition meets at 60°N.

## References (primary)

- **EBS:** Siddon, E. 2023. *Ecosystem Status Report 2023: Eastern Bering Sea* (In Brief), NPFMC —
  https://apps-afsc.fisheries.noaa.gov/REFM/docs/2023/EBSBrief.pdf
- **GOA:** Ferriss, B.E. & Zador, S. 2022. *Ecosystem Status Report 2022: Gulf of Alaska*, NPFMC —
  https://apps-afsc.fisheries.noaa.gov/REFM/docs/2022/GOAecosys.pdf
- **AI:** Zador, S. & Ortiz, I. 2018. *Aleutian Islands Ecosystem Assessment*, NPFMC —
  https://apps-afsc.fisheries.noaa.gov/REFM/Docs/2018/BSAI/ecosysAI.pdf
- **Arctic:** `docs/arctic_region_provenance.md` (NPFMC Arctic Management Area; Marine Regions MRGID 8463).
- **Management contrast (NOT the board's reference):** AFSC AI bottom-trawl survey data report
  NOAA-TM-AFSC-215; 50 CFR 679.2; BSAI Atka mackerel SAFE (Dec 2010, Amendment 28 — "divided at
  177°W and 177°E").
- Machine-checkable values: `config/regions_provenance.json`. Guardrail: `tests/test_region_provenance.py`.
- Rendered boundary map: `docs/region_boundaries.png` (`scripts/plot_region_boundaries.py`).
