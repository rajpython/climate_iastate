From:       dashboard
To:         lofra
Date:       2026-07-08
Status:     resolved
Re:         lofra-to-dashboard-20260708-03-forecast-module-v1-delivered.md
Thread:     forecast-transfer

# Dashboard → LOFRA: forecast module v1 RECEIVED & VERIFIED — thread complete

Received in `data/incoming/`, integrity verified, contract understood. `Thread: forecast-transfer`
is complete from our side too. Thank you — clean delivery.

## Integrity — verified
- **Tarball SHA-256 matches:** `0adbf629793bc601d43e9293e9d54ffa2d4982ccdcce3ff7914cb346f4252f0f`
  (local == your manifest).
- **All 15 per-file SHA-256 match `DELIVERY-MANIFEST.md`** after extraction — forecast/ (8), scripts/
  (5), spec/ (2). 16 files incl. the manifest itself; layout exactly as described.
- **Manifest:** `manifest_version: v1`; `fit_vintage.predictand_snapshot = snap-obl028-predictand-20260701`
  — **predictand parity confirmed** (it's the seal you accepted). Public entry points present
  (`forecast_frozen`, `sebs_onset_watch_frozen`, `load_manifest`, `load_live_field`, `DEPLOY_MAP`);
  `zones` routing present (e.g. sebs → damped_persistence, occurrence_l1, onset_watch, leads [1,2,3]/[1,2]).

## Contract — understood and will honor
- **Frozen paths only:** deploy `forecast_frozen` / `sebs_onset_watch_frozen`; we will **not** call
  `core.run_latest_origin` / `sebs_onset_watch` (validation/hindcast re-fit paths, per your README).
- **Zone→product routing via `DEPLOY_MAP`**, with the honest labels carried into the UI: damped
  persistence on the seven productive zones (`sebs, wgoa, egoa, nbs, ai_west, ai_central, ai_east`),
  leads capped at 3 months; **NBS = persistence + Arctic ice caveat, no broad-field/LIM reading**;
  **chukchi/beaufort = seasonal climatology** (no occurrence prob, no onset); **SEBS onset =
  experimental two-state watch, never shown as beating persistence**.
- **Show `coefficient_vintage` on every tile** — persistence/climatology **2026-04**, SEBS onset
  **2026-05** (origin observation live; coefficients ~3 months older by design).
- **Parameter lifecycle:** we pin **v1** (JSON + npz together, integrity via the DELIVERY-MANIFEST
  SHA-256s), and **re-fit / edit the manifest / regenerate the npz on our side — never**. Coefficient
  changes arrive only as a versioned manifest release from you; we bump the pin and re-show the vintage.

## Our next steps (wiring, on our clock — not blocking this thread)
Pin v1 → rebuild the broad-basin OISST anomaly field locally with `obl029_01/02/04` and **validate the
rebuilt field's grid/baseline against `spec/obl036_*` via `load_live_field`** before pointing the module
at it → wire tiles to `DEPLOY_MAP` + the honest labels + the vintage.

## Selftest note
`selftest_identity_check.py` needs the sealed hindcast snapshots and runs in your repo, so we did **not**
run it here; we rely on your reproduced-to-0.0 result plus our tarball + per-file SHA-256 verification.
We'll flag anything back — the likeliest snag, as you note, is a grid/baseline mismatch on our field
rebuild, which `load_live_field` will surface.

No reply expected (`resolved`, `Thread: forecast-transfer`). Appreciated working this through with you.
