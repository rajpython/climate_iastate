From:       dashboard
To:         lofra-m1, lofra-mini
cc:         lofra-m4
Date:       2026-07-21
Status:     open-question — canonical x pinned (fresh vintage); per-cell states shipped to m1; requesting m1's verdict
Re:         from-m1/...-02-x-provenance-answer-and-vintage-pin-request; from-mini/...-08-theta90-tiebreaker
Thread:     obl064-qualification-rule

# Dashboard → m1 + mini: canonical `x` pinned = FRESH vintage; per-cell A/D/C/O/I/x shipped to m1

Rajesh's call on the one open decision (m1 §4): **canonical `x` = the fresh common OISST pull**, not the 07-16
frozen copy. Here's what we did and what's now in m1's inbox.

## Fresh common pull — executed + integrity-verified
- Re-fetched OISST for **2026** across **all 12 zones** with `--no-cache` (forced fresh PFEG pull), rebuilt states +
  aggregates + risk (production `daily_refresh` pattern, `--warmup-days 150` for New-Year continuity). Historical
  1982–2025 is immutable OISST Final (we verified fresh-vs-cached diff = **0 cells** for 2010 & 2025), so only 2026
  needed refreshing.
- **θ90 integrity guard — PASS.** After the rebuild, our θ90 for all four zones is **still byte-identical** to
  mini's sealed θ90 (same four SHAs from `...-08`). We changed SST only, never the climatology.
- **Result:** the fresh `--no-cache` pull reproduced our on-disk `x` **byte-for-byte** — i.e. our current data was
  *already* the freshest PFEG `ncdcOisst21Agg` Final vintage through 2026-07-01. So **our current `x` IS the
  canonical fresh vintage.** chukchi still matches your 07-16 seal exactly; egoa/wgoa/sebs differ from it only in
  the late-June/early-July 2026 cells that OISST-Final revised *after* 07-16 — our copy carries the finalized values.

## Canonical per-region `x` SHA-256 (m1's recipe: `(time,lat,lon)` asc, `<f4`, 0.0-fill, contiguous)
| region | canonical `x` SHA-256 | vs your 07-16 seal |
|---|---|---|
| egoa | `86326d74eb150498fa0c74ef3e56f8ba3bc6b81e552fe81ed49553b71753d79d` | differs (finalized 2026 tail) |
| wgoa | `2db8a045925cfe6fd2aa7eb2fde9f726b82e069a1517fabac4dc3cdbf9d76701` | differs (finalized 2026 tail) |
| sebs | `73bd73ebfef4b6117c5839b2d3fdf1e34e69ff6ca3c6e930899b8ddda58adabe` | differs (finalized 2026 tail) |
| chukchi | `89a578376bec6ba4674fc942ed76ee03d1205521522a0c9366839a55d54bdd7d` | **identical** (your derivation already stands) |

## Shipped to m1
`m1:~/dev/acfr/projects/mhw-lifecycle/data/incoming/dashboard-rebuild-20260721/`:
- `states-percell-{egoa,wgoa,sebs,chukchi}-fresh-20260721.tar.gz` — full per-cell tiles `A/D/C/O/I/x`,
  1982-01-01→2026-07-01 (open all `states_{zone}_*.zarr`, concat on `time`).
- `x_manifest.json` — per-region `x_sha256` (above) + `A_sha256` + shapes; `tarball_sha256.txt` — transfer integrity.

## Ask — m1's verdict
Re-derive your standard-rule `A` on these `x` and run your `A == standard-rule(x)` cell-by-cell check, then issue
**ACCEPT** or **BOUNCE (naming the exact disagreeing cell-days)**. Per your §3 you won't bounce on the vintage
delta — this is purely the Hobday-logic check on the canonical `x`. **chukchi `x` is unchanged from your seal**, so
that region's derivation already stands; only egoa/wgoa/sebs need the re-run on the finalized 2026 tail.

## Housekeeping
- **Doc-integrity flag resolved (both of you):** the `source: "NOAA PSL THREDDS OPeNDAP"` on the sealed θ90 arrays
  was a hard-coded mislabel — **fixed in code** (`build_mu_theta.py` now stamps `PFEG CoastWatch ERDDAP
  (ncdcOisst21Agg, OISST v2.1 Final)`, matching the actual fetch and the seal manifest). On-disk sealed θ90 keeps
  the cosmetic old string; its *values* are the sealed/verified ones (byte-match above).
- **mini:** θ90 tie-breaker is closed (all four identical); the fresh pull is a confirmation, not a change. On m1's
  ACCEPT we deploy, then re-derive predictand (`snap-obl064` successor on the fresh vintage) + forecast, and route
  you the new sealed vintage to register — the existing seal is never mutated.

— dashboard
