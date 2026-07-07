# Bathymetry-Masking Pass — Plan

**Status:** B0 ✅, B1 ✅, B2 ✅, **B3 ✅** (on branch `feat/bathymetry-mask`) — pass complete; ready
to merge + deploy (bathymetry pass + Arctic).
Prerequisite for Phase 3 (Arctic) and an upgrade for GOA/AI; includes an EBS/NBS cross-validation
experiment. Conventions per `CLAUDE.md`.

**Progress:**
- **B0** — ETOPO 2022 bathymetry layer (`BathySource`, `mhw-build-bathymetry`,
  `shelf_mask_from_bathymetry`). EBS sanity: ETOPO vs Bering10K mask 91.3% agreement / 86% IoU.
- **B1** — EBS/NBS cross-validation: the two masks give **essentially identical cold-pool metrics**
  (area corr 1.000; mean shelf BT diff ≤ 0.08 °C) because they differ only in cells where the
  *model* has no data. **Decision: keep Bering10K mask for the Bering (unchanged), use ETOPO for
  new regions** (`region.mask_source`); no user-facing toggle.
- **B2** — GOA/AI got their continuous 1993–2025 modelled shelf bottom-temperature series (ETOPO
  ≤200 m mask), with a frame-aware regrid for the AI dateline; surfaced as a "Modelled shelf
  bottom temperature — continuous" card (modelled line + survey dots overlaid).
- **B3 (Arctic)** — Chukchi & Beaufort region descriptors (`group="arctic"`, model-only:
  `observed=None`, `has_survey_hauls=False`, MOM6, ETOPO ≤200 m mask). New model-only render path
  (prominent "model-only / unvalidated here" banner + the continuous modelled series, no survey
  overlay). Arctic nav = Bottom Temperature only (no catch). Beaufort basin excluded by the
  ≤200 m cut (narrow ~50k km² shelf vs Chukchi's broad ~250k km²); Arctic bottom temps near
  freezing (−1.2..0.7 °C), physically sensible. Suite 123 green.

## 1. Problem

Regional **domain-averaged** model metrics (mean shelf bottom temperature; cold-pool area) need
a **shelf mask** — the set of grid cells with seafloor depth ≤ 200 m (the slope uses a 200–1200 m
band). Today that depth comes from **Bering10K's own bathymetry** (`z_w`), so the mask can only be
built where **Bering10K covers** (the Bering: EBS/NBS/slope). Consequences:

- **GOA/AI:** no Bering10K depth → **no continuous modelled shelf series** (they rely on
  survey-replication at haul points, which needs no mask, so they only have survey-year data).
- **Arctic (Chukchi/Beaufort):** **no survey at all** → can't fall back on replication → the only
  possible product is a domain average → needs a mask → **blocked** (no Bering10K, and MOM6's
  regrid product carries no depth variable). The Beaufort deep basin (>3000 m, near-freezing
  year-round) makes a depth mask essential, not optional.

Why ≤ 200 m matters: the shelf is where the survey, the fisheries, and the cold pool live; it's
the cold-pool definition's own domain; it matches the survey footprint (apples-to-apples); and it
keeps the large, persistently-cold deep basin from drowning the interannual shelf signal.

## 2. Solution

Read depth from a **standalone, global bathymetry** (model-agnostic) instead of from Bering10K.
A shelf mask is *always* "depth ≤ threshold" — only the **depth source** changes:

| | Depth source | Coverage | Model-tied? |
|---|---|---|---|
| Current | Bering10K `z_w` | Bering only | yes (a model byproduct) |
| Proposed | **ETOPO 2022 / GEBCO** | global | no (model-agnostic) |

This unblocks the Arctic, lets GOA/AI gain a continuous modelled shelf series, and gives **every**
model the identical neutral footprint. **Recommend ETOPO 2022** (NOAA NCEI; clean lat/lon OPeNDAP
subset; `z` = elevation, depth = −z where z<0). GEBCO 2024 is the alternative (higher native res).

## 3. Architecture (mirrors the source-descriptor + cached-mask pattern)

- **`BathySource` descriptor** (`mhw/bottom/sources.py`): OPeNDAP URL, elevation/depth var, lat/lon
  coords — like `BottomSource`.
- **`mhw-build-bathymetry`** CLI (`mhw/bottom/bathymetry.py`): fetch ETOPO over a region's bounds →
  regrid to the region's 0.25° analysis grid → cache a per-region depth grid
  (`data/derived/cold_pool/<region>_depth.npz`). Handle the **dateline** for AI (0–360 subset).
- **`shelf_mask_from_bathymetry(region)`** (`mhw/bottom/coldpool.py`): same
  `shelf_max_depth_m`/`shelf_min_depth_m` thresholds, depth from the cached ETOPO grid.
  `build_shelf_mask(region, source="bathy"|"bering10k")` gains a source switch (keep the
  Bering10K path for the B1 comparison).
- Downstream (`build_model_coldpool_series`, `mean_shelf_bottom_temp`, `coldpool_area_km2`)
  unchanged — they just receive a different mask.
- **Cell-aggregation rule (lock at B0):** a 0.25° cell (~28 km) is "shelf" if its **mean** ETOPO
  depth ≤ threshold (document; mainly affects shelf-break edge cells). Ocean only (depth > 0).

## 4. Phases

- **B0 — Bathymetry layer.** `BathySource` + `mhw-build-bathymetry` + `shelf_mask_from_bathymetry`
  + cached per-region depth grids. Network-free unit tests on the pure depth→mask helper. First
  sanity: ETOPO-mask vs Bering10K-mask **cell overlap** on the EBS grid.
- **B1 — EBS/NBS cross-validation (the experiment).** Rebuild EBS/NBS modelled cold-pool series
  (Bering10K **and** MOM6) with the **ETOPO mask**; compare to current **Bering10K-mask** numbers:
  per-year **cold-pool area (≤2 °C)** and **mean shelf BT** → correlation + mean/abs difference +
  side-by-side plot. *Expect:* mean shelf BT very robust; area may differ near the shelf break
  (footprint-sensitive). **Decision gate:** agree → adopt ETOPO universally; diverge → ETOPO for
  new regions only, Bering10K mask retained for EBS/NBS (documented).
- **B2 — GOA/AI upgrade.** Build the missing **continuous 1993–2025 modelled shelf bottom-temp
  series** (ETOPO mask); add a continuous modelled line + anomaly to the GOA/AI pages, survey dots
  overlaid, labelled "validated at survey years."
- **B3 — Arctic (Phase 3).** Chukchi/Beaufort region descriptors + **model-only** pages on the
  ETOPO mask (tight shelf box excludes the Beaufort basin). Prominent "model-only, no in-region
  validation" labels. No cold pool / catch / replication.

## 5. Key decisions
1. ETOPO 2022 vs GEBCO 2024 (recommend ETOPO).
2. Cell-aggregation rule for 0.25° "is-shelf" (recommend mean depth ≤ threshold).
3. Universal adoption vs new-regions-only — decided by the B1 agreement.
4. Whether to rebuild **slope** (200–1200 m band) on ETOPO for consistency.

## 6. Verification
- **B1 numeric comparison** (ETOPO vs Bering10K mask, EBS/NBS) is the headline validation — if a
  model-independent global bathymetry reproduces the Bering10K-masked cold-pool numbers, the whole
  masked-domain approach is shown robust and portable.
- Suite green; new pure tests for depth→mask.
- Live screenshot checks on upgraded GOA/AI (B2) + new Arctic (B3) pages.

## 7. Data sources
- **ETOPO 2022** — NOAA NCEI global relief (THREDDS/OPeNDAP; `z` elevation, depth = −z).
- **GEBCO 2024** — alternative global bathymetry (THREDDS).
- Existing: Bering10K `z_w` (retained for the B1 comparison), CEFI MOM6 NEP, AFSC survey/coldpool.
