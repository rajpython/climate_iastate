# Research Proposal — Which Marine Heatwave Forecast Method for the Sub-Arctic? A Methods Survey Toward a Recommendation for the Gulf of Alaska

**A systematic review of forecasting methods, their technical configurations, and
regional performance — to identify the appropriate method for the Gulf of Alaska and
similar sub-Arctic shelf seas.**

*Working title (manuscript):* "Forecasting marine heatwaves in sub-Arctic shelf seas:
a systematic review of methods and a recommendation for the Gulf of Alaska."

**Status:** governing document for the forecast effort. The immediate study is the
review below. Any empirical implementation, and any public dashboard/API product,
follows the review and is gated separately (§9).

---

## 1. Purpose

One question drives this study:

> **What marine-heatwave (and SST) forecasting methods have been applied, with what
> technical configurations and what regional strengths and weaknesses — and which is
> the most appropriate method for the Gulf of Alaska and similar sub-Arctic shelf
> seas?**

The goal is not (yet) to build a forecast. It is to **find the right method** by
reading the field carefully: what has been tried, exactly how it was set up, where it
worked and where it failed, and what those results imply for our regions.

---

## 2. Why this, and why now

- A NOAA AFSC collaborator producing annual crab-stock ecosystem report cards has
  asked whether we can forecast MHW conditions. Before committing to any method, we
  need to know which approach is defensible for these waters.
- Published MHW/SST forecast skill is concentrated in open-ocean, temperate, and
  low-latitude systems. The **Gulf of Alaska, eastern and northern Bering, Chukchi,
  and Beaufort shelves** — shallow, strongly seasonal, sea-ice-affected, with recent
  regime shifts — are underrepresented, so a method validated elsewhere cannot be
  assumed to transfer. A focused review settles what is known and what is not.

---

## 3. Review questions

- **Q1 — What methods have been applied** to short-term MHW/SST forecasting?
- **Q2 — How, exactly?** For each method, the technical configuration:
  - **predictors and lag structure** (which inputs, lag lengths, memory horizon);
  - **estimation / training window** (period, length, rolling vs expanding, seasonal
    stratification, how the climatology baseline is handled);
  - **out-of-sample design** (hold-out, k-fold, rolling-origin/walk-forward,
    leave-one-year-out; hindcast vs reforecast; leakage controls);
  - **lead times** forecast and **verification metrics** used.
- **Q3 — Strengths and weaknesses**, and how performance varies by region/regime —
  especially high-latitude, ice-affected, shelf systems.
- **Q4 — Recommendation:** which method (or small set) is most appropriate for the
  Gulf of Alaska and similar sub-Arctic regions, and why.

---

## 4. Scope

- **In scope:** short-to-medium lead (days to ~3 months) forecasting of SST anomalies
  and/or MHW occurrence/probability.
- **Method families to capture (non-exclusive):** persistence and damped persistence;
  autoregressive models (AR, ARMA, ARIMA, periodic/seasonal AR); regression on
  large-scale climate indices (ENSO/PDO/AO/PNA) with lags; linear inverse models
  (LIM); analog methods; machine learning / neural networks; dynamical and statistical-
  dynamical/hybrid systems; operational products (e.g. NOAA Coral Reef Watch outlooks,
  PSL/Jacox seasonal MHW forecasts).
- **Out of scope:** bottom-temperature/MOM6 forecasting (separate track); fish-stock
  forecasting; building/validating a model ourselves (that is the contingent follow-on,
  §10).

---

## 5. Review method

A systematic, reproducible protocol (PRISMA-style).

- **Sources:** Web of Science, Scopus, Google Scholar; agency/grey literature (NOAA,
  Copernicus, ICES); citation chaining from key papers.
- **Search terms (illustrative):** ("marine heatwave" OR "SST anomaly" OR "ocean
  temperature") AND (forecast* OR predict* OR hindcast OR "lead time") AND (skill OR
  verification OR persistence OR autoregressive OR "machine learning" OR seasonal),
  with regional qualifiers (Alaska, Bering, "Gulf of Alaska", Arctic, sub-Arctic,
  "high latitude", shelf, sea ice).
- **Inclusion / exclusion:** documented criteria; screening log; PRISMA flow diagram
  (records found → screened → included).
- **Extraction:** every included study coded into the structured schema in §6.

---

## 6. Extraction schema (the technical core)

One row per study × method × region. This is where the lag / window / out-of-sample
detail is captured systematically.

| Field | What to record |
|-------|----------------|
| Citation | Authors, year, venue |
| Region & system | Location, latitude band; open-ocean / shelf / coastal; ice-affected? |
| Target | SST anomaly / MHW occurrence / MHW probability / category |
| Method family | Persistence, damped persistence, AR/ARMA/ARIMA, index regression, LIM, analog, ML/NN, dynamical, hybrid |
| **Predictors & lags** | Inputs used; **lag lengths**; memory/decorrelation horizon; AR order if stated |
| **Estimation/training window** | Calibration period & length; **rolling vs expanding**; seasonal stratification; baseline/climatology handling; sample size |
| **Lead times** | Forecast leads evaluated (e.g. 1 wk, 2 wk, 1–3 mo) |
| **Out-of-sample design** | In-sample only / hold-out / k-fold / **rolling-origin** / leave-one-year-out; hindcast vs reforecast; **leakage controls** |
| Probabilistic? | Deterministic vs probabilistic; predictive-distribution form (Gaussian / empirical / ensemble) |
| **Verification metrics** | Deterministic (RMSE, ACC) and/or probabilistic (Brier, BSS, CRPS, reliability, ROC/AUC); reference baselines |
| **Skill result** | Skill vs baselines; lead at which skill is lost; calibration if reported |
| **Strengths / weaknesses** | As stated by authors and as judged on extraction |
| Transferability | Relevance to high-latitude / ice / shelf; data requirements; transparency for management |

---

## 7. Synthesis and recommendation

- **Comparison matrix** of method families across the §6 fields, with particular
  attention to the technical settings (lags, windows, OOS protocol) that distinguish
  good practice from leakage-prone or in-sample-only studies.
- **Sub-Arctic suitability criteria** — the recommendation is argued against the
  specific demands of the Gulf of Alaska and neighbours:
  1. skill at operational short leads (≈1–4 weeks);
  2. handles strong **seasonal heteroskedasticity** and a **warming trend**;
  3. behaves sensibly under **sea-ice masking / ice-edge** non-normality;
  4. robust to **regime shifts** (e.g. 2014–16 Blob, 2018–19 Bering events);
  5. works with **available data** (OISST; optional climate indices);
  6. **probabilistic** output and **transparent** enough for management use.
- **Output:** a reasoned recommendation of the most appropriate method (or a short
  shortlist), with a concrete configuration specification — predictors/lags,
  estimation window, and out-of-sample protocol — ready to implement and test.

---

## 8. Deliverables

1. **Systematic review manuscript** (the publication) answering Q1–Q4.
2. **Method-comparison matrix** (the populated §6 schema) and PRISMA flow diagram.
3. **Annotated bibliography.**
4. **Recommendation memo** for the Gulf of Alaska / sub-Arctic: the chosen method and
   its configuration (lags, window, OOS design), with justification against §7
   criteria — the bridge to the contingent follow-on.

---

## 9. Roles

| Role | Responsibility |
|------|----------------|
| **Literature-review assistants** | Run the search protocol; screen; populate the §6 extraction schema; draft annotated bibliography |
| **Expert Econometrician** | Adjudicate technical extraction (lag structure, window design, out-of-sample validity, metric correctness); ensure the recommendation is statistically sound |
| **Data Analyst** | Feasibility check — confirm the recommended method's data/configuration are reproducible with our OISST holdings |
| **Senior Research Associate** | Own the protocol, synthesis, recommendation, and manuscript; AFSC liaison (Erin, natural co-author) |

---

## 10. Contingent follow-on (separate, gated)

If the review identifies a defensible candidate, a second phase implements and
validates it for our regions using the existing engine (`src/mhw/forecast/`):
leakage-free rolling-origin verification; skill (BSS) vs climatology and persistence;
calibration; field significance under spatial dependence. **No product reaches the
dashboard or public API until it clears that validation gate.** That phase will be
specified separately once the review's recommendation is in hand.

---

## 11. Timeline and gates

| Phase | Weeks | Work | Gate |
|-------|-------|------|------|
| **P0 — Protocol** | 1–2 | Finalise search terms, inclusion criteria, extraction schema | **Gate A:** protocol signed off |
| **P1 — Search & extraction** | 3–7 | Search, screen, extract into §6 schema | **Gate B:** populated matrix + PRISMA diagram |
| **P2 — Synthesis** | 8–11 | Comparison, suitability assessment, recommendation | **Gate C:** recommendation memo accepted |
| **P3 — Manuscript** | 12–16 | Write, internal + AFSC review, submit | **Gate D:** review manuscript submitted |

---

## 12. Key references (seed set; expanded during the review)

- Hobday, A. J., et al. (2016). *A hierarchical approach to defining marine
  heatwaves.* Progress in Oceanography.
- Frankignoul, C., & Hasselmann, K. (1977). *Stochastic climate models, Part II.*
  Tellus, 29(4). (AR(1)/red-noise basis for SST anomalies.)
- Jacox, M. G., et al. (2022). *Global seasonal forecasts of marine heatwaves.*
  Nature.
- *Probabilistic extreme SST and marine heatwave forecasts in Chesapeake Bay.*
  Frontiers in Marine Science (2022).
- *Skillful subseasonal Indian Ocean marine heatwave forecasts using a neural
  network.* Environmental Data Science (2024/25).
- *Seasonal forecasting of subsurface marine heatwaves.* Communications Earth &
  Environment (2023).
- Companion internal docs: `sst-forecast-methodology.md`, `sst-forecast-mvp-plan.md`.
