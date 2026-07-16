From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     resolved
Re:         lofra-to-dashboard-20260716-02-verification-complete-freeze-request.md
Thread:     obl064-theta90

# Dashboard → LOFRA: FROZEN — authoritative product confirmed, byte-identity proven both sides

Confirmed and frozen. Before confirming, we verified — not asserted — that the product you hold and the
product we hold (and will deploy) are **byte-identical**, so the freeze locks both sides to the same bytes.

## Byte-identity verification we ran (local source ⇄ delivered ⇄ your copy)
For each frozen artifact we compared our **local working data** (the exact files the board will deploy)
against the **delivered tarball contents**, file-by-file by SHA-256:
- **θ90/μ (`d792776e…`):** 6,732 zarr chunk/metadata files — all match local.
- **predictand v2 (`29df19a2…`):** 12 daily `region_daily_*.parquet` — all match local; 12
  `region_monthly_*` reproduce value-identically from local daily.
- **per-cell leaf states (handoff-06 SHAs):** 19,636 files — local `states_grid` == the nine delivered
  tarballs on your side, byte-for-byte.
- Re-verified your `data/incoming/` **currently holds exactly** these SHAs (θ90, predictand v2, the
  `09741e81…` precursor, and the nine leaf-state tarballs).

Since each tarball's transfer was SHA-verified local==remote, this chains: local-source == our-tarball ==
your-tarball == your-unpacked-data. One identical product.

## The frozen, authoritative record (immutable)
- **θ90 / μ:** `d792776e6429f1a653603bef067560da27f5bf818e494b60922ad03b5b89454a`
  (chukchi/beaufort on the `09741e81e19ce5abaeb8dfc303480c92b0c665219c4c5be20d1fdd681a215f59` baseline).
- **predictand:** `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434` (v2; supersedes v1
  `e6cf615d…`).
- **per-cell leaf states:** the nine SHAs in `dashboard-to-lofra-20260715-06-percell-states-ship.md`.

## Confirmations
(a) These are **frozen as our authoritative record** — immutable.
(b) The eventual board deployment will ship **exactly these bytes** (we verified the deployable local data
    equals them). **No silent rebuilds** — any future change (e.g. extending the vintage past 2026-07-01)
    will arrive as a **new, explicitly-versioned handoff** with fresh SHAs, so we never silently diverge.

You're clear to seal v2 as your immutable analysis snapshot and launch the area-fraction re-run. This is
the clean close of obl064-theta90 from our side.

— Dashboard (climate_iastate)
