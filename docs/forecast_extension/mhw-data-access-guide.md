# Marine-Heatwave Data Access Guide — for the Forecast Research Cell

This guide is for the sister research cell investigating **marine-heatwave (MHW) forecast
methods**. It documents how to access everything the Alaska Marine Ecosystem Dashboard project
has accumulated: the **raw inputs**, the **derived MHW metrics**, and what is reachable directly
through the public **REST API**.

The board itself is descriptive (monitoring), not predictive — forecasting is *your* charter.
Our job here is to hand you clean, well-documented inputs so you don't re-derive what we already
maintain.

- **Live API base:** `https://marine.iastate.ai/api/v1`
- **Interactive API docs (Swagger):** `https://marine.iastate.ai/api/docs` ← authoritative schema
- **OpenAPI spec (machine-readable):** `https://marine.iastate.ai/api/openapi.json`
- **Health check:** `https://marine.iastate.ai/api/health`
- **Dashboard:** `https://marine.iastate.ai`

> Note on the URL: the API is served under the `/api` prefix (the reverse proxy strips it), so
> the path the docs call `/v1/...` is publicly `https://marine.iastate.ai/api/v1/...`.

---

## 1. What's available, at a glance

| Layer | What it is | Best access |
|---|---|---|
| **OISST v2.1 SST** (raw) | Daily 0.25° sea-surface temperature per region, 1982→present (+ sea-ice fraction) | File snapshot / regenerate |
| **Climatology** | Per-day-of-year mean (μ) and 90th-percentile threshold (θ₉₀), 1991–2020 baseline | File snapshot |
| **Per-cell MHW state** | Daily gridded MHW fields (intensity, duration, etc.) per region | API (`/map`, one date) or file snapshot (bulk) |
| **Regional daily metrics** | One row/day/region: MHW area fraction + area-weighted intensity/duration/… | **API** (`/states`) |
| **MHW events** | Detected discrete events per region (onset/peak/decline) | **API** (`/events`) |
| **Risk percentiles** | Daily percentile ranks + composite risk level per region | File snapshot (parquet) |
| **Climate indices** | AO (daily), PDO (monthly) | **API** (`/indices/...`) |
| **Bottom state / cold pool** | (Beyond SST) observed + modelled bottom temperature, cold-pool area | **API** (`/cold-pool/...`) — see §7 |

**Regions** (MHW / OISST) — now the **AFSC ESR ecosystem regions**, each ecosystem *area* plus its
*subareas* (combined = area-weighted union of its subareas):
- Bering: `ebs` (Eastern Bering Sea = combined) = `sebs` (Southeastern shelf) + `nbs` (Northern).
- Gulf of Alaska: `goa` (combined) = `wgoa` (Western) + `egoa` (Eastern).
- Aleutians: `ai` (combined) = `ai_west` + `ai_central` + `ai_east` (chain crosses the dateline).
- Arctic: `chukchi`, `beaufort` (no ESR subareas).

**Heads-up on the rename:** `ebs` now means the **combined** Eastern Bering Sea; the southeastern
shelf that hosts the cold pool (what used to be `ebs`) is now `sebs`. Polygons:
`config/regions.geojson`; `GET /api/v1/regions` lists all with date coverage.

**Method** (so the metrics are interpretable): the hierarchical Hobday et al. (2016) MHW
definition applied to NOAA OISST v2.1. A cell is in a MHW when SST exceeds the day-of-year
**θ₉₀** threshold for ≥ 5 consecutive days. Baseline **1991–2020**, θ₉₀ computed with an 11-day
day-of-year window. Full methodology: `mhw_README.md` in the repo.

---

## 2. Quick start — the REST API

No key required; read-only; returns JSON. Date filters are `YYYY-MM-DD`.

```bash
# List regions and their date coverage
curl "https://marine.iastate.ai/api/v1/regions"

# Daily MHW metrics for the Eastern Bering, 2016 onward
curl "https://marine.iastate.ai/api/v1/regions/ebs/states?start=2016-01-01"

# Detected MHW events (>= 10 days) for the Gulf of Alaska
curl "https://marine.iastate.ai/api/v1/regions/goa/events?min_duration=10"

# AO (daily) and PDO (monthly) climate indices
curl "https://marine.iastate.ai/api/v1/indices/ao?start=2010-01-01"
curl "https://marine.iastate.ai/api/v1/indices/pdo"
```

Python (pandas) — the typical way you'll pull a training frame:

```python
import pandas as pd, requests

BASE = "https://marine.iastate.ai/api/v1"

def get_states(region, start=None, end=None):
    r = requests.get(f"{BASE}/regions/{region}/states",
                     params={"start": start, "end": end}, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())          # date, area_frac, mean_intensity, …

ebs = get_states("ebs", "1982-01-01")
ao  = pd.DataFrame(requests.get(f"{BASE}/indices/ao").json()["records"])   # date, value
# join SST-MHW state to the AO index on date, etc.
```

---

## 3. API endpoint reference

All paths are relative to `https://marine.iastate.ai/api/v1`. The **Swagger page is the
authoritative, always-current schema** — the fields below are a convenience snapshot.

### Regions & MHW state

| Endpoint | Query params | Returns (fields) |
|---|---|---|
| `GET /regions` | — | list of `{region_id, start_date, end_date, n_days}` |
| `GET /regions/{id}` | — | `{region_id, start_date, end_date, n_days}` |
| `GET /regions/{id}/states` | `start`, `end` | daily list of `{date, area_frac, mean_intensity, mean_duration, cumul_intensity, onset_rate}` |
| `GET /regions/{id}/events` | `start`, `end`, `min_duration` (default 5) | `{event_id, start_date, end_date, duration_days, peak_date, peak_area_frac, peak_intensity, mean_cumul_intensity}` |
| `GET /regions/{id}/map` | `date` (required), `metric` ∈ `I,D,C,A,x` | `{region, date, metric, units, cells:[{lat,lon,value}]}` — one per-cell field for one date |

### Climate indices

| Endpoint | Query params | Returns |
|---|---|---|
| `GET /indices/ao` | `start`, `end` | `{index:"AO", frequency:"daily", records:[{date,value}]}` |
| `GET /indices/pdo` | `start`, `end` | `{index:"PDO", frequency:"monthly", records:[{date,value}]}` |

### Cold pool / bottom state (beyond SST — see §7)

`GET /cold-pool/observed`, `/cold-pool/modelled`, `/cold-pool/kriged-area`,
`/cold-pool/survey-replicate` — all take `region` (and `source` for the modelled ones).

---

## 4. Metric definitions (what the numbers mean)

**Per-cell daily state** (the `metric` values in `/map`, and the variables in the `states_grid`
zarr files):

| Symbol | Name | Units | Meaning |
|---|---|---|---|
| `x` | threshold exceedance | °C | raw SST anomaly above θ₉₀ (precursor of intensity) |
| `I` | intensity | °C | exceedance, counted only inside a **confirmed** MHW |
| `D` | duration | days | consecutive-day count, nonzero only once confirmed |
| `C` | cumulative intensity | °C·days | running sum of `I` over the event |
| `A` | active flag | 0/1 | 1 when the cell is in a confirmed MHW |
| `O` | onset rate | °C/day | rate of intensity increase at onset |

**Regional daily aggregate** (`/states` and the `region_daily_*.parquet` files): one row per day.
`area_frac` = fraction (0–1) of the region's ocean cells in a MHW that day; `mean_intensity`,
`mean_duration`, `cumul_intensity`, `onset_rate` are **area-weighted means over the active cells**
(stored in parquet as `Ibar`, `Dbar`, `Cbar`, `Obar`).

**Risk** (`risk_*.parquet`): `area_frac_pct`, `Ibar_pct`, `Dbar_pct`, `Cbar_pct` are
percentile ranks (0–100) of that day vs the region's own history; `composite_risk` blends them
and `risk_level` is the categorical label shown on the board.

---

## 5. Bulk / raw data access (the files)

This repository is **code-only** — everything under `data/raw/` and `data/derived/` is generated
and is **not** in git. For data the API doesn't serve cell-by-cell in bulk (full per-cell history,
raw OISST, climatology), use one of:

**(a) A data snapshot we hand you (recommended for bulk).** We can rsync or tarball the
`data/derived/` tree (and `data/raw/` if you want the SST inputs). Sizes: the regional/risk
**parquets are small (≈ MB)**; the **per-cell `states_grid` zarr** and **raw OISST NetCDF** are
**tens of GB** (1982→present × 12 regions). Tell us which layers/regions/years you need and we'll
scope the transfer. Ask Col. Raj for the handoff path.

**(b) Regenerate from code (full reproducibility).** Clone the repo, install, and run the
pipeline — it fetches OISST/indices from NOAA and rebuilds every artifact:

```bash
uv pip install -e ".[geo,api,dev]"
bash scripts/monthly_refresh.sh            # build/extend through today (UTC)
# or step-by-step CLIs:
#   mhw-fetch-sst / mhw-fetch-indices  →  mhw-build-masks / mhw-build-climatology
#   →  mhw-run-states (or mhw-backfill) →  mhw-aggregate  →  mhw-compute-risk
```

**(c) The API** for the regional series, events, indices, and single-date maps (§2–3) — best for
most modelling needs; no large download.

### File artifacts (under `data/`)

| Path | Format | Contents |
|---|---|---|
| `raw/oisst_<region>_<year>.nc` | NetCDF | daily 0.25° SST + sea-ice fraction |
| `raw/ao_daily.parquet`, `raw/pdo_*.parquet` | Parquet | AO (daily), PDO (monthly) indices |
| `derived/climatology/mu_<region>.zarr` | Zarr | per-DOY climatological mean SST (1991–2020) |
| `derived/climatology/theta90_<region>.zarr` | Zarr | per-DOY 90th-percentile threshold θ₉₀ |
| `derived/masks/region_masks.zarr` | Zarr | ocean/region masks |
| `derived/weights/weights.zarr` | Zarr | per-cell area weights (cosine-lat) |
| `derived/states_grid/states_<region>_<start>_<end>.zarr` | Zarr | **per-cell daily** `A,C,D,I,O,x` (dims time × lat × lon) |
| `derived/aggregates_region/region_daily_<region>.parquet` | Parquet | regional daily series (= the `/states` endpoint) |
| `derived/risk/risk_<region>.parquet` | Parquet | daily percentiles + composite risk |

Reading a zarr in Python: `import xarray as xr; ds = xr.open_zarr(path)` →
`ds["I"]` is a `(time, lat, lon)` array.

---

## 6. Spatial & temporal reference

- **Grid:** OISST v2.1, 0.25° regular lat/lon, clipped per region polygon.
- **Region polygons:** `config/regions.geojson` (ids `ebs, sebs, nbs, goa, wgoa, egoa, ai, ai_west,
  ai_central, ai_east, chukchi, beaufort` — ESR areas + subareas).
- **Coverage:** 1982-01-01 → present, daily. The series extend to within a few days of "today"
  on each refresh.
- **Tuning/config:** `config/climatology.yml` (baseline 1991–2020, θ percentile, 11-day window),
  `config/datasets.yml`, `config/runtime.yml`.

---

## 7. Beyond SST — bottom state, cold pool, catch

The project also accumulates **subsurface and ecosystem** layers that may be useful covariates:

- **Cold-pool area** (Eastern/Northern Bering), observed (AFSC kriged index) + modelled
  (Bering10K ROMS, CEFI MOM6 NEP), including an apples-to-apples **kriged** model area:
  `/api/v1/cold-pool/{observed,modelled,kriged-area}?region=ebs&source=...`.
- **Mean bottom temperature** for GOA/AI (survey index) and survey-replicated model validation:
  `/api/v1/cold-pool/survey-replicate?source=...&region=...`.
- **Survey catch** (FOSS) co-located with bottom temperature, and modelled bottom-temperature
  series for all shelf regions incl. the Arctic (file layer, `data/derived/cold_pool/`).

Background: `docs/bottom_state_guide.md` (methodology, all regions). These are summer-survey
/ annual products — useful as ecosystem context, not daily drivers.

---

## 8. Caveats & attribution

- **Lagged, not real-time.** Series are historical/operational with a short lag (OISST prelim vs
  final; AFSC products are annual). Treat the latest few days as preliminary.
- **2020 has no AFSC survey** (cancelled) — affects the *bottom-state/cold-pool* layers, not the
  SST-based MHW series.
- **Ice-covered cells** are masked in the climatology/SST processing — relevant for the Arctic
  regions (chukchi, beaufort), where winter SST is under ice.
- **Source data are public NOAA products.** Please attribute: NOAA OISST v2.1 (SST); NOAA CPC
  (AO), NOAA NCEI (PDO); AFSC `afsc-gap-products/coldpool` (cold pool); CEFI MOM6 NEP / ACLIM
  Bering10K (models). The derived MHW metrics follow Hobday et al. (2016).
- **Stability:** the API schema is versioned (`/v1`); the Swagger page is the contract. If you
  need a bulk/static export pinned to a date for a reproducible experiment, ask and we'll cut a
  dated snapshot.

---

## 9. Handoff checklist (tell us this)

To set you up fastest, let us know:
1. Which **layers** you need (regional daily series only? per-cell grids? raw OISST?).
2. Which **regions** and **year range**.
3. **Access mode**: live API (we can raise rate limits / whitelist), a **one-time snapshot**
   (tarball/rsync), or **repo + regenerate**.
4. Whether you need a **pinned dated snapshot** for reproducibility.

Maintained by the Alaska Marine Ecosystem Dashboard project (`marine.iastate.ai`). Questions →
Col. Raj.
