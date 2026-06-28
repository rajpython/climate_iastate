# Alaska Shelf Data Board — Phased Expansion Plan

**Status:** Plan, data-availability **validated live 2026-06-21**. Supersedes the ad-hoc
Appendix A in `bottom_state_guide.md` for the regional matrix (that appendix should be
reconciled to the tables here).

## 1. Vision

The dashboard began as a marine-heatwave (SST) monitor. Building the cold-pool /
bottom-state feature (Bering10K ROMS + CEFI MOM6 + the AFSC survey) surfaced a **wealth of
public ocean and fisheries data** — physical, biogeochemical, and biological — that is real,
downloadable, and largely invisible to the scientists and managers who could use it. The goal
of this expansion is to **bring that data to those users in a friendly, honest, regionally
organised way**.

**Scope boundary (firm):** this is a **data-surfacing board** — observed + model *state*
across variables and regions. **Forecasting is out of scope** here; it is a separate endeavour
owned by the research cell (`docs/forecast_extension/`). The board may *display* a forecast
product the cell delivers later, but the board itself does not build forecasts.

## 2. Verified data-availability matrix (live-checked 2026-06-21)

Five shelf regions have surveys; two Arctic regions are model-only. Key: **✓** available ·
**~** partial / discontinued · **—** none.

### 2a. Observed (AFSC summer bottom-trawl survey + `afsc-gap-products/coldpool`)

| Region | Survey years (cadence) | Observed bottom-temp product | Cold-pool **area** index (≤2 °C) |
|---|---|---|---|
| Eastern Bering Sea (EBS) | 1982–2025 (annual) | ✓ `cold_pool_index` + per-haul | ✓ EBS 1982–2025 |
| Northern Bering Sea (NBS) | 2010–2025 (sporadic) | ✓ `nbs_mean_temperature` 2010–2025 | ✓ NBS 2010–2025 (in NBS product) |
| Gulf of Alaska (GOA) | 1990–2025 (biennial) | ✓ `goa_mean_temperature` 1993–2025 (by subarea) | — (no cold pool) |
| Aleutian Islands (AI) | 1991–2024 (biennial/triennial) | ✓ `ai_mean_temperature` 1991–2024 (by subarea) | — (no cold pool) |
| Bering Sea Slope (BSS) | 2002–2016 (sporadic, **discontinued**) | ~ raw survey hauls only (no packaged product) | — (deep water, no cold pool) |

### 2b. Models (bottom temperature + full health set)

| Region | Bering10K ROMS | MOM6 NEP (CEFI) |
|---|---|---|
| EBS | ✓ 1970–2024 | ✓ 1993–2025 |
| NBS | ✓ 1970–2024 | ✓ 1993–2025 |
| GOA | — (out of domain) | ✓ 1993–2025 |
| AI | ~ Bering-side only (not its validated domain) | ✓ 1993–2025 |
| Bering Sea Slope | ✓ 1970–2024 | ✓ 1993–2025 |
| Chukchi | ~ southern edge | ✓ 1993–2025 |
| Beaufort | — | ✓ 1993–2025 |

### 2c. Catch (FOSS REST API: `afsc_groundfish_survey_{haul,catch,species}`)

Per-species CPUE (kg/km², #/km²) at every haul, joinable to that haul's bottom temperature.

| Region | Catch years |
|---|---|
| EBS | 1982–2025 |
| NBS | 2010–2025 |
| GOA | 1990–2025 |
| AI | 1991–2024 |
| BSS | 2002–2016 |

## 3. Three clarifications that shape the plan

1. **"Cold pool" is an EBS/NBS shelf phenomenon — not a universal product.** It is the ≤2 °C
   bottom water left by winter sea-ice formation on the shallow shelf. The observed cold-pool
   *area* index exists only for **EBS** (`cold_pool_index`) and **NBS** (`nbs_mean_temperature`,
   which carries `AREA_LTE2_KM2`). **GOA, AI, and the slope have no cold pool** — for them the
   product is **bottom-temperature conditions**, not a cold-pool index. So the EBS page
   *replicates as a cold-pool page* only to NBS; GOA/AI/slope become bottom-temperature pages.

2. **The NBS "late start" is a *survey* limit, not a model one.** Observed NBS begins 2010
   (sporadic). But **both models cover NBS from their start** — Bering10K 1970–, MOM6 1993– —
   so the modelled NBS record is long and continuous; only the observed validation is short and
   gappy. Label accordingly.

3. **AI and BSS were absent from the cold-pool appendix because they have no cold pool — not
   because they lack data.** Both have observed bottom temperature (AI: a packaged index
   1991–2024; BSS: raw hauls 2002–2016, survey discontinued) and model bottom temperature
   (MOM6 everywhere; Bering10K covers the slope fully and the AI Bering-side partially). They
   belong on the board as **bottom-temperature + catch** regions.

## 4. Phased plan

### Phase 0 — Foundations (enable everything else)
- **Region dropdown architecture.** Mirror the MHW page pattern: a region selector drives
  re-rendering on the same page. The bottom-state engine is already source-agnostic; make it
  **region-aware** (region → masks, products, model domains, labels).
- **Catch × bottom-state adapter** (kept from the A.4 sketch). A small reusable module that
  pulls FOSS `haul` ⟕ `catch` on `hauljoin` (simple `{"species_code":N}` filter, **not** the
  WAF-blocked `$in`), returns a tidy per-haul `(year, region, lat, lon, depth, bottom_temp,
  species, cpue)` frame, cached to parquet. Feeds both the catch page and the catch×temp view.
- **Deliverable:** no new user page yet; the plumbing that Phases 1–2 build on.

### Phase 1 — Complete the Bering (EBS ✓ → add NBS + slope) + Bering catch page
*Highest priority; the cold-pool science and the snow-crab story live here.*
- **NBS cold pool:** replicate the existing EBS two-page treatment for NBS — observed index
  (`nbs_mean_temperature`, 2010–2025) + Bering10K + MOM6, survey-replicated validation. Same
  code, new region + masks.
- **Bering Sea slope:** **bottom-temperature** panels only (no cold pool — deep water).
  Observed = survey hauls 2002–2016 (clearly flagged discontinued); models = Bering10K + MOM6.
- **Region dropdown:** EBS / NBS / Slope on the bottom-state page(s).
- **Bering catch page (new page):** haul catch for EBS + NBS + slope. **Snow crab is the
  headline** (cold-water specialist); lead with the **catch × bottom-temperature** view
  demonstrated in A.4 (2023 EBS: ~8× denser in the cold pool, ~84 % of biomass ≤2 °C). Add
  red king crab, pollock, Pacific cod as contrasts.
- **Validation status:** all green — every input verified above.

### Phase 2 — Gulf of Alaska + Aleutian Islands (bottom-temp conditions + catch)
*These shelves have no cold pool; the product is bottom-temperature conditions and catch.*
- **GOA:** observed `goa_mean_temperature` (1993–2025, by subarea) + **MOM6** (1993–2025;
  no Bering10K by construction). Bottom-temperature conditions page + GOA catch page.
- **AI:** observed `ai_mean_temperature` (1991–2024) + **MOM6** (Bering10K only partial).
- **Region-appropriate key species** (defer exact list to ESR/Erin input): GOA — Pacific cod,
  walleye pollock, sablefish, arrowtooth flounder, Pacific ocean perch; AI — Atka mackerel,
  Pacific ocean perch, Pacific cod.
- **Validation note:** MOM6's validation outside the Bering is less established (see the
  Holsman outreach) — label GOA/AI model panels as *less-validated* until confirmed.

### Phase 3 — Arctic (Chukchi / Beaufort), model-only
- **MOM6 bottom temperature + health indicators** only — **no survey**, so **no observed
  validation and no catch**. Include for completeness with prominent "model-only, unvalidated
  here" labelling. Lowest priority.

### Cross-cutting: other health indicators (any phase, MOM6-led)
The full COBALT set (salinity, dissolved oxygen incl. seafloor, nutrients, plankton, currents,
sea ice, acidification/aragonite) is public for the whole MOM6 domain (1993–2025) and Bering10K
carries most of it (no acidification). These become **per-variable layers** once the regional
scaffolding exists — oxygen and aragonite (crab-shell) are the highest-value for the fisheries
audience.

## 5. Remaining validation items before/within each phase
- ⬜ Confirm `nbs_mean_temperature` area-index methodology matches the EBS index (so the NBS
  cold-pool page is apples-to-apples) — read the coldpool package docs.
- ⬜ Confirm the EBS-shelf ≤200 m mask logic generalises to NBS (and define a slope/GOA/AI
  depth treatment — these are *not* cold-pool ≤200 m problems).
- ⬜ GOA/AI: pick the management-relevant key species with ESR/Erin input (Phase 2 gate).
- ⬜ MOM6 GOA/AI/Arctic validation standing (open question in the Holsman email).
- ⬜ BSS: decide how to present a **discontinued** survey (2002–2016) honestly alongside live
  models.

## 6. Data sources (all public, verified)
- **Observed:** `afsc-gap-products/coldpool` (Zenodo 10.5281/zenodo.16915337) — `cold_pool_index`
  (EBS), `nbs_mean_temperature`, `goa_mean_temperature`, `ai_mean_temperature`, per-haul temps.
- **Catch:** NOAA FOSS REST API `apps-st.fisheries.noaa.gov/ods/foss/afsc_groundfish_survey_*`.
- **Models:** Bering10K ROMS (PMEL ACLIM THREDDS) · CEFI MOM6 NEP (PSL THREDDS / CEFI S3).
- **Biomass indices / assessments (future):** afsc-gap-products `gap_products`, AKFIN, RAM Legacy.
