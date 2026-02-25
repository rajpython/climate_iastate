# 🌊 Climate-Ready Fisheries: Marine Heatwave State Dashboard
## Project Concept & Implementation Plan

---

## 1. Project Overview

High-latitude fisheries are increasingly exposed to persistent and extreme **Marine Heatwaves (MHWs)**. These events introduce non-stationarity into marine ecosystems and challenge traditional fisheries management frameworks.

This project operationalizes the Hobday et al. hierarchical MHW definition into a **live, state-based dashboard** that:

- Detects and characterizes marine heatwaves in real time.
- Provides regime-based predictability context.
- Generates state-dependent risk indicators suitable for adaptive management.

The dashboard does **not** begin with fisheries biomass data.
It begins with **marine heatwaves as physical state variables**, consistent with the submitted Wakefield Symposium abstract.

---

## 1.1 Repository Structure

```text
mhw-state-dashboard/
├── mhw_README.md                  # This file — science spec (source of truth)
├── pyproject.toml                 # Dependencies, CLI entrypoints, build config
│
├── config/
│   ├── climatology.yml            # Baseline, thresholds, MHW definition, onset, risk
│   ├── datasets.yml               # Data source registry (OISST, AO, PDO, ice)
│   ├── runtime.yml                # Paths, grid spec, refresh schedule
│   └── regions.geojson            # 5 region bounding-box polygons
│
├── src/mhw/
│   ├── fetch/
│   │   ├── oisst.py               # ERDDAP SST fetcher (CLI: mhw-fetch-sst)
│   │   └── indices.py             # AO/PDO parsers (CLI: mhw-fetch-indices)
│   ├── climatology/
│   │   ├── build_mu_theta.py      # Baseline mu/theta90 (CLI: mhw-build-climatology)
│   │   ├── smooth_doy.py          # 11-day DOY window logic
│   │   └── storage.py             # Zarr read/write
│   ├── states/
│   │   ├── update_states.py       # Daily state engine (CLI: mhw-run-states)
│   │   ├── aggregates.py          # Regional aggregation (CLI: mhw-aggregate)
│   │   └── risk.py                # Risk percentiles (CLI: mhw-compute-risk)
│   ├── regions/
│   │   ├── masks.py               # Rasterize polygons (CLI: mhw-build-masks)
│   │   └── weights.py             # cos(lat) weights
│   └── utils/
│
├── src/api/                       # FastAPI endpoints (Step 10)
├── src/dashboard/                 # Streamlit UI (Steps 7–9)
│
├── data/
│   ├── raw/                       # Downloaded SST, indices
│   └── derived/
│       ├── climatology/           # mu.zarr, theta90.zarr
│       ├── masks/                 # Region masks
│       ├── weights/               # Latitude weights
│       ├── states_grid/           # Daily grid-level states
│       └── aggregates_region/     # region_daily.parquet
│
├── docs/
│   ├── dashboard_wireframe.md     # UI specification (2 pages, 8 panels)
│   ├── plans/
│   │   └── sequential_coding_plan.md  # Step-by-step coding roadmap
│   ├── archive/                   # Superseded planning documents
│   └── references/                # Hobday et al. (2016) PDF
│
├── notebooks/                     # Exploratory notebooks (optional)
├── outputs/plots/                 # Generated figures
├── scripts/                       # Backfill, daily refresh scripts
└── tests/                         # pytest suite
```

> **Note:** Files under `src/api/`, `src/dashboard/`, `scripts/`, and `tests/` are created in later implementation steps. The tree above shows the full planned layout.

---

## 2. Scientific Framework

### 2.1 Hobday Hierarchical MHW Definition

A marine heatwave at grid cell $g$ is defined as:

- SST exceeds the seasonally varying 90th percentile threshold
- For at least 5 consecutive days
- With measurable:
  - Intensity
  - Duration
  - Cumulative exposure
  - Onset rate

This dashboard operationalizes these metrics as daily state variables.

---

## 3. State Variable Definition

We define the MHW state vector:

$$
S_{g,t}^{\text{MHW}}=\{I_{g,t},D_{g,t},C_{g,t},O_{g,t}\}
$$

Where:

- $I_{g,t}$: Intensity (°C above threshold)
- $D_{g,t}$: Duration (days)
- $C_{g,t}$: Cumulative intensity (degree-days)
- $O_{g,t}$: Onset rate (°C/day)

We also define conditioning variables:

$$
Z_{t}=\{AO_{t},PDO_{t}\}
$$

These are **predictability regime indicators**, not part of the MHW state.

---

## 4. Data Sources (Live / Near-Real-Time APIs)

### 4.1 Core SST Input
**NOAA OISST v2.1 (Daily, 0.25° grid)**

Coverage: 1981–present
Updated daily

Access options:

- NCEI product portal:
  https://www.ncei.noaa.gov/products/optimum-interpolation-sst

- PSL THREDDS / OPeNDAP:
  https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/

Required variable:
- `sst`

Optional:
- `ice` (masking)

This dataset is sufficient for full MHW detection.

---

### 4.2 Sea Ice (Conditioning Layer)

NSIDC Near-Real-Time Sea Ice Concentration CDR:

https://nsidc.org/data/g10016/versions/2

Used only to:

- Mask ice-covered grid cells
- Contextualize open-water MHWs

---

### 4.3 Climate Regime Indicators

Arctic Oscillation (daily):

https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/ao_index.html

Pacific Decadal Oscillation (monthly):

https://psl.noaa.gov/data/timeseries/month/PDO/

These variables provide regime context for persistence and predictability.

---

## 5. Climatology & Threshold Build Procedure

### 5.1 Baseline Window

Recommended baseline:

- 1991–2020

Alternative:

- 1982–2011

Baseline is fixed and not recomputed daily.

---

### 5.2 Day-of-Year Mapping

For each grid cell and baseline day:

Map to day-of-year
$d \in \{1,\ldots,366\}$

---

### 5.3 11-Day Moving Window Smoothing

For each day-of-year $d$:

$$
W(d)=\{d-5,\ldots,d+5\}
$$

Compute:

**Climatological Mean**

$$
\mu_g(d)=\mathrm{mean}\left(T_{g,t}\in W(d)\right)
$$

**90th Percentile Threshold**

$$
\theta_g(d)=\mathrm{quantile}_{0.9}\left(T_{g,t}\in W(d)\right)
$$

---

### 5.4 Storage Design

Precompute and store:

- $\mu_g(d)$ — climatological mean, indexed as `[d, lat, lon]`
- $\theta_g(d)$ — 90th percentile threshold, indexed as `[d, lat, lon]`
- $w_g = \cos(\varphi_g)$ — latitude weights, indexed as `[lat, lon]`
- Region masks — binary masks per region, indexed as `[lat, lon]`

Recommended format:

- Zarr (chunked)
- Or NetCDF4 with chunking

These are immutable lookup tables used during daily refresh.

---

## 6. Daily MHW State Update Scheme

For each grid cell $g$ and day $t$:

### 6.1 Threshold Exceedance

$$
x_{g,t}=\max\left(0,\;T_{g,t}-\theta_g(d(t))\right)
$$

### 6.2 Consecutive Exceedance Counter (with gap-bridging)

A gap counter $G_{g,t}$ tracks consecutive sub-threshold days. Gaps of $\leq$ `gap_days` (default 2, per Hobday et al.) are bridged into continuous events:

$$
\text{If } x_{g,t}>0: \quad G_{g,t}=0,\quad \tilde{D}_{g,t}=\tilde{D}_{g,t-1}+1
$$

$$
\text{If } x_{g,t}=0: \quad G_{g,t}=G_{g,t-1}+1
$$

$$
\tilde{D}_{g,t}=
\begin{cases}
\tilde{D}_{g,t-1}+1, & G_{g,t}\le \texttt{gap\_days}\\
0, & G_{g,t}> \texttt{gap\_days}
\end{cases}
$$

Setting `gap_days=0` in `climatology.yml` disables bridging (strict mode). Default `gap_days=2` matches the Hobday et al. (2016) specification that gaps of ≤2 days between exceedance spells are treated as a continuous event.

### 6.3 Confirmed Event Indicator

$$
A_{g,t}=
\begin{cases}
1, & \tilde{D}_{g,t}\ge 5\\
0, & \text{otherwise}
\end{cases}
$$

> **Note:** Under the gap-bridging rules above, $\tilde{D}_{g,t}$ either grows monotonically or resets to 0 — it never decreases to an intermediate value. Therefore, once $A=1$ the event can only end when $\tilde{D}$ resets to 0 (gap exceeded), making a three-case formulation unnecessary.

### 6.4 State Variable Updates

**Intensity**

Default (threshold-referenced, operational):

$$
I_{g,t}=\max\left(0,\;T_{g,t}-\theta_g(d(t))\right)
$$

Alternative (mean-referenced, Hobday-canonical):

$$
I_{g,t}^{\text{mean}}=\max\left(0,\;T_{g,t}-\mu_g(d(t))\right)
$$

Controlled by `intensity_reference` in `climatology.yml` (`"threshold"` or `"climatological_mean"`). The threshold-referenced definition is the default: $I=0$ at the detection boundary. The mean-referenced definition matches Hobday et al. (2016) Table 2 and produces larger intensity values since $\mu < \theta_{90}$ by definition.

**Duration**

$$
D_{g,t}=
\begin{cases}
\tilde{D}_{g,t}, & A_{g,t}=1\\
0, & A_{g,t}=0
\end{cases}
$$

**Cumulative Exposure**

$$
C_{g,t}=
\begin{cases}
C_{g,t-1}+I_{g,t}, & x_{g,t}>0\\
0, & x_{g,t}=0
\end{cases}
$$

**Onset Rate**

Onset rate captures how rapidly intensity increases at the beginning of an event. The onset window is configurable via `onset_reference` in `climatology.yml`.

**Mode 1: `"physical_start"`** (default)

Onset measures the initial intensity ramp during the first $k$ days of the exceedance spell. On the confirmation day ($A_{g,t}=1$ and $A_{g,t-1}=0$), the event start is recoverable from existing state:

$$
s_g = t - D_{g,t} + 1
$$

The onset rate is the mean intensity slope over the first $k$ days:

$$
O_{g,t} =
\begin{cases}
\displaystyle\frac{1}{k}\sum_{j=0}^{k-1}\left(I_{g,s_g+j} - I_{g,s_g+j-1}\right), & A_{g,t}=1 \text{ and } A_{g,t-1}=0 \\
0, & \text{otherwise}
\end{cases}
$$

This telescopes to $O_{g,t} = (I_{g,s_g+k-1} - I_{g,s_g-1}) / k$. Requires a rolling buffer of $I$ values for the last `confirm_days` time steps.

**Mode 2: `"at_confirmation"`**

Onset measures intensity change during the first $k$ days after event confirmation:

$$
O_{g,t} =
\begin{cases}
I_{g,t} - I_{g,t-1}, & A_{g,t}=1 \text{ and } 5 \le D_{g,t} \le 4+k \\
0, & \text{otherwise}
\end{cases}
$$

Forward-only (no buffer needed), but captures mid-event dynamics rather than initial shock.

In both modes, $O_{g,t}=0$ on all non-onset days. Default $k=3$.

---

## 7. Regional Aggregation

Let $w_g=\cos(\varphi_g)$ (latitude weight).

**Area Fraction**

$$
\mathrm{MHW\_area\_frac}_{r,t}=\frac{\sum w_g A_{g,t}}{\sum w_g}
$$

> **Note:** All regional aggregates and regional event detection use the confirmed active flag $A_{g,t}$ (events with $\tilde{D} \geq 5$). Candidate spells (1–4 days) do not contribute to $\mathrm{MHW\_area\_frac}$ or any conditional means.

**Conditional Means** (zero when $\sum w_g A_{g,t} = 0$, i.e., no active MHW in the region)

$$
\bar{I}_{r,t}=\frac{\sum w_g I_{g,t}A_{g,t}}{\sum w_g A_{g,t}}, \quad
\bar{D}_{r,t}=\frac{\sum w_g D_{g,t}A_{g,t}}{\sum w_g A_{g,t}}, \quad
\bar{C}_{r,t}=\frac{\sum w_g C_{g,t}A_{g,t}}{\sum w_g A_{g,t}}, \quad
\bar{O}_{r,t}=\frac{\sum w_g O_{g,t}A_{g,t}}{\sum w_g A_{g,t}}
$$

> **Note on $C_{g,t}$:** Cumulative exposure tracks raw exceedance streaks independent of event confirmation. The confirmation flag $A$ governs $D$ and event reporting only. This means $C$ can accumulate during candidate spells (1–4 days) that never reach confirmed status. This is by design: $C$ serves as a precautionary exposure signal.

---

## 8. Panel 4 — Composite MHW Risk Indicator

### 8.1 Percentile-Based Risk

Convert each regional metric to historical percentile:

$$
p_X(t)=\mathrm{PercentileRank}\left(X_{r,t}\right)
$$

Risk score:

$$
\mathrm{Risk}_{r,t}=0.4\,p_{\bar{C}}+0.3\,p_{\bar{I}}+0.2\,p_{A^{area}}+0.1\,p_{\bar{O}}
$$

Mapped to:

- Green (<0.6)
- Yellow (0.6–0.8)
- Red (>0.8)

### 8.2 Percentile Reference Policy

**Distinction:** Hobday thresholds ($\theta_{90}$) are fixed baseline climatology used for MHW *detection* (Section 5). The percentiles in this section ($p_X$) are ranks of *regional metrics* against a reference distribution used for *risk scoring*. These are separate concepts with separate update policies.

**Frozen mode** (default): Build the reference distribution once after backfill completes, using all `region_daily` records through a cutoff date (configurable in `climatology.yml`). During daily refresh, compute today's percentile ranks against this frozen reference. The reference is rebuilt only on explicit schedule or config change — not every day. In frozen mode, past-day percentile values are stable across queries.

**Incremental mode** (optional): Append each new day's regional metrics to the reference distribution during daily refresh. Percentile ranks reflect a growing baseline. Simpler operationally, but historical percentile values may shift as the reference grows.

Controlled by `risk_percentiles.mode` in `climatology.yml`. See Section 10.3 for domain-specific filtering rules (MHW-active days for $\bar{I}$/$\bar{C}$, onset-active days for $\bar{O}$, all days for area fraction).

---

## 9. Dashboard Architecture

### Page 1: Operational MHW State Monitor

**Panel 1 — Live MHW Map**
- Intensity map
- Confirmed vs candidate toggle

**Panel 2 — Event Characterization**
Time series of:

- $\bar{I}_t$
- $\bar{D}_t$
- $\bar{C}_t$
- $\bar{O}_t$

**Panel 3 — Predictability Context**
- AO index
- PDO index
- Lagged SST anomaly

**Panel 4 — Current Risk Indicator**
- Composite risk gauge
- Percentile rank
- Trigger ON/OFF indicator

---

### Page 2: Historical & Non-Stationarity View
- Panel 1 — Annual MHW Days (1982–Present)
- Panel 2 — Extreme Event Explorer
- Panel 3 — Distribution of Cumulative Exposure
- Panel 4 — Regime Comparison (PDO/AO phases)

---

## 10. State Engine: Backfill & Daily Refresh

The state engine operates in two modes using identical update logic.

### 10.1 Phase A — Historical Backfill (run once before launch)

```
backfill_states(start_date, end_date):
    initialize Dtilde = 0, A = 0, C = 0 arrays (full grid)
    for t in date_range(start_date, end_date):
        load SST for t
        identify day-of-year d(t)
        load theta90[d,:,:]
        compute exceedance x_{g,t}
        update Dtilde, A, D, C, O (same rules as Section 6)
        compute region aggregates (Section 7)
        append to region_daily.parquet
    build percentile reference tables from completed backfill
```

Start date: 1982-01-01 (first full year of OISST).
This must complete before risk percentile tables (Section 8) can be built.

### 10.2 Phase B — Daily Refresh

1. Fetch latest OISST SST field.
2. Identify day-of-year.
3. Load `theta90[d,:,:]`.
4. Compute exceedance $x_{g,t}$.
5. Update state arrays $\tilde{D}, A, D, C, O$.
6. Compute region aggregates.
7. Compute risk percentiles against reference distribution (Section 8.2).
8. If incremental mode: update reference distribution with today's metrics.
9. Store compact region-level tables for dashboard.

No climatology recomputation required.

### 10.3 Percentile Reference Note

Percentile references for $\bar{I}$, $\bar{C}$, and area fraction are computed over their respective domains (MHW-active days for $\bar{I}$ and $\bar{C}$; all days for area fraction).

For $\bar{O}$ (onset rate): because onset is zero on most MHW-active days, **the percentile reference for $p_{\bar{O}}$ should be computed only over days where $\bar{O}_{r,t} > 0$** (i.e., days when at least one cell in the region is in its onset window). This avoids a degenerate zero-inflated distribution that would make the percentile rank uninformative.

---

## 11. Design Philosophy

This dashboard:

- Treats MHWs as state variables, not anomalies.
- Mirrors the abstract's structure.
- Supports dynamic harvest control rule development.
- Avoids drifting into generic climate visualization.
- Is extensible to fisheries exposure modeling later.

---

## 12. Future Extensions (Not in MVP)

- Species sensitivity weights
- Bioeconomic model integration
- Subsurface heat content
- Forecast module
- Rate of decline ($r_{\text{decline}}$) for post-hoc event characterization in Event Explorer
- Retrospective "as-of" percentile queries (recompute past-day risk ranks against the reference distribution available at that date)

---

## Final Statement

This project creates an operational, state-based MHW monitoring framework suitable for high-latitude fisheries management under increasing climate non-stationarity.

It bridges:

**Detection → Characterization → Predictability → Decision Relevance**

Without prematurely embedding biological assumptions.
