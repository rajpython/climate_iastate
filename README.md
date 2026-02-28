# Marine Heatwave State Dashboard

A live monitoring dashboard for marine heatwaves in high-latitude North Pacific and Arctic waters.

**Live dashboard**: [mhw.iastate.ai](https://mhw.iastate.ai)
**API docs**: [mhw.iastate.ai/api/docs](https://mhw.iastate.ai/api/docs)

## Overview

This project operationalizes the Hobday et al. (2016) hierarchical MHW definition into a state-based dashboard that:

- Detects and characterizes marine heatwaves in near-real-time using NOAA OISST v2.1
- Tracks intensity, duration, cumulative exposure, and onset rate at 0.25° resolution
- Provides climate regime context via Arctic Oscillation (AO) and Pacific Decadal Oscillation (PDO) indices
- Generates composite risk scores against 43 years of historical data (1982–present)

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
streamlit run src/dashboard/MHW_Dashboard.py

# Run the API
uvicorn api.main:app --reload --port 8000

# Run tests
pytest tests/
```

## Project Structure

```
src/
  mhw/            # Core MHW detection, aggregation, risk scoring
  dashboard/      # Streamlit multipage app
    MHW_Dashboard.py          # Entry point
    pages/
      1_Operational.py        # Real-time monitoring
      2_Historical.py         # 1982–present analysis
      3_User_Guide.py         # In-app documentation
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

Developed by Dr. Rajesh Singh, Professor, Department of Economics, Iowa State University (rsingh@iastate.edu).
