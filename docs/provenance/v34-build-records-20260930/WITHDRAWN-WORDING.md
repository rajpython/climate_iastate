# Withdrawn wording in the delivered records — and where the correction actually lives

Admin's correction round (`from-admin/admin-to-mini-m1-m4-cc-dashboard-20260930-06-…`) asks us to make two
corrections **at source**, so a future delivery cannot carry them forward again. This file records what was
withdrawn, what replaced it, and why the delivered files in this directory are **not** rewritten.

## The delivered files are deliberately left as shipped

`region_masks_provenance.json` and `build_record_vintage20260722.json` in this directory are byte-identical to
the copies inside the sealed bundles (`7fa9811a…`, `c3e2b924…`) and to mini's sealed
`snap-region-masks-oisst025-20260930`. Mini verified that identity explicitly. Editing our copy would break it
and manufacture a third state — the exact confusion the seal apparatus exists to prevent. So these two files
stay as delivered, and this note sits beside them.

## 1. The land / denominator sentence — WITHDRAWN

`region_masks_provenance.json` → `generator.land_mask` reads:

> "none applied by the generator; land cells inside a polygon carry NaN SST in OISST and drop out downstream"

The second clause is **wrong**, not merely loose. Nothing drops out. Replacement, mini's sentence, now the
wording of record:

> **"no land mask; cells inside a polygon that never carry valid SST are never flagged and remain in the
> area-fraction denominator."**

The denominator `Σ w·mask` is computed **once from the static mask**, so such a cell contributes 0 to the
numerator and its full `cos(lat)` to the denominator on every day; ice-masked cells behave the same way on the
days they are masked. Mini found this from the data: the sealed `area_frac` reproduces only under this reading.

Never-valid mask cells per zone (independently reproduced here): sebs 7, nbs 3, wgoa 24, egoa 56, ai_west 0,
ai_central 0, ai_east 1, chukchi 13, beaufort 5.

**Corrected at source in:**
- `src/mhw/regions/masks.py` — module docstring (the generator)
- `src/mhw/states/aggregates.py` — module docstring (the code that computes the denominator)

## 2. The `Obar` negative count — CORRECTED IN FORM

`build_record_vintage20260722.json` → `columns.Obar.caveat` reads "Five negative values exist, all in
Chukchi/Beaufort." The count is right but the form is ambiguous — it is a total across two series. Say instead:

> **4 daily + 1 monthly** — chukchi daily 2 / monthly 0; beaufort daily 2 / monthly 1; no other zone, daily or
> monthly; most negative daily −0.0248 (beaufort).

**Corrected at source in:** `src/mhw/states/aggregates.py` — module docstring.

## 3. A related inaccuracy in an older delivered manifest (not part of admin's round)

`docs/handoffs/SEAL-MANIFEST.md` (the obl028 seal manifest, 2026-07-01) describes Chukchi/Beaufort as
"**water-only**, ~1,065/908 cells". The cell counts are right; "water-only" invites the same wrong inference
about a land mask. It comes from the *source polygons* being marine EEZ geometry, not from any masking step.
That manifest was delivered and is immutable under the handoff convention, so it is not edited; the correction
was made in `dashboard-to-mini-cc-admin-20260930-02` §4 and is recorded here.
