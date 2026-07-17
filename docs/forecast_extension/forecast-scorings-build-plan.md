# Build plan — v2 pin + occurrence-probability & SEBS-onset scoring pages

**Status:** READY for Col. Raj's approval (2026-07-16). Do not implement until approved.
**Inputs in hand — all LOFRA info received + verified:**
- `coefficient-manifest-v2-20260716.tar.gz` (SHAs PASS) — the v2 coefficient manifest.
- `forecast-scorings-v2-20260716.tar.gz` (SHA `37f6e377…`, all 3 CSVs + manifest PASS) — pinned occurrence
  + onset reference scorings, with LOFRA's display rules and **verbatim captions/labels** (handoff
  `lofra-to-dashboard-20260716-05-forecast-scorings-guidance.md`, `Status: resolved`).
- All previously-starred (★) items are now **resolved** inline below.

---

## Goal

**Framing (from LOFRA's rev-2 briefing — adopt this on the pages and in the guide):** there is **ONE target —
area fraction** (the share of a zone's cells in a marine heatwave). Occurrence and onset are **not separate
forecasts**; they are two additional **"report cards" (scorings)** of that single area-fraction forecast. So the
board shows *one forecast, three report cards*: (1) area/magnitude skill (already live), (2) occurrence
probability, (3) onset discrimination. This is the honest, non-duplicative way to present them.

Extend the Forecast view (today: area-fraction **magnitude** only) to also present the two other scorings the
module already computes, each honestly labelled on the existing confidence ladder:
1. **Occurrence probability** — P(area_frac > q90) per zone×lead, promoted from a tile sub-line to a scored panel.
2. **SEBS onset watch** — currently **deferred/blocked**; un-defer it and show it as an experimental discriminator.

And first, pin the **v2** coefficient manifest so all of the above is fit on the corrected (θ90-smoothed) predictand.

---

## Phase 0 — Pin the v2 manifest (unblocks the existing page on the corrected predictand)

The existing area-fraction tiles are wired to v1 coefficients fit on the *superseded* predictand. This phase is
purely mechanical; no UI change.

1. **Vendor v2.** v2 is a *manifest-only* release (module code byte-identical to v1). Extract
   `coefficient_manifest_v2.json` + `..._v2_frozen_basis.npz` from `data/incoming/coefficient-manifest-v2-20260716.tar.gz`.
   - **Decision needed (naming):** `deploy.VENDOR_DIR` is hardcoded to `vendor/forecast-module-v1/`, and
     `load_manifest()` reads the manifest from inside that tree. Two clean options:
     - **(A, recommended)** Rename the vendor tree to `vendor/forecast-module-v2/` (v1 code + v2 manifest, since
       code is identical), bump `deploy.VENDOR_DIR`, and drop the v1 manifest files. One coherent tree per pin.
     - **(B)** Keep `vendor/forecast-module-v1/`, add the v2 JSON+npz beside v1, and select v2 in the loader.
       Less churn but leaves a v1-named dir holding v2 coefficients (confusing later).
2. **Bump the pin.** `config/forecast.yml`: `module_version: v2`; keep `fit_vintage`/`coefficient_vintage`
   display values (LOFRA confirmed **unchanged** — persistence/clim 2026-04, onset 2026-05); add the v2
   provenance (predictand_snapshot `snap-obl064-…`, manifest SHA `6efcb272…`, npz SHA `cee7a21f…`).
3. **Re-run** `mhw-run-forecast` to regenerate `data/derived/forecast/forecast_<zone>.parquet` on v2 coefficients.
4. **Verify** the existing tiles / Zone-Outlook fan / skill panel still render; spot-check that point/band values
   moved only slightly (LOFRA: largest φ +0.015 nbs, q90 +0.032 egoa).
5. **Reply to LOFRA** `forecast-module-revend` confirming verify+pin (closes OBL-065 their side).

*Deliverable:* area-fraction page live on the frozen v2 target. Self-contained; could ship on its own.

---

## Phase 1 — Occurrence-probability scoring

Occurrence (`l1_prob`) is already produced into `forecast_<zone>.parquet` and shown as a small sub-line. Promote it.

- **Where:** a scored element beside the magnitude tiles, **seven damped zones only** (`sebs, wgoa, egoa, nbs,
  ai_west, ai_central, ai_east`); `chukchi`/`beaufort` have no occurrence panel (climatology-routed); `nbs` shows
  it with the Arctic ice caveat. *(LOFRA-confirmed.)*
- **Metrics (confirmed):** per zone — **BSS vs climatology** (`bss_clim`, headline) + **AUC** + a **reliability
  curve** (`p_mean` vs `o_freq`) + `n`/`base_rate` for context. Occurrence is an **L1 product**; L1 is resolvable
  and positive in all seven zones (`bss_clim`: egoa 0.58, wgoa 0.59, sebs 0.51, nbs 0.39, ai_east 0.37, ai_west
  0.27, ai_central 0.23).
- **Honesty rail (LOFRA, load-bearing):** the occurrence forecast **is** the damped-persistence model (P(area_frac
  > train-q90) read off the same forecast that drives the magnitude tile). `bss_clim` is genuine skill **over
  climatology** — but the panel must **not imply it beats persistence**.
- **Greying:** if L2/L3 are surfaced as context, **grey any cell with `bss_clim ≤ 0` as "watch"** (several zones
  cross ≤0 by L3) — mirrors the magnitude ladder.
- **Data source (delivered + pinned):** `data/incoming/forecast-scorings-v2/occurrence_probabilistic_skill_v2.csv`
  (rows `forecaster=='damped_persistence'`, `stratum=='all'`) + `occurrence_reliability_bins_v2.csv`. Pin as a
  sealed reference artifact (PSL-SEDI pattern). **Verbatim caption** to render is in `SCORINGS-MANIFEST.md` §A.
- **UI:** `bottom_ui` chrome — bordered card, `section_title("Occurrence Probability")`, `kpi_card`s (BLUE accent)
  for P(>q90) + BSS, small reliability chart (per `dataviz`), the verbatim caption in a `callout`.

---

## Phase 2 — SEBS onset watch (un-defer + score)

This is the largest piece: `run_onset_watch()` raises `NotImplementedError` because the frozen onset path needs a
locally-rebuilt broad-basin OISST field.

1. **Build the obl029 field.** Run the vendored chain (network fetch): `obl029_01_fetch_oisst_broadbasin.py` →
   `obl029_02_monthly_aggregate.py` → `obl029_04_zone_sst_anomaly.py`, producing the monthly broad-basin anomaly
   NetCDF on the frozen EOF grid / 1991–2020 baseline. `load_live_field` validates against `spec/obl036_*` and
   **refuses a mismatched grid/baseline**. *(LOFRA-confirmed: no v2 gotchas — EOF basis / `field_snapshot`
   byte-identical to v1, so the v1 rebuild recipe applies unchanged.)*
2. **Wire** `run_onset_watch()` → `forecast.sebs_onset_watch_frozen(df, field, manifest, leads)`; remove the stub;
   write `onset_sebs.parquet` (date, state, threshold). Add a `mhw-run-forecast --onset` path + API route
   `/v1/forecast/onset/sebs` (currently 503).
3. **Refresh cadence.** The field must rebuild monthly. Given the 4 GB VM, follow the established split — heavy
   rebuild local + rsync, light steps VM-cron (see deployment-infra memory). New cron row.
4. **Scoring + label (confirmed — one correction from my draft):** the deployed watch is the **LIM `k=12`** path
   (not damped persistence). Display **elevated/normal** state + threshold (straight from the frozen v2 onset
   calibration), plus **AUC + SEDI + POD/FAR** from the pinned `onset_discrimination_v2.csv`
   (rows `zone=='sebs'`, `forecaster=='lim_k12'`, `lead∈{1,2}`, `stratum=='all'`). **v2 values:** L1 AUC 0.759,
   SEDI 0.583, POD 0.467, FAR 0.682; L2 AUC 0.685, SEDI 0.503. **Honesty anchor (mandatory):** show the
   `persistence` row alongside — persistence onset AUC 0.665 (L1), just below the watch; that adjacency *is* the
   story (discriminates, does not resolvably beat persistence; selection-adjusted improvement p≈0.075 on 16
   onsets). Onset stays **SEBS-only**. Render the **verbatim caption** from `SCORINGS-MANIFEST.md` §B.
5. **UI:** its own bordered card under the SEBS view; PURPLE/AMBER accents (watch/caution), never a probability.

---

## Phase 2.5 — Provenance & user-facing explanation (cross-cutting)

Requirement (Col. Raj, 2026-07-16): the pages must make **how and where these forecasts come from** legible to
users, drawn from LOFRA's plain-English briefing. Two surfaces:

1. **Inline on the pages** — a short "How this forecast works / where it comes from" `callout` (bottom_ui) on the
   Forecast panel, plus the standard `footer(... "Learn more in the guide")` link. One or two sentences each:
   the forecast is a **consumed research-cell product** (LOFRA's `sst-forecast-method-review` study) — **damped
   persistence** applied forward on our own OISST-derived `area_frac`, validated against LIM / SEAS5 / ocean-heat-
   content / climatology, honest to a **2–3-month predictability ceiling**.
2. **In the user guide** — a new section in `docs/marine_heatwave_guide.md` (it already has "## The NOAA PSL
   Marine Heatwave Forecast"; add a sibling **"## The Alaska-Shelf MHW Forecast (damped persistence)"**) covering:
   where it comes from, what "persistence is the forecast to beat" means, the zone→product routing, the honest
   labels, the occurrence/onset scorings, and the ceiling. Rendered via the existing `guides.py` markdown path.

**Source & sign-off (DECIDED 2026-07-16):** author it ourselves from LOFRA's `raj-briefings/
briefing-predictand-correction-and-rerun-2026-07-16.md` (rev-2; plain-English, Section 2 explains the methods in
lay terms) — **no separate LOFRA/ZEBRA ask.** Col. Raj confirmed the briefing is sufficient. We adapt its
first-person research-cell voice ("we tested", "our model") into board/third-person and condense to match the
existing guide's "NOAA PSL Marine Heatwave Forecast" section. The load-bearing skill claims are anchored on
LOFRA's **already-signed-off verbatim panel captions** (from `SCORINGS-MANIFEST.md`), so the honesty-sensitive
statements carry LOFRA's imprimatur without a new request. (LOFRA's OBL-065 ZEBRA public-explanation task is
LOFRA's own initiative for their outputs; we can cross-reference their page later if it lands.)

## Phase 3 — Placement, design system, deploy

- **Placement:** both new elements live inside `render_forecast_panel` (Operational tab, region-filtered) and the
  standalone Forecast page; occurrence beside the magnitude tiles, onset as a SEBS-only card below Zone Outlook.
- **Design system:** all panels wrapped in `st.container(border=True)`, `bottom_ui` chrome only, semantic accent
  colours, `dataviz` for the reliability/skill charts. No hand-rolled page chrome.
- **Tests:** pure-helper unit tests (scoring-table readers, ladder classification) network-free; API tests `skip`
  when artifacts absent — per house pattern.
- **Deploy:** image rebuild + rsync the pinned scoring artifacts + the new onset-field cron row; verify prod tiles.

---

## Open questions for LOFRA — status

1. ✅ **RESOLVED** — Occurrence: BSS-vs-clim (headline) + AUC + reliability + n/base_rate; L1 product; grey `bss_clim≤0`.
2. ✅ **RESOLVED** — Onset: AUC + SEDI + POD/FAR; deployed watch = **LIM k=12**; show persistence row as anchor;
   verbatim label supplied.
3. ✅ **RESOLVED** — CSVs delivered + pinned (`forecast-scorings-v2-20260716.tar.gz`, SHAs verified).
4. ✅ **RESOLVED** — obl029: no v2 gotchas.
5. ✅ **RESOLVED (Col. Raj, 2026-07-16): adapt from the briefing — no LOFRA ask.** The rev-2 briefing is
   sufficient (method definitions, "one target / three report cards" framing, forecast-to-beat logic, ceiling,
   numeric intuition, provenance). We author the guide section + inline callouts by adapting it to board voice,
   anchored on LOFRA's already-signed-off verbatim panel captions for the load-bearing skill claims. No separate
   board-voice passage requested from LOFRA/ZEBRA.

## Suggested sequencing

Phase 0 is independent and low-risk → **ship first**. Phase 1 (occurrence) is small and needs only the pinned
scoring table. Phase 2 (onset) is the real build (field rebuild + cron + un-defer) → largest, do last. Each phase
is separately shippable behind the existing honest-label discipline.
