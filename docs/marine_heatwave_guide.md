# Marine Heatwave Guide
*Alaska Marine Ecosystems Dashboard — Climate • Ocean • Ecosystems • Fisheries*

A detailed guide to the **Alaska-wide marine-heatwave (MHW) indicators** — the **Marine
Heatwaves** entry under the **Alaska-wide Climate** section, with its **Operational** and
**Historical** views. It covers the Hobday-style definition, the two views and their panels,
the AO/PDO context and risk gauge, the climatology and thresholds, the data sources, and the
REST API.

For platform orientation — what the dashboard is and how it is organised — see the **Dashboard
Guide**. For the Bering Sea bottom-state indicators (cold pool, bottom temperature, model
validation, catch–environment relationships) see the **Bering Sea Bottom-State Guide**.

## What is a Marine Heatwave?

A **marine heatwave (MHW)** is a prolonged period of unusually warm ocean surface temperatures. Following the Hobday et al. (2016) framework, an MHW is declared when sea surface temperature (SST) exceeds the local 90th-percentile threshold — based on a 1991--2020 baseline — for at least **5 consecutive days**. Brief cool dips of 2 days or fewer are bridged so that a single continuous event is not artificially split.

Once confirmed, each heatwave is tracked with four metrics:

| Metric | Symbol | Meaning |
|--------|--------|---------|
| **Intensity** | I | How far SST exceeds the threshold (degrees C) |
| **Duration** | D | How many days the event has persisted |
| **Cumulative intensity** | C | Total heat exposure over the event (degree-days) |
| **Onset rate** | O | How rapidly SST rose at the start of the event (degrees C per day) |

These metrics are computed at every 0.25-degree ocean grid cell and then aggregated to regional summaries.

---

## Regions

The dashboard covers five marine regions around Alaska, spanning the sub-arctic North Pacific to the Arctic Ocean:

| ID | Region | Latitude | Longitude |
|----|--------|----------|-----------|
| GOA | Gulf of Alaska | 54--62 N | 170--130 W |
| EBS | Eastern Bering Sea | 54--62 N | 180--160 W |
| NBS | Northern Bering Sea | 62--67 N | 180--160 W |
| Chukchi | Chukchi Sea | 67--73 N | 180--155 W |
| Beaufort | Beaufort Sea | 69--73 N | 155--130 W |

These five regions follow the standard regionalisation used by NOAA's Alaska Fisheries Science Center and the North Pacific Fishery Management Council; the Northern Bering Sea is kept distinct from the Eastern Bering Sea as a biogeographic transition zone with its own sea-ice regime. Arctic regions (Chukchi, Beaufort) are ice-masked in winter, so heatwave activity concentrates in the open-water season. SST observations (OISST) typically lag real time by 1–2 days. Region selection and navigation are described in the Dashboard Guide.

---

## Interpreting Marine Heatwave Metrics

Each metric answers a different ecological question; read together they describe how severe, how long, and how widespread an event is.

- **Intensity (I)** — how far SST sits above the local 90th-percentile threshold (°C). Higher intensity means greater thermal stress relative to what the ecosystem is adapted to at that time of year. Because the reference is the threshold rather than the mean, these values are conservative.
- **Duration (D)** — how many consecutive days the event persists. Persistence often matters more than peak warmth: prolonged exposure depletes energy reserves, shifts distributions, and disrupts spawning and prey availability.
- **Cumulative intensity (C)** — total heat exposure (degree-days): intensity integrated over duration. This is the best single measure of overall ecological burden because it captures both how warm and how long; the 2014–2016 northeast Pacific event ranks extreme on it.
- **Area fraction** — the share of a region under a confirmed MHW at a given time. A low value is a localised event; a high value is a region-wide event with broader ecological consequences. Above roughly 5% is treated here as a regional-scale event.

A short, intense, localised spike and a moderate but prolonged, region-wide event are ecologically very different even when peak intensity is similar — which is why the dashboard reports all four metrics rather than a single number.

---

## The Operational and Historical views

Both views sit under **Alaska-wide Climate → Marine Heatwaves** and are region-selectable.

### Operational

Current and recent MHW state, in four panels:

- **Live MHW map** — the selected metric (active flag, intensity, duration, cumulative intensity, or threshold exceedance) mapped across the region for a chosen date; land and ice-covered cells are masked.
- **Event metrics** — regional time series of area fraction and the mean intensity, duration, cumulative intensity, and onset rate across active cells, with regional-scale events (area fraction > 5%) shaded.
- **Predictability context** — the Arctic Oscillation (AO) and Pacific Decadal Oscillation (PDO) shown alongside MHW coverage and intensity, to assess visually whether climate-mode shifts coincide with changes in heatwave activity. This is correlation context, not prediction.
- **Risk gauge** — a composite 0–100 score combining the current intensity, duration, cumulative-intensity, and onset-rate percentiles against the region's full 1982–present record, with a 30-day trend. Higher means more extreme than most of the historical record.

### Historical (1982–present)

The full record, in four panels:

- **Annual burden** — one bar per year (peak area fraction, mean area fraction, or event days), coloured by where the year ranks in the region's own history (top 10% / 50–90th / bottom 50%). The 2014–2016 *Pacific Blob* is marked for context; colouring is quantile-based, so the Blob reads as extreme where it actually was (GOA, EBS) and unremarkable where it was not (Chukchi, Beaufort).
- **Event explorer** — a chosen year's area fraction, intensity, and duration over time, with regional-event spans shaded and a monthly summary.
- **Distributions** — histograms of daily metric values with percentile rulers, placing current conditions in the full range of historical variability.
- **Regime analysis** — MHW metrics compared across the four AO/PDO phase combinations, computed over **event days only** (area fraction > 5%) so the comparison is not diluted by the many quiet days. The summary reports each regime's event rate and median metrics; in the Gulf of Alaska, warm-phase PDO typically shows roughly twice the event rate of cool-phase PDO.

---

## Data Sources

| Dataset | Provider | Resolution | Coverage |
|---------|----------|------------|----------|
| **OISST v2.1 (SST + sea ice)** | NOAA (NCEI / CoastWatch ERDDAP) | Daily, 0.25 deg | 1982--present |
| **Arctic Oscillation** | NOAA CPC | Daily | 1983--present |
| **Pacific Decadal Oscillation** | NOAA PSL | Monthly | 1983--present |

All data comes from NOAA sources. SST and sea ice are fetched from the same OISST dataset via ERDDAP — cells with ice concentration above 15% are masked out of the MHW analysis. AO is retained from \~1950 and PDO from 1854 so the Regime Analysis tab covers both phases (PDO has been in a sustained negative phase since 2020, so the full record is essential for seeing PDO+ regimes).

In production the dashboard refreshes automatically each day at 14:00 UTC, after OISST publishes new observations (typically by 12:30 UTC). Local development copies are extended via `bash scripts/monthly_refresh.sh` — see the project README.

---

## REST API

A programmatic API is available for researchers who want to access the data directly:

- **Swagger UI**: [marine.iastate.ai/api/docs](https://marine.iastate.ai/api/docs)
- **ReDoc**: [marine.iastate.ai/api/redoc](https://marine.iastate.ai/api/redoc)
- **Health check**: [marine.iastate.ai/api/health](https://marine.iastate.ai/api/health)

All data endpoints are versioned under `/api/v1/`. The service-level health check stays unversioned at `/api/health`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/regions` | List available regions |
| `GET /api/v1/regions/{region_id}` | Single region metadata (date range, row count) |
| `GET /api/v1/regions/{region_id}/states` | Daily aggregate time series |
| `GET /api/v1/regions/{region_id}/events` | Detected MHW events for a region |
| `GET /api/v1/regions/{region_id}/map?date=...&metric=...` | Grid-level state map for a specific date |
| `GET /api/v1/indices/ao` | Arctic Oscillation daily values |
| `GET /api/v1/indices/pdo` | Pacific Decadal Oscillation monthly values |
| `GET /api/health` | Service health (unversioned) |

All responses are JSON with snake_case field names. The regional aggregate fields are `area_frac`, `mean_intensity`, `mean_duration`, `cumul_intensity`, and `onset_rate` (internally these correspond to the Hobday-paper symbols I, D, C, O). Categorical fields use typed enums (`MapMetric`, `IndexName`, `IndexFrequency`, `RiskLevel`) so OpenAPI consumers can codegen against them. See the Swagger UI for full parameter details and query options.

**Data conventions for monthly products** (release note, applies to every monthly series this platform publishes — API, dashboard, and sealed data deliveries):

- **Monthly records are keyed by `date`, set to the first day of the month (`YYYY-MM-01`).** There is no `year_month` field anywhere; if you built a shim converting `year_month`, retire it (convention settled 2026-07-22).
- **An incomplete current month is excluded from monthly series.** A "monthly" mean computed from a few days of a still-running month is not a monthly value — early in a month it can plot as a spurious collapse (or spike). Monthly series shown or published by this platform therefore only use complete months (tables that do show the running month label it as partial); daily endpoints always carry the freshest data.
- **`onset_rate` (O) is signed.** It can be legitimately negative — routinely so in the Chukchi and Beaufort — so consumers should not clamp, drop, or log-transform negative values.

---

## Frequently Asked Questions

**How often is the data updated?**
Daily at 14:00 UTC. NOAA typically publishes new OISST data by 12:30 UTC each day.

**What does "area fraction" mean?**
The percentage of ocean grid cells in a region that are currently experiencing a confirmed MHW. An area fraction of 0.25 means 25% of the region is in active heatwave.

**Why do Chukchi and Beaufort show zero activity in winter?**
Those regions are covered by sea ice from roughly November through June. Ice-covered cells are masked out of the MHW analysis because SST under ice is not physically meaningful for heatwave detection.

**What is the "Blob"?**
An exceptionally large and persistent MHW in the northeast Pacific from 2014 to 2016, driven by a persistent atmospheric ridge. It caused widespread marine ecosystem disruption. On the Annual Burden chart, the period is labeled with a *Pacific Blob* text annotation as historical context, but the bar **coloring is not Blob-specific**: it is quantile-based on the displayed metric, so the Blob shows up red automatically on regions where it actually was extreme (GOA, EBS) and stays blue on regions where it wasn't (Chukchi, Beaufort). The label is a calendar marker; the color is the verdict.

**Can I download the raw data?**
Use the REST API endpoints to retrieve daily aggregate and grid-level data in JSON format. The full backfill dataset (1982--present) is available via the API.

**What does a risk score of 80 mean?**
The current MHW conditions are more extreme than roughly 80% of all historical observations (1982--present) for that region.

**How is the climatological baseline calculated?**
For each day of the year at each grid cell, SST values from 1991--2020 within an 11-day centered window are pooled. The mean and 90th percentile of this pool become the climatological reference and detection threshold, respectively.

**Why do some metrics show 0 even during warm periods?**
MHWs require 5 consecutive days above the 90th-percentile threshold before being confirmed. Candidate warm spells of 1--4 days are tracked internally, but all reported metrics (I, D, C, O) remain zero until the 5-day confirmation criterion is met.

**What is "gap bridging" and why does a heatwave continue through brief cool dips?**
If SST dips below the threshold for 2 days or fewer, the event is bridged — treated as a single continuous event rather than split into two separate events. This follows the Hobday et al. (2016) protocol to prevent artificial fragmentation of one physical heatwave.

**How is intensity measured — above the mean or above the threshold?**
In this dashboard, intensity is the anomaly above the **90th-percentile threshold**, not the climatological mean. This is a more conservative definition and yields smaller intensity values than a mean-referenced approach. Keep this distinction in mind when comparing with other MHW studies.

**Why do risk scores change even if conditions seem similar?**
Risk scores are percentile-based against each region's full 1982--present distribution; they are region-specific but not explicitly season-conditioned. A given intensity value may rank as "normal" in the Gulf of Alaska but "extreme" in the Chukchi Sea.

**Why are AO and PDO included on the Predictability tab?**
The Arctic Oscillation and Pacific Decadal Oscillation are large-scale climate modes that influence North Pacific SST patterns. They are shown alongside MHW metrics for regime context — researchers can visually assess whether phase shifts in AO or PDO coincide with changes in heatwave coverage and intensity. They provide correlation context, not direct predictions.

---

## Technical Details

- **Grid resolution**: 0.25 degrees latitude/longitude (OISST native grid)
- **MHW confirmation**: 5 consecutive days above the 90th-percentile threshold
- **Gap bridging**: Cool dips of 2 days or fewer are bridged into a single event
- **Baseline period**: 1991--2020 (30-year climate normal)
- **Intensity reference**: Anomaly above the 90th-percentile threshold
- **Regional aggregation**: Area-weighted (cosine of latitude) averages across active cells

---

## Credits

**Alaska Marine Ecosystems Dashboard**
Developed by Rajesh Singh, Professor, Department of Economics, Iowa State University (rsingh@iastate.edu).

Built with Streamlit, FastAPI, and Plotly.
Powered by NOAA OISST v2.1, CPC Arctic Oscillation, and PSL Pacific Decadal Oscillation data.

Source code: [github.com/rajpython/climate_iastate](https://github.com/rajpython/climate_iastate)

Scientific methodology follows:
Hobday, A.J. et al. (2016). A hierarchical approach to defining marine heatwaves.
*Progress in Oceanography*, 141, 227--238.

---

*Last updated: May 2026*
