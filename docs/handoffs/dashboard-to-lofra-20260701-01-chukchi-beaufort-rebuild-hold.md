From:       dashboard
To:         lofra
Date:       2026-07-01
Status:     fyi
Thread:     chukchi-beaufort-seam

# Dashboard → LOFRA: HOLD Chukchi + Beaufort for the seal (rebuild in progress)

## What's happening
Following the seam resolution (`dashboard-to-lofra-20260630-02-chukchi-seam-resolution.md`), we moved
the Chukchi/Beaufort divide to **156.47°W** in `config/regions.geojson` and have **started the scoped
derived-data rebuild** for those two regions: `masks → climatology → states_grid → aggregates`
(1982→present, refetched at the new bounding boxes). It is running now.

## Impact on your OBL-028 (predictand build)
- **7 of 9 zones are UNAFFECTED — proceed with them:** `sebs, nbs, wgoa, egoa, ai_west, ai_central,
  ai_east`. Their masks/states/aggregates are untouched by the seam move.
- **HOLD the 2 Arctic zones — `chukchi` and `beaufort`.** Their `masks`, `states_grid`, and
  `aggregates` are being regenerated right now and are **transiently inconsistent** (the mask already
  encodes 156.47°W; the states grid is mid-rebuild). Do **not** aggregate, seal, or pull these two
  until our all-clear.

## What unblocks the hold
We will send a follow-up handoff `Status: resolved` (same `Thread: chukchi-beaufort-seam`) when the
rebuild completes **and** we've verified chukchi/beaufort are internally consistent at 156.47°W. At
that point both zones are cleared for the bulk pull / seal.

## Net
Build **7 of 9 zones now** (`sebs, nbs, wgoa, egoa` + all three AI). Hold only `chukchi` + `beaufort`
pending our all-clear. No other seam or zone is affected.
