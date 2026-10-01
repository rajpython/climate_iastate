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

## 4. The licence file's "Zone definitions" block — CORRECTED (lofra-mini, `…-20260930-05`)

The block as delivered read:

> "The nine zones are the ecosystem subareas of NOAA's Alaska Fisheries Science Center Ecosystem Status Reports
> (Ortiz and Zador 2024)."

**Wrong for two of the nine.** Only the seven ESR subareas (sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east)
come from that source. `chukchi` and `beaufort` are the NPFMC Arctic Management Area / U.S. EEZ north of 66.0°N
(Marine Regions EEZ v12, record 8463), divided at 156.47°W — and **that division is our own construction**: the
Arctic FMP supports only "Point Barrow is where the two seas meet", and no retrieved official document defines
either the 156.47°W meridian or the 66.0°N cut. Mini's Cobra check established this independently.

Note that `build_record_vintage20260722.json` → `zones.definition_credit` was **already correct** (it splits seven
ESR / two Arctic Management Area); the error was confined to the licence file's prose.

**Corrected at source** in `LICENSE-data-CC-BY-4.0.txt` (repo root), with the correction dated in the file. The copy
sealed inside `dashboard-build-records-v34-20260930` keeps the uncorrected wording and is **not** rewritten, for the
same reason as items 1–2: mini verified its byte-identity.
