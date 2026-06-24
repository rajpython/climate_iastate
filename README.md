# Alaska Marine Ecosystem Dashboard

**Climate • Ocean • Ecosystems • Fisheries** — a regionally-organised board surfacing public Alaska-shelf ocean and fisheries data (observed surveys + ocean models). Its current modules are Alaska-wide marine-heatwave monitoring, Bering Sea bottom conditions (the cold pool), cold-pool validation / model comparison, and catch × thermal habitat. Covers the sub-arctic to Arctic waters around Alaska — Gulf of Alaska, Bering Sea (Eastern and Northern), Chukchi, and Beaufort.

**Live dashboard**: [marine.iastate.ai](https://marine.iastate.ai)
**API docs**: [marine.iastate.ai/api/docs](https://marine.iastate.ai/api/docs)

## Overview

This project operationalizes the Hobday et al. (2016) hierarchical MHW definition into a state-based dashboard that:

- Detects and characterizes marine heatwaves in near-real-time using NOAA OISST v2.1
- Tracks intensity, duration, cumulative exposure, and onset rate at 0.25° resolution
- Provides climate regime context via Arctic Oscillation (AO) and Pacific Decadal Oscillation (PDO) indices
- Generates composite risk scores against 40+ years of historical data (1982–present)

## Dashboard Pages

| Page | Panels |
|------|--------|
| **Operational** | Live MHW Map · Event Metrics Time Series · AO/PDO Predictability · Risk Gauge |
| **Historical** | Annual Burden · Event Explorer · Metric Distributions · Regime Analysis |
| **User Guide** | Interactive help with FAQ |

## Regions

Gulf of Alaska (GOA), Eastern Bering Sea (EBS), Northern Bering Sea (NBS), Chukchi Sea, and Beaufort Sea.

## Quick Start (Local Development)

```bash
# Clone and set up
git clone https://github.com/rajpython/climate_iastate.git
cd climate_iastate
python -m venv .venv
source .venv/bin/activate
pip install -e ".[geo,dashboard,api,dev]"

# Run the dashboard
streamlit run src/dashboard/Alaska_Dashboard.py

# Run the API
uvicorn api.main:app --reload --port 8000

# Run tests
pytest tests/
```

### Keeping local data fresh

The repo ships dashboard code only — derived data (`data/raw/`, `data/derived/`) is
generated locally and gitignored. To extend an existing local backfill through the
current date (recommended monthly):

```bash
bash scripts/monthly_refresh.sh                 # extend through today UTC
bash scripts/monthly_refresh.sh 2026-06-30      # or extend through a specific date
```

The script auto-detects the latest date already on disk, runs the state engine,
aggregates regional metrics, recomputes risk percentile tables, and refreshes the
AO/PDO indices. Set a recurring calendar reminder (monthly is plenty) to run it.

In production, `scripts/daily_refresh.sh` runs inside Docker Compose on a 14:00 UTC
cron and keeps `marine.iastate.ai` current automatically. The Bering bottom-state layers
follow their slower cadence: `scripts/bottom_state_refresh.sh` re-fetches the (annual,
lagged) AFSC cold-pool index and FOSS catch on a monthly cron, while the heavy model
rebuild (`scripts/rebuild_bottom_models.sh` — OPeNDAP + full-shelf regrid of Bering10K /
MOM6) is run locally and rsynced to the VM when a new hindcast year is published.

## Project Structure

```
src/
  mhw/            # Core MHW detection, aggregation, risk scoring
  dashboard/      # Streamlit multipage app
    Alaska_Dashboard.py       # Entry point + st.navigation shell (geography-first sections)
    pages/
      operational.py          # Alaska-wide: real-time MHW monitoring
      historical.py           # Alaska-wide: 1982–present MHW analysis
      bottom_observed.py      # Bering: cold-pool index + survey-replicated validation
      bottom_models.py        # Bering: model comparison (Bering10K vs MOM6)
      catch.py                # Bering: catch × bottom state
      user_guide.py           # In-app documentation
      cold_pool_guide.py      # Plain-language cold-pool guide
      research.py             # Research section (stubs)
    components/               # Reusable panel modules
  api/            # FastAPI REST endpoints
config/           # Region definitions, climatology parameters
scripts/          # Data pipeline & PDF generation
docs/             # User guide, wireframe, scientific spec, plans
```

## Documentation

- **[User Guide](docs/user_guide.md)** ([PDF](docs/user_guide.pdf)) — How to use the dashboard and API
- **[Scientific Specification](mhw_README.md)** — Full methodology, equations, and data pipeline
- **[Runtime Architecture](docs/architecture_runtime.md)** — Entry points, data artifacts, refresh flow, and service runtime
- **[Dashboard Wireframe](docs/dashboard_wireframe.md)** — UI layout specification
- **[Development Plan](docs/plans/sequential_coding_plan.md)** — Step-by-step build log

## Technology

Streamlit · FastAPI · Plotly · xarray · Zarr · Docker · Traefik · WeasyPrint

## Data Sources

- [NOAA OISST v2.1](https://www.ncei.noaa.gov/products/optimum-interpolation-sst) — Daily SST at 0.25° resolution
- [CPC Arctic Oscillation Index](https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/ao.shtml)
- [PSL Pacific Decadal Oscillation Index](https://psl.noaa.gov/pdo/)

## Reference

Hobday, A.J. et al. (2016). A hierarchical approach to defining marine heatwaves.
*Progress in Oceanography*, 141, 227–238.

---

Developed by Rajesh Singh, Professor, Department of Economics, Iowa State University (rsingh@iastate.edu).
