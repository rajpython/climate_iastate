# DELIVERY MANIFEST — forecast coefficient-manifest v2 (2026-07-16)

Versioned coefficient-manifest release for the operational forecast module delivered as v1 on 2026-07-08.
Coefficients re-fit on the corrected canonical-Hobday θ90 predictand
(`snap-obl064-predictand-corrected-v2-20260716`); **methods/code unchanged** from v1. This is a manifest
release only — the module code (`forecast/*.py`, `scripts/`, `spec/`) is byte-identical to v1, which you
already hold and pinned; do not re-fetch it.

## Files in this release (per-file SHA-256)

| File | Bytes | SHA-256 |
|---|---|---|
| `coefficient_manifest_v2.json` | 39239 | `052c88d838ea3b5f4e8bda358a707765d6dd909abab8d39e3b8042e696608cd8` |
| `coefficient_manifest_v2_frozen_basis.npz` | 8371291 | `cee7a21f31e252225c890433b6eb5f12a4c405fd0d6b03b7a6b83c68f3d6d74c` |

Keep the `.npz` **beside** the JSON (the JSON records the npz SHA in `frozen.companion_npz_sha256`; the
loaders read the companion by that relative name). Pin them together, exactly as v1.

## Where they go
Into the module's `forecast/` directory, beside the v1 files. Bump your pin from v1 → v2 and re-show the
`coefficient_vintage` (unchanged — see below). No re-fit, manifest edit, or npz regeneration on your side,
per the parameter-lifecycle rule.

## The five confirmations you asked for
1. **`fit_vintage.predictand_snapshot = snap-obl064-predictand-corrected-v2-20260716`**, bound to the
   sealed snapshot's `manifest.json` via `predictand_manifest_sha256 =
   6efcb272c52ceaa7cdf8c43686791624a4d0c61b576e80e3c91f7262e6ebf7ad` (qa_gate PASS). Predictand product
   hash `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434` recorded as a cross-ref.
2. **`coefficient_vintage` UNCHANGED from v1** — the frozen coefficients pin at the same last-scored
   hindcast origins: persistence/climatology **2026-04**, SEBS onset **2026-05** (the v2 predictand
   carries the same 535-row monthly date index, so the correction refreshes the values at the same
   origins, not the calendar). Keep displaying those vintages.
3. **`DEPLOY_MAP` / zone→product routing UNCHANGED** — all nine `deploy` blocks are byte-identical to v1:
   seven damped-persistence productive zones (`sebs, wgoa, egoa, nbs, ai_west, ai_central, ai_east`),
   leads capped at 3; SEBS onset EXPERIMENTAL (never "beats persistence"); chukchi/beaufort → seasonal
   climatology (no occurrence/onset); nbs persistence with no broad-field/LIM. Every honest-product label
   from the v1 handoff still stands.
4. **`selftest_identity_check.py` reproduces the v2 hindcast records to 0.0** — re-pointed at
   `snap-obl064` and run on our side: every gated field `max_abs_diff = 0.000e+00` (baseline + LIM, both
   re-fit and frozen paths); the NO-REFIT structural check confirms the frozen path performs no live
   re-estimation. IDENTITY CHECK: PASS.
5. **Frozen EOF basis / broad-field ingestion UNCHANGED.** `field_snapshot` stays
   `snap-obl029-broadfield-20260701` (same `field_manifest_sha256`, `field_nc_sha256`); the LIM
   `propagator_G1` and the five EOF-basis arrays in the npz (`lim_V, lim_mean, lim_sw, lim_cell_lat,
   lim_cell_lon`) are byte-identical to v1 (`max|Δ| = 0`). **Your local onset-field rebuild via
   `obl029_01/02/04` still aligns** — same grid, 1991–2020 baseline, and `spec/obl036_*` mask hashes.
   Note: the companion npz file SHA differs from v1 (the predictand-space residual sets re-pin), even
   though the EOF arrays inside are byte-equal — so the file-level SHA change is expected.

## What moved (informational — no action)
Only predictand-space couplings: per-zone damped-persistence `phi`/`sigma_eps` (and the h-step band),
seasonal climatology (incl. chukchi/beaufort), `q90_threshold`, L1 occurrence, and the SEBS onset
field→area calibration (isotonic link, decision thresholds). Moves are small and mechanical (largest
`phi` ≈ +0.015 nbs; largest `q90` ≈ +0.032 egoa; decision thresholds essentially unchanged) — the
corrected-threshold shift, not a method change. Pure temperature-space LIM quantities
(`propagator_G1`, `zone_readoff_a_sebs`, `zone_readoff_const_sebs`, `eof_variance_fraction`) did **not**
move — the expected internal-consistency signal that the θ90 correction touched only the predictand.
