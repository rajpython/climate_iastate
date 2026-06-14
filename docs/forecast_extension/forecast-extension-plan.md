# forecast-extension-plan.md

# Marine Heatwave Dashboard Forecast Extension Plan

## Purpose

The current dashboard provides:

* Current marine heatwave conditions
* Historical context
* Percentile rankings
* Regional marine heatwave metrics
* Public API access

The dashboard currently functions primarily as a state-monitoring platform.

The objective of this extension is to transform the dashboard into a decision-support platform capable of supporting:

* NOAA ecosystem scientists
* Fisheries stock assessment scientists
* Fisheries managers
* Fisheries management councils
* Climate-risk researchers

The primary use case is Alaska fisheries, with initial emphasis on:

* Eastern Bering Sea
* Gulf of Alaska
* Chukchi Sea
* Beaufort Sea

---

# Vision

Transform:

State Monitoring

into

Climate Risk Forecasting

and ultimately

Climate-Informed Fisheries Decision Support

---

# Guiding Principles

## Principle 1

Do not develop new ocean models.

The project consumes and interprets existing scientific products.

Examples:

* NOAA OISST
* NOAA MOM6
* NOAA PSL
* NMME
* ECMWF
* Copernicus

---

## Principle 2

Focus on scientific translation.

The dashboard's comparative advantage is:

scientific products → actionable information

---

## Principle 3

Prioritize fisheries-relevant ocean states.

Surface temperature alone is insufficient.

The platform should evolve toward:

* Surface temperature
* Bottom temperature
* Cold pool dynamics
* Sea ice
* Mixed layer properties
* Ocean heat content

---

## Principle 4

Forecast uncertainty must be explicit.

Forecasts should be probabilistic whenever possible.

---

## Principle 5

Forecast from the primitive, at the grid level.

Forecasts are produced per grid cell on the temperature anomaly and converted to a
marine-heatwave exceedance probability against the existing 90th-percentile
threshold. Regional and area-based products are then *derived* from the cell
probability field.

The monitoring aggregates (`area_frac`, conditional means) were built for
situational awareness. They do not bound the forecast. Forecasting them directly
would discard spatial structure and is statistically fragile (bounded,
zero-inflated). Forecast the primitive; derive the aggregate.

---

## Principle 6

One variable- and source-agnostic forecast engine.

The engine forecasts an anomaly field against a threshold field and emits an
exceedance-probability field. Swapping the inputs — surface temperature today,
bottom temperature or a seasonal ensemble later — reuses the same engine. Only the
data adapter changes. New capabilities are adapters, not rewrites.

---

# Engineering & Repository Strategy

This section records the repository design agreed for the extension.

## Capability areas live in the architecture, not in long-lived branches

A branch is a scoped increment that merges into `main` in days-to-weeks and is then
retired. A *capability area* — "all things MOM6", "all things seasonal" — is **not**
a branch. Holding a branch open for an entire subsystem produces drift and parallel
universes that never merge.

Instead, the durable structure lives on `main`:

* the variable/source-agnostic forecast engine (`src/mhw/forecast/`)
* the data-source registry (`config/datasets.yml`)
* the per-region derived-data layout (`data/derived/<product>/<region>...`)

Each new variable or data source then arrives as a short increment branch that
plugs an adapter into that structure and merges.

## Active branches

* `feat/sst-forecast` — statistical short-term SST forecast (current focus).
* `feat/mom6-spike` — MOM6 discovery only; deliverable is `catalog_report.md`.

Future increments (MOM6 bottom temperature, MOM6 mixed-layer/other variables,
PSL/NMME seasonal) each get their own scoped branch **when work on them begins** —
not pre-created.

## Repo reality (correct any planning text against this)

* Source lives under `src/mhw/{fetch,climatology,regions,states,forecast}`.
* Derived data is per-region zarr/parquet under `data/derived/` (e.g.
  `climatology/{mu,theta90}_<region>.zarr`, `states_grid/`, `aggregates_region/`,
  `risk/`).
* The grid is regular 0.25° lat/lon (1440×720); cos-lat weights and rasterized
  region masks assume this grid.

---

# Development Roadmap

The roadmap below is the long-term arc. The **near-term execution order has been
revised**: the project enters forecasting through statistical SST first (a quick,
honest answer to collaborators and a low-risk reuse of the existing pipeline),
while MOM6 bottom-ocean-state is de-risked through discovery first and implemented
as a later increment. Bottom-state is no longer the first thing built.

## Phase 0 (Complete)

Current Dashboard

Features: OISST ingestion, MHW detection, historical rankings, percentiles,
regional metrics, API.

Status: Complete.

---

## Track A — Short-Term Statistical SST Forecasting  *(current focus)*

Branch: `feat/sst-forecast`. Target ~2 weeks.

Objective:

Enter Stage 2 with a statistical forecast on the existing OISST pipeline. Answers a
collaborator's literal question — "can you forecast MHW?" — quickly and honestly.

Forecast Horizon:

* Current
* 2 weeks
* 1 month

Methodologies:

* Persistence
* Damped persistence
* AR(1)

Method:

Per-cell anomaly forecast → Gaussian exceedance probability vs θ₉₀ → regional and
area-based products derived from the cell-probability map (Principle 5).

Deliverables:

* Per-cell MHW probability map
* Regional forecast risk panels
* Skill verification (Brier / Brier Skill Score) vs climatology and persistence

Detailed plan: `docs/forecast_extension/sst-forecast-mvp-plan.md` (on the branch).

---

## Track B — MOM6 Discovery, then Bottom Ocean-State Integration

### B1 — Discovery spike  *(current, ~1 week)*

Branch: `feat/mom6-spike`. Discovery only — no implementation.

Objective:

Reduce uncertainty before any bottom-state engineering. Deliverable is
`catalog_report.md` covering all MOM6 facets (not only bottom temperature) and
answering the two real risks: grid strategy and latency.

### B2 — Bottom Ocean-State Integration  *(later increment, post-spike)*

Branch: `feat/bottom-ocean-state` (opened from the spike findings).

Objective:

Introduce fisheries-relevant bottom conditions.

Data Sources (per spike): NOAA MOM6-COBALT-NEP10k preferred; NOAA CEFI; Copernicus
fallback.

Deliverables:

* Bottom temperature climatology and anomaly
* Bottom heatwave detection (reuse the existing Hobday engine)
* Cold pool extent (EBS)
* Historical rankings

Engineering notes carried from the implementation document:

* MOM6-NEP10k is curvilinear ~10 km — decide regrid-to-0.25° vs native (spike).
* Bottom state is a lagged hindcast, not near-real-time — label accordingly.
* Reconcile daily-vs-monthly cadence and the climatology baseline period.
* Bottom-MHW forecasting later reuses the Track A engine (Principle 6).

Target Regions: Eastern Bering Sea, then Gulf of Alaska.

---

## Phase 3

Seasonal Forecast Integration

Objective:

Leverage existing operational climate forecasts.

Data Sources: NOAA PSL, NMME, ECMWF seasonal systems, NOAA Coral Reef Watch.

Forecast Horizon: 1–12 months.

Method:

Forecast SST → MHW probability following the Jacox et al. framework — the same
exceedance construction as Track A, with an ensemble as the forecast input.

Deliverables:

* Seasonal MHW probability
* Forecast percentile rankings
* Ensemble spread visualization

---

## Phase 4

Fishery-Relevant Climate Indicators

Objective:

Bridge climate and fisheries.

Potential Indicators:

* Snow crab thermal habitat risk
* Cold pool persistence
* Pollock thermal exposure
* Cod thermal exposure
* Recruitment-relevant thermal indices

Important: No stock forecasting is attempted. Indicators remain environmental.

---

## Phase 5

Climate Risk Dashboard

Objective:

Convert environmental forecasts into management-relevant risk communication
(Low / Elevated / High / Extreme).

Deliverables: Risk panels suitable for ecosystem report cards.

---

## Phase 6

Decision Support Framework

Long-Term Objective:

Connect Forecast → Impact → Decision.

Potential Applications: harvest control rules, ecosystem report cards, Management
Strategy Evaluation, climate-ready fisheries management.

This phase is research-oriented and requires collaboration with fisheries
scientists.

---

# Scientific Inspiration

Primary References:

* Hobday et al. Marine Heatwave Framework
* Jacox et al. Global Seasonal Forecasts of Marine Heatwaves
* NOAA CEFI Initiative
* NOAA MOM6-COBALT-NEP10k

---

# Near-Term Priority

Current focus is two parallel tracks:

1. Track A — Short-term statistical SST forecasting (`feat/sst-forecast`).
2. Track B1 — MOM6 discovery spike (`feat/mom6-spike`).

Bottom Ocean-State Integration (Track B2, `feat/bottom-ocean-state`) begins only
after the spike has reduced the grid and latency uncertainties.
