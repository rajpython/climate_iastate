# forecast-implementation-document.md

# Forecast Extension Implementation Document

## Current Development Focus

Track A — Short-Term Statistical SST Forecasting.

Branch: `feat/sst-forecast`.

Bottom Ocean-State Integration (originally "Phase 1") has been **resequenced**: it
is preceded by a discovery spike (`feat/mom6-spike`) and implemented as a later
increment (`feat/bottom-ocean-state`). The rationale and roadmap are in
`forecast-extension-plan.md`; this document gives the implementation specifics for
both the current track and the deferred bottom-state work.

---

# Part 1 — Current: SST Forecast MVP

Mission:

Enter forecasting with a statistical short-term SST forecast on the existing
pipeline. No new data ingestion.

Approach (see `sst-forecast-mvp-plan.md` on the branch for full detail):

* Forecast the **primitive at the grid level**: per-cell anomaly = SST − μ.
* Baselines: persistence, damped persistence, AR(1).
* Convert to a marine-heatwave **exceedance probability** vs the existing θ₉₀.
* **Derive** regional and area-based products from the cell-probability map; do not
  forecast the monitoring aggregates directly.
* One **variable-agnostic engine** (`src/mhw/forecast/`) reused later for bottom
  temperature and seasonal ensembles.

Inputs (all already on disk): μ/θ₉₀ per region, OISST daily cache, region masks,
cos-lat weights.

Outputs: per-cell MHW probability map; regional outlook (current / 14-day /
30-day); skill verification (Brier / Brier Skill Score) vs climatology and
persistence.

Status: engine math implemented and tested; data adapters, CLI wiring, backtest
harness, dashboard panel, and API endpoint are the remaining MVP steps.

---

# Part 2 — Deferred: Bottom Ocean-State Integration

This phase does NOT involve forecasting. It creates the environmental foundation
required for future bottom-temperature forecasting (which then reuses the Track A
engine).

It begins **only after** the discovery spike (`catalog_report.md`) has answered the
grid and latency questions.

---

# Scientific Motivation

Many Alaska fisheries respond more directly to:

* Bottom temperature
* Cold pool dynamics
* Shelf thermal conditions

than to sea surface temperature.

The dashboard currently represents only surface conditions. This phase expands the
dashboard into the water column.

---

# Step 0 (Prerequisite) — Discovery Spike

Branch: `feat/mom6-spike`. Deliverable: `catalog_report.md`.

Resolve before implementation:

* Data source (NEP10k vs CEFI vs Copernicus) and access method.
* Variables and units available (bottom temp, SST, ice, MLD, salinity, currents,
  oxygen, OHC).
* Temporal cadence (daily vs monthly) and coverage.
* Latency (how far behind real time).
* Grid strategy (regrid to 0.25° vs native curvilinear).
* Cold-pool derivability and an observed validation target.

---

# Data Source Priority

1. NOAA MOM6-COBALT-NEP10k (preferred) — OPeNDAP / THREDDS / AWS S3.
2. NOAA CEFI products.
3. Copernicus Marine (fallback, only if NOAA proves difficult).

---

# Engineering Realities (resolve in design, not mid-build)

## Grid mismatch  *(the primary risk)*

The existing pipeline assumes a regular 0.25° lat/lon grid (cos-lat weights,
rasterized region masks, DOY climatology zarr). **MOM6-NEP10k is curvilinear
~10 km** and is not compatible as-is.

Recommended: regrid bottom temperature onto the existing 0.25° grid (e.g. `xesmf`
conservative remap) so masks, weights, climatology, and the states engine reuse
unchanged. The alternative is a parallel native-grid path. Decide in the spike.

## Latency  *(bottom state is not "live")*

The NEP10k hindcast lags real time by months-to-years. A "current bottom anomaly"
panel is misleading unless labelled a **recent-historical / lagged** product. This
is acceptable for retrospective ecosystem report cards, but dashboard copy and API
must not imply real-time bottom monitoring.

## Temporal cadence and baseline period

"Adapt the Hobday engine" (daily DOY) only works cleanly if bottom data is daily.
If only monthly is available, a separate monthly path is required. Decide in the
spike.

Reconcile the climatology baseline: the existing SST climatology is **1991–2020
daily DOY**; NEP10k hindcasts typically start ~1993. Choose a defensible bottom
baseline and document any divergence from the SST baseline.

---

# Directory Structure (actual repo — extend, do not invent a parallel tree)

```
src/mhw/
    fetch/          # OISST + indices ingestion (existing)
    climatology/    # mu / theta90 builders (existing)
    regions/        # masks, weights (existing)
    states/         # Hobday state engine, aggregates, risk (existing)
    forecast/       # variable-agnostic forecast engine (Track A)
    bottom/         # NEW: MOM6 ingest, regrid, bottom climatology, cold pool

data/derived/
    climatology/    # {mu,theta90}_<region>.zarr            (existing pattern)
    states_grid/    # per region/year zarr                  (existing pattern)
    aggregates_region/  region_daily_<region>.parquet       (existing pattern)
    risk/           # risk_<region>.parquet                 (existing pattern)
    bottom_temp/    # NEW: per-region bottom products
    cold_pool/      # NEW: cold-pool metrics
```

Bottom work extends `src/mhw/` and `data/derived/` in the existing per-region
style. Do not create a separate `src/ingestion`, `src/processing`, `src/metrics`
tree.

---

# Initial Regions

Eastern Bering Sea first; Gulf of Alaska after completion.

---

# Variables Required

Mandatory: bottom temperature, sea surface temperature, sea ice concentration.

Optional: mixed layer depth, salinity.

---

# Tasks

## Task 1 — MOM6 Data Discovery

Deliverable: `catalog_report.md` (the spike). Dataset URL, variables, temporal and
spatial resolution, latency, access method, grid strategy.

## Task 2 — MOM6 Ingestion + Regrid Module

File: `src/mhw/bottom/mom6_loader.py`.

Open remote dataset, subset region, select variables, **regrid to the 0.25° grid**
(per spike decision), cache locally. Requirements: xarray, dask, netCDF4, and
(if regridding) xesmf/esmpy.

## Task 3 — Bottom Temperature Climatology

File: `src/mhw/bottom/bottom_climatology.py`. Monthly (or daily, per cadence
decision). Reference period per spike decision; document any divergence from the
1991–2020 SST baseline.

## Task 4 — Bottom Temperature Anomaly

Daily and/or monthly anomalies = bottom temperature − bottom climatology.

## Task 5 — Bottom Heatwave Detection

Reuse the existing Hobday implementation with bottom temperature in place of SST.
Outputs: duration, intensity, maximum intensity, cumulative intensity.

## Task 6 — Cold Pool Metrics

Region: Eastern Bering Sea. Definition: area where bottom temperature < 2 °C.
Outputs: total area, historical percentile, time series.

## Task 7 — API Endpoints (under `/v1`)

`/v1/bottom-temperature`, `/v1/bottom-anomaly`, `/v1/bottom-heatwave`,
`/v1/cold-pool` — consistent with the existing versioned route structure.

## Task 8 — Dashboard Panels

Bottom Conditions panel: bottom anomaly, bottom heatwave category, cold pool
extent, historical percentile — **explicitly labelled as a lagged product**.

---

# Validation

Two complementary checks:

1. **Surface vs bottom heatwave** for the 2014–2016 Blob, 2019 Bering Sea heatwave,
   and 2023–2024 events. Document where surface and bottom diverge.

2. **Cold pool vs AFSC observed index** *(the credibility win)* — compare the
   MOM6-derived EBS cold-pool extent against AFSC's observed summer
   bottom-trawl-survey cold pool index. Agreement is what lets a collaborator cite
   the dashboard in an ecosystem report card.

---

# Success Criteria

Bottom Ocean-State Integration is complete when:

1. NOAA MOM6 data are ingested and regridded automatically.
2. Bottom climatologies are generated.
3. Bottom heatwaves are computed (reusing the Hobday engine).
4. Cold pool metrics are available and validated against the AFSC observed index.
5. Dashboard visualizations are operational and labelled as lagged.
6. API endpoints are documented under `/v1`.

Bottom-temperature *forecasting* is a later step that reuses the Track A engine —
not part of this phase.
