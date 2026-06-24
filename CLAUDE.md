# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A marine-heatwave (MHW) monitoring dashboard for the Alaska shelf seas (Gulf of Alaska, Eastern/Northern Bering, Chukchi, Beaufort), operationalizing the Hobday et al. (2016) hierarchical MHW definition on NOAA OISST v2.1. It is **actively expanding beyond SST** into a comprehensive Alaska-shelf data board — bottom ocean state (cold pool) and survey catch are the newest layers. Live at `marine.iastate.ai`.

Forecasting is deliberately **out of scope** for this board — it is owned by a separate research cell under `docs/forecast_extension/`. The board may display a forecast product later but does not build one. (`src/mhw/forecast/` exists as a source-agnostic engine but is not wired to the dashboard/API.)

## Commands

The venv is **uv-managed** (`.venv/`, no `pip` inside it). Use `.venv/bin/<tool>` directly, or activate it.

```bash
# Install (editable, all extras)
uv pip install -e ".[geo,dashboard,api,dev]"

# Tests (pytest config lives in pyproject.toml; testpaths=tests, -v --tb=short by default)
.venv/bin/pytest                                  # full suite
.venv/bin/pytest tests/test_foss_catch.py         # one file
.venv/bin/pytest tests/test_foss_catch.py::test_cold_pool_summary_shares   # one test
.venv/bin/pytest -k coldpool                       # by keyword

# Lint
.venv/bin/ruff check src tests

# Run the dashboard (Streamlit; entry = the file, pages registered via st.navigation)
.venv/bin/streamlit run src/dashboard/Alaska_Dashboard.py

# Run the API (package import name is `api`, not `src.api`, via setuptools src-layout)
.venv/bin/uvicorn api.main:app --reload --port 8000   # Swagger at /docs, all data under /v1

# Visual dashboard check (needs `playwright install chromium` once)
.venv/bin/python scripts/screenshot_dashboard.py
```

### Refreshing local data

The repo ships **code only** — everything under `data/raw/` and `data/derived/` is generated locally and gitignored. Services read those generated files directly; with no data, API endpoints return 503 and many tests `skip`. To build/extend:

```bash
bash scripts/monthly_refresh.sh            # extend the MHW backfill through today UTC
bash scripts/monthly_refresh.sh 2026-06-30 # ...or through a given date
```

## Architecture

### MHW pipeline (the original spine) — a file-based, staged pipeline

Each stage is a CLI (declared in `[project.scripts]`) that reads upstream artifacts and writes the next. Nothing is a live service except the final read layer.

```
fetch (OISST, AO/PDO)  →  static artifacts (masks, weights, climatology)
   →  state engine (per-cell MHW state arrays)  →  regional aggregation (1 row/day/region)
   →  risk percentiles  →  Streamlit + FastAPI read the generated files
```

CLI ↔ module map: `mhw-fetch-sst`/`mhw-fetch-indices` (`mhw.fetch.*`) → `mhw-build-masks` (`mhw.regions.masks`) + `mhw-build-climatology` (`mhw.climatology.build_mu_theta`) → `mhw-run-states`/`mhw-backfill` (`mhw.states.update_states`) → `mhw-aggregate` (`mhw.states.aggregates`) → `mhw-compute-risk` (`mhw.states.risk`).

Key data artifacts: `data/derived/masks/region_masks.zarr`, `data/derived/weights/weights.zarr`, `data/derived/climatology/`, `data/derived/states_grid/*.zarr`, `data/derived/aggregates_region/region_daily_*.parquet`, `data/derived/risk/`. Region polygons are `config/regions.geojson`; tuning is in `config/*.yml`. Full methodology is in `mhw_README.md`; runtime/data-flow detail is in `docs/architecture_runtime.md`.

### Bottom ocean state / cold pool (`src/mhw/bottom/`)

A newer, **source-agnostic** engine: a `BottomSource` descriptor (`sources.py`) is the *only* source-specific config — adding a model is a new descriptor, not new code. `loader.py` opens any source over OPeNDAP with a uniform contract; `regrid.py` puts curvilinear (Bering10K ROMS) and rectilinear (MOM6 NEP) grids onto a shared 0.25° grid; `coldpool.py` derives the modelled cold-pool series; `survey_replicate.py` co-locates a model at AFSC haul lat/lon+date (the literature-standard, defensible model-vs-survey comparison). The two models share **one** EBS-shelf mask (built once from Bering10K bathymetry) so their areas are directly comparable. The observed validation target is fetched by `mhw.fetch.coldpool` (AFSC `cold_pool_index`, read from `.rda` via `pyreadr`).

Important caveat carried in the code: compare models to survey via **survey replication / mean bottom temperature**, not raw full-shelf area (full-shelf area is a footprint artifact, not skill).

### Survey catch (`src/mhw/fetch/foss_catch.py`)

Pulls NOAA's public **FOSS** REST API and joins survey `haul` ⟕ `catch` on `hauljoin` into a tidy per-haul `(year, region, lat, lon, depth, bottom_temperature_c, species, cpue)` frame. Two non-obvious rules baked in:
- **Left-join + zero-fill.** FOSS `catch` has a row only where a species was caught; take *all* hauls and fill absent CPUE with 0, so each row is a true presence/absence at a known bottom temp (otherwise thermal profiles bias and "share inside the cold pool" is meaningless).
- **Never use `$in`.** The FOSS WAF blocks the `$in` operator. Filter on a single scalar (`species_code` for catch, `srvy` for haul), page by `offset`, and intersect client-side.

### Read layer

- **API** (`src/api/`): FastAPI, all data routers mounted under `/v1` (`routes_states`, `routes_maps`, `routes_indices`, `routes_coldpool`); `/health` is unversioned. Routes read the generated parquet/zarr directly and return 503 when an artifact is missing.
- **Dashboard** (`src/dashboard/`): Streamlit — `Alaska_Dashboard.py` is the entry + `st.navigation` shell that owns the single `set_page_config`, fonts, and a **geography-first hybrid** page registry (Overview · Alaska-wide Climate [MHW] · Bering Sea [bottom state + catch] · reserved GOA/AI + Arctic · Research · Guides). `pages/` modules render bodies only — cross-cutting MHW pages are path-registered scripts; region-specific pages expose a group-aware `render(group=...)` callable (region dropdowns filter by `BottomRegion.group`). `components/` holds reusable panels.

## Conventions worth matching

- **CLI module shape:** new pipeline/fetch modules follow the house pattern — module docstring with a `CLI:` line, `PROJECT_ROOT = Path(__file__).resolve().parents[3]`, pure network-free helpers separated from network/IO, `parse_args(argv)` + `main(argv)`, a `save_parquet(...)`, and a `[project.scripts]` entry. Mirror `fetch/coldpool.py` or `bottom/coldpool.py`.
- **Tests are network-free.** Live fetch/network code is exercised by extracting **pure** helpers (e.g. `join_catch_to_hauls`, `cold_pool_summary`, `haul_skill`) and unit-testing those on small in-memory frames. API tests `skip` (not fail) when the underlying parquet/zarr hasn't been generated — keep that pattern.
- **Regions** are referenced by short codes throughout: EBS, NBS, GOA, AI, BSS (slope), Chukchi, Beaufort. "Cold pool" is an **EBS/NBS-only** product (≤2 °C shelf water); GOA/AI/slope are bottom-temperature regions with no cold pool. Model coverage differs by region (MOM6 NEP spans all; Bering10K is EBS/NBS/slope only) — keep panels labelled by source + period + validation status.
- **Dashboard page design system (`src/dashboard/components/bottom_ui.py`).** Every data page shares one restrained, NOAA-style look via this module — do **not** hand-roll page chrome. Each `render()` calls `inject_css()` once, then composes:
  - `page_header(icon, title, subtitle, region_label_text, caption)` — blue title + region-name subtitle + a right-aligned **region chip**. Select the region *before* the header so the chip reflects it; map short codes to full names with a local `_REGION_NAMES` dict where needed.
  - `section_title(title, note="")` — the blue uppercase panel label (use instead of `st.subheader`/`### `).
  - **KPI numbers go in boxed cards, never bare `st.metric`.** Build `kpi_card(label, value, value_color, sub=, label_note=)` HTML strings and render a row with `kpi_grid([...], cols=N)`. Colour accents are **semantic and fixed**: `GREEN`=area/position, `BLUE`=stats/counts/models, `RED`=warm temperature, `PURPLE`=duration, `AMBER`=cumulative/caution, `SLATE`=neutral stats/dates (all exported from `bottom_ui`).
  - `callout(body_html, icon, tint)` for an interpretation sentence; `footer(left_html)` for a sources line + "Learn more in the guide" link.
  - **Wrap each panel in a bordered card.** Use `with st.container(border=True):` around a section; for tab-based pages wrap the whole tab without re-indenting via `with tab_x, st.container(border=True):`. Numbers *and* charts/tables both sit in bordered cards — uniformity is the goal.
  - CSS classes are `bs-*`; the entry shell (`Alaska_Dashboard.py`) owns `set_page_config`/fonts. This pattern is applied across the Bering pages and the Alaska-wide MHW Operational/Historical pages; new pages must match it.
```
