# `forecast` — Alaska marine-heatwave zone forecast module (v1.1.0)

Operational forward-mode forecasts for the nine Alaska EEZ zones
(`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`),
packaged from the models validated in the working paper
*"SST forecast method review"* (v14, 2026-07). This module introduces no new
science: every coefficient is pinned from the paper-validated fits, and the
shipped selftest proves the shipped code reproduces the paper's hindcast
records to machine precision (max abs diff = 0.0 on every gated field).

**Read this first — what the product honestly is**

1. **Damped persistence is the forecast.** For magnitude (area fraction),
   area, and occurrence across the **seven productive zones** (`sebs`, `wgoa`,
   `egoa`, `nbs`, `ai_west`, `ai_central`, `ai_east`), the operational model is
   damped persistence of the zone anomaly around its seasonal climatology.
   Nothing we tested resolvably beats it at these leads. **Skill fades by
   ~2–3 months**; do not display leads beyond 3 months.
2. **The SEBS onset watch is an EXPERIMENTAL early-warning discriminator.**
   It is a two-state signal (`elevated` / `normal`) with a tunable
   false-alarm threshold, built on a linear-inverse-model reading of the
   broad-basin SST field. It genuinely discriminates onset conditions, but it
   is **not a resolvable skill gain over persistence and must never be
   presented as "beating persistence."** Label it experimental in the UI.
3. **Chukchi and Beaufort use seasonal climatology.** Their SST record is
   ice-contaminated — this is a **data limit, not a skill result**. No
   occurrence probability and no onset product are issued for these zones.
4. **NBS gets a persistence forecast but NO broad-field/LIM reading**, and its
   tile should carry the same Arctic ice-contamination data-limitation caveat
   as Chukchi/Beaufort.

## Zone → product map

| Zone | Magnitude/area model | L1 occurrence prob | Onset watch |
|---|---|---|---|
| sebs | damped persistence | yes | yes (experimental, leads 1–2) |
| wgoa, egoa, ai_west, ai_central, ai_east | damped persistence | yes | no |
| nbs | damped persistence (carry ice-contamination caveat) | yes | no |
| chukchi, beaufort | seasonal climatology (ice-contaminated SST; data limit) | no | no |

Leads: 1–3 months (magnitude/occurrence), 1–2 months (SEBS onset watch). The
zone → product routing is encoded in `forecast.DEPLOY_MAP`; the entry points
enforce it, so a zone cannot be routed to a model the paper did not validate
for it.

## Layout and dependencies

Keep `forecast/` and `scripts/` as sibling directories (the package resolves
`scripts/` relative to itself):

```
forecast/    core.py  frozen.py  __init__.py  selftest_identity_check.py
             build_coefficient_manifest.py  coefficient_manifest_v1.json
             coefficient_manifest_v1_frozen_basis.npz  README.md
scripts/     stage3_harness.py  stage3_lim.py
             obl029_01_fetch_oisst_broadbasin.py
             obl029_02_monthly_aggregate.py
             obl029_04_zone_sst_anomaly.py
spec/        obl036_domain_spec.json  obl036_region_masks_hash.json
```

Python ≥ 3.11 with `numpy`, `pandas`, `scipy`, `scikit-learn`, `xarray`,
`netCDF4` (the latter two only for field ingestion). The frozen coefficient
file `coefficient_manifest_v1.json` and its binary companion
`coefficient_manifest_v1_frozen_basis.npz` must stay together in `forecast/`.

## Operational entry points (use these)

There are exactly two operational entry points, plus two loaders. Both
operational paths apply **frozen, pinned coefficients** and re-estimate
nothing: the only live inputs are the origin observation (persistence) and
the origin field state (onset).

### 1. `forecast_frozen` — magnitude / area / occurrence

```python
import pandas as pd
from forecast import load_manifest, forecast_frozen

mani = load_manifest()                    # pinned coefficients (JSON + npz)
df = pd.read_csv("sebs_monthly.csv")      # columns: date, area_frac
out = forecast_frozen(df, "sebs", mani, leads=(1, 2, 3))

out["leads"][1]["point_area_frac"]        # point forecast (area fraction)
out["leads"][1]["predictive_variance"]    # AR(1) h-step predictive variance
out["leads"][1]["occurrence_prob_q90"]    # lead-1 only, damped zones only
out["coefficient_vintage"]                # show this on the tile: '2026-04-01'
```

Input contract: a contiguous monthly `date` column and a NaN-free `area_frac`
column; the last row is the forecast origin. Gaps or NaNs raise (the
persistence lag structure is positional). Points are unclipped, exactly as
scored in the paper — clip to [0, 1] for display only.

### 2. `sebs_onset_watch_frozen` — SEBS onset watch (experimental)

```python
from forecast import load_manifest, load_live_field, sebs_onset_watch_frozen

mani  = load_manifest()
field = load_live_field("broadbasin_oisst_monthly.nc")   # rebuilt monthly, see below
watch = sebs_onset_watch_frozen(sebs_df, field, mani, leads=(1, 2))

watch["leads"][1]["watch"]                # 'elevated' | 'normal'
watch["leads"][1]["onset_prob_q90"]       # probability behind the state
watch["leads"][1]["decision_threshold"]   # default = warn-above-climatology
```

The last month of `sebs_df` must be present in the field (truncate the frame
to the field's last month if the predictand vintage leads the field vintage).
`threshold=` overrides the decision threshold for all leads: raise it for
fewer false alarms, lower it for earlier warnings. The default is the paper's
"warn above climatology" operating point (the climatological base rate of a
q90 exceedance). SEBS only — other zones have no validated onset product.

### Loaders

- `load_manifest(path=None)` — reads `coefficient_manifest_v1.json` + the
  companion `.npz` (frozen EOF basis and residual sets). Default path is the
  copy inside `forecast/`.
- `load_live_field(nc_path)` — ingests a broad-basin OISST monthly-anomaly
  NetCDF (variable `sst_monthly_anom`) into a projectable field. Cells are
  aligned onto the frozen EOF basis by native (lat, lon); if any frozen cell
  is missing the call **raises** rather than silently truncating the basis —
  that means your rebuilt field is not on the fit-vintage grid/baseline.

## Return contract

`forecast_frozen`, per lead: `target_date`, `point_area_frac` (unclipped),
`predictive_variance` + `predictive_variance_kind` (damped zones: the
stationary-AR(1) h-step forecast-error variance
σ²ε·(1−φ^{2h})/(1−φ²) on the pinned φ, σε — a standard textbook result
(Hamilton 1994, *Time Series Analysis*, Ch. 4; Hyndman & Athanasopoulos,
*FPP3* §9.8; Brockwell & Davis 2016); climatology zones: the frozen per-lead
train residual variance), and for lead 1 in damped zones
`occurrence_prob_q90` = P(area_frac > pinned q90 threshold), computed
distribution-free from the frozen one-step residual set.

`sebs_onset_watch_frozen`, per lead: `target_date`,
`zone_mean_anom_forecast_degC`, `point_area_frac`, `onset_prob_q90`,
`decision_threshold`, `paper_default_threshold`, and `watch`
(`elevated` iff prob ≥ threshold). Both returns carry `coefficient_vintage`
and `origin_date` — display the vintage.

## Rebuilding the broad-basin field (onset input)

The onset watch needs a monthly-updated broad-basin OISST anomaly NetCDF on
the exact fit-vintage grid and baseline. Rebuild it with the shipped chain:

1. `scripts/obl029_01_fetch_oisst_broadbasin.py` — NOAA OISST v2.1 daily SST
   via public ERDDAP (no credentials), domain 20.125–79.875°N,
   120.125–239.875°E (0–360), 0.25°, quarterly checkpointed chunks.
2. `scripts/obl029_02_monthly_aggregate.py` — monthly means, the 1991–2020
   monthly climatology, and `sst_monthly_anom` (the field the module reads);
   writes `broadbasin_oisst_monthly.nc`.
3. `scripts/obl029_04_zone_sst_anomaly.py` — optional: per-zone SST anomaly
   aggregation using the zone masks (reference for zone-level QA; the frozen
   onset path itself needs no masks — zone read-off vectors are pinned).

`spec/obl036_domain_spec.json` records the nine zone definitions and per-zone
grid extents; `spec/obl036_region_masks_hash.json` pins the SHA-256 of every
member of the dashboard region-mask set those definitions came from. Use them
to verify your mask/grid build before pointing the module at a rebuilt field.
Do not change the domain, grid, or climatology baseline: `load_live_field`
will refuse a mismatched field rather than mis-project it.

## Frozen coefficient vintage — and why it is not "latest"

The pinned coefficients are fit through the **last scored hindcast origin**
for every deployed lead: **persistence/climatology 2026-04, SEBS onset
2026-05**. That specific vintage is what makes the coefficients literally
paper-validated — it is exactly the fit the paper's rolling-origin hindcast
scored at every deployed lead, and the shipped selftest reproduces those
records to 0.0. Pinning at the latest data row instead would ship a
coefficient set no hindcast record validates. Coefficients are therefore up
to ~3 months older than the newest observation by design; only the origin
observation/state is live. Show `coefficient_vintage` in the UI.

## Validation / replication path — do NOT deploy it

`forecast.run_latest_origin` and `forecast.sebs_onset_watch` (in `core.py`)
**re-fit every coefficient on the caller's frame on every call**. They exist
to reproduce the paper hindcast bit-for-bit and to drift-check the frozen
path; run forward monthly they would silently re-estimate φ, σε, the LIM
operator, the isotonic link, and the thresholds as the record grows. Use the
frozen entry points for anything user-facing.

## Selftest

```
python forecast/selftest_identity_check.py
```

Re-runs the input QA gates, then checks: re-fit path == paper hindcast at the
final origins; frozen path == paper hindcast at the fit-vintage origins;
and a structural no-refit check (every estimator patched to raise; the frozen
path must fire none). Ships passing at exactly 0.0 on all gated fields. Note
the selftest needs the original sealed snapshots and hindcast record files,
so it runs in the research repo, not against your live data.

## Parameter lifecycle and versioning

- The research cell owns re-fits. Coefficients are updated only through
  **versioned manifest releases** (this is v1): on an annual re-fit cycle, or
  off-cycle if a structural break in the zone series is detected.
- The dashboard **pins v1** (`coefficient_manifest_v1.json` + companion npz,
  integrity via the SHA-256s in `DELIVERY-MANIFEST.md`) and **shows the
  coefficient vintage** on every tile. Do not re-fit, edit the manifest, or
  regenerate the npz on the dashboard side.
- `code_provenance` inside the manifest records the SHA-256 of the exact
  shipped code files (`stage3_harness.py`, `stage3_lim.py`, `core.py`,
  `frozen.py`) that the coefficients were built and validated with.

## Display caveats (carry these on the tiles)

- Persistence/climatology forecasts, leads 1–3 months only; skill fades by
  ~2–3 months.
- SEBS onset watch: "experimental early-warning discriminator"; never framed
  as beating persistence.
- `nbs`, `chukchi`, `beaufort`: Arctic ice-contamination data-limitation
  caveat (`chukchi`/`beaufort` are climatology-only for that reason).
- Show `coefficient_vintage` and the module version (v1.1.0).
