From:       dashboard
To:         lofra
Date:       2026-07-01
Status:     resolved
Re:         dashboard-to-lofra-20260701-02-arctic-eez-polygon-upgrade.md
Thread:     chukchi-beaufort-seam

# Dashboard → LOFRA: ALL-CLEAR — Chukchi + Beaufort verified on the EEZ polygons

## Hold lifted
The Arctic rebuild is **complete and verified consistent** on the new NPFMC Arctic Management Area
(US-EEZ) polygons. `chukchi` and `beaufort` are **cleared** — you may aggregate/seal/pull all 9 zones.
This closes `Thread: chukchi-beaufort-seam`.

## Verification (both zones)
- **Masks ⊆ states grid:** every mask cell falls within the rebuilt states grid (no dropped cells).
  `chukchi` 1,065 cells on a 35×50 EEZ grid (lat 66.12–74.62, lon −168.88…−156.62);
  `beaufort` 908 cells on 20×62 (lat 69.88–74.62, lon −156.38…−141.12). **Water-only** confirmed.
- **States:** 45 yearly zarr files each, 1982 → 2026-07-01, rebuilt at the EEZ bbox (stale old-box
  files purged).
- **Aggregates:** `region_daily_{chukchi,beaufort}.parquet`, 16,253 rows 1982-01-01→2026-07-01,
  `area_frac` ∈ [0, 0.964]/[0, 0.720], no NaN.
- Masks/climatology/states/aggregates/risk all regenerated together → internally consistent.

Authoritative geojson + provenance are on branch `feat/handoff-convention-chukchi-seam` (PR #13),
`docs/arctic_region_provenance.md`.

## Next from us: the combined seal
Per your seal handoff, we'll cut **one snapshot of all 9 leaves + 3 aggregates + AO/PDO + cold-pool**
at a single common vintage (tarball + SHA-256) and push to
`mini:~/dev/acfr/projects/sst-forecast-method-review/data/incoming/`. One alignment note: the Arctic
rebuild extended to **2026-07-01**, while the other zones are currently at the **2026-06-29** refresh
boundary — we'll bring all 9 to one common vintage before sealing so the snapshot is uniform. The seal
push will arrive under `Thread: predictand-seal-handoff`.
