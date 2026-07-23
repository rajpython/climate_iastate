# Chukchi & Beaufort region-polygon provenance

> Part of the whole-map provenance set. See **`docs/region_provenance.md`** for the doctrine
> (ESR ecoregions are authoritative), the full 12-zone boundary table, and the CI guardrail
> (`config/regions_provenance.json` + `tests/test_region_provenance.py`). This note is the
> Chukchi/Beaufort detail.


The Chukchi and Beaufort SST/MHW regions (`config/regions.geojson`) were the last two regions still
defined as crude lat/lon **boxes** after the 2026-06-29 board-wide re-base onto AFSC ESR "Alaska
Marine Management Areas" (that dataset's ecosystem-area layer has **no Arctic stratum**, so the two
Arctic regions were left unchanged). This note documents their upgrade to real managed-area polygons,
bringing all 12 regions to the same NOAA managed-area standard.

## Boundary standard
**NPFMC / NMFS Arctic Management Area** (the Arctic Fishery Management Plan area) — the same NOAA /
NMFS / AFSC governance family as the ESR ecosystem areas used by the other regions. Definition (Arctic
FMP): all US EEZ marine waters of the Chukchi and Beaufort Seas, ~3 nm offshore to the 200 nm EEZ,
**north of Bering Strait**, west to the 1990 US/Russia maritime boundary, east to the US/Canada
maritime boundary (141°W).

## Source & method (reproducible)
- **Source geometry:** US Exclusive Economic Zone (Alaska), **Marine Regions MRGID 8463**
  (marineregions.org), the canonical EEZ provider — fetched via the Marine Regions WFS.
- **Clip:** intersect with the Arctic Management Area definition — EEZ **north of Bering Strait**
  (66°N clip), lon window to the US/Russia (west) and US/Canada 141°W (east) EEZ edges, out to the
  200 nm EEZ limit.
- **Split:** at **Point Barrow ≈ 156.47°W** (156°28′W; IHO S-23 / NOAA Coast Pilot 9 convention) into
  `chukchi` (west) and `beaufort` (east).
- **Cleanup:** `make_valid`, `simplify(0.005°)` (~500 m, far below the 25 km OISST grid), coords
  rounded to 5 dp.
- **Result:** coastline-following, **water-only** polygons (the EEZ excludes land) —
  `chukchi` lon −168.98…−156.47, lat 66.0…74.71°N (~1,065 OISST cells);
  `beaufort` lon −156.47…−141.0, lat 69.63…74.71°N (~908 cells).

## Caveats
1. **Reconstructed, not an official single shapefile.** The NPFMC Arctic FMP boundary is not published
   as one clean downloadable polygon, so it is reconstructed from the authoritative US EEZ per the
   FMP's textual definition. Faithful to the definition; documented here for external review.
2. **~0.5° realized mask gap to NBS (2 grid rows).** The Chukchi polygon's southern clip is 66.0°N and
   NBS's northern extent 65.83°N — a 0.17° *polygon* gap at the Bering Strait divide. At 0.25°
   rasterization the nearest NBS and Chukchi mask cell-rows land ~0.5° apart (2 rows). Functional impact
   is nil: that row is land at OISST resolution, so **0 ocean cells are left unassigned** (confirmed by
   LOFRA's tiling QA).
