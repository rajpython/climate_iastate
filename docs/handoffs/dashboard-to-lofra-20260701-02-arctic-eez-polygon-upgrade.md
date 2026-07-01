From:       dashboard
To:         lofra
Date:       2026-07-01
Status:     fyi
Supersedes: dashboard-to-lofra-20260630-02-chukchi-seam-resolution.md
Thread:     chukchi-beaufort-seam

# Dashboard → LOFRA: Chukchi/Beaufort upgraded to EEZ management-area polygons (scope change)

## What changed since the seam resolution
The Chukchi/Beaufort fix grew from a **seam move** into a **full polygon upgrade**, so this note
**supersedes** `dashboard-to-lofra-20260630-02-chukchi-seam-resolution.md`. Reason: on review, those
two were the *only* regions still defined as crude lat/lon **boxes** — the board-wide AFSC ESR re-base
had skipped them (the AFSC ESR "ecosystem area" layer has no Arctic stratum). They are now brought to
**parity** with the other 10 regions: real NOAA managed-area polygons.

## New Chukchi/Beaufort definition (adopt verbatim; supersedes any prior box/seam values)
- **Boundary = NPFMC/NMFS Arctic Management Area** (the Arctic FMP area) — same NOAA/NMFS/AFSC
  governance family as the ESR ecosystem areas the other regions use.
- **Geometry:** reconstructed from the authoritative **US EEZ (Alaska)** — Marine Regions MRGID 8463 —
  clipped to the FMP definition (**US EEZ north of Bering Strait**, west US/Russia line, east
  US/Canada 141°W, out to the 200 nm EEZ), then split at **Point Barrow 156.47°W**.
- **`chukchi`:** lon −168.98…−156.47, lat 66.0…74.71°N; coastline-following, **water-only**; ~1,065 OISST cells.
- **`beaufort`:** lon −156.47…−141.0, lat 69.63…74.71°N; coastline-following, **water-only**; ~908 OISST cells.
- The old boxes were both larger *and wrong* (ran to the dateline, included Russian waters + land). The
  new polygons are US-EEZ-only and land-clipped, so their area weights are now correct.

Provenance caveats (for your zone-definitions artifact): (1) the FMP is not published as a single clean
shapefile, so the polygon is **reconstructed** from the US EEZ per the FMP's textual definition; (2) a
**~0.17° sub-grid gap** exists between NBS's top (65.83°N) and Chukchi's bottom (66°N) — the Bering
Strait divide; negligible at 0.25°. `config/regions.geojson` remains authoritative — mask to it.

## Impact on OBL-028 / OBL-027
- **`config/regions.geojson` now encodes the EEZ polygons.** For your zone-definitions artifact,
  replace the Chukchi/Beaufort entries entirely (not just the seam value).
- **The 2 zones' masks/states/aggregates are being fully regenerated** on the new polygons right now.

## Hold status — UNCHANGED, still in force
- **Proceed with the 7 unaffected zones** (`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east`).
- **HOLD `chukchi` + `beaufort`** — do not aggregate/seal/pull until our all-clear. (Same hold as the
  prior note; the reason is now the polygon upgrade, not just the seam.)

## What lifts the hold
A follow-up handoff `Status: resolved` on `Thread: chukchi-beaufort-seam` once the rebuild finishes and
we've verified the two zones are consistent on the new EEZ polygons.
