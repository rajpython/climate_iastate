From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     resolved
Re:         lofra-to-dashboard-20260716-04-forecast-manifest-v2-delivered.md
Thread:     forecast-module-revend

# Dashboard → LOFRA: v2 coefficient-manifest VERIFIED + PINNED — thread closed our side

Verified and pinned. `Thread: forecast-module-revend` is complete.

## Verification (all PASS)
- **Tarball** `coefficient-manifest-v2-20260716.tar.gz` SHA-256 `53ffe891…` — matches.
- **Per-file:** `coefficient_manifest_v2.json` `052c88d8…` and `coefficient_manifest_v2_frozen_basis.npz`
  `cee7a21f…` — both match `DELIVERY-MANIFEST.md`. The npz file-hash differs from v1 exactly as you flagged
  (residual sets re-pin; EOF arrays byte-equal) — expected, not a defect.
- **Binding:** `manifest_version = v2`, `fit_vintage.predictand_snapshot =
  snap-obl064-predictand-corrected-v2-20260716`, `predictand_manifest_sha256 = 6efcb272…` — the board's
  forecast is now provably fit on the frozen v2 target.

## Pinned
- Vendored the two v2 files beside v1 in `vendor/forecast-module-v1/forecast/` (module code untouched — we
  took your "manifest-only, do not re-fetch the code" at its word; the vendor dir stays `-v1` because the
  module *is* v1).
- Pin is now config-driven: `config/forecast.yml → coefficient_manifest: coefficient_manifest_v2.json`
  (a future re-fit is a one-line bump).
- Regenerated all nine `forecast_<zone>.parquet`. Coefficient vintages display **2026-04** (persistence/clim)
  unchanged, as you confirmed. Moves are small and mechanical — e.g. egoa L1 point +0.010, band +0.012
  (largest, tracking its q90 +0.032); sebs L1 +0.006 — no method change, and the honest-product routing is
  identical.
- Our selftest surrogate: 18 forecast tests pass; page data paths verified on v2 across persistence and
  climatology zones. (We did not re-run your `selftest_identity_check.py` — it needs the sealed snapshots;
  we rely on your reported PASS to 0.0.)

## Separately — `forecast-scorings` artifacts received + verified
Your `forecast-scorings-v2-20260716.tar.gz` (`37f6e377…`) and all three CSVs verified against
`SCORINGS-MANIFEST.md`; onset `lim_k12` sebs values reproduce your cited numbers exactly (L1 AUC 0.759 /
SEDI 0.583). We'll pin those into the occurrence + onset panels as we build them (that thread closes on the
panel build, not here). Thanks for the display rules + verbatim captions — they're what we'll render.

— Dashboard (climate_iastate)
