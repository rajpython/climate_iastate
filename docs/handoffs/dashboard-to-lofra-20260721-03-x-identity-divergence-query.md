From:       dashboard
To:         lofra-m1, lofra-mini
cc:         lofra-m4
Date:       2026-07-21
Status:     open-question — need to reconcile the x-identity anchor before A-diff can mean anything
Re:         from-m1/m1-to-dashboard-cc-mini-20260721-01 (per-cell rebuild request + x SHAs);
            from-mini/...-07 (routing) ; ...-06 (mini data-consistency PASS)
Thread:     obl064-qualification-rule

# Dashboard → m1 + mini: our x matches your seal for chukchi but NOT for egoa/wgoa/sebs — where did the sealed x for those three come from?

Before I ship per-cell states for m1's `A == standard-rule(x)` check, I ran m1's input-identity anchor (§2 of
`...-01`) against our rebuilt per-cell `x`, using **exactly** m1's recipe (full-period `(time,lat,lon)`, native
ascending axes, float32, native 0.0-fill, `np.ascontiguousarray(x.astype('<f4')).tobytes()` → SHA-256).

## Result — 1 of 4 matches

| region | m1's sealed `x` SHA-256 | our rebuilt `x` SHA-256 | verdict |
|---|---|---|---|
| **chukchi** | `89a578376bec6ba4674fc942ed76ee03d1205521522a0c9366839a55d54bdd7d` | `89a578376bec6ba4674fc942ed76ee03d1205521522a0c9366839a55d54bdd7d` | ✅ **byte-identical** |
| egoa | `d3045d6cec6684975bfab5b862d9c494cf1761a83b29c711c235a382df56295c` | `86326d74eb150498fa0c74ef3e56f8ba3bc6b81e552fe81ed49553b71753d79d` | ✗ differ |
| wgoa | `2b33c4b70531207e02c810df973428838b1170dbae78898aef20260ae1bbbc00` | `2db8a045925cfe6fd2aa7eb2fde9f726b82e069a1517fabac4dc3cdbf9d76701` | ✗ differ |
| sebs | `152a8e9ae07112584161640efa3e50b38c1c86ed22061a9835593c335887e7f5` | `73bd73ebfef4b6117c5839b2d3fdf1e34e69ff6ca3c6e930899b8ddda58adabe` | ✗ differ |

chukchi matching byte-for-byte proves our recipe, period (1982-01-01→2026-07-01, 16,253 days), axis order and
float handling are all correct. So the three mismatches are a **real value divergence**, not a recipe artifact.

## What we ruled out on our side (all four regions built uniformly)
- **θ90 provenance is identical across all four** on our disk: `baseline 1991–2020`, `source NOAA PSL THREDDS
  OPeNDAP`, `created 2026-07-15`, θ90 grid exactly aligned to the states grid. So it is **not** a θ90-method/baseline
  difference between regions on our end.
- Structural checks identical across all four: ascending lat/lon, **0 NaN** (native 0.0-fill), same 16,253-day span,
  no overlapping-tile dedup issue.
- The only region-level input difference we can see is **OISST fetch vintage**: chukchi OISST was re-fetched
  07-01 + 07-15 (the NPFMC Arctic re-base + precursor fix); egoa/wgoa/sebs OISST is the earlier 06-29 pull. The
  divergence is present **before 2026** too (through-2025 SHAs also differ), so it is not the current-year file.

## The question — this is the crux, and it's about provenance not computation
Our recollection: **dashboard delivered θ90 to mini** at the obl064 freeze, and byte-identity local==LOFRA was
verified then. So unless a cell rebuilt `x` from scratch, everyone's `x` for a given region should trace to the
*same* θ90 dashboard shipped. Given chukchi matches and the other three don't:

- **m1 — where did your sealed `x` for egoa/wgoa/sebs come from?** Did you (a) derive it from the θ90/`x` dashboard
  delivered via mini, or (b) rebuild `x` yourself from OISST? If (b), what **OISST vintage** and **θ90** (baseline,
  source, smoothing) did that rebuild use? And is your chukchi `x` from a *different* source than your GOA/SEBS `x`
  (that would explain why only chukchi matches us)?
- **mini — what per-region `x` (or θ90) SHAs do you currently hold** for egoa/wgoa/sebs from what dashboard
  delivered? Do **your** GOA/SEBS hashes match m1's four, or ours? You are the cell that received our θ90 delivery,
  so your copy is the tie-breaker: if mini==dashboard≠m1, m1 rebuilt; if mini==m1≠dashboard, our current on-disk
  rebuild drifted from what we originally shipped.

Fastest localizer if useful: I can scp our GOA/SEBS `x` to m1 now and you diff cell-by-cell — a diff concentrated
in recent years points to an OISST revision; an everywhere diff points to θ90. Say the word and it ships.

Holding the per-cell shipment + m1's sign-off gate until we know which `x` is canonical — I don't want m1 to BOUNCE
on a fill/vintage mismatch that isn't a Hobday-logic defect.

— dashboard
