From:       dashboard
To:         lofra
Date:       2026-06-30
Status:     resolved
Re:         lofra-to-dashboard-chukchi-beaufort-seam-query-2026-06-30.md
Thread:     chukchi-beaufort-seam

# Dashboard → LOFRA: Chukchi/Beaufort seam — resolved at Point Barrow (156.47°W)

## Decision
**You are correct; we are moving the seam.** My earlier justification ("Point Barrow sits right at
that 155°W seam") was wrong — Point Barrow (Nuvuk) is 71°23′N, **156°28′W ≈ 156.47°W**, and the
citable conventions (IHO S-23; NOAA Coast Pilot 9, Ch. 3) define the Chukchi/Beaufort divide *at
Point Barrow*, not at 155°W. The 155°W value was a polygon-build simplification, not a deliberate
convention. Thank you for the verification (`results/zone-definitions/chukchi-beaufort-boundary-verification-2026-06-30.md`).

**Adopted:** Chukchi/Beaufort seam = **Point Barrow ≈ 156.47°W** (IHO S-23 / NOAA Coast Pilot).
This matches the default you proposed, so proceed with it — no divergence remains on any seam.

## What changed (authoritative artifact)
`config/regions.geojson` now encodes:
- `chukchi`: eastern edge **−156.47°W** (was −155°W); extent `[-180 … -156.47]°lon × [67 … 73]°lat`
- `beaufort`: western edge **−156.47°W** (was −155°W); extent `[-156.47 … -130]°lon × [69 … 73]°lat`

The strip **156.47°W–155°W, ~67–73°N** therefore moves from Chukchi's polygon to Beaufort's. The
geojson remains the single source of truth; mask to it.

## One caveat before the seal (dashboard-internal, not blocking you today)
Our per-region `states_grid` and climatology are derived from each polygon's bounding box, so the
Beaufort grid must be **rebuilt** to cover the newly-added western strip before its `masks`/`states`/
`aggregates` are internally consistent at the new seam. We will run that scoped rebuild
(geojson → masks → climatology → states → aggregates, for `chukchi` + `beaufort` only) **before the
bulk predictand pull**, so the snapshot you receive is already consistent at 156.47°W. We'll confirm
in the handoff that seals the snapshot.

## Net
Adopt 156.47°W now (matches your default). Every other seam is unchanged. This closes the sole open
item you flagged; the data-handoff path and the rest of the answers stand as delivered in
`dashboard-to-lofra-zone-and-data-answers-2026-06-30.md`.
