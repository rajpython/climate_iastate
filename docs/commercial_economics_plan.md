# Commercial Landings & Fishery-Economics Extension — Phased Plan

**Status:** Plan. Data-availability **verified live 2026-06-26**. To be undertaken **after the
ecosystem-state expansion Phase 2 (GOA + Aleutian Islands)** is complete (Phase 2 done /
on branch `feat/goa-ai-bottom-state`). This is a **new data domain** (fishery-*dependent*
harvest economics), distinct from the current board's fishery-*independent* survey/model state.
Numbered **E0–E4** to avoid collision with the ecosystem-state Phase 0–3 numbering.

## 1. Vision & scope

The board currently shows ecosystem *state* (survey CPUE, model bottom temperature, the cold
pool). This extension adds the **commercial harvest** layer that fishery economists work with:
**region-wise commercial landings (tons) and ex-vessel value ($)** by species and year, clearly
separated from the scientific survey.

**Scope boundary (firm).**
- **Aggregated, non-confidential data only.** Vessel/processor-level and fine area×species×gear
  cells are suppressed under NOAA's "rule of three" (≥3 vessels/processors). Every page is
  area × species × year (× sector/gear where non-confidential).
- **Commercial harvest ≠ survey.** Always labelled **fishery-dependent (commercial harvest)** to
  distinguish from the survey pages. The survey is a separate, fishery-independent program; no
  commercial vessel is part of it. See the survey-vs-commercial framing in
  `bering_bottom_state_guide.md`.
- **No forecasting / no confidential data ingest.** Same firm boundaries as the rest of the board.

## 2. Verified data-availability matrix (live-checked 2026-06-26)

| Source | Content | Region resolution | Value ($)? | Access pattern | Years |
|---|---|---|---|---|---|
| **NOAA FOSS Commercial Landings** | landings by species | **statewide AK only** | ✅ ex-vessel $ | **live REST API** (`…/ods/foss/landings/`, same infra as the survey tables) | 1950–2024 |
| **AKFIN Apex Reports** (`reports.psmfc.org/akfin`) | Comprehensive **Blend CA** (total groundfish catch, Blend + Catch Accounting System); **Comprehensive FT** (fish tickets + earnings); **ENCOAR** (processor production/value); **Economic SAFE** | ✅ **NPFMC areas** (BSAI / GOA subareas / AI) | ✅ (Economic SAFE / FT) | **public interactive tool → Excel/text export** (no login for public reports; **no open API**; granular tables credentialed) | 1991– (ENCOAR 1984–) |
| **ADF&G** (`adfg.alaska.gov` → Statistics & Data) | **COAR** (ex-vessel + wholesale value by area/species); crab/shellfish harvest; BSAI **crab annual management reports** | ✅ ADF&G areas/districts (e.g. Registration Area J) | ✅ COAR | dashboards + table downloads + **PDF reports** | multi-decade |
| *Reference only* | Economic SAFE PDF; RAM Legacy (catch-by-stock); NPFMC SAFE | broad/stock | — | PDF / DB | — |

**Headline finding:** region-wise commercial data **is public and non-confidential at the area
level**, but — unlike the survey — **none of it is a live REST API except FOSS (statewide only)**.
AKFIN is a public *interactive* tool with Excel/text export; ADF&G is dashboards + tables + PDFs.
So the ingestion pattern is **"download a published export → cache to parquet → refresh on a
periodic (annual/seasonal) cadence,"** plus PDF extraction for some crab series — not live fetch.

## 3. Three clarifications that shape the plan

1. **Spatial units don't match the survey.** Survey regions (EBS, NBS, GOA, AI, slope) ≠ NPFMC
   **management areas** (BSAI bundles Bering + Aleutians; GOA splits into Western 610 / Central
   620+630 / West Yakutat 640 / Southeast Outside 650; crab by Bering Sea districts). A
   **management-area ↔ board-group crosswalk** is the first build artifact (see §6).
2. **Catch (CAS) vs landings (fish tickets) vs value (COAR/Economic SAFE) are different numbers.**
   *Total catch* (retained + discarded, from the Catch Accounting System) ≠ *landings* (retained,
   from fish tickets) ≠ *ex-vessel value* ($). Label each panel by which it is.
3. **Update cadence is slow.** These refresh annually/seasonally (finalized with a lag), not
   daily. Refresh is a periodic job, and "latest finalized year" labelling matters.

## 4. Architecture (mirrors the existing source-descriptor + CLI pattern)

- **New package `src/mhw/econ/`** (parallels `src/mhw/bottom/`):
  - `sources.py` — a `LandingsSource` descriptor per source (FOSS / AKFIN-export / ADF&G), the
    only source-specific config (URL or local-export path, field map, units, value fields).
  - `areas.py` (or `config/mgmt_areas.yml`) — the **management-area ↔ board-group crosswalk**
    (`bering`, `goa`, `ai`) + native-area labels.
  - `confidential.py` — a small helper enforcing the rule-of-three aggregation and a
    `confidential` flag (defensive; public exports are already suppressed).
- **Fetch/ingest CLIs** following the house pattern (docstring `CLI:` line, `PROJECT_ROOT`,
  pure helpers separated from IO, `parse_args/main`, `save_parquet`, `[project.scripts]` entry):
  `mhw-fetch-landings-foss` (live API), `mhw-ingest-landings-akfin` (parse a downloaded Apex
  export), `mhw-ingest-crab-adfg` (tables/PDF). Mirror `fetch/foss_catch.py`.
- **Tidy target schema** (one parquet per source, cached under `data/raw/`, gitignored):
  `(year, mgmt_area, area_group, species, species_code, sector, gear, landings_t, value_usd,
  catch_or_landings, source, confidential)`.
- **Read layer:** API routes under `/v1/landings/*` (return 503 when a parquet is absent, per
  house convention); dashboard **Economics** pages reusing `components/bottom_ui.py` (header +
  region chip, KPI cards, bordered sections, footer with sources + confidentiality note).
- **Nav:** add an **Economics** entry within each geographic section (Bering Sea / Gulf of Alaska
  / Aleutian Islands) via the existing group-aware `render(group=…)` pattern, *or* a top-level
  **Economics** section — decide at E0 (recommend per-region, consistent with geography-first nav).

## 5. Phased plan

### E0 — Foundations
- Build the **crosswalk** (`areas.py`), the **tidy schema**, the `LandingsSource` descriptor, and
  the **confidentiality helper**. No user page yet.
- Add a cross-link from the existing **Catch × Bottom State** pages ("survey CPUE is not landings —
  see Commercial Landings") once E1+ exist.

### E1 — FOSS statewide landings (live API, quick public proof)
- `mhw-fetch-landings-foss` → statewide AK landings + ex-vessel value by species/year (1950–2024).
- A first **Economics (statewide)** panel: landings (t) and value ($) time series by species,
  with a clear **"statewide Alaska — not sub-region"** label. Fully public, live, low effort.

### E2 — AKFIN region-wise groundfish (the core economist view)
- Ingest a downloaded **AKFIN Apex / Economic SAFE export**: groundfish **landings (t) + ex-vessel
  value** by **NPFMC area × species × year** (and sector where non-confidential).
- Per-region **Economics** pages (Bering / GOA / AI) via the crosswalk: landings, value, price
  (value/landings), value share by species. Document the **refresh SOP** (which Apex report, what
  filters, export → ingest command).
- Species aligned to the existing catch pages (cod, pollock, POP, sablefish, Atka, arrowtooth).

### E3 — ADF&G crab (the cold-pool tie-in)
- Ingest **BSAI crab** harvest + value by district (snow, king, Tanner) from ADF&G COAR/AMRs
  (table downloads; PDF extraction where needed).
- Surfaces on the **Bering** Economics page; directly complements the snow-crab cold-pool story.

### E4 — Ecosystem × economics integration (the unique value-add)
- Join landings/value to what the board already has — **survey biomass + bottom temperature**:
  e.g. ex-vessel value in warm vs cold years; value concentrated in the cold pool (snow crab);
  landings vs survey CPUE. This is where the fisheries-econ angle becomes distinctive. Exploratory,
  clearly non-causal.

## 6. Management-area ↔ board-group crosswalk (first draft — confirm at E0)

| NPFMC / ADF&G area | Board group | Notes |
|---|---|---|
| Bering Sea (groundfish BS subarea; crab BS districts) | `bering` | EBS/NBS survey regions ≈ BS management |
| Aleutian Islands (AI subarea) | `ai` | BSAI bundles BS+AI — must split |
| GOA Western (610) / Central (620, 630) / West Yakutat (640) / Southeast Outside (650) | `goa` | aggregate to GOA, or keep subareas as a toggle |
| Bering Sea slope | (n/a) | no directed commercial groundfish fishery to surface |

Decision to lock at E0: **present in native management units with a crosswalk label**, aggregated
to the board's groups where it aids comparison — do **not** silently relabel management areas as
survey regions.

## 7. Confidentiality handling
- Display only **aggregated** area × species × year (× sector/gear) cells.
- Carry a `confidential` flag; suppress and label any cell that fails the rule-of-three (public
  exports already suppress, but enforce defensively so we never display a thin cell).
- Footer note on every Economics page: source + "aggregated to protect confidential
  vessel/processor data (NOAA rule of three)."

## 8. Refresh cadence
- **FOSS landings:** live API, refresh with the monthly/periodic data job.
- **AKFIN / ADF&G:** periodic (annual/seasonal) **download-and-ingest**, documented as an SOP
  (not auto-fetched). Label each series with its latest finalized year.

## 9. Open validation gates (resolve before/within each phase)
- ⬜ Is the AKFIN Apex export **scriptable** (stable URL/params) or **manual download**? Sets E2 effort.
- ⬜ Lock the **area crosswalk** against an authoritative NPFMC management reference.
- ⬜ Confirm public exports already satisfy rule-of-three (vs our own aggregation).
- ⬜ ADF&G crab: which series are tabular vs PDF-only; choose extraction method.
- ⬜ Native-area vs crosswalked presentation (and whether to expose GOA subareas).
- ⬜ Catch vs landings vs value labelling — pick the primary metric per page.

## 10. Data sources (all public, verified 2026-06-26)
- **FOSS Commercial Landings** — `https://apps-st.fisheries.noaa.gov/ods/foss/landings/`
  (statewide AK; species, year, pounds, dollars; live REST).
- **AKFIN** — `https://akfin.psmfc.org/` ; public reports `https://reports.psmfc.org/akfin`
  (Comprehensive Blend CA, FT, ENCOAR, Economic SAFE; Excel/text export).
- **ADF&G commercial fisheries** — `https://www.adfg.alaska.gov/index.cfm?adfg=fishingCommercial.statisticsanddata`
  (COAR value; crab/shellfish harvest by area; AMR PDFs).
- *Reference:* Economic SAFE ("Economic Status of the Groundfish Fisheries off Alaska"); RAM Legacy
  Stock Assessment Database; NPFMC SAFE reports.
