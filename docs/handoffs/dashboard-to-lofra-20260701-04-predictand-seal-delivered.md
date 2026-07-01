From:       dashboard
To:         lofra
Date:       2026-07-01
Status:     resolved
Re:         lofra-to-dashboard-20260701-01-predictand-seal-handoff.md
Thread:     predictand-seal-handoff

# Dashboard → LOFRA: predictand seal DELIVERED (all 9 zones, vintage 2026-07-01)

## Landed in your staging dir
`~/dev/acfr/projects/sst-forecast-method-review/data/incoming/`
- **`predictand-seal-2026-07-01.tar.gz`** (323 MB)
- **`predictand-seal-2026-07-01.tar.gz.sha256`**

**SHA-256:** `e2b97e95c4a9677df9b725496fffe212b45f18c1ce250b10e12f464282ef250d`
**Transit-verified:** local == remote hash after push. (`.sha256` holds the bare digest.)

## Vintage
**Uniform 2026-07-01** across all 12 region series — the 6 Bering/GOA and 4 Aleutian series were
extended forward to match the Arctic rebuild before sealing. (Late-June `area_frac=0` are genuine
no-MHW summer days, not missing data — verified against the states time axis.)

## Contents (full list in `SEAL-MANIFEST.md` at the tar root)
`config/regions.geojson` · `docs/arctic_region_provenance.md` · `masks/region_masks.zarr` ·
`weights/weights.zarr` · `states_grid/` (per-cell `x,A,D,I,C,O`, 1982→2026-07-01) ·
`aggregates_region/` (9 leaves + 3 aggregates) · `cold_pool/` (modelled) ·
`coldpool_index_observed*.parquet` (observed) · `ao_daily.parquet` · `pdo_monthly.parquet`.

## Reminders for your QA / re-seal
- **Aggregation contract:** `area_frac = Σ(w·A)/Σ(w)` over mask cells; `Ibar/Dbar/Cbar/Obar` weighted
  means over active cells (0 when `area_frac=0`). Masks keyed by geojson region ids.
- **states_grid assembly:** open all `states_{id}_*.zarr`, concat on `time`, **de-dup by date
  keeping latest tile** on overlap. The `aggregates_region` parquet is the already-deduplicated series.
- **Partition:** 9 leaves; `ebs/goa/ai` are roll-up aggregates (for your `/states` cross-check only).
- **Arctic:** `chukchi`/`beaufort` are the NPFMC Arctic Management Area (US EEZ) polygons — water-only,
  ~1,065 / 908 cells; provenance + the ~0.17° NBS gap in `docs/arctic_region_provenance.md`.

## Over to you
Verify SHA-256 → `qa_gate` → re-seal as your snapshot-of-record → aggregate the 9 zones per the
contract → cross-check your GOA/EBS/AI roll-ups against `/v1/regions/{goa,ebs,ai}/states`. Flag back
anything that doesn't reconcile (esp. the Arctic water-only masks and the Bering-Strait gap). This
closes `Thread: predictand-seal-handoff` from our side.
