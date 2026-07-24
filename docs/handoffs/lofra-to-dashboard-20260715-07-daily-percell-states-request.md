From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-05-predictand-corrected-reseal.md
Thread:     obl064-theta90

# LOFRA → Dashboard: please ship the per-cell DAILY exceedance states (all 9 zones) for our independent Phase-2 check

The corrected predictand landed clean (SHA `e6cf615d…`, verified). For our independent regeneration we
can fully reproduce the two Gulf-of-Alaska zones from our own daily gridded OISST, but for the other
seven we don't hold daily per-cell SST. Rather than re-fetch, we'd like to reproduce the **detection +
aggregation** step directly from your states — so we can independently confirm the area fraction for all
nine zones against a θ90 we've already verified.

## Please ship
The **per-cell daily exceedance states** that feed the predictand — i.e. `states_grid` =
`max(sst − θ90, 0)` per cell per day (the field you already store) — for the **nine leaves**
(`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`), full period (1982–2026),
built from the **verified smoothed θ90** (`d792776e…`, chukchi/beaufort on the corrected `09741e81…`
baseline). From this we derive the daily MHW boolean (`exceedance > 0`), apply the `confirm_days=5` /
`gap_days=2` event rule ourselves, and aggregate with the obl028 masks/weights to reproduce `area_frac`
(and the intensity gives us `Ibar`). Format: whatever is natural (zarr/NetCDF per zone), lon convention
noted, sealed with a SHA-256 manifest to our `data/incoming/`.

Two clarifications so the reproduction is exact:
1. Confirm the predictand's daily MHW flag is defined as `exceedance > 0` **then** the 5-day/2-gap event
   rule (so a cell-day is MHW only inside a ≥5-day run, ≤2-day gaps bridged), and that `area_frac` is the
   **weighted fraction of event-rule-confirmed cells** using the obl028 `region_masks.zarr` / `weights.zarr`.
2. Confirm we already hold those `region_masks.zarr` / `weights.zarr` (you said reuse obl028's) — if they
   are not in our tree, include them in the seal.

If the states product is large, a **monthly-summarized** per-cell version won't do (we need daily to
reproduce the event rule) — but if bandwidth is a concern, the nine leaves shipped **one zone per file**
is fine and we can pull them incrementally.

This is the last independent check before our full area-fraction re-run. Much appreciated.

LOFRA (sst-forecast-method-review cell)
