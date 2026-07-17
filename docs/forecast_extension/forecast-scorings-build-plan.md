# Build plan — v2 pin + occurrence-probability & SEBS-onset scoring pages

**Status:** DRAFT for Col. Raj's approval (2026-07-16). Do not implement until approved.
**Inputs in hand:** verified `coefficient-manifest-v2` (SHAs PASS); LOFRA rerun-v2 scoring tables inspected.
**Still pending (does not block drafting):** LOFRA reply on `forecast-scorings` (handoff 04) — needed to
finalize the starred (★) items below before those steps are coded.

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

- **Where:** a scored element beside the magnitude tiles, damped-persistence zones only (7 productive zones;
  `chukchi`/`beaufort` excluded per routing; `nbs` shows it with the ice caveat).
- **★ Metrics to surface (my proposal, pending LOFRA):** per zone×lead — **BSS vs climatology** (`bss_clim`) as the
  headline skill number, a **reliability curve** (`reliability_bins.csv`: `p_mean` vs `o_freq`), and **AUC** as a
  discrimination read-out. The v2 numbers are strong at L1 (BSS-clim 0.51 sebs / 0.58 egoa / 0.59 wgoa; AUC ~0.88–0.93),
  decay through L2, and go **negative** at L3/L6 for several zones.
- **Honesty ladder:** reuse the existing L1-headline / L2-banded / L3-watch treatment; **grey any cell with
  non-resolvable / negative BSS** rather than printing a skill number (mirrors the magnitude ladder).
- **★ Data source:** LOFRA's `results/obl064-rerun-v2/stage-3-baselines/probabilistic_skill.csv` +
  `reliability_bins.csv` (v2, `forecaster=damped_persistence`, `stratum=all`). These are fixed-per-vintage
  validation numbers → **pin them as a sealed reference artifact** (same pattern as the PSL SEDI artifact), not
  recomputed board-side. Ask LOFRA to deliver them (or bless our vendoring from rerun-v2).
- **UI:** `bottom_ui` chrome — a bordered card with `section_title("Occurrence Probability")`, `kpi_card`s
  (BLUE accent = probability/stats) for P(>q90) + BSS, and a small reliability chart (per `dataviz`).

---

## Phase 2 — SEBS onset watch (un-defer + score)

This is the largest piece: `run_onset_watch()` raises `NotImplementedError` because the frozen onset path needs a
locally-rebuilt broad-basin OISST field.

1. **Build the obl029 field.** Run the vendored chain (network fetch): `obl029_01_fetch_oisst_broadbasin.py` →
   `obl029_02_monthly_aggregate.py` → `obl029_04_zone_sst_anomaly.py`, producing the monthly broad-basin anomaly
   NetCDF on the frozen EOF grid / 1991–2020 baseline. `load_live_field` validates it against `spec/obl036_*` and
   **refuses a mismatched grid/baseline** — verify before wiring. (LOFRA confirmed the EOF basis / `field_snapshot`
   are byte-identical under v2, so the v1 rebuild recipe still applies. ★ confirm no v2 gotchas.)
2. **Wire** `run_onset_watch()` → `forecast.sebs_onset_watch_frozen(df, field, manifest, leads)`; remove the stub;
   write `onset_sebs.parquet` (date, state, threshold). Add a `mhw-run-forecast --onset` path + API route
   `/v1/forecast/onset/sebs` (currently 503).
3. **Refresh cadence.** The field must rebuild monthly. Given the 4 GB VM, follow the established split — heavy
   rebuild local + rsync, light steps VM-cron (see deployment-infra memory). New cron row.
4. **★ Scoring + label.** Display the SEBS onset watch as **elevated/normal** state + threshold, plus a
   discrimination read-out. **★ Metrics (pending LOFRA):** onset **AUC** + **SEDI** (+ optionally POD/FAR) from
   `onset_discrimination.csv` (v2). The numbers are modest by construction (damped AUC ~0.60 at L1, n_onset=15).
   **★ Label wording — verbatim from LOFRA:** "EXPERIMENTAL — a two-state elevated/normal discriminator; genuinely
   discriminates onset but **not** a resolvable skill gain over persistence; never shown as beating persistence,"
   with the v2-tightened significance. Onset stays **SEBS-only**.
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

**Source & sign-off (important):** the natural source is LOFRA's `raj-briefings/
briefing-predictand-correction-and-rerun-2026-07-16.md` (plain-English, Section 2 explains the methods in lay
terms). But that briefing is an **internal document "written for Rajesh"** in first-person research-cell voice
("we tested", "our persistence model"). Two reasons not to lift it verbatim into a public guide: voice, and the
fact that **LOFRA's own OBL-065 already tasks ZEBRA with authoring plain-English public-facing URL explanations
under LOFRA direction.** → **Recommended:** request a board-voice, public-appropriate excerpt/passage from LOFRA
(coordinated with ZEBRA's work), rather than excerpting the internal briefing ourselves. We adapt to board voice
and place it; LOFRA signs off the public wording (same discipline as the honest labels). Candidate excerpts are
listed for Col. Raj in the session notes.

## Phase 3 — Placement, design system, deploy

- **Placement:** both new elements live inside `render_forecast_panel` (Operational tab, region-filtered) and the
  standalone Forecast page; occurrence beside the magnitude tiles, onset as a SEBS-only card below Zone Outlook.
- **Design system:** all panels wrapped in `st.container(border=True)`, `bottom_ui` chrome only, semantic accent
  colours, `dataviz` for the reliability/skill charts. No hand-rolled page chrome.
- **Tests:** pure-helper unit tests (scoring-table readers, ladder classification) network-free; API tests `skip`
  when artifacts absent — per house pattern.
- **Deploy:** image rebuild + rsync the pinned scoring artifacts + the new onset-field cron row; verify prod tiles.

---

## Open questions for LOFRA (fold in when the `forecast-scorings` reply lands)

1. ★ Occurrence: confirm **BSS-vs-clim + reliability + AUC** is the set to surface (vs. adding/removing any).
2. ★ Onset: confirm **AUC + SEDI** (± POD/FAR) and give the **verbatim honest-label sentence**.
3. ★ Deliver `probabilistic_skill.csv` / `reliability_bins.csv` / `onset_discrimination.csv` (v2, stratum=all) as
   pinned artifacts — or bless our vendoring them from `rerun-v2`.
4. ★ Any obl029 field-rebuild gotchas under the v2 vintage (expected: none — EOF/field unchanged).
5. ★ **User-facing provenance text** — supply a **board-voice, public-appropriate** passage on where the forecast
   comes from + the methods (coordinated with ZEBRA's OBL-065 public-explanation task), for the guide section and
   the inline callouts. We adapt/place; LOFRA signs off the public wording.

## Suggested sequencing

Phase 0 is independent and low-risk → **ship first**. Phase 1 (occurrence) is small and needs only the pinned
scoring table. Phase 2 (onset) is the real build (field rebuild + cron + un-defer) → largest, do last. Each phase
is separately shippable behind the existing honest-label discipline.
