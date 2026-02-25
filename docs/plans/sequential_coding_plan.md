# MHW State Dashboard — Sequential Coding Plan

## Context

All planning documents are finalized (15 revision items resolved, Hobday alignment verified). This plan lays out a **step-by-step coding sequence** where each step produces visible, verifiable output before the next begins. The user wants to see dashboard figures working before building a full API layer.

**Gap-bridging status:** Already formalized in `mhw_README.md` Section 6.2 (explicit gap counter G equations with LaTeX) and `config/climatology.yml` (`gap_days: 2` with Hobday reference notes). Code will read `gap_days` from config — no drift possible.

---

## Step 0: Project Setup & Dependencies ✅ Completed

**What:** Create `pyproject.toml`, directory structure, and install core dependencies.

**Files created:**
- `pyproject.toml` — split extras: core, `[geo]`, `[dashboard]`, `[api]`, `[dev]` (see actual file for full spec)
- `src/mhw/__init__.py`, `src/mhw/fetch/__init__.py`, `src/mhw/climatology/__init__.py`
- `src/mhw/states/__init__.py`, `src/mhw/regions/__init__.py`, `src/mhw/utils/__init__.py`

**Package manager:** uv (fast, handles venvs natively)

**Outcome:** `uv venv && uv pip install -e ".[geo,dev]"` succeeded. All core + geo + dev dependencies installed. Extras install incrementally: `[dashboard]` at Step 7, `[api]` at Step 10.

---

## Step 1: OISST Fetcher — Connect & Visualize One Day ✅ Completed

**Goal:** Fetch a single day of SST for the GOA bounding box from ERDDAP and display it as a map.

**Files created:**
- `src/mhw/fetch/oisst.py` — ERDDAP OPeNDAP fetcher with `main()` CLI entrypoint (271 lines)

**CLI:** `mhw-fetch-sst --region goa --date 2024-06-15 --plot [--backend plotly|cartopy]`

**What it does:**
1. Connect to NCEI ERDDAP via OPeNDAP, fetch SST for GOA bbox
2. Handle 0–360 → −180–180 longitude conversion
3. Save as NetCDF in `data/raw/`
4. With `--plot`: Plotly interactive heatmap (default) or Cartopy projected map (`--backend cartopy`)

**Outcome:** Plotly HTML map + NetCDF saved. Data shape matches 0.25° grid. Lat/lon/SST ranges printed to console.

---

## Step 2: AO & PDO Fetchers — Conditioning Indices ✅ Completed

**Goal:** Fetch AO (daily) and PDO (monthly) indices and plot recent time series.

**Files created:**
- `src/mhw/fetch/indices.py` — AO (CPC FTP CSV) and PDO (PSL CSV) fetchers with `main()` CLI entrypoint (271 lines)

**CLI:** `mhw-fetch-indices --ao-years 2 --pdo-years 5 --plot`

**What it does:**
1. Fetch AO daily values from CPC FTP CSV (configurable years of history)
2. Fetch PDO monthly values from PSL CSV (handles −9999 missing sentinel)
3. Save as parquet in `data/raw/` (`ao_daily.parquet`, `pdo_monthly.parquet`)
4. With `--plot`: Plotly interactive line (AO daily) + step (PDO monthly) plots, saved as HTML + PNG

**Outcome:** AO and PDO parquet files saved. Interactive HTML plot with two-panel subplot (AO daily line + PDO monthly step). PNG export via kaleido (added to `[geo]` extras). Dates confirmed current.

**⚠️ Index coverage note:** Step 2 was initially run with `--ao-years 2 --pdo-years 5`, producing only ~1–5 years of index data. The Step 8 backfill covers 1982–2024 (43 years). For regime-conditioned analysis (AO±/PDO± box plots, predictability panel) to be meaningful across the full record, **re-run Step 2 with full coverage before Step 9:**
```
mhw-fetch-indices --ao-years 43 --pdo-years 43 --plot
```
This ensures `ao_daily.parquet` and `pdo_monthly.parquet` span 1982–present, matching the backfill period. Without this, regime analysis will be limited to the most recent years only.

---

## Step 3: Region Masks & Weights ✅ Completed

**Goal:** Rasterize the 5 region polygons onto the OISST grid and compute cos(lat) weights.

**Files created:**
- `src/mhw/regions/masks.py` — rasterize GeoJSON polygons to grid, with `main()` CLI (276 lines)
- `src/mhw/regions/weights.py` — compute cos(lat) weight array (34 lines)

**CLI:** `mhw-build-masks --plot`

**What it does:**
1. Load `config/regions.geojson`
2. Create a lat/lon grid matching OISST (0.25°)
3. Rasterize each polygon → binary mask per region (shapely `contains_xy`)
4. Compute `weights[lat, lon] = cos(lat_rad)`
5. Store masks and weights as Zarr in `data/derived/masks/` and `data/derived/weights/`
6. With `--plot`: 6-panel Plotly figure (5 region masks + cos(lat) weight field)

**Outcome:** Masks and weights Zarr stores saved. All 5 regions rasterized. Weight range for Alaska latitudes ~0.24–0.64.

---

## Step 4: Climatology Build (GOA First) ✅ Completed

**Goal:** Build mu[d,lat,lon] and theta90[d,lat,lon] for GOA only, using 1991–2020 baseline.

**Files created:**
- `src/mhw/climatology/build_mu_theta.py` — baseline extraction + 11-day window stats, with `main()` CLI (276+ lines)
- `src/mhw/climatology/smooth_doy.py` — DOY binning and window logic
- `src/mhw/climatology/storage.py` — Zarr read/write
- `notebooks/step4_climatology_explore.ipynb` — notebook checkpoint

**CLI:** `mhw-build-climatology --region goa --plot`

**What it does:**
1. Fetch **1982–present** daily SST **and ice concentration** for the region bbox from ERDDAP/OPeNDAP (chunked by year). Only 1991–2020 is used for climatology, but all years are cached as NetCDF in `data/raw/` so Steps 5 and 8 have zero additional ERDDAP calls.
2. Read `apply_ice_mask` and `ice_threshold_percent` from `config/climatology.yml`
3. If ice masking is enabled, for each daily field set SST to NaN where ice > threshold (15%). This excludes ice-covered samples from all subsequent statistics.
4. For each DOY d ∈ {1..366}, collect SST in [d-5, d+5] across baseline years
5. Compute mu (mean) and theta90 (90th percentile) per grid cell per DOY, using `np.nanmean` / `np.nanpercentile` to skip NaN'd ice cells
6. Store as Zarr: `data/derived/climatology/{mu,theta90}.zarr`
7. With `--plot`: maps for DOY 1, 90, 180, 270 + single-cell annual cycle

**Verify:** theta90 > mu everywhere. Smooth seasonal cycle. Summer theta90 a few °C above winter.

**Outcome:** mu and theta90 Zarr arrays built from 30 years of PFEG CoastWatch ERDDAP data (`ncdcOisst21Agg`). Year-level NetCDF caching in `data/raw/`. Ice masking applied (cells with ice > 15% NaN'd). Cartopy DOY snapshot maps and Plotly annual cycle plots generated. Notebook checkpoint verified.

**Note:** Longest computational step. GOA-only first; expand to all regions later.

**Ice masking note:** The OISST `ice` variable is on the same 0.25° grid as SST. The fetcher already supports `variables=("sst", "ice")`. Cells where ice > 15% (from `config/climatology.yml`) are NaN'd before computing DOY statistics. This prevents artificial SST signals in seasonally ice-covered cells from contaminating mu and theta90. The threshold and enable flag are config-driven — set `apply_ice_mask: false` to revert to ice-unaware climatology.

**📓 Notebook checkpoint (before proceeding to Step 5):**
Create and run `notebooks/step4_climatology_explore.ipynb`:
- Load mu and theta90 Zarr arrays
- Plot annual cycles for 3–4 selected grid cells (coastal, offshore, near-ice)
- Compare coastal vs offshore seasonal patterns
- Confirm theta90 > mu everywhere visually
- **Ice QA:** For a near-ice cell, confirm that winter DOYs show NaN (masked by ice) while summer DOYs have valid SST-derived values

---

## Step 5: State Engine — Compute MHW States for a Test Period ✅ Completed

**Goal:** Run the state update engine (README Section 6) on a test period (e.g., 2023) for GOA.

**Files created:**
- `src/mhw/states/update_states.py` — daily state logic (x, G, Dtilde, A, D, I, C, O) with `main()` and `backfill_main()` CLI entrypoints
- `notebooks/step5_state_engine_explore.ipynb` — notebook checkpoint

**CLI:** `mhw-run-states --region goa --start 2023-01-01 --end 2023-12-31 --plot`

**What it does:**
1. Load SST **and ice concentration** for GOA, 2023
2. Load precomputed theta90 and mu
3. Read `gap_days`, `intensity_reference`, `onset_reference`, `apply_ice_mask`, and `ice_threshold_percent` from `config/climatology.yml`
4. If ice masking is enabled, set A=0 (inactive) for cells where ice > threshold on that day. These cells cannot be in MHW state regardless of SST.
5. For each day: exceedance x → gap counter G → Dtilde → A → D, I, C, O (ice-masked cells skipped)
6. Store daily state arrays in `data/derived/states_grid/`

**Config note:** `onset_reference` defaults to `"physical_start"` (onset rate computed retroactively from exceedance start). Alternative: `"at_confirmation"` (forward-only from day D=5). See README Section 6.4.

**Ice masking note:** Consistency between baseline (Step 4) and detection (Step 5) is required — both use the same `ice_threshold_percent` from config. If a cell was NaN'd during climatology for a given DOY, it should also be masked during detection when ice exceeds the same threshold. This prevents false MHW triggers from SST artifacts near ice edges.

**Visualizations (--plot):**
- Map of A (active flag) for a date with known MHW activity
- Map of I (intensity) for same date
- Time series of spatially-averaged active fraction over the year
- Single grid cell: SST, theta90, A flag shaded

**Verify:**
- Events require ≥5 consecutive exceedance days
- Gap-bridging: ≤2 sub-threshold days don't break events (gap_days=2 from config)
- I=0 when SST ≤ theta90; D resets when A drops to 0
- Ice-covered cells never show A=1 (active MHW)

**Outcome:** State engine runs on GOA 2023. Peak active day 2023-08-07 (~22% area fraction). A map, I map (0–3.5°C), active fraction time series, and single-cell time series all verified. Notebook checkpoint completed.

**📓 Notebook checkpoint (before proceeding to Step 6):**
Create and run `notebooks/step5_state_engine_explore.ipynb`:
- Overlay SST + theta90 + A flag shading for a single cell over the test year
- Animate daily state maps for a month with known MHW activity
- Validate gap-bridging: construct a synthetic 3-day gap sequence and confirm G counter behavior
- **Ice QA:** Confirm that cells with ice > 15% are never marked active. Check a Chukchi/Beaufort-adjacent cell in winter.

---

## Step 6: Regional Aggregation — Produce region_daily Table ✅ Completed

**Goal:** Aggregate grid-level states to region-level daily metrics.

**Files created:**
- `src/mhw/states/aggregates.py` — weighted regional aggregation with `main()` CLI
- `notebooks/step6_aggregates_explore.ipynb` — notebook checkpoint

**CLI:** `mhw-aggregate --region goa --start 2023-01-01 --end 2023-12-31 --plot`

**What it does:**
1. Apply cos(lat) weights and region masks
2. Compute daily: area_frac, Ibar, Dbar, Cbar, Obar (conditional on A=1, zero when no active cells)
3. Store as `data/derived/aggregates_region/region_daily.parquet`
4. With `--plot`: time series of all 5 metrics for GOA

**Verify:** area_frac ∈ [0,1]. Ibar/Dbar/Cbar/Obar are zero when area_frac=0. Physically reasonable values.

**Outcome:** 365 rows for GOA 2023. Peak 2023-08-08 at 22.6% area fraction, Ibar up to 2.2°C, Dbar up to 32 days. All conditional means exactly zero on 116 inactive days. Scatterplot shows inverse Ibar/area_frac pattern (wide events are mild, intense events are localized). Notebook checkpoint verified.

**📓 Notebook checkpoint (before proceeding to Step 7):**
Create and run `notebooks/step6_aggregates_explore.ipynb`:
- Plot region_daily time series with event shading (area_frac > 0.05)
- Scatter plot of Ibar vs Dbar colored by area_frac
- Confirm conditional means are zero when area_frac = 0

---

## Step 7: Dashboard Panel Prototypes (One at a Time) ✅ Completed

**Goal:** Build each panel as a standalone Streamlit page. Install dashboard extra: `uv pip install -e ".[dashboard]"`

### Step 7a: Panel 1 — Live MHW Map
- `src/dashboard/components/map_mhw.py`
- Plotly/Cartopy map of intensity or active flag; region/date/metric selectors
- **Run:** `streamlit run src/dashboard/components/map_mhw.py`

### Step 7b: Panel 2 — Event Characterization Time Series
- `src/dashboard/components/ts_event_metrics.py`
- Multi-line time series of area_frac, Ibar, Dbar, Cbar, Obar (last 60–90 days)
- **Run:** `streamlit run src/dashboard/components/ts_event_metrics.py`

### Step 7c: Panel 3 — Predictability Context (AO/PDO)
- `src/dashboard/components/predictability_panel.py`
- AO daily + PDO monthly alongside event metrics window
- **Run:** `streamlit run src/dashboard/components/predictability_panel.py`

### Step 7d: Panel 4 — Risk Gauge
- `src/mhw/states/risk.py` — percentile tables + risk score (CLI: `mhw-compute-risk`)
- `src/dashboard/components/risk_gauge.py` — Green/Yellow/Red gauge
- **Note:** Percentile reference mode is configurable via `config/climatology.yml` (`risk_percentiles.mode`): `"frozen"` (default — built once after backfill, stable) or `"incremental"` (grows daily). Uses test-year distribution as proxy until full backfill.
- **Run:** `streamlit run src/dashboard/components/risk_gauge.py`

### Step 7e: Page 2 Panels (after backfill)
- Annual MHW burden bar chart
- Event Explorer dropdown + stats
- Distribution + percentile histogram
- Regime comparison box plots

**Verify (each sub-step):** `streamlit run ...` → see panel in browser, interact with controls.

**Outcome:** All 4 panels (7a–7d) built as standalone Streamlit pages. Risk module (`src/mhw/states/risk.py`) computes percentile ranks with composite weighting (area_frac 40%, Ibar 25%, Dbar 25%, Cbar 10%). Peak 2023-08-07 composite_risk=93.6 (High). All panels use cached data loading, Plotly visualizations, and dynamic path resolution. Minor: AREA_THRESH (0.05) hardcoded in 2 dashboard files instead of reading from config — matches config value, cosmetic fix deferred.

---

## Step 8: Historical Backfill (Full 1982–Present) ✅ Completed

**Goal:** Populate region_daily.parquet with ~15,000+ rows per region.

**CLI:** `mhw-backfill --start 1982-01-01 --end latest`

**What it does:**
1. Iterate year-by-year from 1982 to present
2. Fetch SST, run state engine, aggregate, append to parquet
3. Build percentile reference tables from completed backfill
4. Default mode is `"frozen"` — percentile tables are built once from the complete backfill and remain stable. See README Section 8.2 and `config/climatology.yml` `risk_percentiles` block.

**Verify:** Row counts ~15,000+ per region. GOA 2014–2016 shows elevated area_frac and Cbar ("blob" event).

**Outcome:** 15,706 rows (1982–2024), all 43 years complete (365/366 rows each). Blob peak 2016-10-28: composite risk 98.7. 2016 had MHW active every day (366/366). Blob vs baseline: area_frac 9×, Cbar 5.3×. Risk distribution: 5,770 Normal / 4,487 Elevated / 5,449 High Risk days. Backfill added `--skip-zarr` and `--skip-risk` flags. Regime box plots limited by AO/PDO index coverage (only ~1 year from Step 2) — extend indices to full record as follow-up.

**📓 Notebook checkpoint (before proceeding to Step 9):**
Create and run `notebooks/step8_backfill_qa.ipynb`:
- Row count summary per region per year (expect ~365 rows/yr)
- GOA 2014–2016 "blob" event: confirm elevated area_frac and Cbar
- Percentile distribution histograms for each metric
- Regime-conditioned box plots (AO+/AO− × PDO+/PDO−)

---

## Step 9: Full Dashboard Assembly ✅ Completed

**Prerequisite:** Re-run `mhw-fetch-indices --ao-years 43 --pdo-years 43 --plot` to extend AO/PDO parquet files to 1982–present. This is needed for the historical page's regime analysis panels.

**Files:**
- `src/dashboard/app.py` — Streamlit multipage entry (43 lines)
- `src/dashboard/pages/1_operational.py` — Page 1: 4-tab operational dashboard (Map, Event Metrics, Predictability, Risk Gauge) — 386 lines
- `src/dashboard/pages/2_historical.py` — Page 2: 4-tab historical dashboard (Annual Burden, Event Explorer, Distributions, Regime Analysis) — 514 lines

**Verify:** `streamlit run src/dashboard/app.py` → both pages work, all panels render, region selector controls all. Regime box plots on Page 2 show all four regimes (AO+/PDO+, AO+/PDO−, AO−/PDO+, AO−/PDO−).

**Outcome:** All 8 dashboard panels implemented across 2 pages. Page 1 imports from component files (code reuse); Page 2 defines self-contained loaders with `@st.cache_data` (Streamlit multipage best practice). AO/PDO indices extended to 1982–present (AO: 15,703 rows from 1983-02-22; PDO: 510 months from 1983-03-01). All 4 climate regimes represented in regime box plots. Blob annotation, year-range slider, risk score distributions all working. Minor: `AREA_THRESH` hardcoded (0.05) in 2 files, unused `subprocess` import in Page 1, dead `df_f` variable in Page 2 — cosmetic, deferred.

---

## Step 10: API Layer (FastAPI) ✅ Completed

Install: `uv pip install -e ".[api]"`

**Files:** `src/api/{__init__,main,routes_states,routes_maps,routes_indices,schema}.py` (538 lines total)

**Endpoints (7 total):**
- `GET /health` — liveness check
- `GET /regions` — list available regions with date coverage
- `GET /states/region/{region_id}` — daily aggregates with date range params
- `GET /events/{region_id}` — event detection from aggregates (min_duration param)
- `GET /map/mhw` — per-cell metric values for region/date/metric (GeoJSON grid)
- `GET /indices/ao` — AO daily with date range
- `GET /indices/pdo` — PDO monthly with date range

**Outcome:** All 7 endpoints return valid JSON. Proper HTTP semantics (404/503/422). GET-only CORS. Pydantic response models (9 schemas). Swagger UI at `/docs`. In-memory zarr caching for map endpoint. Event detection uses gap-bridging consistent with Hobday et al. `RiskPayload` schema defined but endpoint not yet wired (forward-looking).

**Verify:** `uvicorn src.api.main:app --reload` → curl all endpoints, confirm JSON.

---

## Step 10.5: Pre-Expansion Bug Fixes & Code Cleanup ✅ Completed

**Context:** Before running the multi-region expansion, fix all known bugs and code quality issues identified during dashboard and API reviews. These must be resolved first because Fix 1 (climatology overwrite) is a **data-loss bug** that would destroy GOA's climatology when building the next region.

### Fix 1 — CRITICAL: Make climatology storage region-aware

The current code stores mu.zarr and theta90.zarr at **hardcoded paths** with no region ID in the filename. Running `mhw-build-climatology --region ebs` will **overwrite** the existing GOA climatology.

**Files:**
- `src/mhw/climatology/build_mu_theta.py` line 464 — output paths have no region suffix
- `src/mhw/states/update_states.py` lines 58–81 — `_load_climatology(cfg)` takes no region parameter; caller at line 234

**Fix:**
1. In `build_mu_theta.py` (line 464), interpolate `args.region` into the path: replace `.zarr` with `_{region}.zarr` → produces `mu_goa.zarr`, `theta90_ebs.zarr`, etc.
2. In `update_states.py`, add `region_id: str` parameter to `_load_climatology()`, apply same path interpolation inside (lines 70–74), update caller at line 234 to pass `region_id`.
3. Rename existing GOA files: `mu.zarr` → `mu_goa.zarr`, `theta90.zarr` → `theta90_goa.zarr`
4. Do NOT modify `config/climatology.yml` paths — code appends suffix programmatically.

### Fix 2 — Read AREA_THRESH from config instead of hardcoding

`AREA_THRESH = 0.05` is hardcoded in 4 files. Config key: `regional_events.area_frac_threshold` in `config/climatology.yml` line 102.

**Files to fix:**
- `src/dashboard/components/ts_event_metrics.py` line 25
- `src/dashboard/components/predictability_panel.py` line 26
- `src/dashboard/pages/2_historical.py` line 26
- `src/api/routes_states.py` line 17

**Fix:** In each file, load from config via `yaml.safe_load()` at module level.

### Fix 3 — Read GAP_DAYS from config in API

`GAP_DAYS = 2` hardcoded in `src/api/routes_states.py` line 18. Config key: `mhw_definition.gap_days` (line 67).

**Fix:** Load from config alongside AREA_THRESH.

### Fix 4 — Remove unused `subprocess` import

`src/dashboard/pages/1_operational.py` line 14: `import subprocess` — unused. Delete.

### Fix 5 — Remove dead `df_f` variable

`src/dashboard/pages/2_historical.py`:
- Line 143: `df_f = None` — never assigned a real value
- Lines 221–224 and 308–311: `if df_f is None` always True

**Fix:** Delete line 143. Replace `if/else` blocks with just `df_full = _load_agg(region)`.

### Fix 6 — Add TTL to all `@st.cache_data` decorators

All 20 `@st.cache_data` decorators across 5 files lack `ttl=`. Daily refresh data won't appear until dashboard restart.

**Files (20 decorators total):**
- `src/dashboard/components/map_mhw.py` — lines 41, 54, 83, 99
- `src/dashboard/components/ts_event_metrics.py` — lines 38, 48
- `src/dashboard/components/predictability_panel.py` — lines 31, 41, 51, 61
- `src/dashboard/components/risk_gauge.py` — lines 44, 54, 64
- `src/dashboard/pages/2_historical.py` — lines 39, 50, 60, 71, 77, 93

**Fix:** Add `ttl=3600` to each decorator.

### Fix 7 — Expand `.gitignore`

Current `.gitignore` only has `*.egg-info/`. Add: `data/raw/`, `data/derived/`, `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `outputs/`, `.vscode/`, `.idea/`

### Verify after all fixes:
1. `mhw-run-states --region goa --start 2023-12-01 --end 2023-12-31` — succeeds with renamed `mu_goa.zarr`
2. `streamlit run src/dashboard/app.py` — no import errors, GOA panels render
3. `uvicorn src.api.main:app --reload` + `curl /health` + `curl /regions` — valid JSON
4. `ruff check src/` — no lint issues

---

## Step 11: Multi-Region Expansion (EBS, NBS, Chukchi, Beaufort) ✅ Completed

**Context:** Steps 0–10 are complete for **GOA only**. Step 10.5 bug fixes applied. The climatology (mu/θ90) covers only GOA's bounding box (lat 54–62, lon -170 to -130, shape 32×160). Each region needs its own SST fetch, climatology, states, aggregates, and risk. Only masks and weights are truly global (720×1440 grid covering all 5 regions).

**Current multi-region data status:**

| Component | GOA | EBS | NBS | Chukchi | Beaufort |
|-----------|:---:|:---:|:---:|:-------:|:--------:|
| Masks (global 720×1440) | ✅ 5,120 cells | ✅ 2,560 | ✅ 1,600 | ✅ 2,400 | ✅ 1,600 |
| Weights (global cos(lat)) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Raw SST+ice (1982–2024) | ✅ 43 yr | ❌ | ❌ | ❌ | ❌ |
| Climatology (mu/θ90) | ✅ 32×160 | ❌ | ❌ | ❌ | ❌ |
| States grid (1982–2024) | ✅ 43 zarrs | ❌ | ❌ | ❌ | ❌ |
| Aggregates parquet | ✅ 15,706 rows | ❌ | ❌ | ❌ | ❌ |
| Risk scores | ✅ | ❌ | ❌ | ❌ | ❌ |

**Region bounding boxes (from `config/regions.geojson`):**
- GOA: lat [54, 62], lon [-170, -130] — 32×160 cells
- EBS: lat [54, 62], lon [-180, -160] — 32×80 cells
- NBS: lat [62, 67], lon [-180, -160] — 20×80 cells
- Chukchi: lat [67, 73], lon [-180, -155] — 24×100 cells
- Beaufort: lat [69, 73], lon [-155, -130] — 16×100 cells

**For each remaining region (EBS, NBS, Chukchi, Beaufort), run in order:**

```bash
# Step 4: Fetch 1982–present SST+ice, build mu/θ90
mhw-build-climatology --region $REGION --plot

# Step 5: Test year (quick sanity check)
mhw-run-states --region $REGION --start 2023-01-01 --end 2023-12-31 --plot

# Step 6: Test aggregate
mhw-aggregate --region $REGION --start 2023-01-01 --end 2023-12-31 --plot

# Step 8: Full 1982–present backfill (uses cached SST from Step 4)
mhw-backfill --region $REGION --start 1982-01-01 --end latest

# Risk scores
mhw-compute-risk --region $REGION
```

**Per updated Step 4 spec:** `mhw-build-climatology` fetches **1982–present** (not just baseline), caching all years as NetCDF. `mhw-backfill` uses cached data with zero additional ERDDAP calls.

**Estimated time:** ~2–4 hours per region (dominated by ERDDAP fetch of 43 years of SST). Total: ~8–16 hours for 4 regions.

**Ice masking note for high-latitude regions:** Chukchi (67–73°N) and Beaufort (69–73°N) have heavy seasonal ice cover. Expected behavior:
- Winter months: most cells NaN'd by ice mask → area_frac ≈ 0
- Summer months (Jul–Sep): MHW activity in ice-free cells only
- Fewer "event days" than GOA — this is physically correct, not a bug
- The 15% ice threshold from config applies consistently

**Verify after each region:**
- Parquet exists: `data/derived/aggregates_region/region_daily_{region}.parquet`
- Risk exists: `data/derived/risk/risk_{region}.parquet`
- Row count ≈ 15,706 (matching GOA: 43 years × 365/366 days)
- Dashboard region selector shows the new region
- Chukchi/Beaufort: confirm winter area_frac ≈ 0, summer events present

**Outcome:** All 5 regions operational. 15,706 rows each (1982–2024). Climatology shapes match region bounding boxes (GOA 32×160, EBS 32×80, NBS 20×80, Chukchi 24×100, Beaufort 16×100). θ90 > mu ≥ 94.7% everywhere. Ice masking verified: Chukchi/Beaufort winter area_frac ≈ 0.001. Peak area_frac: EBS 0.886 (strongest), GOA 0.609. All source modules (climatology, states, aggregates, risk, dashboard, API) confirmed multi-region aware with dynamic region discovery. One transient ERDDAP 503 during Beaufort fetch — retried successfully. Total processing: ~5h 17m.

---

## Step 12a: Tests ✅ Completed

**Files created:**

1. **`tests/conftest.py`** — Shared fixtures: sample parquet DataFrames, temp zarr stores, region config loader
2. **`tests/test_states.py`** — Unit tests for `src/mhw/states/update_states.py`:
   - Exceedance detection (SST > θ90 → x=1)
   - 5-day onset rule (D increments only after 5 consecutive exceedance days)
   - Gap bridging (≤ gap_days sub-threshold days don't break events, > gap_days does)
   - Ice masking (cells with ice > threshold forced inactive)
   - Intensity = SST − μ when active, 0 when inactive
3. **`tests/test_aggregates.py`** — Unit tests for `src/mhw/states/aggregates.py`:
   - Parquet schema matches expected columns (date, area_frac, Ibar, Dbar, Cbar, Obar)
   - area_frac ∈ [0, 1]
   - Conditional means are zero when area_frac = 0 (no active cells → Ibar/Dbar/Cbar/Obar = 0)
   - cos(lat) weighting produces different area_frac than uniform weighting
4. **`tests/test_api.py`** — FastAPI endpoint smoke tests using `TestClient`:
   - `GET /health` → 200, `{"status": "ok"}`
   - `GET /regions` → 200, list of 5 regions
   - `GET /states/region/goa` → 200, valid JSON with date/area_frac fields
   - `GET /states/region/nonexistent` → 404
   - `GET /events/goa` → 200, events list
   - `GET /map/mhw?region_id=goa` → 200, GeoJSON-like response
   - `GET /indices/ao` → 200, AO records
   - `GET /indices/pdo` → 200, PDO records
5. **`tests/test_risk.py`** — Unit tests for `src/mhw/states/risk.py`:
   - Composite risk ∈ [0, 100]
   - Risk level categories: Normal / Elevated / High Risk at correct thresholds
   - Zero-activity days → composite_risk near 0

**Verify:** `pytest tests/ -v` — all tests pass.

**Outcome:** 5 test files (conftest.py, test_states.py, test_aggregates.py, test_api.py, test_risk.py), 43 tests passing. Unit tests use synthetic numpy grids (no network). Integration tests use on-disk GOA parquet. API tests use FastAPI TestClient.

---

## Step 12b: Automation & Deployment Prep ✅ Completed

**Architecture:** Traefik v3 reverse proxy with Docker Compose per project. Chosen over nginx because:
- Auto SSL via built-in Let's Encrypt ACME — no certbot, no cron, no manual renewal
- Auto container discovery via Docker labels — no config files to edit per subdomain
- Adding a future project (e.g., `chatbot.iastate.ai`) = write docker-compose.yml with labels → `docker compose up -d` → done
- Native WebSocket support for Streamlit (no special config needed)

**API URL:** `mhw.iastate.ai/api/*` (path-based routing with StripPrefix middleware — no code changes to FastAPI)

**Files to create:**

1. **`Dockerfile`** — `python:3.12-slim-bookworm`, system deps (`libgeos-dev`, `libproj-dev`, `proj-data`, `libhdf5-dev`, `libnetcdf-dev`, `curl`), `pip install -e ".[geo,dashboard,api]"`. Single image for all 3 services.

2. **`docker-compose.yml`** — Three services from the same Dockerfile + Traefik:
   - `traefik`: Traefik v3.2 reverse proxy, ports 80+443, mounts `infra/traefik/` configs + Docker socket + `letsencrypt` named volume.
   - `dashboard`: `streamlit run src/dashboard/app.py --server.port=8501 --server.address=0.0.0.0`. Traefik labels for `Host(mhw.iastate.ai) && !PathPrefix(/api)`. Read-only data mount. Healthcheck on `/_stcore/health`. Sticky sessions for WebSocket.
   - `api`: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2`. Traefik labels for `Host(mhw.iastate.ai) && PathPrefix(/api)` + StripPrefix. Read-write data mount (so daily refresh can write via `docker compose exec`). Healthcheck on `/health`.
   - Network: `mhw_net` with explicit `name: mhw_net` (avoids Docker Compose project-name prefix)
   - Named volume: `letsencrypt` for ACME cert storage
   - No separate cron service — daily refresh runs via `docker compose exec -T api` from host crontab

3. **`.streamlit/config.toml`** — `server.headless = true`, `browser.gatherUsageStats = false`, ocean-themed colors

4. **`scripts/daily_refresh.sh`** — Cron-ready script:
   - Runs from the host via `bash scripts/daily_refresh.sh`, delegates to `docker compose exec -T api` for all Python commands
   - For each region (goa, ebs, nbs, chukchi, beaufort): `mhw-run-states` (Jan 1 → today) → `mhw-aggregate` → `mhw-compute-risk`
   - State engine's `fetch_year()` auto-refreshes stale current-year SST cache (Fix 2 from 12b)
   - Restarts dashboard container at end to clear `@st.cache_data`
   - `set -euo pipefail`, logs to `outputs/cron.log`

5. **`infra/traefik/traefik.yml`** + **`infra/traefik/dynamic.yml`** — Traefik static + dynamic config:
   - Let's Encrypt ACME (HTTP-01 challenge), auto HTTP→HTTPS redirect
   - Docker provider with `exposedByDefault: false`, network `mhw_net`
   - Dynamic config: security headers, rate limiting
   - Traefik runs as a service inside the project's `docker-compose.yml` (not a separate stack)

6. **`.github/workflows/ci.yml`** — Push to main → checkout → setup Python 3.12 → install deps → `pytest tests/ -v`

**Verify:**
1. `docker compose build` — image builds without errors
2. `docker compose up -d` — dashboard at `localhost:8501`, API at `localhost:8000`
3. `curl localhost:8000/health` → `{"status":"ok"}`
4. `scripts/daily_refresh.sh` runs without error
5. All 5 regions visible in dashboard
6. `pytest tests/ -v` still passes (43 tests)

**Outcome:** All deployment files created. Two critical post-implementation fixes applied:
- **Fix 1 — Network name mismatch:** Added `name: mhw_net` to docker-compose.yml network definition. Without it, Docker Compose prefixes the project name (`climate_iastate_mhw_net`), breaking Traefik's `provider.network: mhw_net` routing.
- **Fix 2 — Stale SST cache:** Updated `fetch_year()` in `build_mu_theta.py` to auto-refresh current-year NetCDF cache when last day is > 2 days old. Past years return cached file unchanged. This means `daily_refresh.sh` → `mhw-run-states` → `fetch_year()` self-heals without needing `--no-cache` flags.

---

## Step 13: Deploy to mhw.iastate.ai

**Hosting:** AWS Lightsail, 4 GB / 2 vCPU / 80 GB SSD, US East (Ohio), ~$20/mo
**Domain:** iastate.ai registered at Namecheap
**Reverse proxy:** Traefik v3 (from Step 12b) — auto SSL, auto container discovery. Shared across all iastate.ai projects.

### Pre-deploy checklist ✅ Done:

1. ~~**Update Traefik ACME email**~~ — Set to `rsingh@iastate.edu` in `infra/traefik/traefik.yml`
2. ~~**Refresh AO/PDO indices**~~ — AO: 15,703 rows (1983–2026-02-21), PDO: 510 months (1983–2025-08)
3. **Cron PATH** — `daily_refresh.sh` calls `docker compose` without absolute path. Fix by adding `export PATH="/usr/bin:/usr/local/bin:$PATH"` at the top of the script, or setting PATH in the crontab before the job entry.

### Part 1: Provision the AWS Lightsail VM

1. Go to https://lightsail.aws.amazon.com
2. Click **Create instance**
3. Settings:
   - Region: **US East (Ohio)** (closest to Iowa)
   - Platform: **Linux/Unix**
   - Blueprint: **OS Only → Ubuntu 22.04 LTS**
   - Plan: **$20/mo** (4 GB RAM, 2 vCPU, 80 GB SSD, 4 TB transfer)
   - Instance name: `iastate-ai` (this will host all future projects too)
4. Click **Create instance**, wait ~60 seconds
5. Go to **Networking** tab → note the **Public IP**
6. **Attach a static IP** (free while attached to a running instance):
   - Networking tab → Create static IP → attach to `iastate-ai`
   - This ensures the IP doesn't change on reboot
7. **Open firewall ports:**
   - Networking tab → IPv4 Firewall
   - Add rule: **HTTPS (443)**
   - HTTP (80) and SSH (22) should already be open by default

### Part 2: Point mhw.iastate.ai to the VM (Namecheap DNS)

1. Log in to https://namecheap.com → **Domain List** → click **Manage** next to `iastate.ai`
2. Go to **Advanced DNS** tab
3. Add a new **A Record**:
   - Host: `mhw`
   - Value: your Lightsail static IP (e.g., `3.15.xxx.xxx`)
   - TTL: Automatic
4. Click the green checkmark to save
5. DNS propagation takes 5–30 minutes. Test with:
   ```
   dig mhw.iastate.ai
   ```
   Should return your Lightsail IP.

**For future projects:** Just add another A record (e.g., Host: `chatbot`, same IP).

### Part 3: Set Up the VM

SSH into the VM from Lightsail console (click the terminal icon) or:
```bash
ssh -i ~/.ssh/your-lightsail-key.pem ubuntu@YOUR_STATIC_IP
```

#### 3a. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (official method)
curl -fsSL https://get.docker.com | sudo sh

# Add your user to docker group (avoids sudo for docker commands)
sudo usermod -aG docker ubuntu

# Log out and back in for group change to take effect
exit
# SSH back in

# Verify
docker --version
docker compose version
```

#### 3b. Create project directory structure

```bash
sudo mkdir -p /opt/iastate-ai/projects
sudo chown -R ubuntu:ubuntu /opt/iastate-ai
```

#### 3c. Traefik setup

Traefik is a service inside the project's `docker-compose.yml` — there is no separate Traefik stack. The Traefik config files (`infra/traefik/traefik.yml` and `infra/traefik/dynamic.yml`) are included in the git repo and will be deployed with the project in step 3d. SSL certificates are stored in a Docker named volume (`letsencrypt`), created automatically by `docker compose up`.

#### 3d. Deploy the MHW project

**Prerequisites:** The GitHub repo must be set up first (see Step 13.5 below). Complete Step 13.5 before this step.

```bash
# On the VM:
cd /opt/iastate-ai/projects

# Clone the repo (public, no auth needed)
git clone https://github.com/YOUR_USERNAME/climate_iastate.git mhw
cd mhw

# Sync data from your local machine (data is gitignored — must rsync separately).
# On your LOCAL machine, run:
rsync -avz --progress \
  -e "ssh -i ~/.ssh/your-lightsail-key.pem" \
  /Users/rajpython/dev/climate_iastate/data/ \
  ubuntu@YOUR_STATIC_IP:/opt/iastate-ai/projects/mhw/data/

# This syncs ~1.76 GB of data. Will take a few minutes.
# Verify data/raw/ exists on the VM (to avoid ERDDAP re-fetch):
ls data/raw/  # should show NetCDF files for all 5 regions

# Back on the VM — build and start all containers (Traefik + dashboard + API)
docker compose up -d --build

# This will take 5-10 minutes on first build (installs all Python deps)

# Check containers are running
docker ps
# Should show 3 containers: traefik, dashboard (mhw-*-dashboard-1), api (mhw-*-api-1)
```

#### 3e. Verify it works

```bash
# On the VM — check API
curl http://localhost:8000/health
# Should return: {"status":"ok","version":"0.1.0"}

# Check from outside (after DNS propagates):
curl https://mhw.iastate.ai/api/health

# Open in browser:
# https://mhw.iastate.ai       → Streamlit dashboard
# https://mhw.iastate.ai/api/docs → Swagger UI
```

#### 3f. Set up daily refresh cron

```bash
# On the VM:
crontab -e

# Add these lines (PATH ensures docker/docker compose resolve from cron):
PATH=/usr/local/bin:/usr/bin:/bin
0 14 * * * cd /opt/iastate-ai/projects/mhw && bash scripts/daily_refresh.sh >> outputs/cron.log 2>&1
```

Note: `daily_refresh.sh` uses `docker compose exec -T api` internally to run Python commands inside the running `api` container. The `PATH=` line in crontab ensures `docker` and `docker compose` resolve correctly (cron has minimal PATH by default).

#### 3g. Set up monitoring (optional but recommended)

1. Go to https://uptimerobot.com (free tier)
2. Add new monitor:
   - Type: HTTP(s)
   - URL: `https://mhw.iastate.ai/api/health`
   - Interval: 5 minutes
   - Alert: your email

### Part 4: Verification Checklist

- [ ] `https://mhw.iastate.ai` loads the Streamlit dashboard
- [ ] Region selector shows all 5 regions (GOA, EBS, NBS, Chukchi, Beaufort)
- [ ] Page 1 (Operational): all 4 tabs work for each region
- [ ] Page 2 (Historical): all 4 tabs work for each region
- [ ] `https://mhw.iastate.ai/api/health` returns `{"status":"ok"}`
- [ ] `https://mhw.iastate.ai/api/docs` shows Swagger UI
- [ ] SSL certificate is valid (padlock icon in browser)
- [ ] Chukchi/Beaufort show ice-masked seasonal patterns (winter area_frac ≈ 0)

### Troubleshooting

**Dashboard not loading?**
```bash
docker logs mhw-dashboard  # check for Python import errors
```

**API not responding?**
```bash
docker logs mhw-api  # check for uvicorn startup errors
```

**SSL certificate not provisioning?**
- Verify DNS: `dig mhw.iastate.ai` must return your VM's IP
- Verify port 80 is open (Lightsail firewall)
- Check Traefik logs: `docker logs traefik`
- `acme.json` must be `chmod 600`

**Containers can't see each other?**
- Verify network: `docker network inspect mhw_net`
- All containers must be on `mhw_net`

### Adding Future Projects

Currently Traefik lives inside this project's `docker-compose.yml`. For the first additional project, extract Traefik into a shared stack (`/opt/iastate-ai/traefik/docker-compose.yml`) with an external `mhw_net` network, then connect both projects to it. For now, single-project is fine.

For any new project at `whatever.iastate.ai`:

1. **Namecheap:** Add A record → Host: `whatever`, Value: same VM IP
2. **VM:** Create `/opt/iastate-ai/projects/whatever/docker-compose.yml` with Traefik labels pointing to `whatever.iastate.ai`, connected to the shared network
3. `docker compose up -d` — Traefik auto-discovers and provisions SSL

### Nice-to-have (not blocking deployment):
- Add a "last updated" indicator in the dashboard using the newest date in `region_daily_*.parquet`
- Centralize cron + API logs to a file or systemd journal

---

## Step 13.5: Git, GitHub & Deploy-via-Git Workflow

### One-time setup: Initialize repo and push to GitHub

**On your local machine:**

```bash
cd /Users/rajpython/dev/climate_iastate

# 1. Initialize git repo
git init

# 2. Verify .gitignore is correct (data/ is excluded, code is included)
cat .gitignore
# Should include: data/raw/, data/derived/, .venv/, __pycache__/, outputs/, .DS_Store

# 3. Stage all code files
git add .

# 4. Review what will be committed (should NOT include data/, .venv/, etc.)
git status

# 5. First commit
git commit -m "Initial commit: MHW State Dashboard (Steps 0-12b complete)"

# 6. Create the GitHub repo (requires gh CLI — install with: brew install gh)
gh auth login  # follow prompts to authenticate (one-time)
gh repo create climate_iastate --public --source=. --remote=origin --push

# That's it — repo is live at https://github.com/YOUR_USERNAME/climate_iastate
```

**If you don't have `gh` CLI**, create the repo manually:
1. Go to https://github.com/new
2. Repo name: `climate_iastate`, Public, do NOT add README/.gitignore (we already have them)
3. Click **Create repository**
4. Follow the "push an existing repository" instructions:
```bash
git remote add origin https://github.com/YOUR_USERNAME/climate_iastate.git
git branch -M main
git push -u origin main
```

### Ongoing workflow: Local dev → GitHub → VM

This is your day-to-day cycle for making changes:

```
┌─────────────┐     git push     ┌──────────┐     git pull + rebuild     ┌─────────────┐
│  Local Mac  │ ───────────────→ │  GitHub  │ ←─────────────────────────  │  Lightsail  │
│  (develop)  │                  │  (repo)  │                             │  VM (prod)  │
└─────────────┘                  └──────────┘                             └─────────────┘
```

#### Step A: Make changes locally

```bash
# Edit code (dashboard, API, config, etc.)
# Test locally:
streamlit run src/dashboard/app.py
# or (PYTHONPATH must include src/):
PYTHONPATH=src uvicorn api.main:app --reload
```

#### Step B: Commit and push

```bash
git add -A
git commit -m "description of changes"
git push
```

#### Step C: Deploy to VM

```bash
# SSH into the VM
ssh -i ~/.ssh/your-lightsail-key.pem ubuntu@YOUR_STATIC_IP

# Pull latest code
cd /opt/iastate-ai/projects/mhw
git pull

# Rebuild and restart containers (only needed if dependencies or Dockerfile changed)
docker compose up -d --build

# If only dashboard/API code changed (no new deps), just restart:
docker compose restart dashboard api
```

**When to rebuild vs restart:**
- **Code-only changes** (dashboard panels, API routes, config): `docker compose up -d --build` (rebuilds image with new code, ~1-2 min with cached layers)
- **New Python dependencies** (pyproject.toml changed): `docker compose up -d --build` (slower, pip install layer rebuilds)
- **Data changes** (new region, recomputed risk): rsync data separately, then `docker compose restart dashboard api`

#### Quick deploy one-liner (from your local machine)

```bash
# Push + deploy in one command (add to ~/.bashrc or ~/.zshrc as an alias):
alias mhw-deploy='git push && ssh -i ~/.ssh/your-lightsail-key.pem ubuntu@YOUR_STATIC_IP "cd /opt/iastate-ai/projects/mhw && git pull && docker compose up -d --build"'
```

### What goes in git vs what stays on disk

| In git (version controlled) | NOT in git (rsync or generate on VM) |
|------------------------------|--------------------------------------|
| `src/` (all code) | `data/raw/` (1.6 GB OISST NetCDFs) |
| `config/` (YAML + GeoJSON) | `data/derived/` (159 MB zarr/parquet) |
| `tests/` | `.venv/` |
| `Dockerfile`, `docker-compose.yml` | `outputs/` (plots) |
| `infra/traefik/` | `notebooks/` (optional) |
| `scripts/daily_refresh.sh` | |
| `.streamlit/config.toml` | |
| `.github/workflows/ci.yml` | |
| `docs/` | |
| `pyproject.toml` | |
| `.gitignore` | |

---

## Execution Rules

1. **One step at a time.** Do not start Step N+1 until Step N is verified.
2. **Each step has a CLI command** that produces visible output (plot, printed stats, or Streamlit page). Steps 4, 5, 6, and 8 have a **notebook checkpoint** — create and run the notebook before proceeding to the next step.
3. **Start with GOA only** for Steps 4–6, expand to all regions in Step 11.
   - **Data fetch sequencing:** Step 4 fetches **all years 1982–present** (not just the baseline), caching them as NetCDF. This ensures Steps 5 and 8 never wait for ERDDAP. GOA was done with a split-fetch (baseline only in Step 4, remainder in Step 8) — future regions must follow the updated Step 4 spec.
   - **Climatology is per-region, not global:** mu/θ90 zarr stores are built per region's bounding box. Each `mhw-build-climatology --region X` creates its own zarr files. Only masks and weights are global.
4. **Production logic lives in `src/`** — CLI entrypoints defined in pyproject.toml.
5. **Config is already written** — code reads `gap_days`, `intensity_reference`, `onset_reference`, `apply_ice_mask`, `ice_threshold_percent`, `risk_percentiles.mode`, etc. from `config/*.yml`. No hardcoded magic numbers.
6. **Extras install incrementally** — `[geo]` from Step 1, `[dashboard]` from Step 7, `[api]` from Step 10.
7. **Deployment target:** `mhw.iastate.ai` on a Cloud VM with Docker Compose + Traefik reverse proxy + auto Let's Encrypt SSL.
