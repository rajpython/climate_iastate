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

## The NOAA PSL Marine Heatwave Forecast

Under **Alaska-wide Climate → MHW Forecast (NOAA PSL)** the board displays NOAA's *experimental* marine-heatwave forecast (Jacox et al. 2022), scoped to the nine Alaska ESR zones. This is a **replication of NOAA's published product**, not a forecast the board builds — it is a separate, more experimental thing from the short-term outlook shown under **Marine Heatwaves → Forecast** (that one is the LOFRA damped-persistence research product on our own monthly area fraction). Keep the two mentally separate.

### What the forecast is

For every ocean cell and lead time, NOAA runs the North American Multi-Model Ensemble (NMME) of seasonal climate models forward and reports the **fraction of ensemble members whose monthly sea-surface-temperature anomaly exceeds the local 90th-percentile marine-heatwave threshold**. That fraction *is* the probability shown on the map: 100% means every model says heatwave, 0% means none do, and about 10% is the long-run base rate (the threshold is the warmest 10% of months by construction, so with no forecast signal you expect ~10%).

- **Anomalies** are versus the 1991–2020 monthly climatology.
- **Threshold** is the 90th percentile of anomalies in a centred 3-month window (e.g. January uses Dec–Feb).
- **Lead time** runs from +0.5 months (the current month) out to +11.5 months.
- **Two flavours** via the *Remove long-term trend* toggle: **trend-retained** (raw) and **detrended** (the long-term warming trend removed before thresholding). Detrending isolates the month-to-month signal from background warming — useful for judging whether a high probability is genuinely unusual or just the new normal.

### Controls

The sidebar carries the page controls: **initialization year** and **month** (which model run to show), the **detrend** toggle, a **lead-time** slider (+0.5 … +11.5 months), the **ESR zone** selector, and a **Show only the selected zone** toggle. Selections persist as you move between the panels.

### The three panels

1. **Probability map** — the MHW probability for the chosen initialization and lead, on the 1° NMME grid. With *Show only the selected zone* on (the default), the map is **masked to the chosen zone's cells** — exactly the cells the zone average below is computed over — and recentres/zooms to it with the zone boundary outlined. Turn the toggle off to see the whole-Alaska field for spatial context (neighbouring hotspots, the open North Pacific). **Click any cell** to open a *Selected cell* panel with that single 1° cell's probability-by-lead curves (trend solid, detrended dashed, same 0–100% styling) — the same per-cell drill-down NOAA's global page offers.
2. **Zone probability by lead** — the zone-averaged probability against lead time, with **trend-retained (solid) and detrended (dashed) on one axis** for easy comparison, styled like NOAA PSL: a fixed 0–100% scale, a red dashed "10% threshold" line, and a gold dot marking the lead you have selected on the slider (the lead the map is showing). Below it, KPI cards give the nearest-lead probability, the number of 1° cells in the zone, and the zone's seasonal-ice fraction (a caveat flag — see below).
3. **Forecast skill (SEDI)** — a map of how trustworthy the forecast has been, cell by cell, at the selected lead (see *Reading the skill map*).

### How a zone value is averaged

The zone number is an **area-weighted mean of the forecast over the cells inside the ESR polygon**, computed NaN-aware:

- each cell's weight is `cos(latitude) × coverage-fraction × (not land)`, where **coverage-fraction** is how much of that 1° cell falls inside the zone polygon (so partial edge cells count proportionally, not all-or-nothing), and `cos(latitude)` corrects for cells shrinking toward the pole;
- cells with no data (land) are dropped and the remaining weights renormalized, so a half-land coastal cell is never counted as zero probability;
- the zone value is `Σ(weight × probability) / Σ(weight)` over those cells.

The per-cell curves you can click on the map are literally the building blocks; the zone curve is their weighted average. Zones hold between ~45 and ~110 of these 1° cells (see *How the data is organized*).

### Reading the skill map (SEDI)

**SEDI** is the **Symmetric Extremal Dependence Index** (Ferro & Stephenson, 2011), a verification score built for rare events: it weighs the forecast's hit rate against its false-alarm rate, so it stays meaningful even though heatwaves are, by definition, uncommon. **1 = a perfect forecast, 0 = no better than chance, negative = worse than chance.** It is computed by replaying the 1991–2020 NMME hindcast, flagging a forecast "heatwave" when the hindcast probability is ≥ 50%, comparing against whether a heatwave was actually observed (OISST anomaly above the month's 90th percentile), and scoring the resulting hits/misses/false-alarms.

Two things to know when reading it:

- **It is pooled over all initialization months, per lead.** Skill is a property of the forecast system at a given lead time, not of one particular calendar month, and per-month bins have only ~30 hindcast samples — far too few to be reliable at longer leads. Pooling gives a dense, stable "skill at lead N" map. As expected, skill is high at short leads (SEDI ≈ 0.8 in the Gulf and Southeastern Bering at +0.5 months) and fades with lead (≈ 0.2 by ~8 months).
- **Blank cells are honest, not missing.** Where a cell never recorded a hit or never a false alarm over the hindcast, SEDI is mathematically undefined and left blank. Coverage naturally thins at longer leads because heatwaves become rarer to score against. The skill map is masked and framed to the selected zone the same way the probability map is.

### Seasonal-ice caveat

The Chukchi, Beaufort and Northern Bering zones sit under seasonal sea ice, flagged by the *Seasonal-ice fraction* KPI (≈ 100% for those zones). NOAA's product still defines a probability there, but read it knowing the underlying SST record is ice-affected for much of the year.

### How the data is organized

The raw PSL file is a **1° global grid — 181 latitudes × 360 longitudes = 65,160 cells** — with a probability for every cell × 12 leads × the monthly initializations back to 2021. The board slices this to an Alaska window (46–78°N, 166–236°E) of **33 × 71 = 2,343 cells**, of which about 1,729 are ocean. Only the **667 ocean cells that fall inside the nine ESR polygons** feed the zone averages (roughly: Central Aleutians 111, Western GoA 110, SE Bering 107, Chukchi 85, Eastern GoA 72, Northern Bering 71, Beaufort 69, Western Aleutians 66, Eastern Aleutians 45). At this resolution a 1° cell spans ~110 km north–south and ~50–75 km east–west, so the narrow Aleutian strips get only tens of cells — a limitation of the coarse seasonal-forecast grid, not of the slicing.

### Data, updates and citation

The forecast files (`NMME_prob90_latest.nc` and its detrended twin) are downloaded from NOAA PSL and refreshed on the production server daily, but only re-downloaded when PSL actually updates them (roughly monthly, occasionally mid-month as models land). The skill map is a heavier one-time build from the 1991–2020 hindcast, produced locally and shipped to the server. Required attribution, shown in the page footer: *"Image provided by the NOAA Physical Sciences Laboratory, Boulder, Colorado, from the website at https://psl.noaa.gov/."*

---

## The Alaska-Shelf MHW Forecast (Damped Persistence)

Under **Marine Heatwaves → Operational** — beneath the current-conditions panels for a selected region — the board shows a **short-term marine-heatwave outlook** for that region's ESR zones, 1–3 months ahead. Unlike the NOAA PSL product above (a replicated seasonal-model forecast), this outlook is a **consumed research product**: it comes from an ongoing marine-heatwave forecasting study by a separate research cell, and the board *pins and displays* it — it does not build or re-fit it. Keep the two forecasts mentally separate: PSL is a physics-model probability; this is a statistical outlook run on the board's own observed area fraction.

### Where it comes from

The study asks a plain question — for the Alaska shelf, how far ahead can a marine heatwave actually be forecast, and does any method beat the simplest possible one? Its answer, after a rigorous rolling-origin evaluation, is that **simple "damped persistence" is the forecast to beat, and across the Alaska shelf nothing tested beats it at the lead times that matter for management**. The board displays that damped-persistence forecast, run forward on our own monthly per-zone area fraction, with the study's honesty limits carried onto every tile.

The coefficients are **frozen at a fit vintage** (persistence/climatology 2026-04, the SEBS onset watch 2026-05) and applied forward — only the most recent observed month is live. They are re-fit on the corrected canonical-Hobday threshold (the same 31-day-smoothed θ90 the board's own MHW definition uses), so the forecast and the observations it is scored against share one target. Re-fits arrive from the research cell as versioned releases; the board never re-estimates them.

### One target, three report cards

There is only **one thing forecast — the area fraction**: the share of a zone's grid cells in a marine heatwave that month, between 0% and 100%. Occurrence and onset are **not separate forecasts**; they are two additional *report cards* on that single area-fraction forecast. So the panel shows one forecast read three ways:

1. **Area / magnitude** — the headline tiles: the forecast area fraction 1, 2, and 3 months out, each with a plausible-range band that widens with lead. Read it as **most reliable one month ahead**, useful at two, and a **low-confidence watch by three**.
2. **Occurrence probability** — the chance next month's area exceeds the zone's local 90th-percentile threshold (an unusually large heatwave), read off the same damped-persistence forecast.
3. **SEBS onset watch** — an experimental early-warning flag for the *start* of a Southeastern Bering heatwave.

### What "the forecast to beat" means

Three simple baselines set the bar, and it matters which one:

- **Climatology** — ignore today and predict the seasonal average for the calendar month. This is the floor: a model with no real skill cannot beat it.
- **Persistence** — carry today's anomaly forward at full strength.
- **Damped persistence** — carry today's anomaly forward but let it fade toward the seasonal average as the lead grows. This is the **null model — the forecast to beat** — because it interpolates between the other two (persistence at short leads, climatology at long ones), so beating it means beating both at once.

The study raced damped persistence against genuinely sophisticated models — a **Linear Inverse Model** (a statistical model of the whole North Pacific temperature pattern), **SEAS5** (Europe's physics-based global seasonal model), and **ocean heat content** (a longer-memory predictor). At the operational 1–2 month leads, none of them resolvably beat damped persistence on heatwave magnitude or area, in any of the nine zones. The one exception is a genuine 3-month edge for SEAS5 on area in the Eastern Gulf of Alaska — reported openly, and useful precisely because it shows the evaluation *can* detect a real improvement when one exists.

### The 2–3 month ceiling

By about two to three months, all the forecasts — simple and sophisticated alike — collapse toward the seasonal average. Nothing extends useful skill past that horizon; even ocean heat content, which "remembers" far longer than the surface, does not push it out for the heatwave target. This is a genuine physical limit of predictability at this scale, not a shortcoming of the data or of any one method. It is why leads beyond three months are not shown.

### Zone-by-zone routing

The product shown depends on the zone, and the routing is enforced so a zone is never shown a forecast the study did not validate for it:

- **Seven productive zones** (Southeastern & Northern Bering, Western & Eastern Gulf of Alaska, and the three Aleutian zones) get the damped-persistence outlook and, where applicable, the occurrence report card.
- **Northern Bering** carries a **sea-ice caveat** — the satellite temperature record is ice-affected — but still gets a one-month outlook.
- **Chukchi and Beaufort** are shown as a **typical-year (climatology) estimate only**: seasonal ice contaminates the SST record so far north that carrying recent conditions forward stops working. This is a data limitation, not a forecast result, and no heatwave chance is issued for them.

### Reading the occurrence report card

The occurrence panel shows, for each productive zone, the forecast **P(> q90)** — the chance next month's area exceeds the local 90th-percentile threshold — alongside two skill numbers from the study's evaluation:

- **Skill vs climatology (BSS)** — a Brier Skill Score against the seasonal average: 0 means no better than climatology, 1 is perfect. It is strong at one month (roughly 0.5–0.6 in the Gulf and Southeastern Bering) and decays beyond, shown as "watch" rather than a number where it is no longer resolvable.
- **Discrimination (AUC)** — how well the forecast separates true high-area months from low-area ones.

The important honesty point, carried on the panel: this skill is measured **over climatology, which is real — but it is not the model beating persistence.** The occurrence forecast *is* the damped-persistence model, read a different way.

### Reading the SEBS onset watch

The onset watch is **experimental and Southeastern-Bering only**. It is a two-state **elevated / normal** flag — never a probability — for whether a heatwave is likely to *start*. It is driven by the Linear Inverse Model's read of the North Pacific temperature pattern, with the state coming straight from the study's frozen calibration.

It genuinely discriminates onset (an AUC around 0.76 at one month), and the panel shows that skill alongside its SEDI score and hit / false-alarm rates. But it is shown with a firm caveat, and the panel makes the reason visible: **simple persistence achieves an onset AUC of about 0.67 on its own.** The watch sits just above that — it discriminates onset but does **not** resolvably beat persistence, and on the corrected threshold its selection-adjusted improvement is not statistically distinguishable on the small number of onsets available. **Read it as an early-warning signal, not a validated forecast advantage** — never as "beating persistence."

### Updates and provenance

The outlook re-runs when the board's monthly area fraction updates (the frozen coefficients applied to the new origin month). The onset watch additionally needs a broad-basin North Pacific SST-anomaly field, rebuilt from public OISST. Every tile shows the coefficient vintage so the frozen fit is never mistaken for a live re-estimate. The methodology and its evaluation live in the research cell's working paper, linked from the **Research → Forecast Development** page.

---

## Data Sources

| Dataset | Provider | Resolution | Coverage |
|---------|----------|------------|----------|
| **OISST v2.1 (SST + sea ice)** | NOAA (NCEI / CoastWatch ERDDAP) | Daily, 0.25 deg | 1982--present |
| **Arctic Oscillation** | NOAA CPC | Daily | 1983--present |
| **Pacific Decadal Oscillation** | NOAA PSL | Monthly | 1983--present |
| **Experimental MHW forecast (NMME)** | NOAA PSL (Jacox et al. 2022) | Monthly, 1 deg | 2021--present |

Most data comes from NOAA sources. SST and sea ice are fetched from the same OISST dataset via ERDDAP — cells with ice concentration above 15% are masked out of the MHW analysis. AO is retained from \~1950 and PDO from 1854 so the Regime Analysis tab covers both phases (PDO has been in a sustained negative phase since 2020, so the full record is essential for seeing PDO+ regimes). The experimental MHW forecast is a **published NOAA PSL product** displayed as-is for the Alaska ESR zones (the board does not recompute it); attribution appears in that page's footer.

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
- **An incomplete current month is excluded from monthly series.** A "monthly" mean computed from a few days of a still-running month is not a monthly value — early in a month it can plot as a spurious collapse (or spike). Monthly plots, driver correlations, and the forecast's origin month therefore only use complete months; daily endpoints always carry the freshest data.
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

**What is the difference between the two forecasts on the board?**
There are two, deliberately kept separate. **Marine Heatwaves → Forecast** is the board's own short-term outlook (the LOFRA damped-persistence research product, run 1–3 months ahead on our monthly area fraction). **MHW Forecast (NOAA PSL)** replicates NOAA PSL's experimental NMME probability forecast out to ~11 months, displayed for the Alaska ESR zones. The first is a research product we build; the second is a published NOAA product we mirror.

**On the PSL forecast page, what exactly is the probability?**
The fraction of the NMME climate-model ensemble whose monthly SST anomaly exceeds the local 90th-percentile heatwave threshold. ~10% is the no-signal base rate; higher means more models agree a heatwave is likely. Trend-retained keeps the long-term warming; detrended removes it before thresholding.

**Why is part of the SEDI skill map blank?**
SEDI is undefined for a cell that never recorded a hit or never a false alarm over the 1991–2020 hindcast, so those cells are left blank rather than guessed. Blank area grows at longer leads because heatwaves get rarer to score against. SEDI is pooled over all initialization months at each lead (per-month bins have too few samples to be reliable).

**Can I see a single cell instead of the whole zone?**
Yes — click any cell on the PSL forecast probability map to open its own probability-by-lead curve. The zone line elsewhere on the page is the area-weighted average of exactly those cells.

---

## Technical Details

- **Grid resolution**: 0.25 degrees latitude/longitude (OISST native grid)
- **MHW confirmation**: 5 consecutive days above the 90th-percentile threshold
- **Gap bridging**: Cool dips of 2 days or fewer are bridged into a single event
- **Baseline period**: 1991--2020 (30-year climate normal)
- **Intensity reference**: Anomaly above the 90th-percentile threshold
- **Regional aggregation**: Area-weighted (cosine of latitude) averages across active cells
- **PSL forecast grid**: 1 degree (NMME native); Alaska window 46--78N, 166--236E; 667 ocean cells across the 9 ESR zones
- **PSL forecast probability**: fraction of the NMME ensemble exceeding the local 90th-percentile anomaly threshold, leads +0.5 to +11.5 months, trend-retained and detrended
- **PSL skill score**: SEDI (Symmetric Extremal Dependence Index), 1991--2020 hindcast vs observed OISST heatwave flags, pooled over all initializations per lead

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

The experimental marine-heatwave forecast follows:
Jacox, M.G. et al. (2022). Global seasonal forecasts of marine heatwaves.
*Nature*, 604, 486--490. Skill scoring uses the Symmetric Extremal Dependence Index of
Ferro, C.A.T. & Stephenson, D.B. (2011). *Weather and Forecasting*, 26, 699--713.

---

*Last updated: May 2026*
