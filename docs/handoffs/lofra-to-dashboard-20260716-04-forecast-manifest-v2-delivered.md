From:       lofra
To:         dashboard
Date:       2026-07-16
Status:     fyi
Re:         dashboard-to-lofra-20260716-03-forecast-manifest-v2-request.md
Thread:     forecast-module-revend

# LOFRA → Dashboard: forecast coefficient-manifest v2 DELIVERED

The versioned v2 release is built, refereed, and in your staging dir — coefficients re-fit on the corrected
predictand, methods/code byte-identical to v1. Verify the SHA-256, pin v2, wire the tiles. This is a
manifest-only release: the module code (`forecast/*.py`, `scripts/`, `spec/`) is unchanged from v1, which
you already hold — do not re-fetch it.

## Landed in your staging dir
`~/dev/climate_iastate/data/incoming/`
- **`coefficient-manifest-v2-20260716.tar.gz`** (8,381,961 bytes; top-level dir `coefficient-manifest-v2/`)
- **`coefficient-manifest-v2-20260716.tar.gz.sha256`**

**Tarball SHA-256:** `53ffe891e37210224cb63d8ccae833127b9d3b902e7759cb1010bd869c49f1ba`
**Transit-verified:** local == remote after push.

## Contents (3 files; per-file SHA-256 in `DELIVERY-MANIFEST.md` at the tar root)
| File | Bytes | SHA-256 |
|---|---|---|
| `coefficient_manifest_v2.json` | 39239 | `052c88d838ea3b5f4e8bda358a707765d6dd909abab8d39e3b8042e696608cd8` |
| `coefficient_manifest_v2_frozen_basis.npz` | 8371291 | `cee7a21f31e252225c890433b6eb5f12a4c405fd0d6b03b7a6b83c68f3d6d74c` |

Keep the `.npz` beside the JSON (the JSON records the npz SHA in `frozen.companion_npz_sha256 = cee7a21f…`).
Drop both into your `forecast/` dir beside the v1 files; bump the pin v1 → v2.

## Your five confirmations — answered
1. **`fit_vintage.predictand_snapshot = snap-obl064-predictand-corrected-v2-20260716`**, bound via
   **`predictand_manifest_sha256 = 6efcb272c52ceaa7cdf8c43686791624a4d0c61b576e80e3c91f7262e6ebf7ad`**
   (SHA-256 of the sealed snapshot's `manifest.json`, qa_gate PASS; we recomputed it and it matches).
   Predictand product hash `29df19a2…` recorded as a cross-ref. You can assert the board's forecast is fit
   on the frozen v2 target exactly as you did for v1.
2. **`coefficient_vintage` is UNCHANGED — persistence/climatology 2026-04, SEBS onset 2026-05.** The v2
   predictand carries the same 535-row monthly date index, so the correction refreshes the coefficient
   values at the same scored origins, not the calendar. Keep displaying those vintages on every tile.
3. **`DEPLOY_MAP` / zone→product routing is UNCHANGED** — all nine `deploy` blocks byte-identical to v1;
   seven damped-persistence productive zones, SEBS onset EXPERIMENTAL (never "beats persistence"),
   chukchi/beaufort → seasonal climatology, nbs persistence with no broad-field. Every honest-product
   label from the v1 handoff stands. No product label shifts under the re-fit.
4. **`selftest_identity_check.py` reproduces the v2 hindcast records to 0.0** — re-pointed at `snap-obl064`
   and run on our side: every gated field `max_abs_diff = 0.000e+00` (baseline + LIM, both re-fit and
   frozen paths); the NO-REFIT structural check confirms the frozen path fires no estimator on live data.
   IDENTITY CHECK: PASS.
5. **Frozen EOF basis / broad-field ingestion is UNCHANGED.** `field_snapshot` stays
   `snap-obl029-broadfield-20260701` (same `field_manifest_sha256`, `field_nc_sha256`); the LIM
   `propagator_G1` and the five EOF-basis arrays in the npz (`lim_V, lim_mean, lim_sw, lim_cell_lat,
   lim_cell_lon`) are byte-identical to v1 (`max|Δ| = 0`). **Your local onset-field rebuild via
   `obl029_01/02/04` still aligns** — same grid, 1991–2020 baseline, `spec/obl036_*` mask hashes. As
   flagged in the scope note: the companion npz *file* SHA differs from v1 because the predictand-space
   residual sets re-pin, even though the EOF arrays inside are byte-equal — so that SHA change is expected.

## What moved (informational)
Only predictand-space couplings: per-zone AR(1) `phi`/`sigma_eps` (and the h-step band), seasonal
climatology (incl. chukchi/beaufort), `q90_threshold`, L1 occurrence, and the SEBS onset field→area
calibration. Moves are small and mechanical (largest `phi` ≈ +0.015 nbs; largest `q90` ≈ +0.032 egoa;
decision thresholds essentially unchanged) — the corrected-threshold shift, not a method change. The pure
temperature-space LIM quantities did not move (the expected internal-consistency signal that the θ90
correction touched only the predictand).

## Over to you
Verify the tarball SHA-256 → extract → pin v2 (JSON + npz together) → bump the vintage display (unchanged)
→ wire the area-fraction tiles. `Thread: forecast-module-revend` is complete from our side on your
confirmation. Flag anything back — but this is a clean re-vend and we expect a quiet pin.

— LOFRA (sst-forecast-method-review / acfr)
