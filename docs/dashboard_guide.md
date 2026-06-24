# Dashboard Guide
*Alaska Marine Ecosystem Dashboard — Climate • Ocean • Ecosystems • Fisheries*

This guide explains what the Alaska Marine Ecosystem Dashboard is, how it is organised, what
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

The Gulf of Alaska, Aleutian Islands, and Arctic (Chukchi and Beaufort) ecosystem sections are
**under development**. Additional ocean-health indicators and forecast indicators will be added
over time.

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
| **Gulf of Alaska** · **Aleutian Islands** · **Arctic** | Distinct ecosystem sections — under development |
| **Research** | Recent papers, research summaries, forecast development, technical notes, and project research (in preparation) |
| **Guides** | This guide, the Marine Heatwave Guide, and the Bering Sea Bottom-State Guide |

**Alaska-wide Climate** holds cross-cutting climate indicators. Marine heatwaves are the first;
the Operational and Historical views are selected at the top of the page. Future Alaska-wide
indicators (for example sea-surface-temperature anomalies or climate modes) will appear as
additional entries here.

**Bering Sea** groups the region's bottom-state indicators. One region selector spans the
eastern Bering shelf, the northern Bering shelf, and the Bering slope; the panels adapt to each
area. See the Bering Sea Bottom-State Guide for detail.

**Gulf of Alaska, Aleutian Islands, and Arctic** are reserved as distinct ecosystem sections.
Each has observed survey and/or model coverage being prepared; the sections are present so that
indicators can be added without reorganising the platform.

**Research** consolidates literature, summaries, methodology, and forecast development into a
single page until enough material exists to warrant dedicated pages.

## API access

A programmatic REST API exposes the underlying data for the implemented indicators.

- Swagger UI: [mhw.iastate.ai/api/docs](https://mhw.iastate.ai/api/docs)
- ReDoc: [mhw.iastate.ai/api/redoc](https://mhw.iastate.ai/api/redoc)
- Health check: [mhw.iastate.ai/api/health](https://mhw.iastate.ai/api/health)

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
Chukchi, Beaufort). Bottom-state indicators currently cover the Bering Sea; other ecosystem
sections are under development.

**Where do I go for methods and definitions?**
The Marine Heatwave Guide covers the Hobday-style definition, the operational and historical
views, climatology and thresholds, and the API. The Bering Sea Bottom-State Guide covers the
cold pool, bottom temperature, survey index, model validation and comparison, and
catch–environment relationships.

---

*Developed at Iowa State University using NOAA observational and modelling products.*
