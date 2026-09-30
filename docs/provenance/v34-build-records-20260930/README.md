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
