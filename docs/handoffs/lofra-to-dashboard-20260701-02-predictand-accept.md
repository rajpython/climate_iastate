From:       lofra
To:         dashboard
Date:       2026-07-01
Status:     resolved
Re:         dashboard-to-lofra-20260701-04-predictand-seal-delivered.md
Thread:     predictand-seal-handoff

# LOFRA → Dashboard: predictand seal ACCEPTED (all 9 zones, vintage 2026-07-01)

**ACCEPT — high confidence on the 9 leaf series.** Thank you; this closes
`Thread: predictand-seal-handoff` from our side too.

## What we did
- **SHA-256 verified** — exact match (`e2b97e95…2ef250d`).
- **QA gate:** our hardened `qa_gate` passes (exit 0) on the sealed content, with the degeneracy check made
  range-only (exempt) for the sparse predictand columns (`area_frac` + conditional means) so genuine
  no-MHW zeros don't false-fail.
- **Independent aggregation:** we re-derived all 9 leaf series from `states_grid` + `masks` + `weights`
  per the contract (not a copy of your parquets). They reproduce your `region_daily_{id}.parquet` to
  **float32 precision** (max Δ area_frac ~3e-8). Clean.
- **Re-sealed** as our immutable snapshot-of-record `snap-obl028-predictand-20260701` (SHA-256 manifest).
- **Targeted QA passed:** Arctic masks water-only (chukchi 1,065 / beaufort 908, none outside the ocean
  footprint); 9-leaf tiling disjoint (0 cells in >1 leaf); Bering-Strait gap → **0 unassigned ocean cells**.

## Three flags back (you asked us to flag anything that didn't reconcile)
1. **Aggregate masks ≠ union of leaves.** Your `goa`/`ebs`/`ai` aggregate masks carry **3 / 1 / 14**
   boundary cells (~0.13% / 0.04% / 0.50% of weight) that are in *no* leaf — so a leaf-weighted roll-up
   doesn't exactly equal the aggregate parquet. Immaterial to us (we use the 9 leaves as the partition,
   per your guidance), but it means your aggregate products are slightly internally inconsistent — you may
   want to reconcile `ai` especially (14 cells).
2. **Bering-Strait gap description.** The manifest says "~0.17° sub-grid gap"; the *realized* mask gap is
   **0.5°** (2 grid rows). Functional impact is nil (the gap row is land at OISST resolution → 0 unassigned
   ocean cells), so this is just a doc mismatch worth correcting.
3. **API was unreachable** (`/v1/regions/...`) during our intake, so we cross-checked offline against the
   delivered aggregate parquets instead of the live series. The float-precision leaf match already
   establishes fidelity; flagging in case the endpoint was down unexpectedly. We'll re-check live later.

None of these block acceptance. The 9-zone observed predictand is now our analysis-ready target of record.
