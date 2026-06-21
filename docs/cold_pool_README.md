# Cold Pool — Technical README

Engineering companion to the plain-language `cold_pool_user_guide.md`. Covers the data
sources, modules, CLIs, derived artifacts, methods, API, dashboard, and validation numbers
for the eastern Bering Sea (EBS) cold-pool feature.

The **cold pool** = area of the EBS shelf where summer **bottom** temperature ≤ 2 °C
(also tracked at ≤ 1 / 0 / −1 °C). We consume existing public products; we do **not** run
ocean models.

---

## 1. Data flow

```
fetch (public sources)            derive (data/derived/cold_pool)        serve
─────────────────────             ───────────────────────────────       ─────────────
AFSC coldpool (GitHub/Zenodo) ──> coldpool_index_observed.parquet  ─┐
   index + per-haul                coldpool_hauls_observed.parquet   │
                                                                     ├─> FastAPI /v1/cold-pool/*
Bering10K ROMS (PMEL OPeNDAP) ─┐                                     │   ──> Streamlit pages 4 & 5
CEFI MOM6 NEP  (PSL OPeNDAP)  ─┼> coldpool_model_<src>.parquet       │
                               │  coldpool_model_<src>_monthly.parquet┘
                               └> survey_replicate[_annual]_<src>.parquet
                                  ebs_shelf_mask.npz (shared shelf mask)
```

All `data/` outputs are gitignored; regenerate with the CLIs below.

---

## 2. Data sources

| # | Source | Access | Variable | Grid | Cadence / coverage |
|---|--------|--------|----------|------|--------------------|
| Observed | NOAA **AFSC** cold-pool index + per-haul temps | **file download** from GitHub `afsc-gap-products/coldpool` (Zenodo DOI 10.5281/zenodo.16915337) | `cold_pool_index.rda`, `index_hauls_temperature_data.csv` | survey footprint / stations | annual, **1982–2025** (no 2020) |
| Model 1 | **Bering10K ROMS** (PMEL/UW ACLIM) | **OPeNDAP** `data.pmel.noaa.gov/aclim/thredds/` | `temp` (bottom-5m mean) | curvilinear ~10 km (eta_rho 258 × xi_rho 182), 2-D `lat_rho`/`lon_rho` | weekly, **1970–2024** |
| Model 2 | **CEFI MOM6 NEP** (GFDL/PSL) | **OPeNDAP** `psl.noaa.gov/thredds/...regional_mom6/cefi_portal/northeast_pacific/` | `btm_temp` | **rectilinear** ~10 km (815 × 341), 1-D lat/lon | monthly, **1993–2024** (hindcast to mid-2025) |

Source descriptors live in `src/mhw/bottom/sources.py` (`BERING10K_K20_CORECFS`, `MOM6_NEP`).

---

## 3. Modules (`src/mhw/`)

| Module | Responsibility |
|--------|----------------|
| `fetch/coldpool.py` | Download the AFSC index (`pyreadr` reads `.rda`) and per-haul CSV → parquet. |
| `bottom/sources.py` | `BottomSource` descriptors (URL, var, coord names, cadence) — the only source-specific config. |
| `bottom/loader.py` | `open_bottom_dataset`, `load_bottom_temp` — grid-agnostic: returns `(time, y, x)` with **2-D** lat/lon for *both* curvilinear (2-D coords) and rectilinear (1-D coords broadcast) sources. |
| `bottom/regrid.py` | `regrid_curvilinear_to_regular` — block-average onto the regular 0.25° OISST grid using **only numpy + scipy** (no xesmf/conda); `normalize_lon` handles 0–360 vs −180–180. |
| `bottom/coldpool.py` | Shelf mask, `cell_area_km2`, `coldpool_area_km2`, `mean_shelf_bottom_temp`, `build_model_coldpool_series` (full-shelf annual series; `--monthly` option). |
| `bottom/survey_replicate.py` | `build_survey_replicate` (co-locate model at haul lat/lon + nearest date via `cKDTree`), `haul_skill`, `annual_means`. |

---

## 4. CLIs (entry points in `pyproject.toml`)

```bash
mhw-fetch-coldpool                                   # observed index + per-haul → data/raw/
mhw-build-coldpool-model --source bering10k          # full-shelf series (weekly snapshot)
mhw-build-coldpool-model --source mom6_nep
mhw-build-coldpool-model --source bering10k --monthly # July monthly mean (matched cadence)
mhw-build-coldpool-model --source mom6_nep  --monthly
mhw-build-survey-replicate --source bering10k        # co-located validation
mhw-build-survey-replicate --source mom6_nep
```

Full rebuild from scratch: run all of the above (the model + survey-replicate steps pull
from OPeNDAP, ~10–15 min each). The shared shelf mask (`ebs_shelf_mask.npz`) is built once
from Bering10K bathymetry on first model run and reused.

---

## 5. Derived artifacts (`data/derived/cold_pool/`, gitignored)

| File | Contents |
|------|----------|
| `coldpool_model_{bering10k,mom6_nep}.parquet` | full-shelf annual: `year, source, mean_bottom_temp, area_lte{2,1,0,minus1}_km2` (weekly snapshot for Bering10K, July month for MOM6) |
| `coldpool_model_{…}_monthly.parquet` | same, both on July **monthly-mean** cadence (model-vs-model panel) |
| `survey_replicate_{…}.parquet` | per-haul: `year, stationid, datetime, lat, lon, obs_bottom_temp, model_bottom_temp` |
| `survey_replicate_annual_{…}.parquet` | per-year means: `year, n_hauls, obs_mean_bottom_temp, model_mean_bottom_temp, bias_c` |
| `ebs_shelf_mask.npz` | boolean shelf mask + `EBS_LATS`/`EBS_LONS` on the 0.25° grid |
| `data/raw/coldpool_index_observed.parquet`, `coldpool_hauls_observed.parquet` | observed index + per-haul temps |

---

## 6. Methods & key parameters (`bottom/coldpool.py`)

- **Analysis grid:** `EBS_LATS = arange(54, 63, 0.25)`, `EBS_LONS = arange(-179, -157, 0.25)` (0.25° OISST frame).
- **Shelf mask:** bottom depth from Bering10K `z_w` (bottom s-layer interface), regridded to 0.25°, kept where **depth ≤ `SHELF_MAX_DEPTH_M = 200` m**. **Built once from Bering10K and shared across all sources** so every model is scored on an identical footprint (~1,716 cells ≈ 680,000 km²). The deep basin is cold year-round and is *not* the cold pool, hence the mask.
- **Cell area:** cosine-latitude weighted (`dlat·111 km × dlon·111 km·cos(lat)`).
- **Cold-pool area:** Σ cell areas where bottom temp ≤ threshold (NaN-safe). `THRESHOLDS_C = (2, 1, 0, −1)`.
- **Survey-time selection:** `SURVEY_TARGET_MD = "07-04"` → nearest weekly snapshot (Bering10K) or July month (MOM6); `--monthly` averages all of July.
- **Survey replication:** for each haul, nearest **ocean** model cell (cKDTree over finite cells, lon normalized) at the **nearest model time** to the haul date; compare model bottom temp vs observed gear temp. This is the literature-standard comparison (Kearney 2021; Seelanki et al. 2025) — it matches footprint **and** timing, unlike the full-shelf domain average.

### The three comparisons (why they differ)
1. **Full-shelf model view** (≤200 m, model's own footprint) — model product; absolute area/temperature run larger/warmer than the survey because the footprint is bigger. Use *pattern* (standardized), not level.
2. **Model vs model** (identical ≤200 m shelf + identical monthly cadence) — isolates genuine inter-model differences / uncertainty.
3. **Survey replication** (model co-located at survey hauls) — the only fair model-vs-survey bias.

---

## 7. API (`src/api/routes_coldpool.py`, schema in `src/api/schema.py`)

| Endpoint | Returns |
|----------|---------|
| `GET /v1/cold-pool/observed` | observed index time series (area by threshold + mean bottom/surface temp) |
| `GET /v1/cold-pool/modelled?source={bering10k,mom6_nep}` | full-shelf model series; `note` flags the domain caveat |
| `GET /v1/cold-pool/survey-replicate?source=…` | per-year obs vs model means + overall `bias_c`/`rmse_c`/`corr` |

Pydantic models: `ColdPoolPayload`/`ColdPoolRecord`, `SurveyReplicatePayload`/`SurveyReplicateRecord`.

---

## 8. Dashboard (`src/dashboard/`)

- `components/coldpool_data.py` — shared cached loaders + constants (THRESHOLDS, MODEL_SOURCES, MODEL_MONTHLY, MODEL_COLORS, SR_FILES) used by both pages.
- `pages/4_Cold_Pool_Observed.py` — **Panel A** (observed area+bottom temp; threshold-driven) + **Panel C** (survey-replicated validation). Threshold control affects Panel A only (C is bottom-temperature based).
- `pages/5_Cold_Pool_Models.py` — **Panel B1** (full-shelf models vs observed, pattern) + **Panel B2** (model-vs-model identical footing, monthly). Independent threshold control drives B1/B2 area.

Visual check: `scripts/screenshot_dashboard.py` (Playwright) drives the running app and screenshots a page with chosen multiselect options.

---

## 9. Validation results (current build)

**Survey-replicated (the defensible, literature-comparable numbers):**

| Model | Bias (°C) | RMSE (°C) | r (haul-level) | n hauls / years |
|-------|----------:|----------:|---------------:|-----------------|
| Bering10K ROMS | −0.16 | 1.11 | 0.83 | 15,007 / 1982–2024 |
| CEFI MOM6 NEP | +0.00 | 0.85 | 0.90 | 11,633 / 1993–2024 |

**Full-shelf domain-average (NOT footprint-matched — runs warm; for context only):**
Bering10K bias +0.39 °C, MOM6 +1.22 °C. Full-shelf pattern correlation vs observed:
Bering10K r ≈ 0.90, MOM6 r ≈ 0.97 (area and bottom temp).

**Model vs model (identical ≤200 m shelf + monthly):** r ≈ 0.92 (area and bottom temp);
mean Δ (MOM6 − Bering10K) ≈ +0.52 °C.

Interpretation: compared the fair way, **both models are essentially unbiased**; the
apparent MOM6 "warm bias" is a footprint/cadence artifact (its warm-shallow / cold-slope
biases largely cancel over the survey footprint — consistent with Seelanki et al. 2025).

---

## 10. Caveats

- **Lagged, not real-time.** Survey is annual + post-processed; models are hindcasts (to ~2024). No live feed.
- **Full-shelf absolute area/temperature ≠ survey** (bigger footprint). Quote survey-replicated numbers and pattern, not raw full-shelf level.
- **EBS only.** Bering10K is Bering-only; MOM6 covers the wider NEP (GOA extension is future work).
- **Cold thresholds get noisy.** At ≤ 0 / −1 °C many years have near-zero area → unstable z-scores/correlations.
- **MOM6 release pinned** to `r20250912` in `sources.py`; a `latest/` alias exists if a rolling pointer is preferred.

---

## 11. References

See `cold_pool_user_guide.md` §References: Kinney et al. 2022 (PLOS ONE; cold-pool
definition/ecology), Szuwalski et al. 2023 (Science; snow-crab collapse), Seelanki et al.
2025 (GMD; MOM6-NEP10k Bering evaluation), Drenkard et al. 2025 (GMD; MOM6-COBALT-NEP10k
v1.0). Discovery + source provenance: `docs/forecast_extension/catalog_report.md`.
