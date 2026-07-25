# Build Brief: Alaska Marine Heatwave Forecast page (Streamlit)

**For:** the dashboard agent working in the existing Streamlit project.
**Task:** Add a new page that replicates NOAA PSL's experimental Marine Heatwave (MHW) forecast, scoped to the nine Alaska ESR zones. Build it inside the current Streamlit app — reuse its layout, theme, caching, and data conventions. Do not scaffold a separate app.

Deliver in two stages: **Stage 1** = a working page on NOAA's *published* forecast files. **Stage 2** = recompute the forecast from raw NMME for one zone/model as a validation/methods exercise. Ship Stage 1 first and get it reviewed before starting Stage 2.

---

## Context: what you're replicating

NOAA's page is two products layered together — keep them separate:

1. **The forecast** — a probability, per ocean grid cell and lead time, that the monthly SST exceeds the local 90th-percentile MHW threshold (Jacox et al. 2022). Already published as NetCDF, so Stage 1 just reads it.
2. **The page** — year/month selectors, a trend/detrend toggle, a lead-time slider, a probability map, per-location time series, and a skill map. This is the visualization layer you build in Streamlit.

### Forecast definition (from NOAA's Q&A)
- MHW = SST anomaly (vs **1991–2020 monthly climatology**) above a month-specific threshold.
- Threshold = **90th percentile of SST anomalies in a centered 3-month window** (e.g. January uses Dec–Feb).
- Probability = **fraction of NMME ensemble members** whose anomaly exceeds the threshold.
- Lead time 0.5 mo = current month's mean forecast; +1.5 = next month; … out to +11.5.
- Two flavors via a toggle: **trend-retained** (raw) and **detrended** (warming trend removed before thresholding).
- **Skill** = Symmetrical Extremal Dependence Index (SEDI), 1 = perfect, 0 = chance.

---

## Data (public NetCDF; download locally into the project)

Base URL: `https://downloads.psl.noaa.gov/Datasets/marinehw/`

| File | Use |
|---|---|
| `NMME_prob90_latest.nc` | Extended forecast 2021→present, **trend-retained** (primary map) |
| `NMME_prob90_detrend_latest.nc` | Same, **detrended** (toggle target) |
| `nmme_mhw_forecast_probability_1991_2020.nc` (+ `_detrended`) | 1991–2020 hindcast probabilities (history / earlier init years) |
| `oisst_land_sea_ice_mask_NMMEgrid.nc` | Ocean/ice mask for masking land |
| `oisst.mon.anom_latest.nc` (+ `.detrend`) | Observed OISSTv2 anomalies (verification, "what happened") |
| `oisst.mon.quantile90_latest.nc` (+ `.detrend`) | Observed 90th-pct thresholds |

Download with `wget -c <url>` or `curl -L -O <url>` (no auth). Store under the project's data dir; add the paths to the project's config, don't hardcode.

**First step before writing any UI:** open `NMME_prob90_latest.nc` with `xarray.open_dataset()` and print `ds`, `ds.dims`, `ds.coords`, `ds.data_vars`. Expected shape is roughly `(init_time, lead, lat, lon)` with probability in 0–1 or 0–100, longitude likely 0–360 — **confirm the real names and units from the header and build loaders around those, not these assumptions.**

---

## The nine Alaska ESR zones

Eastern Gulf of Alaska, Western Gulf of Alaska, Southeastern Bering Sea, Northern Bering Sea, Western Aleutians, Central Aleutians, Eastern Aleutians, Chukchi Sea, Beaufort Sea.

Use the **authoritative AFSC ESR polygons** (akmarineheatwaves.org / Jordan Watson, AFSC ESR program publish region shapefiles/GeoJSON). Prototype with the approximate boxes below, then replace with the real polygons before anything is presented as a result. Longitudes in °E (0–360) to match OISST/NMME:

| Zone | Lat (°N) | Lon (°E) |
|---|---|---|
| Eastern Gulf of Alaska | 54–61 | 216–226 |
| Western Gulf of Alaska | 53–60 | 200–216 |
| Southeastern Bering Sea | 54–60 | 190–202 |
| Northern Bering Sea | 60–66 | 187–200 |
| Eastern Aleutians | 51–55 | 190–200 |
| Central Aleutians | 51–54 | 180–190 |
| Western Aleutians | 51–54 | 170–180 |
| Chukchi Sea | 66–72 | 185–205 |
| Beaufort Sea | 70–74 | 200–230 |

Per zone, compute an **area-weighted mean probability** (weight by cos(lat)), masking land/ice via `oisst_land_sea_ice_mask_NMMEgrid.nc`. Use `regionmask` + `geopandas` (or `shapely`) to rasterize polygons onto the NMME grid.

---

## Stage 1 — Streamlit page on published data

### Suggested module layout (fit to the project's existing conventions)
```
pages/ (or wherever the app's pages live)
  alaska_mhw.py           # the Streamlit page: layout + widgets + charts
lib/marine_hw/
  data_loader.py          # open_dataset, cache, subset to Alaska, apply mask
  zones.py                # ESR polygons + area-weighted zonal averaging
  figures.py              # Plotly map, zone time series, skill map builders
```
If the project already registers pages a certain way (multipage `pages/` dir, a nav router, a page registry), follow that pattern rather than introducing a new one.

### Streamlit specifics (this is not Dash — no callbacks)
- The script reruns top-to-bottom on every widget change. Structure accordingly.
- **Cache the expensive things:** wrap dataset opening in `@st.cache_resource` (returns the live xarray handle); wrap derived arrays/zonal series in `@st.cache_data` keyed on (init, lead, trend-flag). This is the single most important performance step — without it, every slider nudge re-reads NetCDF.
- Widgets: `st.selectbox` for initial year and month; `st.radio` (or `st.toggle`) for "Remove long-term trend?"; `st.select_slider` for lead time (+0.5 … +11.5); add an ESR **zone `st.selectbox`** (a useful addition NOAA lacks).
- Use `st.plotly_chart(fig, use_container_width=True)`. Consider `st.session_state` to remember the user's zone/lead selection across reruns.
- Subset to the Alaska window on load — never render the global grid.

### Views
1. **Map** — Alaska-focused Plotly map (`go.Scattergeo`/`go.Densitymapbox`; a polar-friendly projection reads better for Chukchi/Beaufort). Color = MHW probability for the chosen init + lead. Clip to the Alaska bounding window.
2. **Zone time series** — probability vs lead time for the selected zone, with the 10% climatological reference line; show trend and detrended side by side as NOAA does.
3. **Skill map** — SEDI for the selected init-month/lead so users see where the forecast is trustworthy.

### Acceptance criteria (Stage 1)
- Page loads inside the existing app and appears in its nav.
- Changing year/month/trend/lead updates the map and series without a full re-read of NetCDF (caching verified).
- Zone series use area-weighted, land-masked averages over the ESR polygons.
- Spot-check: one init/lead/grid-cell probability matches NOAA's live page for the same selection.

---

## Stage 2 — Recompute forecast from NMME (one zone + one model first)

Do **Eastern Gulf of Alaska** with a single NMME model (e.g. GFDL-SPEAR or NCEP-CFSv2) before generalizing — full global/all-model reproduction is 100s of GB and unnecessary. Refs: Jacox et al. 2022 (*Nature*) and Jacox et al. 2020 (method).

Pipeline:
1. Pull the chosen model's monthly SST hindcasts/forecasts from IRI's NMME archive (`iridl.ldeo.columbia.edu`), subset to the Alaska window on download.
2. **Anomalies:** subtract the 1991–2020 model climatology, computed **per lead and per calendar month** (leads drift differently — climatology is lead-dependent).
3. **Thresholds:** 90th percentile per calendar month from a 3-month window; also a detrended variant.
4. **Probability:** fraction of ensemble members exceeding threshold per cell/lead.
5. **Validate:** compare recomputed zonal probabilities against `NMME_prob90_latest.nc` over the same cells/leads — agreement is the correctness check.
6. (Optional) **Skill:** verify against observed OISST MHW flags, compute SEDI to reproduce the skill map.

### Acceptance criteria (Stage 2)
- Recomputed Eastern GoA zonal probability series tracks NOAA's published series for matching init/leads.

---

## Constraints & notes
- Reuse the project's existing config, theming, caching, and data-directory conventions; don't fork a parallel setup.
- Keep NOAA files out of version control (they're large and update monthly); load paths from config. Optionally add a scheduled monthly re-fetch of the `*_latest.nc` files (they refresh on the 1st as new initializations land).
- Required plot citation: *"Image provided by the NOAA Physical Sciences Laboratory, Boulder, Colorado, from the website at https://psl.noaa.gov/."*
- Likely new deps: `xarray`, `netCDF4`, `regionmask`, `geopandas`/`shapely`, `plotly` — confirm against the project's existing requirements before adding.
