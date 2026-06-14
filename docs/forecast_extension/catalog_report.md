# MOM6 Data Discovery — Catalog Report

**Branch:** `feat/mom6-spike`
**Type:** Discovery only. **No implementation.** Deliverable is this filled-in report.
**Target:** ~1 week. Goal is to *reduce uncertainty* before any `feat/bottom-ocean-state`
work begins — especially the grid and latency questions, which are the real risks.

> Scope note: survey MOM6 **broadly**, not just bottom temperature. MOM6-COBALT
> exposes many ocean-health variables (bottom temp, SST, sea ice, mixed-layer
> depth, salinity, currents, oxygen, ocean heat content). Catalog what exists; the
> *first* implementation increment will likely be EBS bottom temp + cold pool, but
> the spike should map the whole menu so later increments are informed.

---

## 1. Candidate datasets

Fill one block per dataset actually located. Priorities from the implementation doc:
MOM6-COBALT-NEP10k (preferred) → NOAA CEFI → Copernicus Marine (fallback).

### Dataset A — NOAA MOM6-COBALT-NEP10k
- Landing page / catalog URL:
- Access method (OPeNDAP / THREDDS / AWS S3 / HTTPS):
- Endpoint(s) tested and reachable? (Y/N, notes on auth):
- Product type (hindcast / reanalysis / reforecast / forecast):

### Dataset B — NOAA CEFI
- Landing page / catalog URL:
- Access method:
- Endpoint reachable?:
- Product type:

### Dataset C — Copernicus Marine (fallback)
- Landing page / catalog URL:
- Access method:
- Auth required? (CMEMS account):
- Product type:

---

## 2. Variables available

Mark availability per dataset. ✓ / ✗ / units / notes.

| Variable | NEP10k | CEFI | Copernicus | Units | Notes |
|----------|:------:|:----:|:----------:|-------|-------|
| Bottom temperature |  |  |  |  | first-increment priority |
| Sea surface temperature |  |  |  |  | cross-check vs OISST |
| Sea ice concentration |  |  |  |  |  |
| Mixed-layer depth |  |  |  |  |  |
| Salinity |  |  |  |  |  |
| Currents (u, v) |  |  |  |  |  |
| Dissolved oxygen (COBALT) |  |  |  |  |  |
| Ocean heat content |  |  |  |  | derivable? |

---

## 3. Temporal resolution & coverage  — **daily vs monthly?**

This decides whether we can reuse the existing daily Hobday engine directly.

- Native temporal resolution (daily / monthly / other):
- If both exist, which variables at which cadence:
- Coverage start date / end date:
- Reference-period implication: existing SST climatology is **1991–2020 daily DOY**;
  NEP10k hindcast typically starts ~1993. Note any baseline-period mismatch to resolve.

---

## 4. Latency  — **can bottom state ever be "live"?**

- How far behind real time is the hindcast/reanalysis? (months / years):
- Is there a near-real-time or forecast product (CEFI reforecast/forecast)?:
- Implication for the dashboard: bottom panels are almost certainly a
  **recent-historical / lagged** product, not near-real-time like SST. Confirm and
  record the typical lag so dashboard copy/API don't imply live monitoring.

---

## 5. Grid  — **regrid to OISST 0.25° vs keep native?**  *(the key risk)*

The entire existing pipeline assumes a regular 0.25° lat/lon grid (cos-lat weights,
rasterized region masks, DOY climatology zarr). MOM6-NEP10k is a **curvilinear ~10 km**
grid — incompatible as-is.

- Confirm native grid type (curvilinear? resolution?):
- Coordinate variables / how to subset a region on a curvilinear grid:
- **Recommendation:** regrid to existing 0.25° grid (e.g. `xesmf` conservative
  remap) so masks/weights/climatology/states engine reuse unchanged — vs. a
  parallel native-grid path. State the decision and why:
- If regridding: extra dependency (`xesmf`/`esmpy`) install feasibility on the box:

---

## 6. Cold-pool derivability  *(the collaborator's headline product)*

- Can EBS cold-pool extent be derived? (area where bottom temp < 2 °C):
- Spatial coverage adequate over the EBS shelf?:
- **Validation target:** does it track AFSC's observed summer **bottom-trawl-survey
  cold pool index**? (This, not "bottom vs Blob", is the credibility win for the
  Kodiak ESR.) Note where to obtain that observed index for comparison:

---

## 7. Access & feasibility notes

- Typical file size / subsetting feasibility (can we pull a region without bulk download?):
- Any rate limits / auth / reliability concerns:
- Rough storage footprint for EBS+GOA, target variables, full hindcast:

---

## 8. Recommendation

- Go / no-go on NEP10k as the Phase-1 source (or pivot to CEFI / Copernicus):
- Variables to prioritise for the first implementation increment:
- Grid strategy decision (regrid vs native):
- Temporal strategy (daily reuse-engine vs monthly separate path):
- Open questions / risks to carry into `feat/bottom-ocean-state`:
