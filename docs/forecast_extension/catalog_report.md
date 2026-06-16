# Bottom-Ocean-State Data Discovery — Catalog Report

**Branch:** `feat/mom6-spike` (name now a slight misnomer — see *Pivot*, below)
**Type:** Discovery only. **No implementation.** Deliverable is this filled-in report.
**Target:** ~1 week. Goal is to *reduce uncertainty* before any `feat/bottom-ocean-state`
work begins — especially the grid, cadence, and latency questions, which are the real
risks.

**Status:** Discovery passes 1 + 2 complete (2026-06-16). Primary source, access,
grid, cadence, latency, variables, validation target, storage, and the regrid
dependency are all resolved. Remaining open items are narrow and flagged ⬜.
**Layer-3 (forecasting) scoping added as §9.**

---

## Pivot — Bering10K ROMS, not MOM6 (steered by AFSC)

The spike was scoped around NOAA **MOM6-COBALT-NEP10k**. Discovery — prompted by the
CEFI two-pager from our AFSC/Kodiak collaborator (`CEFI.pdf`) and her note — moves the
primary target to the **Bering10K ROMS** model:

> *"I believe the MOM6 validation is still underway as much of the work in our region
> has validated the Bering 10K ROMS model."* — AFSC collaborator, June 2026

The CEFI doc confirms the Alaska CEFI pilots are **ACLIM** (Alaska Climate Integrated
Modeling, Bering Sea — built on Bering10K ROMS) and **GOA-CLIM** (Gulf of Alaska).
For the eastern Bering Sea — and the **cold-pool product** specifically — the
validated, credible model is **Bering10K ROMS**, not MOM6. MOM6/CEFI is demoted to a
watch-list source pending its Alaska validation.

**Headline result:** the *entire credibility loop is self-service*. Both the model
(Bering10K hindcast) and its validation target (the AFSC observed cold-pool index)
are openly downloadable today, with no NOAA request required. We can build and
validate an EBS bottom-temperature / cold-pool product end-to-end ourselves.

---

## 1. Candidate datasets

### Dataset A — Bering10K ROMS / ACLIM  **(PRIMARY, EBS)**
- **Landing / docs:** https://beringnpz.github.io/roms-bering-sea/B10K-dataset-docs/
- **Source code:** GitHub `beringnpz/roms-bering-sea`
- **Dataset doc (PDF):** Zenodo `4586950` (Kearney 2021, "The Bering10K Dataset").
  **Variable list spreadsheet:** `Bering10K_simulation_variables.xlsx`, Google Drive
  ID `1C1FCxRMBm0uBv2wEKwrGfHmLnjt_gFvG` (public; via https://tinyurl.com/b10kvariablelist).
- **The simulation we want — the operational hindcast: `B10K-K20_CORECFS`.**
  Per the dataset doc: *"If you're looking to compare the model to real-world
  observations, this is probably the simulation you want to use."*
  - **K20** = 30-vertical-layer BESTNPZ variant (Kearney et al. 2020); the most
    up-to-date code. (Older `B10K-H16_CORECFS`, 10-layer, also public.)
  - **CORECFS** forcing = CORE2 (1970–94) + CFSR (1995–Mar 2011) + CFSv2 Operational
    Analysis (Apr 2011–present). All reanalysis → reflects observed atmosphere.
  - **Coverage 1970–present; updated ~3×/year** (Jan, late Apr, late Aug).
- **Access (open, no auth for the public server):**
  - THREDDS / OPeNDAP — `https://data.pmel.noaa.gov/aclim/thredds/`
  - ERDDAP — `https://data.pmel.noaa.gov/aclim/erddap/`
  - Live Access Server — `https://data.pmel.noaa.gov/aclim/las/`
  - Two formats: **individual files** (under `files/`; OPeNDAP *or* HTTPS — HTTPS
    recommended for local download) and per-simulation **aggregated** endpoints
    (OPeNDAP only; one combines all bottom-averaged Level 2 variables).
  - (Auth gates only the raw UW hyak-mox cluster files / collaborator-only sims — *not*
    the public hindcast.)
  - ⬜ The 2021 doc's per-dataset catalog sub-paths have since been reorganized on the
    server (guessed `/catalog/B10K-K20_CORECFS/...` and `/catalog/files/...` now 404).
    Server is live (top-level catalog renders); confirm the *current* catalog path /
    ERDDAP dataset ID for the K20_CORECFS bottom-temp files at implementation start.
- **Public vs collaborator-only:** public = the **CORECFS hindcasts** (H16 + K20) and the
  ACLIM Phase-1 CMIP5 projections. Collaborator-only = CMIP6 / ACLIM Phase 2 / carbon /
  physics-only hindcasts. **Our needs are entirely in the public set.**
- **Bonus — ACLIM indices (Level 3), pre-computed:** regional-average time series over
  AFSC groundfish-survey strata polygons (`ACLIMregion_*.nc`) **and survey-replicated
  time series** (model sampled to mimic the bottom-trawl survey). See §6 — these may let
  us skip regridding for regional products and give a near-drop-in observed comparison.
- **Domain caveat:** Bering10K covers the **Bering Sea / EBS** (incl. NBS, slope), **not
  the Gulf of Alaska**. GOA bottom state is the separate **GOA-CLIM** pilot — a later
  question; our first increment is EBS, so this is not a blocker.

### Dataset B — AFSC observed cold-pool index  **(VALIDATION TARGET)**
- **Repo:** GitHub `afsc-gap-products/coldpool`
- **Archive / DOI:** https://doi.org/10.5281/zenodo.16915337
- **Access (open):** R package (`devtools::install_github("afsc-gap-products/coldpool")`)
  **or** plain `.rda` files from the repo `/data/` directory — no R install required.
- **Contents:** cold-pool **area index** (km² of EBS bottom-trawl footprint ≤ 2 °C),
  mean bottom (gear) temperature, mean SST, interpolated temperature rasters, some
  bottom salinity.
- **Coverage:** EBS **1982–2025** (no 2020); NBS sporadic (2010, 2017, 2019, 2021–23);
  GOA 1990–2023; AI 1991–2024.
- **Source:** AFSC summer bottom-trawl surveys (Groundfish + Shellfish Assessment).

### Dataset C — NOAA CEFI regional MOM6 (NEP)  **(WATCH-LIST — but the one public *forecast* feed)**
- **Portal:** https://psl.noaa.gov/cefi_portal/  •  Cookbook:
  `noaa-cefi-portal.github.io/cefi-cookbook/` (Python/R OPeNDAP, query generator).
- **Products:** historical MOM6 simulation (1993–2019, §4) **plus a forecast arm** —
  **1-year seasonal forecasts, initialised 4×/yr**, GFDL **SPEAR** global model downscaled
  to regional MOM6. The **Northeast Pacific (NEP)** domain spans **Baja California → the
  Chukchi**, i.e. it **covers the Bering Sea and Gulf of Alaska**. Per the portal, NEP
  **hindcast + reforecast data are public (as of Jan 2025)**; the NEP **operational**
  forecast is "coming soon."
- **Access (public):** PSL THREDDS, **AWS S3**, **Google Cloud Storage**, OPeNDAP + direct
  download.
- **Why it matters:** this is the **only public *forecast* feed covering our region** —
  more accessible than the Bering10K reforecast (which is not a public download, §9.4).
- **The binding caveat is validation, not access:** this is the same MOM6 product Erin
  flagged as **Alaska validation "still underway."** So for the Bering: the *public-forecast*
  model (CEFI/MOM6) is not yet validated here, while the *validated* model (Bering10K) has
  no public forecast feed. Public ≠ usable-with-confidence.
- ⬜ Verify: does the CEFI NEP product carry **bottom temperature** (`tob`)? Operational vs
  reforecast-only status for NEP? Bering/GOA validation skill?

*(Copernicus Marine retained only as a distant fallback; not pursued given A is open
and validated.)*

---

## 2. Variables available

Bottom temperature is a **Level 2 derived variable** (computed post-run, on the native
grid, netCDF — the doc lists "surface and bottom temperature" as the canonical Level 2
example). 3-D `temp` is Level 1 on the rho-grid. ⬜ Read the exact Level-2 bottom-temp
short name from the variable spreadsheet (Drive `…gFvG`) — the pass-2 read truncated
just before the `t` rows; likely `temp_bottom5m`, confirm before coding `io`.

| Variable | Bering10K (K20_CORECFS) | CEFI MOM6 | AFSC coldpool | Notes |
|----------|:----------------------:|:---------:|:-------------:|-------|
| Bottom temperature | ✓ Level 2 derived | ✓ | ✓ (observed) | first-increment priority |
| Sea surface temperature | ✓ Level 2 derived | ✓ | ✓ (observed) | cross-check vs OISST |
| Sea ice (`aice` fraction, `hice`) | ✓ Level 1 | ✓ | — | same ice-mask role as OISST |
| Salinity | ✓ | ✓ | partial | rho-grid |
| Currents (u, v) | ✓ (`uEast`,`vNorth` geo-rotated) | ✓ | — | aliasing caveat (weekly vs tidal) |
| Surface boundary-layer depth (`Hsbl`) | ✓ Level 1 | ✓ (MLD) | — | ≈ MLD proxy |
| Dissolved O₂ / nutrients / plankton | ✓ (BESTNPZ) | ✓ (COBALT) | — | biological modules |
| Cold-pool area index | derived (≤2 °C) | derived | ✓ (observed) | the product |

---

## 3. Temporal resolution & coverage — **weekly averages**

- **`average` output = WEEKLY-averaged** per cell (time value = midpoint of the week).
  (Also: `history` = weekly snapshots; `stations` = 6-hourly at select points — not
  needed.) Files are split into **5-year blocks**, named
  `{model}_{parent}_{startyr}-{endyr}_{outputtype}_{variable}.nc`.
- **Coverage:** hindcast **1970–present**, refreshed **~3×/year**.
- **Reference-period implication:** our SST climatology is **1991–2020 daily DOY**.
  Bottom-state is **weekly** — the daily Hobday engine does **not** reuse directly. Build
  a **weekly bottom-temp climatology / threshold** (or aggregate the daily engine to
  weekly). Main engine-adaptation consequence of the pivot.

---

## 4. Latency — **lagged, not live (but fresher than MOM6)**

- **Bering10K K20_CORECFS:** CFSv2 forcing runs to ~recent; hindcast refreshed **~3×/yr**
  → effective lag on the order of months. Genuinely "recent historical," not real-time.
- **CEFI MOM6:** historical sim ends **2019** → multi-year lag; clearly not NRT.
- **Implication:** bottom-state panels are a **recent-historical / lagged** product, *not*
  near-real-time like the OISST SST monitor. Dashboard copy and API must say so; update
  cadence ≈ the ROMS ~3×/yr refresh.

---

## 5. Grid & the regrid dependency — **resolved; not a blocker**

- **Grid (confirmed):** curvilinear, terrain-following **s-coordinate** (30 layers, K20);
  horizontal ~**10 km**, cells relatively even (no curving/distortion) but **rotated**
  vs geographic N–E; Arakawa C-grid (temp/salinity on the **rho**-grid). Grid ≈
  **182 (ξ) × 258 (η)** ≈ 47k cells. **lat/lon are embedded in every Level 1–2 file**
  (also `Bering_grid_withFeast.nc`). Bottom temp is a **2-D field** once the Level-2
  bottom layer is taken — no vertical handling needed on our side.
- **The dependency finding (the real risk, now characterized):** this repo is
  **pyenv + pip only — no conda** (`pyproject.toml`; `xarray 2026.2.0`, `scipy 1.12`,
  `netcdf4` present; `xesmf`/`esmpy` **not** installed). `xesmf`/`esmpy` are hard to
  pip-install (ESMF bindings effectively need conda-forge), so the catalog's original
  "xesmf conservative remap" assumption would force a conda toolchain.
- **Mitigations (why it's not a blocker):**
  1. Grid is evenly-sized & merely rotated, with lat/lon embedded → a **pip-installable
     `pyresample`** (kd-tree nearest/Gaussian) or even `scipy.interpolate` is adequate to
     regrid onto our 0.25° grid for a first increment.
  2. The **ACLIM Level 3 regional / survey-replicated indices** are *already* aggregated
     off the native grid → for regional-outlook products we may **not regrid at all**.
- **Decision (revised):** **pyresample/scipy path first** (no conda); reserve
  conservative `xesmf`-via-conda only if area-weighted remap proves necessary later.

---

## 6. Cold-pool derivability — **yes, and observationally validatable**

- **Derivable:** cold-pool extent = area where bottom temp **≤ 2 °C** (also 1/0/−1 °C).
  Directly computable from the K20_CORECFS Level-2 bottom-temp field over the EBS shelf.
- **Two validation routes against observations:**
  1. **AFSC observed cold-pool index** (Dataset B) — does the modeled cold pool track the
     observed summer bottom-trawl index? The credibility win for the Kodiak ESR.
  2. **ACLIM survey-replicated bottom-temp time series** (Level 3) — Bering10K already
     sampled to mimic the bottom-trawl survey → a near-apples-to-apples comparison that
     removes sampling-mismatch as a confound.
- **Prior art / benchmark:** Frontiers in Marine Science (2025), *"An updated regional
  model skill assessment for seasonal and interannual variability of bottom temperature
  across the eastern Bering Sea shelf"*; Kearney et al. (2020, GMD) model + skill.

---

## 7. Access & feasibility notes

- **Subsetting:** OPeNDAP/ERDDAP allow server-side region+variable subsetting; HTTPS for
  whole-file local copies. NetCDF, 5-year blocks.
- **Storage:** bottom temp is a single 2-D field, weekly: ~47k cells × 4 B ≈ 0.19 MB/step;
  weekly × ~55 yr ≈ 2,860 steps ≈ **~0.5 GB uncompressed** for the *entire* hindcast
  bottom-temp field (full domain). Trivial; a few GB even adding SST + ice. EBS-only
  subset is far smaller.
- **Auth / reliability:** public PMEL server, no account; only the UW cluster / collaborator
  sims are gated. No CMEMS-style login needed for A or B.
- **New dependency:** `pyresample` (pip) for regrid — see §5. No conda required.

---

## 8. Recommendation

- **Go / no-go:** **GO on Bering10K ROMS `B10K-K20_CORECFS` (public hindcast) as the
  Phase-1 EBS source.** Open, validated in region, fresher than MOM6, with two
  observational validation routes in hand.
- **First increment:** **bottom temperature → EBS cold-pool area index.**
- **Validation:** modeled cold pool vs **AFSC observed index** (Zenodo `16915337`) and vs
  the **ACLIM survey-replicated** series; benchmark against the 2025 Frontiers assessment.
- **Grid strategy:** **`pyresample`/`scipy` regrid → 0.25°** (pip, no conda); or use ACLIM
  Level 3 regional indices and skip regridding for regional products. Bottom temp is 2-D.
- **Temporal strategy:** **weekly** — build a weekly bottom-temp climatology/threshold; do
  *not* assume the daily DOY engine transfers unchanged.
- **MOM6/CEFI:** watch-list only, revisit when Alaska MOM6 validation lands.
- **GOA:** deferred to GOA-CLIM; out of scope for the first increment.

### Open items to carry into `feat/bottom-ocean-state`
1. ⬜ Exact Level-2 bottom-temp short name from the variable spreadsheet (Drive `…gFvG`;
   likely `temp_bottom5m`).
2. ⬜ Current live catalog path / ERDDAP dataset ID for K20_CORECFS bottom temp. Partial:
   a working `files/` path exists, e.g.
   `data.pmel.noaa.gov/aclim/thredds/catalog/files/B10K-K20nobio_CORECFS_daily.html`.
3. ⬜ Bottom-temp climatology cadence. Note a **daily** physics-only variant
   (`B10K-K20nobio_CORECFS_daily`) is on the public server → daily Hobday-engine reuse may
   be feasible after all; weigh vs the weekly `average` product.
4. ⬜ `pyresample` install + a one-cell regrid sanity check on the box (conda-free path).
5. ⬜ GOA-CLIM access (only when GOA bottom state is in scope).

---

## 9. Layer 3 — Forecasting (scope)

*Discovery, 2026-06-16. Scopes whether and how a bottom-state **forecast** (beyond the
historical product of §§1–8) is feasible self-service. The §§1–8 hindcast is the
foundation; this section is the forward-looking layer.*

### 9.1 Is EBS bottom temperature seasonally forecastable? — Yes, with published skill
- **Kearney et al. 2021** (*JGR Oceans*, "Seasonal predictability of sea ice and bottom
  temperature across the eastern Bering Sea shelf") — **now read in full** (open-access
  CC-BY). It downscaled NMME global reforecasts (CFSv2, CanCM4) through Bering10K for
  1982–2010, initialised every month, and assessed skill via anomaly correlation
  coefficient (ACC; 0.5 ≈ threshold for synoptic skill) vs a **persistence** baseline.
  Findings, verbatim where it matters:
  - **Summer bottom temperature is predictable at leads up to ~4 months** *when initialised
    in the ice-free window (≈April–October)* — ACC near 1.0 at 1-month lead, staying high
    through summer until the next ice season.
  - **"The majority of the prediction skill derives from the persistence signal, and a
    persistence forecast is comparably skillful to the dynamic forecast."** The dynamic
    model's gain is **marginal** (≈1–2 months in specific init windows, mostly
    May-initialised 1–3-month leads); "considered independently, neither CFS nor CanCM4
    outperformed the persistence forecast."
  - **Sea ice is a prediction *barrier*:** forecasts initialised before/during the ice
    season (Oct–Feb) lose skill — neither dynamic nor persistence predicts summer bottom
    temperature across the ice season. Sea-ice extent itself is barely predictable beyond
    persistence (low Pacific-sector predictability).
  - **Damped persistence ≈ persistence** for ice-crossing leads (a useful config note).
- **Mechanism = real physical memory:** the cold pool forms each winter via brine
  rejection under sea ice and *persists* into summer. That memory is what makes
  spring→summer prediction work — sea-*surface* temperature has no equivalent.
- **Cox et al. 2026** (*JGR Oceans*) predicts the wintertime Bering ice edge with a
  **Linear Inverse Model (LIM)** — one of the exact method families in our SST research
  proposal. The two tracks share methods.

### 9.2 The authors' own recommendation — *use persistence* (this is Route A)
Kearney 2021's Discussion concludes (paraphrasing closely): running a dynamically
downscaled multimodel forecast operationally is **high-cost**; adding a **persistence
forecast** to the hindcast framework (which already updates ~3×/yr to within weeks of real
time) is **simple**; and given the dynamic model's only *marginal* skill gain, **"the
persistence forecast is the more efficient choice… capable of providing a skillful,
spatially resolved prediction of the cold pool as early as April"** — early enough for the
NPFMC management/quota cycle. **The domain authority recommends precisely what our engine
does.** They flag **linear inverse modeling (LIM)** as the natural next step *beyond*
persistence — which is our SST proposal's method family and the Cox et al. 2026 ice-edge
paper. The two tracks converge on the same toolkit.

### 9.3 Two routes
- **Route A — our own statistical engine on bottom-temp anomalies (FAVOURED, self-service).**
  The source-agnostic engine (`src/mhw/forecast/`) applies unchanged: forecast a bottom-temp
  anomaly field (persistence / damped persistence / AR(1)) vs a bottom-temp threshold →
  exceedance probability → cold-pool-probability map + regional outlook. The field's own
  product is persistence-based and Kearney 2021 supplies the skill benchmark and scientific
  cover. **Uses only public data we already have (§§1–8) — no NOAA ask.**
- **Route B — ingest the dynamical seasonal forecast (DEFERRED, collaboration).** Heavier,
  and gated by access (§9.4); the dynamical run's value is a skill *ceiling*, not a
  prerequisite. Revisit via collaboration once Route A is proven.

### 9.4 Access status — *now resolved from the paper's Data Availability Statement*
- **Hindcast + observed index:** public, confirmed (§§1–2). Bonus: a **daily** physics-only
  hindcast variant (`B10K-K20nobio_CORECFS_daily`) is on the public server.
- **The dynamical reforecast output:** **only the *summarized* output behind the figures is
  public** — Zenodo **10.5281/zenodo.4735496** (Kearney et al. 2021, *Supporting data*).
  The **full gridded reforecast ensemble** (1,044 sims × 2 parent models) is **not**
  published as a downloadable product. *(This corrects an earlier overstatement: it's not
  that it's "locked away" — the authors simply archived summaries, not the full ensemble.)*
- **No public *Bering10K* forecast feed** — Kearney 2021 was a **retrospective** reforecast
  (1982–2010); the validated Bering10K model has no operational public forecast output.
  **However — correcting an earlier overstatement — public NOAA forecast data *for our
  region* does exist elsewhere:** the **CEFI regional MOM6 (NEP)** forecast arm (Dataset C)
  — 1-yr SPEAR-driven seasonal forecasts, NEP reforecast public since Jan 2025, operational
  "coming soon", on PSL THREDDS / AWS / GCS — and **NMME** global seasonal forecasts
  (NCEI/IRI, ~1°) usable as coarse predictors. The constraint on these is **validation for
  the Bering, not access** (CEFI/MOM6 Alaska validation is "still underway").
- **Why Route B is deprioritised — by the science, not just access:** the authors
  themselves conclude the dynamic forecast isn't worth the cost over persistence (§9.2).
  So even with full access, Route B adds little. **Route A is self-service** — we generate
  the persistence forecast ourselves from the public hindcast + climatology.
- **If Route B is ever revisited, it's a *capability* collaboration, not a data grab:** the
  CFSv2→downscaling chain is not reproducible without dynamical-modeling infrastructure, so
  it would mean co-production with ACLIM/AFSC (Holsman, Kearney) — a joint product with
  authorship/ownership implications — pursued only if the *relationship* (not the skill) is
  the goal.

### 9.5 Connection to the research program & the gate
Bottom-state forecasting is the **bottom-temperature analogue of the SST forecast-skill
study** and lives under the *same* governing research proposal and the *same* deployment
gate (BSS > 0 vs climatology **and** persistence; calibration; field significance). The
method-survey work package already spans these families (persistence, AR, LIM). No new
governance needed — it extends the existing program.

### 9.6 Why this may be the *stronger* forecast story
- Genuine **seasonal predictability** (~4-month skill) from ice-driven memory — SST
  persistence decays in weeks.
- Our statistical approach **matches established operational practice** → lower novelty
  risk, easier to defend to a Council.
- A **probabilistic cold-pool outlook ahead of the summer survey** is directly useful to
  the snow-crab / groundfish ESR audience.

### 9.7 Open items / next steps (Layer 3)
1. ✓ *Resolved.* Route B output is not publicly archived beyond figure summaries (Zenodo
   `4735496`); no live forecast feed. Route B = capability collaboration only (§9.4).
2. ✓ *Resolved.* Kearney 2021 read in full; configuration captured below.
3. ⬜ Spec a bottom-temp **persistence / damped-persistence** backtest reusing `baselines`
   / `exceedance` / `backtest`, following Kearney 2021's design so results are comparable:
   - **Target:** summer cold pool (paper's window ≈ **June 1–Aug 1**); init from the
     ice-free side (**≈April–May**) — *do not* expect skill across the Oct–Feb ice barrier.
   - **Bottom temp** = mean over the **bottom 5 m** of each cell; **threshold = 2 °C** for
     cold-pool area.
   - **Baseline** = persistence of the hindcast anomaly from the month before init across
     all leads; **metric** = ACC vs lead-dependent climatology (ACC ≈ 0.5 = skill floor),
     alongside our BSS gate.
   - **Truth:** Bering10K hindcast (1982–2010+) as primary, plus the **AFSC observed**
     cold-pool index and the **survey-replicated** series (§6).
4. ⬜ Later: **LIM as the "beyond-persistence" step** (Kearney's own suggestion). Region-
   specific template now in hand — **Cox & Penland 2026** applies LIM to the wintertime
   Bering **ice edge**, benchmarked against **persistence and AR(1)**, with **public MATLAB
   code** (Zenodo `10.5281/zenodo.18461482`, NOAA-PSL, public domain → port to Python).
   Folds into the SST research program's method survey. **Scope caveat — method reference,
   not a recipe:** Cox forecasts ice-edge *latitude* at *weather-to-subseasonal* leads
   (skill ~5–9 days, Jan–Mar) — a different variable, timescale, and *season* (inside the
   ice barrier) than our seasonal cold-pool product. Two transferable lessons regardless:
   (a) persistence is again beaten only marginally (~1 day by LIM/AR1) → baselines-first
   holds; (b) **"forecasts of opportunity"** — condition forecast *confidence* on the
   atmospheric state (ALBSA index) — a defensible state-dependent uncertainty pattern for
   the dashboard.
5. ⬜ *Candidate separate product (park, don't bundle):* a short-lead (days) **ice-edge**
   forecast is itself ESR / crab-fisher-relevant (Cox's motivation is navigation safety in
   ice) and Cox 2026 is a near-drop-in blueprint with public code. Different product from
   the cold pool, **same audience** (snow crab / Erin). Not part of the cold-pool increment.

---

*Discovery sources (passes 1–3, 2026-06-16): Bering10K dataset doc (Kearney 2021,
Zenodo 4586950) + variable spreadsheet (Drive); PMEL ACLIM THREDDS/ERDDAP/LAS;
`afsc-gap-products/coldpool` (Zenodo 10.5281/zenodo.16915337); NOAA CEFI portal
(psl.noaa.gov/cefi_portal); CEFI two-pager (`CEFI.pdf`); Kearney et al. 2021 (JGR
Oceans, seasonal predictability); Cox et al. 2026 (JGR Oceans, ice-edge LIM);
Frontiers 2025 EBS bottom-temp skill assessment; Kearney et al. 2020 (GMD); local
`pyproject.toml`.*
