# Runtime Architecture

This document supplements the project [README](/Users/rajpython/dev/climate_iastate/README.md). The README is the landing page. This file explains how the system actually runs: which entry points produce data, which modules consume it, and how the dashboard and API serve the final output.

## Purpose

The project has a file-based runtime architecture:

- `src/mhw/` builds the dataset
- `data/` stores the dataset
- `src/dashboard/` renders the dataset in Streamlit
- `src/api/` exposes the dataset over HTTP
- Docker Compose runs the services and mounts the shared `data/` directory

The key design choice is that the Streamlit dashboard and the FastAPI service both read the same materialized files from `data/`. The dashboard does not fetch its own charts from the API.

## High-Level Flow

1. Raw SST and index data are fetched from NOAA sources.
2. Static derived artifacts are built:
   - region masks
   - latitude weights
   - climatology lookup tables
3. The state engine computes grid-level marine heatwave state arrays.
4. Regional aggregation collapses grid data into one row per day per region.
5. Risk scoring computes percentile-based risk tables from the aggregated history.
6. Streamlit and FastAPI read those generated files directly and serve them to users.

## Main Entry Points

Python CLI entry points are declared in [pyproject.toml](/Users/rajpython/dev/climate_iastate/pyproject.toml):

- `mhw-fetch-sst` -> `mhw.fetch.oisst:main`
- `mhw-fetch-indices` -> `mhw.fetch.indices:main`
- `mhw-build-masks` -> `mhw.regions.masks:main`
- `mhw-build-climatology` -> `mhw.climatology.build_mu_theta:main`
- `mhw-plot-climatology` -> `mhw.climatology.build_mu_theta:plot_main`
- `mhw-run-states` -> `mhw.states.update_states:main`
- `mhw-aggregate` -> `mhw.states.aggregates:main`
- `mhw-compute-risk` -> `mhw.states.risk:main`
- `mhw-backfill` -> `mhw.states.update_states:backfill_main`

Runtime service entry points:

- Dashboard: [src/dashboard/MHW_Dashboard.py](/Users/rajpython/dev/climate_iastate/src/dashboard/MHW_Dashboard.py)
- API: [src/api/main.py](/Users/rajpython/dev/climate_iastate/src/api/main.py)
- Daily refresh orchestrator: [scripts/daily_refresh.sh](/Users/rajpython/dev/climate_iastate/scripts/daily_refresh.sh)

## Data-Producing Modules

### 1. Raw Data Fetch

Files:

- [src/mhw/fetch/oisst.py](/Users/rajpython/dev/climate_iastate/src/mhw/fetch/oisst.py)
- [src/mhw/fetch/indices.py](/Users/rajpython/dev/climate_iastate/src/mhw/fetch/indices.py)

Responsibilities:

- `oisst.py`
  - fetches daily OISST SST for one region and date
  - saves single-day NetCDF files for inspection and diagnostics
- `indices.py`
  - fetches AO daily index
  - fetches PDO monthly index
  - saves parquet files used by the dashboard and API

Primary outputs:

- `data/raw/oisst_<region>_<YYYYMMDD>.nc` (manual / diagnostic)
- `data/raw/ao_daily.parquet`
- `data/raw/pdo_monthly.parquet`

### 2. Static Region Artifacts

Files:

- [src/mhw/regions/masks.py](/Users/rajpython/dev/climate_iastate/src/mhw/regions/masks.py)
- [src/mhw/regions/weights.py](/Users/rajpython/dev/climate_iastate/src/mhw/regions/weights.py)

Responsibilities:

- rasterize `config/regions.geojson` polygons onto the OISST grid
- compute `cos(lat)` area weights

Primary outputs:

- `data/derived/masks/region_masks.zarr`
- `data/derived/weights/weights.zarr`

These are static prerequisites for all regional aggregation.

### 3. Climatology Build

File:

- [src/mhw/climatology/build_mu_theta.py](/Users/rajpython/dev/climate_iastate/src/mhw/climatology/build_mu_theta.py)

Responsibilities:

- fetch and cache yearly SST + ice fields for the baseline period
- apply ice masking according to `config/climatology.yml`
- compute:
  - `mu(doy, lat, lon)`
  - `theta90(doy, lat, lon)`

Primary outputs:

- `data/raw/oisst_<region>_<year>.nc` (year-level cache)
- `data/derived/climatology/mu_<region>.zarr`
- `data/derived/climatology/theta90_<region>.zarr`

These climatology files are immutable lookup tables for the state engine unless the science configuration changes.

### 4. State Engine

File:

- [src/mhw/states/update_states.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/update_states.py)

Responsibilities:

- load precomputed climatology
- load cached or remote SST + ice by year
- compute daily grid-level state variables:
  - `x` threshold exceedance
  - `A` active flag
  - `D` duration
  - `I` intensity
  - `C` cumulative intensity
  - `O` onset rate

Key internal functions:

- `run_state_engine()`
- `_update_one_day()`
- `save_states()`

Primary output:

- `data/derived/states_grid/states_<region>_<start>_<end>.zarr`

This grid-level Zarr is the source for the dashboard map and the map API endpoint.

### 5. Regional Aggregation

File:

- [src/mhw/states/aggregates.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/aggregates.py)

Responsibilities:

- load grid-level states
- load region mask and weights
- compute daily region-level metrics:
  - `area_frac`
  - `Ibar`
  - `Dbar`
  - `Cbar`
  - `Obar`

Primary output:

- `data/derived/aggregates_region/region_daily_<region>.parquet`

This parquet file is the central historical dataset used by most dashboard panels and several API endpoints.

### 6. Risk Computation

File:

- [src/mhw/states/risk.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/risk.py)

Responsibilities:

- compute percentile ranks of regional metrics against a reference distribution
- compute a weighted composite risk score
- assign categorical risk labels

Primary output:

- `data/derived/risk/risk_<region>.parquet`

The risk gauge in the dashboard reads this file directly.

## Backfill vs Daily Refresh

### Backfill

`mhw-backfill` is the historical reconstruction command. It is implemented by `backfill_main()` in [src/mhw/states/update_states.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/update_states.py).

What it does:

1. loops year by year through the requested historical range
2. runs the state engine for each year
3. aggregates each year into the regional daily parquet
4. rebuilds the full risk table at the end

It imports and calls internal functions from:

- [src/mhw/states/update_states.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/update_states.py)
- [src/mhw/states/aggregates.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/aggregates.py)
- [src/mhw/states/risk.py](/Users/rajpython/dev/climate_iastate/src/mhw/states/risk.py)

Backfill is normally:

- run once during initial setup
- rerun only when rebuilding history after a methodology or configuration change

It is not intended to be run every day.

### Daily Refresh

The routine operational update is [scripts/daily_refresh.sh](/Users/rajpython/dev/climate_iastate/scripts/daily_refresh.sh).

What it does for each region:

1. runs `mhw-run-states` from January 1 of the current year to today
2. runs `mhw-aggregate` for that same range
3. runs `mhw-compute-risk`
4. restarts the dashboard container to clear Streamlit caches

This keeps the current edge of the dataset fresh without recomputing the full 1982-present archive every day.

## Data-Consuming Modules

## Dashboard

Entry point:

- [src/dashboard/MHW_Dashboard.py](/Users/rajpython/dev/climate_iastate/src/dashboard/MHW_Dashboard.py)

Streamlit discovers pages from:

- [src/dashboard/pages](/Users/rajpython/dev/climate_iastate/src/dashboard/pages)

Primary pages:

- [src/dashboard/pages/1_Operational.py](/Users/rajpython/dev/climate_iastate/src/dashboard/pages/1_Operational.py)
- [src/dashboard/pages/2_Historical.py](/Users/rajpython/dev/climate_iastate/src/dashboard/pages/2_Historical.py)
- [src/dashboard/pages/3_User_Guide.py](/Users/rajpython/dev/climate_iastate/src/dashboard/pages/3_User_Guide.py)

Reusable data loaders and plotting logic live in:

- [src/dashboard/components/map_mhw.py](/Users/rajpython/dev/climate_iastate/src/dashboard/components/map_mhw.py)
- [src/dashboard/components/ts_event_metrics.py](/Users/rajpython/dev/climate_iastate/src/dashboard/components/ts_event_metrics.py)
- [src/dashboard/components/predictability_panel.py](/Users/rajpython/dev/climate_iastate/src/dashboard/components/predictability_panel.py)
- [src/dashboard/components/risk_gauge.py](/Users/rajpython/dev/climate_iastate/src/dashboard/components/risk_gauge.py)

What the dashboard reads:

- map page:
  - `data/derived/states_grid/*.zarr`
- event metrics and historical pages:
  - `data/derived/aggregates_region/*.parquet`
- predictability and regime panels:
  - `data/raw/ao_daily.parquet`
  - `data/raw/pdo_monthly.parquet`
- risk gauge:
  - `data/derived/risk/*.parquet`
- guide page:
  - `docs/user_guide.md`
  - `docs/user_guide.pdf`

Important: the dashboard reads these files directly. It does not call the FastAPI service for its own rendering path.

## API

Entry point:

- [src/api/main.py](/Users/rajpython/dev/climate_iastate/src/api/main.py)

Routers:

- [src/api/routes_states.py](/Users/rajpython/dev/climate_iastate/src/api/routes_states.py)
- [src/api/routes_maps.py](/Users/rajpython/dev/climate_iastate/src/api/routes_maps.py)
- [src/api/routes_indices.py](/Users/rajpython/dev/climate_iastate/src/api/routes_indices.py)

Schema models:

- [src/api/schema.py](/Users/rajpython/dev/climate_iastate/src/api/schema.py)

What the API reads:

- `routes_states.py`
  - `data/derived/aggregates_region/region_daily_<region>.parquet`
  - derives event summaries from aggregated time series
- `routes_maps.py`
  - `data/derived/states_grid/*.zarr`
  - optionally uses `data/raw/oisst_<region>_<year>.nc` to infer land masking
- `routes_indices.py`
  - `data/raw/ao_daily.parquet`
  - `data/raw/pdo_monthly.parquet`

The API is a parallel consumer of the same file-based dataset. It is not a data source for the Streamlit dashboard.

## Runtime Services and Ports

Container build:

- [Dockerfile](/Users/rajpython/dev/climate_iastate/Dockerfile)

Service orchestration:

- [docker-compose.yml](/Users/rajpython/dev/climate_iastate/docker-compose.yml)

Defined services:

- `dashboard`
  - runs Streamlit
  - command: `streamlit run src/dashboard/MHW_Dashboard.py`
  - mounts `./data:/app/data:ro`
- `api`
  - runs FastAPI via uvicorn
  - command: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
  - mounts `./data:/app/data:rw`
- `traefik`
  - reverse proxy and TLS termination

Ports:

- Streamlit listens on `8501` inside the dashboard container
- FastAPI listens on `8000` inside the API container
- Traefik binds host ports `80` and `443`

Routing:

- `/api/*` -> API service
- all other application routes -> Streamlit dashboard

## Operational Model

The practical operating model is:

1. Build or rebuild static prerequisites when needed:
   - masks
   - weights
   - climatology
   - AO/PDO files
2. Run backfill to construct or reconstruct the historical archive.
3. Start the dashboard and API services.
4. Use the daily refresh script to keep the current year updated.

The system remains consistent because both serving layers read from the same `data/` directory.

## Typical First-Time Setup

1. `mhw-build-masks`
2. `mhw-fetch-indices --ao-years 43 --pdo-years 43`
3. `mhw-build-climatology --region <region>`
4. `mhw-backfill --region <region> --start 1982-01-01 --end <end-date>`
5. `python scripts/build_pdf.py`
6. start Streamlit and FastAPI, or run Docker Compose

## Typical Ongoing Daily Operation

1. fetch or use cached current-year SST as needed
2. recompute current-year states
3. recompute aggregates
4. recompute risk
5. clear Streamlit cache by restarting the dashboard service

In production, this is handled by [scripts/daily_refresh.sh](/Users/rajpython/dev/climate_iastate/scripts/daily_refresh.sh).

## Summary

This repository is a materialized-data pipeline with two serving front ends.

- `src/mhw/` produces and updates files
- `data/` is the shared contract between producer and consumers
- `src/dashboard/` visualizes those files
- `src/api/` exposes those files
- Docker Compose runs both services against the same mounted dataset

That shared-file design is why a backfill or refresh updates the entire dashboard and API at once.
