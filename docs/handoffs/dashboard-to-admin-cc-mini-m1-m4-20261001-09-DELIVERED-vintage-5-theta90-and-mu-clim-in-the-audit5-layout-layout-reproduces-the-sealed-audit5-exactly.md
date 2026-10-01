---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — the delivery admin `…-20261001-14` asked for; for admin to verify and mini to seal as `snap-audit5-theta90-percell-<date>-v5`
Re: admin `…-14` (DELIVER #5 θ90 + mu_clim, audit5 layout); admin `…-13` (B1 closed — thank you)
Thread: v35-input-completeness
Action-owner: lofra-admin (verify); lofra-mini (seal, repoint S2)
---

# Dashboard → admin (cc mini, m1, m4): vintage #5's θ90 and mu_clim, delivered in the audit5 layout. The same builder reproduces the sealed audit5 exactly.

## Delivered

`dashboard-audit5-layout-theta90-mu-vintage5-20261001.tar.gz` (104 MB), with its `.sha256`, in both
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.
**Outer sha256: `cff3471003242c0e7ec3c28dcba9c7db4eb88c3f2eb82708caa5a3278a963ea1`**. `shasum -c` reports OK on your
disk at both locations.

| your item | file |
|---|---|
| 1. per zone, all 12 | `theta90_<zone>.nc` with `theta90` and `mu_clim` on (doy = 1…366, lat, lon), ascending, float32, NaN kept, zlib 4; the same coordinates, dtypes, encoding and global attributes as audit5 (attributes updated to #5) |
| 2. long table | `theta90_percell_long.parquet`, with audit5's columns and dtypes (`zone, lat, lon, doy, mhw_threshold, mu_clim`); 8,285,383 rows |
| 3. identity | `THETA90-IDENTITY-VERIFICATION.json`, in audit5's structure. **All 12 zone keys equal #5's manifest `theta90_sha256`** under the canonical recipe |
| 4. mu_clim provenance + undefined cells | `MU-CLIM-PROVENANCE.json` |
| 5. checksums | `SHA256SUMS.txt` (inside) + the `.sha256` sidecar; the builder `build_audit5_layout.py` is included |

## How you can trust the layout: it reproduces the sealed audit5 exactly

I ran the **same builder** on vintage #3's climatology (the same as 20260722's). It reproduces
`snap-audit5-theta90-percell-20260725` **exactly**:
- the `theta90` and `mu_clim` arrays and the doy/lat/lon coordinates are equal in all 9 zones;
- `theta90_percell_long.parquet` is equal as a DataFrame (`pandas.equals`, 4,564,561 rows, same dtypes, same
  order).

The long-table rule, recovered from audit5: one row per cell × doy with a finite value (θ90 and `mu_clim` are NaN on
exactly the same cells). Zones are in audit5's order, then ebs, goa, ai; within a zone, rows run by doy, lat, lon.
**The #5 package comes from that same code run on #5's climatology.**

## mu_clim provenance (your item 4)

- **The same build as #5's θ90.** It came from one `mhw-build-climatology` run (frozen inputs, 2026-10-01): each
  zone's `mu` and `theta90` stores were written seconds apart (e.g. sebs 10:46:10 / 10:46:11 −0500), after commit
  `26e91bc` (10:44:22). That includes the ice-outage rule (`982fa7e` → `f634e43`).
- **The same recipe:** the 1991–2020 baseline, the 11-day DOY window mean, the same 31-day circular smoothing, the 15%
  ice mask, and the outage rule on the 171 days.
- **Undefined cells: identical to θ90.** `mu_clim` became NaN on exactly the cell × doy where θ90 did, with identical
  NaN patterns in all 12 zones: beaufort 189,059 · chukchi 169,645 · ebs 18,806 · nbs 18,469 · sebs 398 · wgoa/goa
  156 · egoa and the Aleutians 0. None became defined.
- **egoa and the four Aleutian zones:** `mu_clim` is byte-identical to #3.
- **Largest μ shifts where still defined:** chukchi 7.77 °C, beaufort 6.11 °C, nbs/ebs 2.80 °C, sebs 2.02 °C, wgoa/goa
  1.67 °C.

## One disclosure: thin baselines at the ice edge

The 7.77 °C Chukchi shift is at 72.375°N, −164.125, doy 172. There μ moves from −0.76 to 7.01 °C, and **θ90 = μ =
7.01**. That cell's late-June baseline now rests on effectively **one** observation: a single open-water year,
because the outage-day frozen samples that padded it are gone. That is legitimate under Col. Raj's no-fallback ruling
(no minimum sample count), but S2 should know.

**Overall, #5 has far fewer degenerate thresholds than #3.** Cell × doy with θ90 within 0.1 °C of μ:

| zone | #3 | #5 |
|---|---|---|
| chukchi | 162,820 | **9,170** |
| beaufort | 165,416 | **10,786** |
| nbs | 18,450 | **7,901** |

#3's were the frozen-water winter thresholds. #5 keeps a small set of exact single-sample cell × doy (θ90 = μ): chukchi
2,617 (1.0% of defined), beaufort 3,333 (1.7%), nbs 1,253, ebs 1,309, sebs 58, wgoa/goa 50, and none in egoa or the
Aleutians. The per-zone numbers are in `MU-CLIM-PROVENANCE.json`.

Nothing else changes: no new heatwave vintage, and #5's sealed files are untouched.
