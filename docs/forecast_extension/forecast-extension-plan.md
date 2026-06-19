# Marine Heatwave Dashboard — Forecast Extension Plan (Program Roadmap)

> **Role of this doc:** the program-level **roadmap and vision** for the forecast
> extension. For the *why*, see `scientific-rationale.md`; for the bottom-state
> *build plan*, see `forecast-implementation-document.md`; for the SST MVP, see
> `sst-forecast-mvp-plan.md`; for the SST research study, see
> `sst-forecast-research-proposal.md` (+ `forecast-research-program-abstract.md`);
> for the completed bottom-state discovery, see `catalog_report.md`.
> *Last refreshed 2026-06-17 (post mom6-spike merge).*

## Purpose

The current dashboard provides current MHW conditions, historical context, percentile
rankings, regional MHW metrics, and a public API — i.e. it is a **state-monitoring**
platform. The objective of this extension is to evolve it into a **decision-support**
platform for NOAA ecosystem scientists, stock-assessment scientists, fisheries
managers and councils, and climate-risk researchers. Primary use case: Alaska
fisheries — Eastern Bering Sea first, then Gulf of Alaska, Chukchi, Beaufort.

---

# Vision

State Monitoring → Climate-Risk Forecasting → Climate-Informed Fisheries Decision Support.

---

# Guiding Principles

1. **Do not develop new ocean models.** Consume and interpret existing scientific
   products (OISST, Bering10K ROMS, MOM6/CEFI, NOAA PSL, NMME, ECMWF, Copernicus).
2. **Focus on scientific translation:** scientific products → actionable information.
3. **Prioritise fisheries-relevant ocean states:** surface temperature alone is
   insufficient — evolve toward bottom temperature, cold-pool dynamics, sea ice,
   mixed-layer properties, ocean heat content.
4. **Forecast uncertainty must be explicit** — probabilistic wherever possible.
5. **Forecast the primitive, at the grid level.** Forecast the per-cell temperature
   anomaly, convert to an MHW exceedance probability vs the existing θ₉₀, and *derive*
   regional/area products from the cell-probability field. The monitoring aggregates
   (`area_frac`, conditional means) do not bound the forecast.
6. **One variable- and source-agnostic forecast engine.** It forecasts an anomaly
   field vs a threshold field → an exceedance-probability field. Swapping inputs
   (surface temp today; bottom temp or a seasonal ensemble later) reuses the engine;
   only the data adapter changes. New capabilities are adapters, not rewrites.

---

# Engineering & Repository Strategy

- **Capability areas live in the architecture on `main`, not in long-lived branches.**
  A branch is a scoped increment that merges in days-to-weeks and is retired. "All
  things MOM6" / "all things seasonal" are *not* branches.
- Durable structure on `main`: the variable/source-agnostic engine
  (`src/mhw/forecast/`), a data-source registry (`config/datasets.yml`, planned), and
  the per-region derived-data layout (`data/derived/<product>/<region>…`).
- **Repo reality** (correct planning text against this): source under
  `src/mhw/{fetch,climatology,regions,states,forecast}`; derived data per-region
  zarr/parquet under `data/derived/`; the grid is **regular 0.25° lat/lon**
  (1440×720) — cos-lat weights and rasterised region masks assume it.

## Branch status (2026-06-17)

- `feat/sst-forecast` — **merged to `main`.** Statistical SST forecast engine scaffold
  + research proposal. Empirical SST work is **gated** behind the research cell's
  method recommendation.
- `feat/mom6-spike` — **merged to `main`. Discovery complete** (`catalog_report.md`).
- `feat/bottom-ocean-state` — **next branch**, opened from the spike findings, for the
  bottom-state build (see `forecast-implementation-document.md`).

---

# Development Roadmap

Near-term order: SST statistical forecast (quick, honest, low-risk reuse) **and**
bottom-ocean-state (discovery done; build next). Bottom-state is *not* the first thing
built.

## Phase 0 — Current dashboard *(complete)*
OISST ingestion, MHW detection, historical rankings, percentiles, regional metrics, API.

## Track A — Short-term statistical SST forecasting *(engine scaffolded; gated)*
Horizon: current / 2-week / 1-month. Methods: persistence, damped persistence, AR(1).
Per-cell anomaly → Gaussian exceedance vs θ₉₀ → derived regional/area products
(Principle 5). Skill: Brier / BSS vs climatology **and** persistence. Empirical
deployment gated behind the research cell (`sst-forecast-research-proposal.md`).

## Track B — Bottom ocean-state *(discovery complete; build is the next increment)*
- **B1 — Discovery spike** *(complete → `catalog_report.md`)*. Resolved the grid,
  cadence, latency, validation-target, and forecasting questions.
- **B2 — Bottom ocean-state integration** *(`feat/bottom-ocean-state`)*. Bottom
  temperature climatology/anomaly, bottom-MHW detection (reuse Hobday engine), EBS
  cold-pool extent, historical rankings. **Model decision: present BOTH** Bering10K
  ROMS (validated, weekly, 1970–present) **and** MOM6 NEP10k (CEFI; 1993→2025-06,
  `btm_temp`, cold-pool built-in, published forecast arm) as separate labelled options.
  Validation:
  AFSC observed cold-pool index + ACLIM survey-replicated series. See
  `forecast-implementation-document.md`. Regions: EBS first, then GOA (GOA-CLIM).

## Phase 3 — Seasonal forecast integration
Leverage operational seasonal products (NOAA PSL/Jacox, NMME, ECMWF, Coral Reef
Watch; CEFI MOM6 seasonal arm). Horizon 1–12 months. SST → MHW probability via the
same exceedance construction (Jacox et al. framework), ensemble as input. Bottom-state
seasonal forecasting leads with **persistence** (Kearney et al. 2021 finding), LIM as
the beyond-persistence step (Cox & Penland 2026).

## Phase 4 — Fishery-relevant climate indicators
Environmental indicators only (no stock forecasting): snow-crab thermal-habitat risk,
cold-pool persistence, pollock/cod thermal exposure, recruitment-relevant indices.

## Phase 5 — Climate-risk dashboard
Convert environmental forecasts into management-relevant risk communication
(Low / Elevated / High / Extreme); panels suitable for ecosystem report cards.

## Phase 6 — Decision-support framework
Forecast → Impact → Decision: harvest control rules, ESRs, Management Strategy
Evaluation, climate-ready management. Research-oriented; requires fisheries-science
collaboration.

---

# Governing constraint

Nothing forecast-related reaches the dashboard/public API until it is publication-grade
scientifically and econometrically **defensible** (deployment gate: BSS > 0 vs
climatology **and** persistence, calibration, field significance). This applies to SST
and bottom-state alike.

# Scientific inspiration

Hobday et al. (MHW framework); Jacox et al. (global seasonal MHW forecasts); Kearney
et al. 2020/2021 (Bering10K, seasonal predictability); Cox & Penland 2026 (LIM ice
edge); NOAA CEFI; NOAA MOM6-COBALT-NEP10k; Bering10K ROMS / ACLIM.
