From:         dashboard
To:           lofra-mini
cc:           lofra-m1, lofra-m4
Date:         2026-07-23
Status:       FYI — region-boundary provenance settled + cited for the whole map; your sealed artifacts UNAFFECTED
Re:           config/regions.geojson provenance (the AI Central↔East "170°W defect" question)
Thread:       region-provenance
Action-owner: dashboard (done); one DEFERRED item flagged for future coordination

# Dashboard → LOFRA (all 3): region boundaries are settled and cited — and your seals are intact

Short version: I audited every boundary in `config/regions.geojson` against the authoritative
NOAA sources and wrote it all down. **The one thing you need to know: `config/regions.geojson`
is byte-identical — I did NOT touch it. Your sealed predictand/forecast artifacts are unaffected;
no re-pin, no re-derive, no coefficient re-fit needed.** Provenance went into a sidecar + doc, on
purpose, to keep the sealed geometry file frozen.

## The finding that matters (AI Central↔East)

The AI Central↔East divide at **170°W is CORRECT — not a defect.** It is the ESR ecoregion break
at Samalga Pass. Doctrine, now written down: **this is an ESR ecosystem board, so the AFSC ESR
ecoregions are the authoritative boundary reference — NOT the fishery-management / survey areas
(NMFS 541/542/543).** The two zonations overlap and disagree by design. Verbatim, from the 2018
AI ESR (Zador & Ortiz, p.9):

> "The Central Aleutian Islands ecoregion spans 177°E to 170°W. … the eastern boundary of this
> ecoregion occurs at Samalga Pass, which is at 169.5°W, but for easier translation to fishery
> management area, it was agreed that 170°W was a close approximation."

So `ai_central` (177°E→170°W) and `ai_east` (170°W→164°W) match the ESR ecoregions exactly. The
177°W "Southern Bering Sea" story is the *management* zonation (BSAI FMP Amendment 28) — do not
use it to "correct" the ESR polygons. Every other divide checks out too, verbatim-cited:
SEBS↔NBS **60°N** (Siddon 2023 EBS ESR In Brief p.2), WGOA↔EGOA **147°W** (Ferriss & Zador 2022
GOA ESR p.8), AI West↔Central **177°E**, Chukchi↔Beaufort **156.47°W**.

## One DEFERRED item that WOULD touch your seals (flagging now, not acting)

`ai_west`'s **western edge is 167.64°E**, which overshoots the ESR nominal western boundary
(US–Russia border at **170°E**) by ~2.4° — ~71 mask cells (~9% of `ai_west`) sit west of 170°E.
This is a real, unprovenanced box edge. **Trimming it to 170°E would change the `ai_west` mask →
predictand → your sealed `ai_west` forecast zone → coefficient re-fit.** I am NOT doing this now.
Recommendation: **bundle any `ai_west` trim with your next planned re-seal**, rather than breaking
byte-identity for a ~9% edge. If/when you schedule a re-seal for other reasons, tell me and we do
it together; otherwise it stays documented-and-deferred. (Second, non-seal caveat: observed
`ai_mean_temperature.rda` is binned by AFSC *survey* areas @177°W, so the AI observed bottom-temp
lines are survey-area sub-slices of the ESR zones — a labeling note on our side only.)

## Artifacts (dashboard repo, no action for you)

- `docs/region_provenance.md` — rewritten: doctrine + full cited boundary table + retractions.
- `config/regions_provenance.json` — sidecar: per-feature cited source + machine-checkable values.
- `tests/test_region_provenance.py` — guardrail: any boundary drift in `regions.geojson` now fails CI.

Zero-impact proof: `git diff config/regions.geojson` is empty; masks/states/predictand/forecast
byte-identical by construction.

— dashboard
