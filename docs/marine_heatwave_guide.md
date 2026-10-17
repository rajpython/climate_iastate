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

## The heatwave record: vintage #7 (D1)

**What the board shows.** The heatwave pages and the `/v1` API read the sealed record **vintage #7 (D1)**
(`mhw-hobday-consecutive-20261009-icegap-d1`), certified from 1 January 1982 to **31 August 2026**. It
replaces vintage #6. The event rules are unchanged: five-day qualification and joins of at most two days.

**What D1 changed.**
- **Ice-outage days are no longer filled.** NOAA's OISST v2.1 omits its sea-ice field on 171 days (for
  example April–June 2016 and January–February 2017). Vintage #6 filled ice on those days from the days
  either side. D1 does not. A cell without an ice observation on an outage day is *unknown*, unless SST is present and no ice above 15 % is
  observed on every other day of its record (and the cell is not barred). That exemption is an inference from the absence of observed
  ice, not verified open water.
- **A fixed reporting domain.** 142 cells whose satellite ice record is inconsistent over time (for
  example, blank before 2005 and routinely ice-covered after) are excluded from every regional figure,
  in every season: SEBS 18, NBS 27, WGOA 34, EGOA 11, AI East 2, Chukchi 37, Beaufort 13. Area is
  always a share of the same retained domain.
- **Observed ice comes first.** A cell observed with more than 15 % ice is ice-covered even if SST is
  above 2 °C. The old "SST > 2 °C means open water" override is retired.

**What "unknown" means.** Every zone-day splits into three exclusive parts: scorable water, observed ice,
and **unknown**. Unknown is absent input + missing SST + unknown ice + a missing threshold. The board
draws it as a grey band under every area chart; the tooltip splits unknown ice into cell runs or
regional intervals and the global outage days.
- **More than 25 % unknown:** the day is *incomplete coverage*, hatched, and never shown as zero. If
  nothing in the zone could be scored, the area line has a gap.
- **25 % or less unknown:** the area is drawn as computed. Observed ice is a real zero, labelled
  "ice-covered". A zero day with more unknown than the zone's constant never-observed floor reads
  "none detected in the assessed area", not "no heatwave".
- **Months** use eligible days only (unknown ≤ 25 %). A month with 11 or more rejected days, or 5 or
  more in a row, is incomplete and shown as missing, never as zero. Annual figures, distributions,
  regimes and risk percentiles also use eligible days only.

**Why the record stops at 31 August 2026.** D1 is certified to that date and its code refuses later
dates. No daily rule has been validated for new days, so daily heatwave updates are **paused**. The
OISST source files keep being collected. Updates resume when a validated daily extension is adopted.

**The 2016 southeast Bering spring.** The Historical page (SEBS, 2016) carries a separate evidence panel
for the outage of 18 April – 30 June 2016. It shows the observed + externally corroborated area as a
headline, an estimated area as a sensitivity, and unresolved coverage. It is a documented analysis
beside the record, not a revision of it; every gap day remains incomplete coverage.

---

## What is a Marine Heatwave?

A **marine heatwave (MHW)** is a prolonged period of unusually warm ocean surface temperatures. Following the Hobday et al. (2016) framework, an MHW is declared when sea surface temperature (SST) exceeds the local 90th-percentile threshold — based on a 1991--2020 baseline — for at least **5 consecutive days**. Brief cool dips of 2 days or fewer are bridged so that a single continuous event is not artificially split.

Once confirmed, each heatwave is tracked with four metrics:

| Metric | Symbol | Meaning |
|--------|--------|---------|
| **Intensity** | I | How far SST sits above the seasonal climatological mean (degrees C) |
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

- **Intensity (I)** — how far SST sits above the local seasonal climatological mean (°C), following Hobday et al. (2016). Higher intensity means greater thermal stress relative to what the ecosystem is adapted to at that time of year. The 90th-percentile threshold decides *whether* a day is in a heatwave; intensity measures *how warm* it is relative to the normal for that day of the year.
- **Duration (D)** — how many consecutive days the event persists. Persistence often matters more than peak warmth: prolonged exposure depletes energy reserves, shifts distributions, and disrupts spawning and prey availability.
- **Cumulative intensity (C)** — total heat exposure (degree-days): intensity integrated over duration. This is the best single measure of overall ecological burden because it captures both how warm and how long; the 2014–2016 northeast Pacific event ranks extreme on it.
- **Area fraction** — the share of a region under a confirmed MHW at a given time. A low value is a localised event; a high value is a region-wide event with broader ecological consequences. Above roughly 5% is treated here as a regional-scale event.

A short, intense, localised spike and a moderate but prolonged, region-wide event are ecologically very different even when peak intensity is similar — which is why the dashboard reports all four metrics rather than a single number.

---

## The Operational and Historical views

Both views sit under **Alaska-wide Climate → Marine Heatwaves** and are region-selectable.

### Operational

Current and recent MHW state, in four panels:

- **MHW map** — the selected metric (active flag, intensity, duration, cumulative intensity, or threshold exceedance) mapped across the region for a chosen date. Only retained, scorable cells in a heatwave are coloured (A·V·R); observed ice is pale blue, unassessed cells are grey, and the 142 excluded cells are never coloured.
- **Event metrics** — regional time series of area fraction and the mean intensity, duration, cumulative intensity, and onset rate across active cells, with regional-scale events (area fraction > 5%) shaded.
- **Predictability context** — the Arctic Oscillation (AO) and Pacific Decadal Oscillation (PDO) shown alongside MHW coverage and intensity, to assess visually whether climate-mode shifts coincide with changes in heatwave activity. This is correlation context, not prediction.
- **Risk gauge** — a composite 0–100 score combining the area-fraction, intensity, duration and cumulative-intensity percentiles against every eligible day of the region's record (1982 – 31 August 2026), with a 30-day trend. Higher means more extreme than most of the historical record. Incomplete-coverage days get no score.

### Historical (1982 – 31 August 2026)

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

The heatwave record is paused at 31 August 2026 (see *The heatwave record: vintage #7 (D1)* above). The production job still collects the new OISST source files each day at 14:00 UTC, but no heatwave states are computed from them until a validated daily extension is adopted.

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

Daily states also carry each day's coverage: `unknown_share`, `eligible` (unknown ≤ 0.25) and the board label `coverage`. On a no-coverage day (more than 25 % unknown and nothing in the zone scorable) every metric is `null`, never 0. On other days with `eligible = false` the record's value is returned, but it is incomplete coverage, not an observed figure. Event detection skips ineligible days. Map cells carry a `cell_class` (`scorable`, `observed_ice`, `unknown`); excluded cells are omitted.

All responses are JSON with snake_case field names. The regional aggregate fields are `area_frac`, `mean_intensity`, `mean_duration`, `cumul_intensity`, and `onset_rate` (internally these correspond to the Hobday-paper symbols I, D, C, O). Categorical fields use typed enums (`MapMetric`, `IndexName`, `IndexFrequency`, `RiskLevel`) so OpenAPI consumers can codegen against them. See the Swagger UI for full parameter details and query options.

**Data conventions for monthly products** (release note, applies to every monthly series this platform publishes — API, dashboard, and sealed data deliveries):

- **Monthly records are keyed by `date`, set to the first day of the month (`YYYY-MM-01`).** There is no `year_month` field anywhere; if you built a shim converting `year_month`, retire it (convention settled 2026-07-22).
- **An incomplete current month is excluded from monthly series.** A "monthly" mean computed from a few days of a still-running month is not a monthly value — early in a month it can plot as a spurious collapse (or spike). Monthly series shown or published by this platform therefore only use complete months (tables that do show the running month label it as partial); daily endpoints always carry the freshest data.
- **Monthly heatwave values use eligible days only** (unknown share ≤ 0.25). A month with 11 or more rejected days, or 5 or more consecutive rejected days, is missing — never zero.
- **`onset_rate` (O) is signed.** It can be legitimately negative — routinely so in the Chukchi and Beaufort — so consumers should not clamp, drop, or log-transform negative values.

---

## Frequently Asked Questions

**How often is the data updated?**
The heatwave record is currently paused at 31 August 2026, the end of the certified vintage #7 (D1). Daily updates resume when a validated daily extension is adopted; the OISST source files are still collected every day.

**What does "area fraction" mean?**
The percentage of ocean grid cells in a region that are currently experiencing a confirmed MHW. An area fraction of 0.25 means 25% of the region is in active heatwave.

**Why do Chukchi and Beaufort show zero activity in winter?**
Those regions are covered by sea ice from roughly November through June. Observed ice is a real zero for heatwave area, so those days read "ice-covered". On the satellite record's ice-outage days, the ice cannot be known; those days are hatched as incomplete coverage instead of zero.

**What is the "Blob"?**
An exceptionally large and persistent MHW in the northeast Pacific from 2014 to 2016, driven by a persistent atmospheric ridge. It caused widespread marine ecosystem disruption. On the Annual Burden chart, the period is labeled with a *Pacific Blob* text annotation as historical context, but the bar **coloring is not Blob-specific**: it is quantile-based on the displayed metric, so the Blob shows up red automatically on regions where it actually was extreme (GOA, EBS) and stays blue on regions where it wasn't (Chukchi, Beaufort). The label is a calendar marker; the color is the verdict.

**Can I download the raw data?**
Use the REST API endpoints to retrieve daily aggregate and grid-level data in JSON format. The full record (1 January 1982 – 31 August 2026) is available via the API.

**What does a risk score of 80 mean?**
Conditions on that day are more extreme than roughly 80% of the eligible days in that region's record (1982 – 31 August 2026).

**How is the climatological baseline calculated?**
For each day of the year at each grid cell, SST values from 1991--2020 within an 11-day centered window are pooled. The mean and 90th percentile of this pool become the climatological reference and detection threshold, respectively.

**Why do some metrics show 0 even during warm periods?**
MHWs require 5 consecutive days above the 90th-percentile threshold before being confirmed. Candidate warm spells of 1--4 days are tracked internally, but all reported metrics (I, D, C, O) remain zero until the 5-day confirmation criterion is met.

**What is "gap bridging" and why does a heatwave continue through brief cool dips?**
If SST dips below the threshold for 2 days or fewer, the event is bridged — treated as a single continuous event rather than split into two separate events. This follows the Hobday et al. (2016) protocol to prevent artificial fragmentation of one physical heatwave.

**How is intensity measured — above the mean or above the threshold?**
Above the **seasonal climatological mean** (1991–2020 baseline), as in Hobday et al. (2016) and the heatwaveR / marineHeatWaves packages. The 90th-percentile threshold is used only to detect heatwave days. Earlier versions of this board (before July 2026) measured intensity above the threshold, which gave smaller values; compare with older figures accordingly.

**Why do risk scores change even if conditions seem similar?**
Risk scores are percentile-based against each region's eligible days, 1982 – 31 August 2026; they are region-specific but not explicitly season-conditioned. A given intensity value may rank as "normal" in the Gulf of Alaska but "extreme" in the Chukchi Sea.

**Why are AO and PDO included on the Predictability tab?**
The Arctic Oscillation and Pacific Decadal Oscillation are large-scale climate modes that influence North Pacific SST patterns. They are shown alongside MHW metrics for regime context — researchers can visually assess whether phase shifts in AO or PDO coincide with changes in heatwave coverage and intensity. They provide correlation context, not direct predictions.

---

## Technical Details

- **Grid resolution**: 0.25 degrees latitude/longitude (OISST native grid)
- **MHW confirmation**: 5 consecutive days above the 90th-percentile threshold
- **Gap bridging**: Cool dips of 2 days or fewer are bridged into a single event
- **Baseline period**: 1991--2020 (30-year climate normal)
- **Intensity reference**: Anomaly above the seasonal climatological mean (Hobday et al. 2016); the 90th-percentile threshold is used for detection only
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

*Last updated: October 2026*
