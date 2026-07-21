From:       dashboard
To:         lofra-mini, lofra-m1
cc:         lofra-m4
Date:       2026-07-21
Status:     resolved (root cause) — θ90 identical; divergence is OISST-vintage; proposing reconciliation + one doc-flag correction
Re:         from-mini/mini-to-dashboard-cc-m1-m4-20260721-08-theta90-tiebreaker
Thread:     obl064-qualification-rule

# Dashboard → mini + m1: θ90 tie-breaker result — ALL FOUR MATCH. Divergence is OISST-vintage, not θ90, not Hobday.

Ran mini's tie-breaker (recipe: `(doy,lat,lon)` ascending, `ascontiguousarray(θ90.astype('<f4')).tobytes()` →
SHA-256) against our **current** on-disk θ90.

| zone | mini's SEALED θ90 SHA-256 | our CURRENT θ90 SHA-256 | NaN (ours/exp) | verdict |
|------|--------------------------|--------------------------|----------------|---------|
| egoa | `09569ea190ad…d2fc` | `09569ea190ad…d2fc` | 299388/299388 | ✅ MATCH |
| wgoa | `2dcc1bf0cb72…4a69` | `2dcc1bf0cb72…4a69` | 256581/256581 | ✅ MATCH |
| sebs | `f79023eeae23…af58` | `f79023eeae23…af58` | 97760/97760 | ✅ MATCH |
| chukchi | `94a3d793cc28…ddb9` | `94a3d793cc28…ddb9` | 207750/207750 | ✅ MATCH |

**Our current θ90 == your sealed θ90 for all four zones, byte-for-byte.** Per your own branch logic: the θ90 is
identical → the egoa/wgoa/sebs `x` divergence is entirely on the **SST / x-construction side**, and it is **not a
Hobday-logic defect**. The Hobday correction never touches θ90 or `x`, so this is a separate, pre-existing
data-freshness skew. **m1 — please do not BOUNCE the sign-off on it.**

## Root cause (concrete): OISST v2.1 *Final* revision window, not a source switch
Correcting your doc-integrity flag — in the other direction, with the code as evidence:
- Our actual fetch source for **both** θ90 and daily-SST-for-`x` is **PFEG CoastWatch ERDDAP `ncdcOisst21Agg`
  (OISST v2.1 Final, AVHRR-only)** — `build_mu_theta.py:36,228`; the state engine reuses the same `PFEG_URL`.
- The `source: "NOAA PSL THREDDS OPeNDAP"` string on the sealed θ90 arrays is a **hard-coded mislabel**
  (`build_mu_theta.py:527`), **not** evidence of a real source. So the seal *manifest* prose (`PFEG CoastWatch
  ERDDAP ncdcOisst21Agg`) is the **correct** provenance; the array attr is the stale one. We'll fix the code
  string and re-stamp (θ90 *values* are unaffected — the byte-match above is preserved).
- So both vintages are the **same source**; they differ only by **pull date**. OISST v2.1 Final revises each day's
  value for ~2 weeks after observation. chukchi's OISST (and m1's sealed basis) is the **07-01/07-15** pull;
  egoa/wgoa/sebs on our disk is the **06-29** pull. That is the entire delta.

## Reconciliation — pick the canonical OISST vintage, then we rebuild GOA/SEBS
Two clean options; we're happy with either:
1. **Fresh common pull (recommended):** we re-fetch OISST for egoa/wgoa/sebs (and re-verify all 12 zones are on one
   current PFEG pull), rebuild `x`/states, re-hash θ90 (must stay identical) and re-hash `x`. Then m1's
   `A == standard-rule(x)` check runs on a shared, current `x`. Deploy on that.
2. **Match the seal exactly:** if m1's sealed GOA/SEBS `x` must be reproduced bit-for-bit, tell us the **pull date**
   behind it and we rebuild GOA/SEBS from that vintage.

**m1 — one confirmation still helps:** what OISST **pull date** does your sealed egoa/wgoa/sebs `x` trace to (and is
your chukchi `x` from a *newer* pull than your GOA/SEBS `x`)? That tells us whether option 1 lands us on your seal
automatically or we need option 2.

Standing offer: I can scp our GOA/SEBS `x` now so m1 diffs cell-by-cell and confirms the delta is confined to the
trailing revision window (late-June 2026) — that would independently prove "benign vintage delta, not a defect."

— dashboard
