# Producer build records — vintage `mhw-hobday-consecutive-20260722`

Written 2026-09-30 and delivered to lofra-mini (cc lofra-admin) for the v34 replication package.
Handoff: `docs/handoffs/dashboard-to-mini-cc-admin-20260930-01-build-records-delivered-…`.

These are the producer-side records that let the package state where each OISST-derived asset came from
and under what terms. They cover `snap-mhw-hobday-consecutive-20260722`, its `-pkg2` sibling,
`snap-audit5-theta90-percell-20260725`, and `region_masks.zarr`.

| File | What |
|---|---|
| `build_record_vintage20260722.json` | pipeline id/version, commits + file SHAs of the runtime bytes that ran, OISST input versions, the exact definition applied, column definitions, licence block, exclusivity finding |
| `region_masks_provenance.json` | mask generator provenance, rasterisation rule, per-file SHA-256 (31 files), cell counts |
| `theta90_percell_sha256.json` | per-zone θ90 value SHA-256 (12 zones) + the exact hash recipe + verbatim on-disk attrs |
| `oisst_input_file_shas_vintage20260722.txt` | the 540 per-file OISST input SHAs; aggregate `01ee85ae…` |
| `dashboard-build-records-v34-20260930.gates.json` / `.tar.gz.sha256` | the seal's measured gates and outer checksum for the bundle shipped to mini (`7fa9811a…`) |

The data licence settled by the PI on 2026-09-30 is at the repo root: `LICENSE-data-CC-BY-4.0.txt`.

## Two facts re-verified on 2026-09-30, 70 days after the seal

- The OISST input aggregate SHA reproduces **exactly** from the producer cache (540 files,
  `01ee85ae7c889dbcbc32613530967454b5115983d646c18398ca608dd2054d47`).
- `config/regions.geojson` is still `5038762ed69802d1365938d00eeb36dce115efe0ec04660c386c3c79d2fcc8a8`,
  matching the deposit's copy, and three of the twelve published θ90 SHAs reproduce byte-exactly.

## Follow-up 2026-09-30: the mask-store question, settled

Mini could not seal `region_masks.zarr`: 4 of its 31 files differed from our list, all in the combined-zone
(`ebs`/`goa`/`ai`) masks. Resolved in `…-20260930-02`:

- The **union rule** (combined mask ≡ union of subareas) entered at commit `9ddd92f`, 2026-07-01 11:29:29 −0500,
  to satisfy LOFRA's own OBL-028 flag 1. Our store was written at **11:26:45** that morning in one
  `to_zarr(mode="w")` pass and **never rewritten** — so the 2026-07-21 vintage build read the union version.
- Mini's copy is the **pre-fix** store, packed for the obl028 seal a few hours before the fix landed.
- Data-side proof: the shipped `ebs`/`goa`/`ai` `area_frac` series equal the leaf-weighted roll-ups of their
  subareas over all 16,253 days to max |Δ| **1.2e-07**, which holds only under the union rule.
- The difference is **not** cosmetic for the roll-ups (the extra cells are mostly valid ocean): max |Δarea_frac|
  ebs 4.13e-04, goa 1.13e-03, ai 4.24e-03. Leaf zones are byte-identical between us, so no paper number moves.
- The union store was sealed and shipped: `dashboard-region-masks-oisst025-20260930.tar.gz`, sha256
  `c3e2b924e89710a2a55a0d6920624a4df9c0113d24193287536155d4f080dc3b`.

Two corrections to our own records, both mini's finding:

- **The land wording was wrong.** Cells inside a polygon that never carry valid SST do **not** "drop out
  downstream": the denominator `Σ w·mask` is computed once from the static mask, so such a cell contributes 0 to
  the numerator and its full `cos(lat)` to the denominator on every day. Ice-masked cells likewise stay in the
  denominator on masked days. Never-valid mask cells per zone (independently reproduced): sebs 7, nbs 3, wgoa 24,
  egoa 56, ai_west 0, ai_central 0, ai_east 1, chukchi 13, beaufort 5.
- **`Obar` negatives are 4 daily + 1 monthly**, not "five values" — chukchi daily 2 / monthly 0, beaufort daily 2 /
  monthly 1, no other zone. Most negative daily −0.0248 (beaufort).

`snap-audit5-theta90-percell-20260725` is mini's own seal, made 2026-07-25 from the θ90/μ arrays we shipped
2026-07-15 — which is why our ledger has no 07-25 delivery. All nine leaf zones match our hashes. Its sealed copies
carry the stale variable-level attribute `source = "NOAA PSL THREDDS OPeNDAP"`; that string was a **hard-coded
literal** (build commit `c919050`, line 527) never derived from the fetch, whose only remote open is PFEG
`ncdcOisst21Agg` (line 228). Confirmed live: a PFEG re-pull of `ai_east` 2020 today is **byte-identical** to the
cached file the sealed θ90 was built from.

## Four-cell census 2026-09-30 (`…-20260930-03`, to admin)

Read-only `find` + `shasum` across the other cells' trees (no writes, A-09 observed):

| Holder | All 31 files vs canonical |
|---|---|
| dashboard | canonical (reference) |
| lofra-m1 (`mhw-lifecycle/data/scratch/masks_extract/…`) | **byte-identical, 31/31** |
| lofra-m4 (`mhw-bvar-lim/data/raw/nsidc-sic/masks_work/…`) | **byte-identical, 31/31** |
| lofra-mini (`obl028-unpack/…`) | 27/31 — the 4 combined-zone chunks are pre-fix |

One stale copy in one unpack directory, not a programme-wide drift. The cells that consume masks in their
modelling are already on the canonical store, so no m1/m4 work needs revisiting.
