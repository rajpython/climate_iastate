# Dashboard Guide
*Alaska Marine Ecosystems Dashboard — Climate • Ocean • Ecosystems • Fisheries*

This guide explains what the Alaska Marine Ecosystems Dashboard is, how it is organised, what
it currently covers, and where to find each indicator. It is the platform-level orientation;
the **Marine Heatwave Guide** and the **Bering Sea Bottom-State Guide** document specific
indicators in depth.

---

## Purpose

The dashboard brings public, Alaska-shelf ocean and ecosystem information into one place:
climate, ocean, ecosystem, and fisheries indicators for Alaska marine ecosystems, integrating
observed surveys, operational products, and regional ocean models. It surfaces observed and
modelled **state** — what conditions are and have been — for scientists, managers, and the
interested public. Forecast indicators are under development and will be integrated into the
relevant sections as they mature.

## Current coverage

Two indicator areas are implemented today:

- **Alaska-wide Climate — Marine Heatwaves.** Operational (live and recent) and historical
  (1982–present) marine-heatwave state across the Alaska shelf seas, derived from NOAA OISST.
- **Bering Sea — Bottom State.** The cold-pool area index and bottom-temperature conditions
  from the AFSC summer bottom-trawl survey, a derived cold-pool **southern-extent** position
  indicator, model validation and model comparison (Bering10K ROMS, CEFI MOM6 NEP), and
  catch–environment relationships.
- **Gulf of Alaska — Bottom Temperature & Catch.** The Gulf shelf has **no cold pool** (deep
  water, no winter sea ice), so the product is bottom-temperature *conditions*: the official
  AFSC summer bottom-trawl survey bottom temperature (region-wide and by subarea, biennial),
  validated against CEFI MOM6 NEP sampled at the survey hauls, plus catch–environment
  relationships for the Gulf's key groundfish. Bering10K ROMS is out of the Gulf domain, so the
  Gulf is MOM6-only and its model panels are labelled as less-validated outside the Bering.

- **Aleutian Islands — Bottom Temperature & Catch.** Like the Gulf, the Aleutian shelf has no
  cold pool, so it surfaces the official AFSC survey bottom temperature (region-wide and by
  Western / Central / Eastern Aleutian subarea, 1991–2024), validated against CEFI MOM6 NEP at
  the survey hauls, plus catch–environment relationships for the chain's key species (Atka
  mackerel, Pacific ocean perch, Pacific cod). MOM6-only, labelled less-validated.

- **Arctic (Chukchi & Beaufort) — Bottom Temperature (model-only).** The Arctic shelves have no
  AFSC bottom-trawl survey, so there is no observed index, catch, or in-region validation — these
  pages show only the CEFI MOM6 NEP modelled bottom temperature over the ≤ 200 m shelf, prominently
  labelled **model-only / unvalidated here**.

Additional ocean-health indicators and forecast indicators will be added over time.

## Planned expansion

Coverage will broaden along several lines: Gulf of Alaska, Aleutian Islands, and Arctic
(Chukchi and Beaufort) ecosystem indicators; additional ocean-health variables (for example
dissolved oxygen and aragonite saturation) where survey and model coverage allow; and forecast
indicators integrated into the relevant Alaska-wide and regional sections as they become
available. The platform currently emphasizes observed and modelled ecosystem state; forecast
indicators are developed separately and surfaced here as they mature.

## Navigation structure

The top navigation is organised so that cross-cutting Alaska-wide indicators sit alongside
region-specific ecosystem sections, with research and documentation kept separate.

| Section | Contents |
|---|---|
| **Overview** | Orientation and current coverage |
| **Alaska-wide Climate** | **Marine Heatwaves** → Operational and Historical views (region-selectable) |
| **Bering Sea** | **Cold Pool & Bottom Temperature**, **Model Comparison**, **Cold-Pool Position**, and **Catch × Bottom State** |
| **Gulf of Alaska** · **Aleutian Islands** | **Bottom Temperature** and **Catch × Bottom State** (no cold pool; MOM6-only) |
| **Arctic** | **Bottom Temperature** — Chukchi & Beaufort, MOM6 model-only (no survey/validation) |
| **Research** | Recent papers, research summaries, forecast development, technical notes, and project research (in preparation) |
| **Guides** | This guide, the Marine Heatwave Guide, and the Bering Sea Bottom-State Guide |

**Alaska-wide Climate** holds cross-cutting climate indicators. Marine heatwaves are the first;
the Operational and Historical views are selected at the top of the page. Future Alaska-wide
indicators (for example sea-surface-temperature anomalies or climate modes) will appear as
additional entries here.

**Bering Sea** groups the region's bottom-state indicators. One region selector spans the
eastern Bering shelf, the northern Bering shelf, and the Bering slope; the panels adapt to each
area. See the Bering Sea Bottom-State Guide for detail.

**Gulf of Alaska** carries bottom-temperature conditions and catch–environment relationships
for the Gulf shelf. The Gulf has no cold pool, so it leads with the observed survey bottom
temperature (region-wide and by subarea), MOM6 validation at the survey hauls, and catch for the
Gulf's key groundfish. **Aleutian Islands and Arctic** are reserved as distinct ecosystem
sections; each has observed survey and/or model coverage being prepared, and the sections are
present so that indicators can be added without reorganising the platform.

**Research** consolidates literature, summaries, methodology, and forecast development into a
single page until enough material exists to warrant dedicated pages.

## API access

A programmatic REST API exposes the underlying data for the implemented indicators.

- Swagger UI: [marine.iastate.ai/api/docs](https://marine.iastate.ai/api/docs)
- ReDoc: [marine.iastate.ai/api/redoc](https://marine.iastate.ai/api/redoc)
- Health check: [marine.iastate.ai/api/health](https://marine.iastate.ai/api/health)

Data endpoints are versioned under `/api/v1/`; responses are JSON with snake_case fields. The
Marine Heatwave Guide lists the marine-heatwave endpoints in detail.

## Frequently asked questions

**What does the dashboard show — observations, models, or forecasts?**
Observed and modelled **state**. Observations come from NOAA satellite SST and AFSC surveys;
modelled fields come from regional ocean models. Forecast indicators are under development and
are not yet shown.

**How current is the data?**
The marine-heatwave indicators update daily (NOAA OISST is typically 1–2 days behind real
time). Survey-based Bering Sea indicators are annual and lagged (recent-historical), not
near-real-time.

**Which regions are covered?**
Marine heatwaves span the five Alaska shelf seas (Gulf of Alaska, eastern and northern Bering,
Chukchi, Beaufort). Bottom-state indicators cover the Bering Sea (eastern, northern, slope),
the Gulf of Alaska, the Aleutian Islands, and the Arctic (Chukchi & Beaufort, model-only).

**Where do I go for methods and definitions?**
The Marine Heatwave Guide covers the Hobday-style definition, the operational and historical
views, climatology and thresholds, and the API. The Bering Sea Bottom-State Guide covers the
cold pool, bottom temperature, survey index, model validation and comparison, and
catch–environment relationships.

## Data sources & attribution

All products are public and free; each panel also carries a short source note in its footer.

- **Marine heatwaves** — NOAA OISST v2.1 (sea-surface temperature); climate indices (AO/PDO)
  from NOAA.
- **Observed cold-pool *area* index** (≤ 2/1/0/−1 °C) — NOAA AFSC `afsc-gap-products/coldpool`
  (Zenodo DOI 10.5281/zenodo.16915337), spatially interpolated from the survey.
- **Per-haul survey temperatures and catch** — NOAA **FOSS** REST API
  (`apps-st.fisheries.noaa.gov/ods/foss/…`), the operational copy of the AFSC bottom-trawl
  survey database. Used for model validation, the southern-extent position, and catch.
- **Bering10K ROMS** — NOAA PMEL / University of Washington, ACLIM program.
- **CEFI MOM6 NEP** — NOAA GFDL / PSL, Climate, Ecosystems & Fisheries Initiative (CEFI).

The Bering Sea Bottom-State Guide gives the per-product detail; survey temperatures and the
cold-pool index come from the *same* AFSC surveys, distributed through two channels (FOSS is
current; the coldpool package is the official, curated index and lags).

---

*Developed at Iowa State University using NOAA observational and modelling products.*
