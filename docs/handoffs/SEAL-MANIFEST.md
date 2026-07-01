# Predictand seal — dashboard → LOFRA

- **Producer:** Alaska Marine Ecosystems Dashboard · **For:** LOFRA OBL-028 (9-zone predictand)
- **Vintage (uniform):** 2026-07-01 — all 12 region series end on this common date.
- **Thread:** predictand-seal-handoff · **Convention:** HANDOFF-CONVENTION v1

## Contents
| Path | What |
|------|------|
| `config/regions.geojson` | Authoritative 12-feature partition (9 leaves + 3 aggregates). |
| `docs/arctic_region_provenance.md` | Chukchi/Beaufort = NPFMC Arctic Management Area (US EEZ) provenance. |
| `data/derived/masks/region_masks.zarr` | Per-region uint8 masks (1 inside), OISST 0.25° global grid. |
| `data/derived/weights/weights.zarr` | cos(lat) area weights, same grid. |
| `data/derived/states_grid/` | Per-cell daily MHW state (`x,A,D,I,C,O`), per region, 1982→2026-07-01. |
| `data/derived/aggregates_region/` | `region_daily_{id}.parquet` — daily `area_frac,Ibar,Dbar,Cbar,Obar` per region (the deduplicated authoritative series + your `/states` cross-check target). |
| `data/derived/cold_pool/` | Modelled cold-pool covariates (Bering10K, MOM6 NEP). |
| `data/raw/coldpool_index_observed*.parquet` | Observed cold-pool index covariates (AFSC). |
| `data/raw/ao_daily.parquet`, `data/raw/pdo_monthly.parquet` | AO / PDO climate-index covariates. |

## Aggregation contract (match exactly)
`area_frac[t] = Σ_g(w_g·A_g[t]) / Σ_g(w_g)` over mask cells; `Ibar/Dbar/Cbar/Obar` are weighted
means over active cells, 0 when `area_frac=0`. Masks are keyed by the same region ids as the geojson.

## Assembling the per-cell states_grid
`states_grid/` holds per-region zarr tiles named `states_{id}_{start}_{end}.zarr` (yearly files plus
monthly-refresh increments). To build a region's continuous per-cell series, open all
`states_{id}_*.zarr`, concatenate along `time`, and **de-duplicate by date keeping the latest
(most-recent-mtime) tile** where ranges overlap. The `aggregates_region` parquet is the already-
deduplicated per-zone series and is the source of truth for cross-checks.

## Notes / caveats
- **Chukchi/Beaufort** were re-based this vintage from boxes → the NPFMC Arctic Management Area (US
  EEZ, Marine Regions MRGID 8463, split at Point Barrow 156.47°W); **water-only**, ~1,065/908 cells.
  See `docs/arctic_region_provenance.md`. ~0.17° sub-grid gap to NBS at the Bering Strait.
- Partition = 9 leaves (`sebs,nbs,wgoa,egoa,ai_west,ai_central,ai_east,chukchi,beaufort`); do not use
  `ebs/goa/ai` as partition zones (they are the roll-up aggregates, included for your cross-check).
- Cold pool is an EBS/NBS-only product; compare models via survey-replicate / mean bottom temp.

## Integrity
SHA-256 of the tarball is in the sibling file `<tarball>.sha256`, pushed alongside.
