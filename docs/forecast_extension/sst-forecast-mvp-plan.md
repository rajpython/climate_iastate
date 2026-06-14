# SST Forecast MVP — Implementation Plan

**Branch:** `feat/sst-forecast`
**Target:** ~2 weeks to a demoable short-term MHW outlook.
**Motivation:** answers the AFSC/Kodiak collaborator's literal question — *"Do you
have an ability to produce MHW forecasts?"* — with something we can show before the
next annual ecosystem-report-card / Council cycle. Honest framing for the email:
*"We've begun testing short-term MHW outlooks."*

---

## Scope

In scope:

* **Current MHW probability**, **2-week outlook**, **1-month outlook**.
* Per-cell **probability map** + **regional outlook** for all five regions
  (goa, ebs, nbs, chukchi, beaufort).
* Statistical baselines only: **persistence**, **damped persistence**, **AR(1)**.

Out of scope (each a separate, later increment that merges into an
engine-agnostic `main` — not this branch):

* Bottom temperature / MOM6 (`feat/mom6-spike` → `feat/bottom-ocean-state`).
* Seasonal / NMME / PSL-Jacox dynamical forecasts.

---

## Key design decision — forecast the primitive at the grid, not the aggregate

The monitoring aggregates (`data/derived/aggregates_region/region_daily_*.parquet`:
`area_frac, Ibar, Dbar, Cbar, Obar`) were built to answer *"what's happening now"*.
Forecasting `area_frac` directly would be a shortcut with real problems: it is
bounded, heavily zero-inflated, and discards spatial structure.

Instead we forecast **from first principles at the grid level** and *derive* the
regional/area products:

```
anomaly_now = SST − μ                                  (per 0.25° cell)
anomaly_fc  = baseline(anomaly_now, φ, σ_eps, lead)    (persistence/damped/AR1)
P(MHW,lead) = P(anomaly_fc > θ₉₀ − μ) = Φ((mean − thr)/σ)   (Gaussian exceedance)
regional    = area-weighted mean of the cell-probability field
```

This yields a **probability map** (the compelling ESR product) *and* a regional
outlook number, and the "what % of the region has a chance" framing falls out of
the cell probabilities (expected area fraction) — we derive it, not forecast it.

This is the Jacox et al. (2022) construction: a continuous forecast mapped to an
exceedance probability against the **same θ₉₀** the monitor already uses.

## Key design decision — variable- and source-agnostic engine

The engine forecasts *an anomaly field* vs *a θ₉₀ field*. Swapping `SST → bottom
temp` (+ `theta90_bottom`) or feeding an NMME ensemble reuses `baselines`,
`exceedance`, and `regional` unchanged — only `io` adapters differ. Building it
this way now makes the bottom-temperature and seasonal forecasts near-free later,
and is the reason those are *increments on `main`*, not standing branches.

---

## Inputs — all already on disk (nothing new to ingest)

| Input | Source |
|-------|--------|
| μ(doy), θ₉₀(doy) per region | `data/derived/climatology/{mu,theta90}_*.zarr` (loader: `states.update_states._load_climatology`) |
| daily SST | OISST year cache (`climatology.build_mu_theta.fetch_year`) |
| region mask + cos-lat weights | `mhw.regions.masks`, `mhw.regions.weights` |
| ice mask | OISST internal ice, same convention as monitoring |

---

## Module map (`src/mhw/forecast/`)

| File | Role | Status |
|------|------|--------|
| `baselines.py` | persistence / damped persistence / AR(1) fit + forecast | **implemented** |
| `exceedance.py` | Gaussian anomaly → MHW probability | **implemented** |
| `regional.py` | area-weighted aggregation of the prob field | **implemented** |
| `io.py` | data adapters (the only source-specific layer) | **stub — MVP wiring** |
| `backtest.py` | Brier / BSS + rolling-origin harness | scores done; harness stub |
| `cli.py` | `mhw-forecast` entry point | arg surface done; compute stubbed |

---

## Build order

1. Implement `io` adapters against existing loaders (climatology, SST cache, mask/weights).
2. Wire `cli.main`: load → `fit_ar1` on training window → forecast leads → exceedance map → regional series → write outputs (+ optional plot).
3. Implement `backtest.rolling_origin_backtest` (leakage-free) and report Brier Skill Score vs **climatology** and **persistence** per region and lead. Ship only leads/regions that beat both.
4. Dashboard "Outlook" panel — probability map + regional gauge, understated copy, explicit uncertainty.
5. API: versioned `/v1` forecast endpoint mirroring the existing route style.

## Success criteria

1. `mhw-forecast` produces a probability map + regional outlook for current / 14-day / 30-day leads, all regions.
2. Backtest shows positive Brier Skill Score over climatology **and** persistence for at least the 14-day lead (honestly report where it does not).
3. Dashboard panel live with explicit uncertainty and no implication of dynamical skill.
4. API endpoint documented under `/v1`.

---

## Decision log

* **Grid-up, not aggregate-derived** — better science, better product (a map), and
  reuses the existing θ₉₀; the monitoring aggregates do not bound the forecast.
* **Engine is variable/source-agnostic** — so bottom-temp and seasonal are future
  increments, not rewrites and not long-lived branches.
* **Baselines first** — they are the bar any future dynamical product must clear;
  ship them, measure skill honestly, then decide what (if anything) to add.
