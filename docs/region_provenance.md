# Region boundary provenance — `config/regions.geojson`

Provenance and NOAA/AFSC basis for the 12 zone polygons that define the MHW monitoring regions
(masks, aggregation, and the live maps). Companion to `docs/arctic_region_provenance.md`, which covers
Chukchi/Beaufort in full. Written 2026-07-22 to close a documentation gap: until now only the Arctic
zones carried a cited boundary source.

## Structure — 12 features = 9 leaves + 3 roll-ups
- **9 leaf zones** (the partition; no overlap): `sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east,
  chukchi, beaufort`.
- **3 roll-ups** (unions, for combined views): `ebs = sebs ∪ nbs`, `goa = wgoa ∪ egoa`,
  `ai = ai_west ∪ ai_central ∪ ai_east`.

## Two facts that answer "are the boundaries right?"
1. **Outer edges follow the real coast/shelf**, not bounding boxes — each polygon has 2,000–9,900
   vertices tracing the coastline; only ocean OISST 0.25° cells inside the polygon feed a zone.
2. **Internal divides between adjacent zones are straight meridians/parallels** — this is *correct*
   and matches how NOAA/AFSC ESR sub-regions are earmarked: they are management/reporting units whose
   internal boundaries are administrative lines, not ecological gradients.

## The internal divides (measured from the polygons) and their basis

| divide | value (in geojson) | NOAA/AFSC basis | confidence |
|---|---|---|---|
| **SEBS ↔ NBS** | **60°N** | Standard AFSC southeastern/northern Bering shelf split (60°N). | High — canonical. |
| **WGOA ↔ EGOA** | **147°W** | NMFS statistical area **630 (Kodiak) ↔ 640 (West Yakutat)**; the standard Western/Eastern GOA line. | High — but note some GOA analyses draw W/E at **144°W**; confirm against the exact ESR product being mirrored. |
| **Chukchi ↔ Beaufort** | **156.47°W** (Point Barrow) | NPFMC Arctic Management Area (US EEZ), MRGID 8463 — see `arctic_region_provenance.md`. | High — documented. |
| **AI West ↔ Central** | **177°E** | AFSC Aleutian survey district boundary (Western ↔ Central). | Medium. |
| **AI Central ↔ East** | **170°W** | ⚠️ **Does not match the AFSC AI survey**, which splits Central↔Eastern at **177°W** and treats 170–164°W as the **Southern Bering Sea** district. Our `ai_east` (170–164°W) is therefore closer to SBS than to "Eastern Aleutians." | **Low — reconcile.** |

Western/outer extents: `ai_west` starts at ~167.6°E (AFSC Western Aleutian nominally 170°E); `egoa`
ends at ~130°W (Dixon Entrance / SE Alaska); `nbs` tops out ~65.8°N (Bering Strait, ~0.17° sub-grid
gap to the Chukchi per the seal manifest).

## Open items / recommendations
1. **AI sub-division (the one real discrepancy).** Reconcile `ai_central`/`ai_east` against the
   authoritative ESR Aleutian definition. If the board should mirror the AFSC AI survey districts,
   the Central↔Eastern divide should move **170°W → 177°W**, and a Southern-Bering-Sea zone may be
   warranted for 170–164°W. If it should mirror a coarser ESR "3-zone Aleutian" narrative, confirm
   that narrative's exact meridians. Currently unverified against a single cited source.
2. **GOA W/E value.** 147°W is defensible (630|640) but 144°W appears in some ESR/ocean analyses —
   pin to the specific product.
3. **Two zone definitions coexist by design.** These monitoring **polygons** (OISST 0.25°) are
   distinct from the coarse lat/lon **boxes** used to slice the 1° NOAA-PSL seasonal-forecast grid
   (`docs/forecast_extension/psl_noaa_replication/…`) — the forecast boxes are a deliberate
   low-resolution approximation, not the monitoring geometry.
4. **Feature properties carry no source tag.** Consider adding a `source`/`boundary_note` property per
   feature so the provenance travels with the data.

## References
- NOAA Fisheries — [Ecosystem Status Reports (GOA / BSAI)](https://www.fisheries.noaa.gov/alaska/ecosystems/ecosystem-status-reports-gulf-alaska-bering-sea-and-aleutian-islands)
- AFSC — [Alaska Marine Ecosystem Status Reports portal](https://apps-afsc.fisheries.noaa.gov/refm/reem/ecoweb/index.php?ID=8)
- `docs/arctic_region_provenance.md` — Chukchi/Beaufort (NPFMC Arctic Management Area).
- Rendered boundary map: **`docs/region_boundaries.png`** (regenerate with `scripts/plot_region_boundaries.py`).
