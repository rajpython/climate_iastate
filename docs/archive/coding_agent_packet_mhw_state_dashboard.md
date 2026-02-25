# MHW State Dashboard — Repo & Implementation Plan (Coding Agents Packet)

This document packages the repo structure, technical architecture, implementation milestones, and GitHub roadmap for the **Marine Heatwave (MHW) State Dashboard** project.  
Scope is **MHW-only** and aligned to the 2-page / 8-panel dashboard plan.

---

## 1) Repository-ready folder structure plan

A structure that cleanly separates **science**, **data**, **pipeline**, **API**, and **UI**:

```text
mhw-state-dashboard/
├─ README.md
├─ docs/
│  ├─ architecture.md
│  ├─ data_sources.md
│  ├─ state_variables.md
│  ├─ climatology_thresholds.md
│  ├─ api_spec.md
│  ├─ dashboard_wireframe.md
│  └─ operations.md
│
├─ config/
│  ├─ regions.geojson              # GOA, EBS, NBS, Chukchi, Beaufort, etc.
│  ├─ datasets.yml                 # URLs, refresh cadence, variables
│  ├─ climatology.yml              # baseline years, smoothing window, percentile
│  └─ runtime.yml                  # paths, chunk sizes, environment flags
│
├─ data/
│  ├─ raw/                         # optional cache for downloaded files
│  ├─ derived/
│  │  ├─ climatology/              # mu[d,lat,lon], theta90[d,lat,lon]
│  │  ├─ weights/                  # cell weights arrays
│  │  ├─ masks/                    # region masks per region_id
│  │  ├─ states_grid/              # rolling state arrays (A, Dtilde, C, etc.)
│  │  └─ aggregates_region/        # compact parquet/csv for dashboard queries
│  └─ logs/
│
├─ src/
│  ├─ mhw/
│  │  ├─ fetch/
│  │  │  ├─ oisst.py               # fetch/subset daily SST
│  │  │  ├─ nsidc_ice.py           # optional ice conditioning
│  │  │  └─ indices.py             # AO/PDO scraping/parsing
│  │  ├─ climatology/
│  │  │  ├─ build_mu_theta.py      # baseline climatology + thresholds
│  │  │  ├─ smooth_doy.py          # 11-day window logic
│  │  │  └─ storage.py             # zarr/netcdf writers/readers
│  │  ├─ states/
│  │  │  ├─ update_states.py       # daily update rules A, D, C, O
│  │  │  ├─ aggregates.py          # region aggregation w_g, masks
│  │  │  └─ risk.py                # percentile risk score + triggers
│  │  ├─ regions/
│  │  │  ├─ masks.py               # rasterize polygons to grid
│  │  │  └─ weights.py             # cos(lat) or true area weights
│  │  └─ utils/
│  │     ├─ time.py                # doy, leap handling
│  │     ├─ io.py                  # common readers/writers
│  │     └─ validate.py            # sanity checks
│  │
│  ├─ api/
│  │  ├─ main.py                   # FastAPI app
│  │  ├─ routes_states.py
│  │  ├─ routes_maps.py
│  │  ├─ routes_indices.py
│  │  └─ schema.py                 # pydantic response models
│  │
│  └─ dashboard/
│     ├─ app.py                    # Streamlit (or React) entry
│     ├─ pages/
│     │  ├─ 1_operational.py
│     │  └─ 2_historical.py
│     └─ components/
│        ├─ map_mhw.py
│        ├─ ts_event_metrics.py
│        ├─ predictability_panel.py
│        ├─ risk_gauge.py
│        └─ event_explorer.py
│
├─ scripts/
│  ├─ init_build_climatology.sh
│  ├─ run_daily_refresh.sh
│  ├─ backfill_states.sh
│  └─ dev_server.sh
│
├─ tests/
│  ├─ test_climatology.py
│  ├─ test_state_updates.py
│  ├─ test_region_aggregates.py
│  └─ test_risk_score.py
│
├─ docker/
│  ├─ Dockerfile.api
│  ├─ Dockerfile.dashboard
│  └─ docker-compose.yml
│
└─ .github/
   └─ workflows/
      ├─ ci.yml
      └─ daily_refresh.yml          # optional GH actions if desired
```

---

## 2) Technical architecture document (backend + frontend stack)

### 2.1 Guiding constraints

- **MHW-first**: everything flows from SST → thresholds → event states.
- **Fast daily refresh**: climatology is precomputed; daily runs only do “today” + update rolling state arrays.
- **Two “lanes”**: gridded state lane + compact region-aggregate lane.

### 2.2 Data flow (minimal, robust)

**Inputs**
- OISST daily SST (required)
- AO daily index, PDO monthly index (conditioning)
- Optional: NSIDC daily sea ice concentration (conditioning mask)

**Derived**
- `mu[d,lat,lon]`, `theta90[d,lat,lon]` precomputed once
- Daily `A, Dtilde, D, I, C, O` updated incrementally
- Regional aggregates computed daily and stored as compact tables

**Storage**
- **Zarr** (or chunked NetCDF) for gridded arrays:
  - `mu`, `theta90`, `weights`, `region_masks`, rolling state arrays
- **Parquet** (recommended) for region aggregates and indices:
  - `region_daily.parquet` with columns: `date, region_id, area_frac, Ibar, Dbar, Cbar, Obar, risk, triggers…`
- Optional Postgres later; not required for prototype if Parquet is sufficient.

### 2.3 Services (simple and scalable)

**Service 1: Pipeline runner**
- A scheduled job (cron / GH action / server scheduler) runs:
  - `build_climatology` (one-time)
  - `daily_refresh` (daily)
  - `backfill` (optional)

**Service 2: API**
- FastAPI exposing computed products to the dashboard:
  - small JSON for time-series and risk
  - optionally pre-rendered map tiles or “downsampled grids” for maps

**Service 3: Dashboard UI**
- Streamlit for fastest prototype OR React for production UX.
- Two pages with four panels each.

### 2.4 Minimal API spec (for coding agents)

These endpoints keep UI simple and prevent “data fishing.”

- `GET /regions` → list `region_id`, names
- `GET /states/region/{region_id}?start=YYYY-MM-DD&end=YYYY-MM-DD`
  - returns daily: `area_frac, Ibar, Dbar, Cbar, Obar, risk, trigger`
- `GET /map/mhw?date=YYYY-MM-DD&region_id=...&metric=intensity|duration|cumulative|active`
  - returns a compact grid subset for the region bbox
  - MVP downsampling default: block-mean to 0.5° for duration/cumulative/active; block-max for intensity (preserves extremes)
  - Native 0.25° served if region bbox ≤ 20° × 20°; downsampled otherwise
- `GET /indices/ao?start=...&end=...`
- `GET /indices/pdo?start=...&end=...`
- `GET /events/{region_id}?start=...&end=...`
  - returns identified regional events (start/end, peak metrics) for Event Explorer

---

## 3) Implementation task breakdown for coding agents

### Milestone 0 — Guardrails (Day 0)
- [ ] Freeze scope: MHW-only; no fisheries PDFs, no biomass.
- [ ] Define regions polygons (GOA, EBS, NBS, Chukchi, Beaufort).
- [ ] Choose baseline: default 1991–2020.
- [ ] Decide: Streamlit vs React (Streamlit recommended for v1).

### Milestone 1 — Data fetchers (Day 1–2)
- [ ] Implement OISST fetch/subset reader (xarray) with caching.
- [ ] Implement AO fetch parser (daily CPC table).
- [ ] Implement PDO fetch parser (monthly PSL page/table).
- [ ] Optional: NSIDC ice fetch (daily files) + basic reader.

Deliverable: `src/mhw/fetch/*.py` and a small CLI to fetch “today”.

### Milestone 2 — Region masks + weights (Day 2–3)
- [ ] Build region masks aligned to OISST grid.
- [ ] Compute weights (`w_g = cos(lat)`) array.
- [ ] Store `weights.zarr` and `region_masks.zarr`.

Deliverable: `weights` + `masks` stored and reusable.

### Milestone 3 — Climatology + thresholds build (Day 3–5)
- [ ] Baseline data extraction (1991–2020) for required region bounding boxes (or full globe if feasible).
- [ ] Day-of-year binning and 11-day window smoothing.
- [ ] Compute `mu[d,:,:]` and `theta90[d,:,:]`.
- [ ] Store as Zarr (chunked by day).

Deliverable: `data/derived/climatology/{mu,theta90}.zarr`

### Milestone 4 — State update engine (Day 5–7)
Implement the daily update rules:

- [ ] Compute exceedance `x = max(0, sst - theta90[d])`
- [ ] Update `Dtilde` counter
- [ ] Update active flag `A` with ≥5-day confirmation
- [ ] Update `C` cumulative intensity
- [ ] Compute onset `O` during first 3 days of event (per definitions)
- [ ] Implement configurable gap-bridging (`gap_days` from climatology.yml; default=2, Hobday-faithful)
- [ ] Implement configurable intensity reference (`intensity_reference` from climatology.yml; threshold vs climatological_mean)
- [ ] Persist rolling states for next run (including gap counter G)

Deliverable: `src/mhw/states/update_states.py`

### Milestone 4b — Historical Backfill (Day 7–9)
Run the state engine in backfill mode over the full historical record:

- [ ] Execute `backfill_states(1982-01-01, latest_date)` using the state update engine from Milestone 4
- [ ] Verify sequential state propagation (Dtilde, A, C carry forward correctly)
- [ ] Output: populated `data/derived/states_grid/` and `data/derived/aggregates_region/region_daily.parquet`
- [ ] This must complete before Milestone 6 (risk percentile tables depend on the full historical distribution)

Deliverable: `region_daily.parquet` with ~15,000+ rows per region (1982–present).

> **Dependency note:** Milestone 6 (risk percentiles) and Page 2 (Historical View) both require completed backfill output. Do not proceed to Milestone 6 without verifying backfill integrity.

### Milestone 5 — Region aggregation & events (Day 9–10)
- [ ] Compute region aggregates:
  - area fraction
  - conditional intensity mean
  - conditional duration mean
  - conditional cumulative mean
  - conditional onset mean
- [ ] Identify region-level "events" (start/end based on area_frac > alpha, default alpha=0.05; configurable in climatology.yml)
- [ ] Store in `region_daily.parquet` and `region_events.parquet`

Deliverable: `src/mhw/states/aggregates.py`

### Milestone 6 — Risk score & triggers (Day 10–11)
- [ ] Build historical percentile reference tables:
  - percentiles of (`Ibar`, `Cbar`) computed over MHW-active days
  - percentiles of `Obar` computed over onset-active days only (`Obar > 0`) to avoid zero-inflated distribution
  - percentiles of area fraction over all days
- [ ] Compute daily risk:
  - `Risk = 0.4 p_C + 0.3 p_I + 0.2 p_A + 0.1 p_O`
- [ ] Optional trigger flag: threshold exceedance logic (HCR-friendly)

Deliverable: `src/mhw/states/risk.py`

### Milestone 7 — API service (Day 11–12)
- [ ] Implement FastAPI routes reading parquet/zarr
- [ ] Return compact JSON for series, events, indices
- [ ] Provide map endpoint returning downsampled arrays
  - Default: block-mean to 0.5° for area metrics; block-max for intensity to preserve extremes
  - Serve native 0.25° for small region bboxes (≤ 20° × 20°)

Deliverable: `src/api/*`

### Milestone 8 — Dashboard UI (Day 12–14)
Build the two-page UI.

**Page 1: Operational**
- Panel 1 map
- Panel 2 short-window time series
- Panel 3 AO/PDO context
- Panel 4 risk gauge + percentile rank + trigger

**Page 2: Historical**
- Panel 1 annual MHW days
- Panel 2 event explorer
- Panel 3 distribution + current percentile
- Panel 4 regime comparison (PDO/AO phase split)

Deliverable: `src/dashboard/*`

### Milestone 9 — Automation & QA (Day 14–16)
- [ ] One-command setup scripts
- [ ] Daily refresh job
- [ ] Sanity checks:
  - threshold continuity
  - event confirmation correctness
  - leap day handling
  - missing data robustness
- [ ] Minimal tests for state updates + aggregation

Deliverable: scripts + CI.

---

## 4) GitHub project roadmap (milestones + issues)

### Epics
1. **Data ingestion** (OISST + AO/PDO + optional NSIDC)
2. **Climatology + thresholds** (baseline build)
3. **MHW state engine** (daily updates)
4. **Aggregates + risk** (region-level + percentiles)
5. **API layer**
6. **Dashboard UI**
7. **Automation + tests**
8. **Demo story** (GOA 2014–16 event replay)

### Suggested Issues (copy/paste level)
- [ ] Implement OISST reader with bbox subsetting
- [ ] Compute and store region masks for OISST grid
- [ ] Build baseline mu/theta90 with 11-day DOY smoothing
- [ ] Implement daily state updates (A, Dtilde, C, O)
- [ ] Implement region aggregates and store parquet
- [ ] Implement percentile reference tables for risk
- [ ] Implement risk score + trigger badge
- [ ] FastAPI endpoints: regions/states/map/events/indices
- [ ] Streamlit page 1 operational layout
- [ ] Streamlit page 2 historical layout
- [ ] Add daily refresh script + logging
- [ ] Add tests: climatology integrity + state update correctness

---

## Extra: “stack choice” recommendation for fastest prototype
If your priority is **a working demo soon**:

- Pipeline: Python + xarray + Zarr + Parquet
- API: FastAPI (thin)
- UI: Streamlit (fastest)
- Deployment: one VM or container; add managed services later

You can productionize later without changing the science.
