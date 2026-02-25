<!-- docs/dashboard_wireframe.md -->
# Dashboard Wireframe — MHW State Dashboard (Two Pages, Four Panels Each)

## Scope Guardrail
This dashboard is **MHW-first**. It operationalizes Hobday-style marine heatwave state variables and conditioning regime indicators.  
**No fisheries biomass, surveys, or PDFs** in MVP.

---

## Page 1 — Operational MHW State Monitor (Live)

### Panel 1 — Live MHW Map (Detection)
**Purpose:** Theme (i) standardized detection; show where MHWs are occurring today.

**Inputs:**
- Grid: Active flag `A_g,t` (confirmed MHW ≥ 5 days)
- Grid: Intensity `I_g,t` (°C above threshold)
- Optional conditioning overlay: sea ice concentration (mask)

**Controls / Filters:**
- Region selector: GOA / EBS / NBS / Chukchi / Beaufort
- Date picker (default: latest)
- Metric toggle: `active`, `intensity`, `duration`, `cumulative`
- Confirmed vs Candidate toggle:
  - Confirmed: ≥5 days
  - Candidate: 1–4 days (early warning)

**Outputs:**
- Map colored by selected metric
- Badge: `MHW_area_frac_{r,t}` (fraction of region in confirmed MHW)

---

### Panel 2 — Event Characterization (Last 60–90 days)
**Purpose:** Theme (i) characterization of discrete events via Hobday hierarchy.

**Series (regional aggregates):**
- `area_frac_{r,t}` (confirmed)
- `Ibar_{r,t}` (mean intensity conditional on MHW)
- `Dbar_{r,t}` (mean duration conditional on MHW) *(optional; derived from grid `D_g,t`)*
- `Cbar_{r,t}` (mean cumulative intensity conditional on MHW)
- `Obar_{r,t}` (mean onset rate conditional on MHW)

**Controls:**
- Time window: 30 / 60 / 90 days
- Toggle: show candidate spells overlay

**Outputs:**
- Time series chart(s) with event periods visually clear

---

### Panel 3 — Predictability Context (Regime Indicators)
**Purpose:** Theme (ii) short-to-medium predictability context (no forecasting claims in MVP).

**Series:**
- `AO_t` (daily)
- `PDO_t` (monthly; shown as step series)
- Optional: lagged SST anomaly proxy (e.g., `Ibar` or region mean anomaly)

**Controls:**
- Same date range as Panel 2
- Optional: align y-axes for visual correlation only

**Outputs:**
- Context plot(s) for interpreting persistence regimes

---

### Panel 4 — Current Risk Indicator (Composite MHW Risk)
**Purpose:** Theme (iii) management relevance via state-dependent risk signals.

#### Tier 1: Percentile-Based Composite Risk (recommended)
Compute percentiles relative to historical distribution (see risk spec). Display:
- Risk gauge (0–1)
- Current percentile rank

Inputs (regional):
- `Ibar_{r,t}`
- `Cbar_{r,t}`
- `Obar_{r,t}`
- `area_frac_{r,t}`

Default weights:
- Cumulative `0.4`
- Intensity `0.3`
- Area fraction `0.2`
- Onset `0.1`

#### Tier 2: Trigger Badge (optional)
Rule-like indicator:
- “Trigger ON/OFF” based on threshold exceedances (e.g., Cbar > 90th percentile and area_frac > 75th percentile)

**Outputs:**
- Risk gauge + percentile
- Trigger badge with which conditions exceeded

**Risk Color Mapping:**
- Green: Risk < 0.6
- Yellow: 0.6 ≤ Risk ≤ 0.8
- Red: Risk > 0.8

---

## Page 2 — Historical & Non-Stationarity View

### Panel 1 — Annual MHW Burden (1982–present)
**Purpose:** Show non-stationarity in MHW exposure.

Metrics per year:
- Total MHW days (regional)
- Total MHW events (regional)
- Mean/median event duration
- Annual cumulative intensity (sum)

**Controls:**
- Region selector
- Metric selector

---

### Panel 2 — Extreme Event Explorer (Event Replay)
**Purpose:** Retrospective event-focused lens (supports GOA 2014–2016 narrative).

Features:
- Dropdown list of historical events (derived)
- For selected event:
  - Start/end dates
  - Peak intensity
  - Total cumulative exposure
  - Max onset rate (early shock)

Optional:
- Timeline replay slider (map snapshots)

---

### Panel 3 — Distribution & Percentile Context
**Purpose:** “How extreme is the current event relative to history?”

Plots:
- Distribution of `Cbar` on MHW-active days
- Mark current `Cbar_{r,t}` as vertical line with percentile label
- Optional: same for `Ibar` and duration

---

### Panel 4 — Regime Comparison (AO/PDO Phases)
**Purpose:** Connect predictability regimes to MHW burden.

Split historical days into bins:
- PDO positive vs negative
- AO positive vs negative

Compare:
- Mean duration
- Mean cumulative intensity
- Event frequency (per season/year)

Outputs:
- Simple side-by-side bars or box plots

---

## Shared Filters / Global Controls
- Region
- Date (for Page 1 map)
- Time window (for Page 1 series)
- Confirmed vs Candidate view
- Metric selection for map and historical panels

---

## Notes for Implementation Agents
- Page 1 should be fast and responsive; rely on precomputed region-level parquet tables.
- Maps should be served as downsampled grids or cached tiles per date/region/metric.
- All MHW state metrics are derived from OISST and stored; climatology is precomputed once.
