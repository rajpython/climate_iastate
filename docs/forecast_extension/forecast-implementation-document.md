# Bottom Ocean-State — Implementation Plan

> **Role of this doc:** the **build plan** for the bottom-ocean-state increment
> (`feat/bottom-ocean-state`), updated to the discovery findings in
> `catalog_report.md`. The SST MVP implementation lives in `sst-forecast-mvp-plan.md`
> (not duplicated here). Program roadmap: `forecast-extension-plan.md`; rationale:
> `scientific-rationale.md`. *Last refreshed 2026-06-17 (post-spike).*

## Status & sequencing

- **SST forecast (Track A):** engine math implemented + tested; data adapters, CLI
  wiring, backtest harness, dashboard panel and API endpoint are the remaining MVP
  steps. **See `sst-forecast-mvp-plan.md`** — not repeated here.
- **Bottom ocean-state (Track B2):** discovery complete (`catalog_report.md`). This
  doc is the build plan. It does **not** involve forecasting — it creates the
  environmental foundation; bottom-temperature *forecasting* is a later step that
  reuses the Track A engine (lead with **persistence**, per Kearney et al. 2021).

---

# Scientific motivation

Many Alaska fisheries respond to **bottom temperature, cold-pool dynamics, and shelf
thermal conditions** more directly than to SST. This increment extends the dashboard
into the water column. (Full rationale: `scientific-rationale.md`.)

---

# Model decision — present BOTH sources as labelled options

Per the 2026-06-17 decision, surface **two** models side-by-side rather than pick one:

| Source | Period / cadence | Grid | Role | Notes |
|--------|------------------|------|------|-------|
| **Bering10K ROMS** (`B10K-K20_CORECFS`) | weekly, **1970–present**, ~3×/yr refresh | ~10 km curvilinear | validated EBS/Bering; self-service hindcast + persistence | PMEL THREDDS/ERDDAP; daily physics-only variant exists |
| **MOM6 NEP10k** (CEFI) | **1993→2025-06** hindcast (rel. r20250912) + published **forecast** arm | regular lat/lon (815×341) | cold-pool product built-in, AFSC-validated; `btm_temp`; Baja→Chukchi | PSL THREDDS / AWS S3 / GCS; *fresher than Bering10K*; forecast-skill validation for Bering still open |

The source-agnostic engine makes this cheap: **two `io` adapters** feed the same
`exceedance`/`regional` machinery. Each dashboard panel is **labelled** with
provenance, period, and lagged/recent-historical status; where the two models
**disagree, that divergence is the uncertainty signal**.

---

# Engineering realities (resolved in discovery — see `catalog_report.md`)

- **Grid:** **Bering10K** is ~10 km **curvilinear** → regrid to the existing 0.25° grid via
  `pyresample`/`scipy` (repo is pyenv/pip, **no conda** → `xesmf`/`esmpy` avoided). **MOM6
  NEP `regrid` product is already REGULAR** lat/lon (815×341) — a simple regular→0.25°
  block-average, no curvilinear handling (a `raw` curvilinear MOM6 product also exists).
  Bottom temperature is a 2-D field. ⬜ confirm `pyresample` install + a sanity check; ⬜ add
  a 1-D-coord branch to `loader.load_bottom_temp` for the regular MOM6 product.
- **Latency:** bottom state is a **lagged / recent-historical** product (Bering10K to
  ~2024-08; **MOM6 NEP to 2025-06** — corrected, *fresher* than Bering10K), **not**
  near-real-time. Dashboard copy and API must say so.
- **Cadence / baseline:** Bering10K is **weekly** → build a **weekly** bottom-temp
  climatology/threshold (or use the daily physics-only variant). Reconcile the
  baseline period (SST climatology is 1991–2020 daily DOY; ROMS hindcast from 1970,
  MOM6 from 1993) and document any divergence.

---

# Directory structure (extend the actual repo; do not invent a parallel tree)

```
src/mhw/
    fetch/ climatology/ regions/ states/ forecast/   # existing
    bottom/                                           # NEW: ingest, regrid, bottom climatology, cold pool
data/derived/
    climatology/ states_grid/ aggregates_region/ risk/   # existing patterns
    bottom_temp/  cold_pool/                              # NEW per-region products
```

---

# Tasks

1. **Confirm sources** — exact Bering10K Level-2 bottom-temp var name (likely
   `temp_bottom5m`) + live PMEL catalog path; confirm MOM6 NEP `tob` in the THREDDS
   variable table and whether the forecast arm carries it.
2. **Ingest + regrid module** (`src/mhw/bottom/`) — open remote dataset, subset region,
   select variable, **regrid to 0.25°** (`pyresample`/`scipy`), cache. One adapter per
   source. Deps: xarray, dask, netCDF4, pyresample.
3. **Bottom climatology** — weekly (Bering10K) reference period; document divergence
   from the 1991–2020 SST baseline.
4. **Bottom anomaly** — bottom temperature − bottom climatology.
5. **Bottom heatwave detection** — reuse the Hobday engine on bottom temp (duration,
   intensity, max intensity, cumulative intensity).
6. **Cold-pool metrics** — EBS; area where bottom temp **≤ 2 °C** (also 1/0/−1 °C);
   total area, historical percentile, time series.
7. **API endpoints** (under `/v1`) — `/v1/bottom-temperature`, `/v1/bottom-anomaly`,
   `/v1/bottom-heatwave`, `/v1/cold-pool`; per source where both are surfaced.
8. **Dashboard panels** — Bottom Conditions: anomaly, bottom-MHW category, cold-pool
   extent, percentile — **labelled lagged**, with the two sources presented side-by-side.

---

# Validation

1. **Cold pool vs AFSC observed index** *(the credibility win)* — modeled EBS cold-pool
   extent vs AFSC observed summer bottom-trawl index (Zenodo 10.5281/zenodo.16915337),
   plus the **ACLIM survey-replicated** series. Benchmark against the 2025 Frontiers
   EBS bottom-temperature skill assessment.
2. **Surface vs bottom heatwave** for the 2014–2016 Blob, 2019 Bering event, and
   2023–2024 — document where surface and bottom diverge.

# Success criteria

1. Both sources ingested + regridded automatically. 2. Bottom climatologies generated.
3. Bottom heatwaves computed (Hobday engine). 4. Cold-pool metrics validated against
the AFSC observed index. 5. Dashboard panels operational, **labelled lagged**, both
sources side-by-side. 6. API documented under `/v1`. Bottom-temperature *forecasting*
is a later step (persistence-first) — not part of this increment.
