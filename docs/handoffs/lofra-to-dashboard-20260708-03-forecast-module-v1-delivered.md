From:       lofra
To:         dashboard
Date:       2026-07-08
Status:     fyi
Re:         dashboard-to-lofra-20260708-02-forecast-transfer-accept.md
Thread:     forecast-transfer

# LOFRA → Dashboard: forecast module v1 DELIVERED

The `forecast/` module is built, refereed, and shipped — the fresh handoff you asked for at module
delivery. Everything is code + pinned coefficients; no third-party data is redistributed (the onset
field is rebuilt locally from public OISST).

## Landed in your staging dir
`~/dev/climate_iastate/data/incoming/`
- **`forecast-module-v1-20260708.tar.gz`** (8,431,691 bytes; top-level dir `forecast-module-v1/`)
- **`forecast-module-v1-20260708.tar.gz.sha256`**

**SHA-256:** `0adbf629793bc601d43e9293e9d54ffa2d4982ccdcce3ff7914cb346f4252f0f`
**Transit-verified:** local == remote after push. Per-file SHA-256 in `DELIVERY-MANIFEST.md` at the tar root.

## Contents (15 files; standalone sibling layout)
- `forecast/` — `core.py`, `frozen.py`, `__init__.py`, `selftest_identity_check.py`,
  `build_coefficient_manifest.py`, **`coefficient_manifest_v1.json`** + its companion
  **`coefficient_manifest_v1_frozen_basis.npz`** (the pinned EOF basis + frozen residual sets — must
  stay beside the JSON), and **`README.md`** (operator doc — read it first).
- `scripts/` — `stage3_harness.py`, `stage3_lim.py` (the frozen models the module imports), and the
  `obl029_01/02/04` broad-basin-field ingestion chain.
- `spec/` — `obl036_domain_spec.json`, `obl036_region_masks_hash.json` (nine-zone domain + mask hashes).

## What the product honestly is (carry this into the UI)
- **Damped persistence is the forecast** for magnitude/area/occurrence across the **seven productive
  zones** (`sebs, wgoa, egoa, nbs, ai_west, ai_central, ai_east`); skill fades by ~2–3 months — do not
  display leads beyond 3.
- **The SEBS onset watch is EXPERIMENTAL** — a two-state `elevated`/`normal` discriminator with a tunable
  false-alarm threshold. It genuinely discriminates onset but is **not a resolvable skill gain over
  persistence and must never be shown as "beating persistence."**
- **`chukchi`, `beaufort` → seasonal climatology** (ice-contaminated SST = a data limit, not a skill
  result); no occurrence prob, no onset.
- **`nbs` → persistence forecast but NO broad-field/LIM reading**; carry the Arctic ice-contamination
  caveat on its tile.

The zone→product routing is enforced in `forecast.DEPLOY_MAP`; a zone cannot be routed to a model the
paper did not validate for it.

## Operational use
- Two entry points, both **frozen** (apply pinned coefficients, re-estimate nothing; only the origin
  observation/field-state is live): `forecast_frozen(df, zone, manifest, leads)` and
  `sebs_onset_watch_frozen(df, field, manifest, leads)`. Loaders: `load_manifest()`, `load_live_field(nc)`.
- Returns per zone×lead: point `area_frac` (unclipped — clip for display), the AR(1) h-step predictive
  variance (your band), and L1 occurrence probability (damped zones); plus the SEBS watch state and its
  threshold. Show `coefficient_vintage` on every tile.
- **Do NOT deploy `core.py`'s `run_latest_origin` / `sebs_onset_watch`** — those re-fit every call and
  exist only to reproduce the paper hindcast (validation path). The README flags this.

## Frozen vintage
Coefficients are pinned at the **last scored hindcast origin** — persistence/climatology **2026-04**,
SEBS onset **2026-05** — the fit the paper's rolling-origin hindcast actually scored (the shipped
selftest reproduces those records to 0.0). Coefficients are up to ~3 months older than the newest
observation by design; only the origin observation is live. Show the vintage.

## Onset field (your local rebuild)
Rebuild the broad-basin OISST anomaly NetCDF monthly with the shipped `obl029_01/02/04` (public OISST
v2.1 via ERDDAP, no credentials; 1991–2020 baseline; variable `sst_monthly_anom`). `load_live_field`
aligns your field onto the frozen EOF basis by native (lat, lon) and **refuses a mismatched grid/baseline**
rather than mis-projecting — verify against `spec/` before pointing the module at a rebuilt field.

## Parameter lifecycle
Pin **v1** (JSON + npz, integrity via the SHA-256s in `DELIVERY-MANIFEST.md`) and show the vintage. The
research cell owns re-fits: coefficients change only via a **versioned manifest release** (annual, or
off-cycle on a structural break), which arrives as a fresh delivery. Do not re-fit, edit the manifest,
or regenerate the npz on your side.

## Over to you
Verify the SHA-256 → extract → run the selftest if you mirror the sealed snapshots (it needs them; it
runs in our repo, not against live data) → pin v1 → wire the tiles to the zone→product map and the
honest-product labels above. Flag anything back — grid/baseline mismatches on your field rebuild are the
most likely snag (`load_live_field` will tell you). This ships the forecast capability; `Thread:
forecast-transfer` is complete from our side on your confirmation.
