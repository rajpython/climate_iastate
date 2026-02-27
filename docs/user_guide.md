# Marine Heatwave State Dashboard — User Guide

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

The dashboard covers five high-latitude marine regions relevant to North Pacific and Arctic fisheries:

| ID | Region | Latitude | Longitude |
|----|--------|----------|-----------|
| GOA | Gulf of Alaska | 54--62 N | 170--130 W |
| EBS | Eastern Bering Sea | 54--62 N | 180--160 W |
| NBS | Northern Bering Sea | 62--67 N | 180--160 W |
| Chukchi | Chukchi Sea | 67--73 N | 180--155 W |
| Beaufort | Beaufort Sea | 69--73 N | 155--130 W |

Select any region from the **sidebar dropdown** on either dashboard page. Arctic regions (Chukchi, Beaufort) are ice-masked in winter, so MHW activity is concentrated in the open-water season.

---

## Getting Started

1. **Pick a region** — use the sidebar dropdown on any page to select one of the five regions.
2. **Check current conditions** — the Operational page shows today's MHW state, event metrics, and risk level.
3. **Explore history** — the Historical page lets you browse 43 years of MHW records (1982--present).

Note: OISST satellite data is typically 1--2 days behind real time, so the most recent date shown may not be today.

---

## Dashboard Pages

### Page 1 — Operational

The Operational page shows the **current and recent** MHW state. It has four tabs:

#### Tab 1: Live MHW Map

A spatial heatmap of the selected region for a given date. Use the date slider to scroll through recent days. Choose from five metrics in the dropdown:

- **Active flag (A)** — binary: is a confirmed MHW in progress at this cell?
- **Intensity (I)** — degrees C above the 90th-percentile threshold
- **Duration (D)** — how many consecutive days the cell has been in MHW
- **Cumulative intensity (C)** — total heat exposure over the event so far (degree-days)
- **Threshold exceedance (x)** — raw SST anomaly above the seasonal threshold (degrees C)

Grid cells under sea ice or on land are masked out. Below the map, summary statistics show the minimum, maximum, and mean values for the selected metric, plus (when viewing Active flag) a count of active cells.

#### Tab 2: Event Metrics

Time-series charts of five regional aggregate metrics, stacked vertically on a shared time axis:

- **Area fraction** — the share of ocean grid cells in the region experiencing an active MHW (0.25 means 25%)
- **Mean intensity (I)** — average intensity across active cells (degrees C)
- **Mean duration (D)** — average event length across active cells (days)
- **Mean cumulative intensity (C)** — average heat exposure (degree-days)
- **Mean onset rate (O)** — average initial warming speed (degrees C per day)

Use the window dropdown (30, 60, 90, or 180 days, or Full record) to control the time range. Shaded bands mark periods when area fraction exceeds 5%, indicating a regional-scale event. Below the chart, summary metrics show event days, peak area fraction, and peak date.

#### Tab 3: Predictability Context

Four stacked subplots on a shared time axis let you visually assess whether large-scale climate regime shifts correspond to changes in heatwave activity:

- **Arctic Oscillation (AO)** — daily bar chart, colored blue (positive) or red (negative). Positive AO tends to confine cold air to the Arctic; negative AO allows cold air outbreaks southward.
- **Pacific Decadal Oscillation (PDO)** — monthly bar chart, colored orange (positive) or blue (negative). Positive PDO is associated with warmer waters in the northeast Pacific.
- **Area fraction** — MHW spatial coverage as a filled line chart, with a dashed line at the 5% regional event threshold.
- **Mean intensity (I)** — average heatwave intensity across active cells (degrees C).

The AO and PDO indices are shown alongside MHW metrics so you can spot correlations — for instance, whether a shift to positive PDO preceded a surge in heatwave coverage. Use the window dropdown (90 days, 180 days, 1 year, or All) to adjust the time range. Below the chart, summary metrics show the latest AO and PDO values, the window-average AO, and the number of MHW event days.

#### Tab 4: Risk Gauge

A composite risk score (0--100) combining the current values of intensity, duration, cumulative intensity, and onset rate, expressed as percentiles against the full historical record (1982--present). The gauge shows:

- **Overall risk score** — weighted average of the four metric percentiles
- **Individual percentile bars** — how extreme each metric is relative to history
- **30-day trend sparkline** — is risk rising or falling?

Higher risk scores mean current conditions are more extreme than most of the historical record.

---

### Page 2 — Historical (1982--2024)

The Historical page lets you explore the full 43-year backfill. It has four tabs:

#### Tab 1: Annual MHW Burden

A bar chart showing total MHW activity per year, measured as cumulative area-fraction-days. Taller bars mean more extensive or longer-lasting heatwaves that year. The 2014--2016 "Blob" years are annotated for reference.

#### Tab 2: Event Explorer

Select a year to see a detailed timeline of all regional MHW events. Each event is shown as a horizontal bar spanning its start and end dates, with color indicating mean intensity. Summary statistics (count, total days, peak intensity) are provided.

#### Tab 3: Metric Distributions

Histograms of daily metric values across the full record, with vertical percentile rulers (25th, 50th, 75th, 90th, 95th). These show how today's conditions compare to the full range of historical variability.

#### Tab 4: Regime Analysis

Box plots of MHW metrics grouped by the four AO/PDO regime combinations (AO+ PDO+, AO+ PDO-, AO- PDO+, AO- PDO-). This reveals whether certain climate regimes are associated with more intense or persistent heatwaves.

---

## Data Sources

| Dataset | Provider | Resolution | Coverage |
|---------|----------|------------|----------|
| **OISST v2.1 (SST + sea ice)** | NOAA (NCEI / CoastWatch ERDDAP) | Daily, 0.25 deg | 1982--present |
| **Arctic Oscillation** | NOAA CPC | Daily | 1983--present |
| **Pacific Decadal Oscillation** | NOAA PSL | Monthly | 1983--present |

All data comes from NOAA sources. SST and sea ice are fetched from the same OISST dataset via ERDDAP — cells with ice concentration above 15% are masked out of the MHW analysis. Source archives extend further back, but the dashboard aligns index data with the OISST backfill period (1982--present). The dashboard refreshes automatically each day at 14:00 UTC, after OISST publishes new observations (typically by 12:30 UTC).

---

## REST API

A programmatic API is available for researchers who want to access the data directly:

- **Swagger UI**: [mhw.iastate.ai/api/docs](https://mhw.iastate.ai/api/docs)
- **ReDoc**: [mhw.iastate.ai/api/redoc](https://mhw.iastate.ai/api/redoc)
- **Health check**: [mhw.iastate.ai/api/health](https://mhw.iastate.ai/api/health)

Key endpoints include:

| Endpoint | Description |
|----------|-------------|
| `GET /api/regions` | List available regions |
| `GET /api/states/region/{region_id}` | Daily aggregate time series for a region |
| `GET /api/events/{region_id}` | Detected MHW events for a region |
| `GET /api/map/mhw?region_id=...&date=...&metric=...` | Grid-level state map for a specific date |
| `GET /api/indices/ao` | Arctic Oscillation daily values |
| `GET /api/indices/pdo` | Pacific Decadal Oscillation monthly values |

All responses are JSON. See the Swagger UI for full parameter details and query options.

---

## Frequently Asked Questions

**How often is the data updated?**
Daily at 14:00 UTC. NOAA typically publishes new OISST data by 12:30 UTC each day.

**What does "area fraction" mean?**
The percentage of ocean grid cells in a region that are currently experiencing a confirmed MHW. An area fraction of 0.25 means 25% of the region is in active heatwave.

**Why do Chukchi and Beaufort show zero activity in winter?**
Those regions are covered by sea ice from roughly November through June. Ice-covered cells are masked out of the MHW analysis because SST under ice is not physically meaningful for heatwave detection.

**What is the "Blob"?**
An exceptionally large and persistent MHW in the northeast Pacific from 2014 to 2016, driven by a persistent atmospheric ridge. It caused widespread marine ecosystem disruption.

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

**Marine Heatwave State Dashboard**
Developed by Dr. Rajesh Singh, Professor, Department of Economics, Iowa State University (rsingh@iastate.edu).

Built with Streamlit, FastAPI, and Plotly.
Powered by NOAA OISST v2.1, CPC Arctic Oscillation, and PSL Pacific Decadal Oscillation data.

Source code: [github.com/rajpython/climate_iastate](https://github.com/rajpython/climate_iastate)

Scientific methodology follows:
Hobday, A.J. et al. (2016). A hierarchical approach to defining marine heatwaves.
*Progress in Oceanography*, 141, 227--238.

---

*Last updated: February 2026*
