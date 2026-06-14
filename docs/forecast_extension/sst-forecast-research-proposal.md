# Research Proposal — Probabilistic Short-Term Marine Heatwave Forecasting for Alaskan Shelf Seas

**A skill-assessment and decision-support study, to publication standard.**

*Working title (manuscript):* "Are statistical baselines skillful for short-term
marine-heatwave forecasting in sub-Arctic shelf seas? A probabilistic
skill-assessment for Alaska with implications for ecosystem report cards."

**Status:** proposal / governing document. No forecast product is to be displayed on
the public dashboard or API until the deployment gate (§9) is cleared.

**Location:** `docs/forecast_extension/` (with `sst-forecast-methodology.md` and
`sst-forecast-mvp-plan.md`, which this proposal supersedes as the governing plan).

---

## 1. Executive summary

The dashboard currently monitors marine heatwaves (MHWs) from NOAA OISST using the
Hobday et al. (2016) definition over five Alaskan shelf regions. A NOAA AFSC
collaborator producing annual crab-stock ecosystem report cards has asked whether we
can forecast MHW conditions. Forecasting methods exist and are physically grounded,
but their **probabilistic skill and calibration have not been established for these
specific high-latitude, seasonally ice-covered regions.** Displaying an unvalidated
forecast to a Fishery Management Council would be scientifically indefensible.

This proposal frames the work as a rigorous skill-assessment study: characterise the
SST-anomaly process econometrically, specify and estimate a defensible set of
statistical forecast models, evaluate their probabilistic skill and calibration
out-of-sample with formal inference, and decide — against pre-registered criteria —
whether, where, and at what lead any product is good enough to deploy. The intended
output is a first-rate publication and, conditionally, a validated dashboard product.

---

## 2. Motivation and gap

- **Decision-support need.** Ecosystem report cards and Council presentations are
  retrospective; a credible short-lead MHW outlook would create a preparation window
  for survey planning and risk communication.
- **Scientific gap.** Published probabilistic MHW skill assessments concentrate on
  open-ocean, temperate, or low-latitude systems (e.g. Chesapeake Bay; Indian Ocean;
  global seasonal). The **eastern Bering, northern Bering, Chukchi, Beaufort, and
  Gulf of Alaska shelves** — shallow, strongly seasonal, sea-ice-affected, and home
  to high-value fisheries (snow crab, red king crab, pollock, cod) — are
  underrepresented. Their anomaly dynamics (ice masking, cold-pool coupling, strong
  seasonal heteroskedasticity, recent regime shifts) plausibly differ from the
  settings where baselines have been validated.
- **Econometric gap.** Many MHW-forecast studies under-treat the time-series
  econometrics: stationarity/trend testing, conditional heteroskedasticity,
  non-Gaussian predictive distributions, and — critically — **field significance**
  (multiple testing across many grid cells under spatial dependence). A study that
  does these properly is itself a contribution.

---

## 3. Research questions and hypotheses

Each RQ is paired with the work package(s) that answer it and a pre-registered
hypothesis (H) to be confirmed or rejected.

| # | Research question | Hypothesis |
|---|-------------------|-----------|
| **RQ1** | What are the time-series properties of daily SST anomalies in each region — trend, stationarity, seasonality of mean and variance, memory structure, and distributional shape (incl. ice-edge effects)? | **H1**: anomalies are *trend-stationary* with a secular warming trend, seasonally heteroskedastic variance, and regionally varying short-range (AR-type) memory; normality fails near the ice edge. |
| **RQ2** | Do statistical baseline forecasts (persistence, damped persistence, AR(1), and diagnostically justified extensions) yield *skillful, calibrated probabilistic* MHW forecasts at 2-week and 1-month leads, relative to climatology and persistence references? | **H2**: damped persistence/AR(1) beat climatology at ≤2-week leads; skill decays toward the climatology floor by ~1 month. |
| **RQ3** | How does skill vary by **region, season, lead, and ice proximity**, and where is it *significant* after multiple-testing and spatial-dependence corrections? | **H3**: skill is highest in open-water seasons and lower/insignificant in ice-affected cells and seasons. |
| **RQ4** | Are the forecast probabilities **reliable (well-calibrated)** enough for management use? | **H4**: raw Gaussian-exceedance probabilities are over-confident near the ice edge and require recalibration. |
| **RQ5** | Does explicitly accounting for the **warming trend and conditional heteroskedasticity** materially change skill and calibration versus the naive fixed-baseline AR(1)? | **H5**: trend-aware, heteroskedasticity-aware models improve calibration more than they improve point skill. |
| **RQ6** | *(Decision-economics extension.)* What is the **value of the forecast** to a representative decision (e.g. a cost–loss / value-of-information framing for survey or risk-communication decisions)? | **H6**: positive value-of-information exists for a non-trivial range of decision cost–loss ratios at ≤2-week leads. |

RQ1–RQ4 are the core paper. RQ5 strengthens defensibility. RQ6 is a distinctive
economics contribution and a natural second paper if scope demands.

---

## 4. Novel contribution (why it is publishable)

1. First systematic **probabilistic MHW forecast skill assessment for Alaskan shelf
   seas**, including ice-affected regions usually excluded.
2. A **methodologically rigorous template**: stationarity/trend/heteroskedasticity
   diagnostics, leakage-free rolling-origin verification, formal predictive-ability
   tests, and **field significance under spatial dependence** — addressing common
   gaps in the MHW-forecast literature.
3. An explicit, pre-registered **deployment-decision framework** linking statistical
   skill/calibration to an operational go/no-go — a reusable bridge from research to
   public decision-support tools.
4. *(RQ6)* A **value-of-information** treatment connecting forecast skill to fisheries
   decision-making.

---

## 5. Study domain and data

- **Regions (5):** Gulf of Alaska (goa), Eastern Bering Sea (ebs), Northern Bering
  Sea (nbs), Chukchi (chukchi), Beaufort (beaufort).
- **Primary data:** NOAA OISST v2.1, daily, 0.25°, 1982–present (already ingested).
- **Derived inputs (existing):** day-of-year climatology μ and 90th-percentile
  threshold θ₉₀ (Hobday-style, 1991–2020 baseline, 11-day window, ice-masked);
  region masks; cos-latitude area weights. See `config/climatology.yml`.
- **Definitions under test:** primary MHW threshold = θ₉₀; sensitivity to θ₉₅ and to
  the ≥5-day Hobday persistence rule vs instantaneous exceedance.
- **Train/test discipline:** a final **held-out test period** (e.g. the most recent
  ~5–7 years, exact split pre-registered) is untouched until all specification and
  tuning are frozen. All parameter estimation within any forecast uses only data
  strictly prior to the forecast origin (no leakage).

---

## 6. Work packages, methods, and deliverables

Each WP lists its lead role (see §7), methods, and concrete deliverables.

### WP1 — Literature review and pre-registration  *(Lead: Literature-review assistants; QA: Senior Research Associate)*
- Systematic review of: MHW definitions and thresholds; statistical and dynamical
  MHW/SST forecasting; high-latitude/ice-affected SST predictability; forecast
  verification and field-significance methodology; decision-support / value-of-
  information for environmental forecasts.
- Synthesise the specific evidence on baseline (persistence/damped/AR) skill and
  where it has and has not been validated.
- **Deliverables:** annotated bibliography; a 3–5 page gap statement positioning our
  contribution; a **pre-registration document** fixing hypotheses, model set,
  verification metrics, test-period split, and the §9 deployment-gate thresholds
  *before* any test-set evaluation.

### WP2 — Data assembly and exploratory analysis  *(Lead: Data Analyst)*
- Reproducible extraction of per-region SST and anomaly cubes; consistent ice
  masking; documentation of coverage, gaps, and grid.
- EDA: anomaly time series and maps; seasonal mean/variance; empirical
  autocorrelation (ACF/PACF) by region and season; distributional summaries
  (skew/kurtosis) including ice-edge cells; visual evidence of trend and regime
  shifts (e.g. 2014–16 Blob, 2018–19 Bering events, 2023–24).
- **Deliverables:** versioned analysis dataset; EDA report with figures; a data-
  quality and caveats memo.

### WP3 — Econometric characterisation of the anomaly process  *(Lead: Expert Econometrician; support: Data Analyst)*
- **Trend:** test for and characterise the secular warming trend; deterministic vs
  stochastic-trend distinction. Evaluate fixed-baseline vs time-varying / detrended
  anomaly definitions.
- **Stationarity / unit roots:** ADF, KPSS, Phillips–Perron; structural-break-aware
  tests (Zivot–Andrews) given known regime shifts. Resolve the d=0 question
  empirically rather than by assumption.
- **Seasonal heteroskedasticity:** test and model time-varying anomaly variance
  (periodic variance / periodic-GARCH or equivalent).
- **Memory:** AR-order identification (AIC/BIC/HQ); check for long memory (Hurst /
  ARFIMA) to rule it out or in; quantify per-cell vs regionally pooled estimates.
- **Distribution:** formal non-normality assessment; implications for the Gaussian
  exceedance step.
- **Deliverables:** an econometric properties report (per region, with maps and
  tables of test statistics and parameter estimates with proper standard errors);
  a justified recommendation on anomaly definition, model order, error model, and
  predictive-distribution form.

### WP4 — Model specification and estimation  *(Lead: Expert Econometrician)*
- **Model set (parsimony first, escalation gated by WP3):**
  - References: climatology; persistence.
  - Core: damped persistence; AR(1).
  - Diagnostically justified extensions: low-order AR(p)/ARMA; trend-aware variant;
    heteroskedasticity-aware variant (e.g. seasonal/periodic variance).
  - Optional upper-bound reference: a regularised logistic/GAM or a simple ML model
    (to bound achievable skill, not for deployment).
- **Estimation with inference:** parameter estimates with HAC/robust standard errors;
  residual diagnostics (Ljung–Box, residual ACF, normality, heteroskedasticity);
  spatial coherence of estimated parameters.
- **Predictive distribution:** compare analytic Gaussian exceedance vs empirical
  (residual bootstrap / quantile) construction, especially for ice-affected cells.
- **Deliverables:** estimation report; parameter maps with uncertainty; a frozen,
  documented model specification carried into WP5/WP6.

### WP5 — Forecast generation  *(Lead: Data Analyst; methods: Econometrician; toolkit: existing engine)*
- Implement the frozen specifications in the existing variable-agnostic engine
  (`src/mhw/forecast/`) under a strict **rolling/expanding-origin, leakage-free**
  protocol.
- Produce per-cell MHW exceedance-probability fields and derived regional outlooks
  at leads {7, 14, 30} days (final lead set pre-registered).
- **Deliverables:** reproducible forecast archive (probabilities + outcomes) for the
  full verification period; run manifest and seeds.

### WP6 — Verification and statistical inference  *(Lead: Expert Econometrician; support: Senior Research Associate)*
- **Proper scoring:** Brier score with reliability/resolution/uncertainty
  decomposition; CRPS; ROC/AUC; Brier Skill Score vs climatology and persistence.
- **Calibration:** reliability diagrams and calibration slopes; recalibration
  (e.g. isotonic / logistic) where needed, evaluated honestly out-of-sample.
- **Predictive-ability inference:** Diebold–Mariano and Giacomini–White tests for
  conditional predictive ability vs each reference, per region/lead/season.
- **Field significance / multiple testing:** control false discovery across cells
  (Benjamini–Hochberg / Benjamini–Yekutieli for dependence) and apply spatial
  field-significance (Wilks); block bootstrap (respecting temporal autocorrelation)
  for confidence intervals.
- **Stratification:** skill by region, season, lead, and ice proximity.
- **Robustness:** sensitivity to baseline period, threshold (θ₉₀ vs θ₉₅), ice
  masking, and instantaneous-vs-5-day definition.
- **Deliverables:** the verification report — the scientific core of the paper —
  with all skill, calibration, and significance results and robustness checks.

### WP7 — Decision-economics extension (RQ6)  *(Lead: Senior Research Associate / PI; support: Econometrician)*
- Cost–loss / value-of-information analysis for a representative management decision;
  map forecast skill to expected economic value across decision cost–loss ratios.
- **Deliverables:** value-of-information analysis; figure of value vs cost–loss ratio
  by lead. (May be deferred to a companion paper.)

### WP8 — Synthesis, manuscript, and conditional deployment  *(Lead: Senior Research Associate; all contribute)*
- Integrate WP1–WP7 into a publication-grade manuscript; internal review; AFSC
  collaborator review for decision-support framing and (potential) co-authorship.
- Apply the §9 deployment gate; if cleared, specify exactly which regions/leads/
  seasons may be displayed and with what uncertainty and caveats; if not cleared,
  document why and what would be required.
- **Deliverables:** submitted manuscript; a deployment-decision memo; (conditional)
  a dashboard/API specification limited to gate-passing products.

---

## 7. Roles and responsibilities

| Role | Primary work packages | Accountable for |
|------|----------------------|-----------------|
| **Literature-review assistants** | WP1 | Evidence base, gap statement, pre-registration draft |
| **Data Analyst** | WP2, WP5 (support WP3) | Reproducible data + forecast pipelines, EDA |
| **Expert Econometrician** | WP3, WP4, WP6 (support WP7) | Specification, estimation, inference, verification methodology |
| **Senior Research Associate** | WP7, WP8 (coordinate all; support WP6) | Integration, manuscript, deployment-gate, AFSC liaison, QA |
| **Engineering / toolkit (existing code)** | WP5 substrate | `src/mhw/forecast/` engine, reproducibility, run management |

The Senior Research Associate owns the project timeline, the pre-registration
integrity, and the go/no-go gate decisions.

---

## 8. Timeline, milestones, and go/no-go gates

Indicative; weeks are effort-relative, not calendar-fixed. Each gate is a stop point
with a written deliverable reviewed before the next phase begins.

| Phase | Weeks | Work packages | Gate (exit criterion) |
|-------|-------|---------------|-----------------------|
| **P0 — Scoping** | 1–3 | WP1, WP2 | **Gate A:** pre-registration signed; EDA + data report accepted |
| **P1 — Econometrics** | 4–8 | WP3, WP4 | **Gate B:** anomaly process characterised; frozen model specification |
| **P2 — Forecast & verify** | 9–14 | WP5, WP6 | **Gate C:** verification report; **deployment decision** (see §9) |
| **P3 — Synthesis** | 15–20 | WP7, WP8 | **Gate D:** manuscript submitted; (conditional) deployment spec |

**Pre-registration is binding:** hypotheses, model set, metrics, the test-period
split, and the §9 thresholds are fixed at Gate A. The held-out test period is opened
only at WP6. Any post-hoc deviation is reported as such in the manuscript.

---

## 9. Deployment gate (pre-registered)

No forecast product is shown on the dashboard or served by the public API unless, for
that specific region × lead × season, **all** of the following hold on the held-out
test period:

1. **Skill:** Brier Skill Score > 0 versus *both* climatology *and* persistence.
2. **Significance:** the skill advantage is statistically significant after
   FDR/field-significance correction (WP6).
3. **Calibration:** reliability within a pre-set tolerance (calibration slope and
   reliability component of the Brier decomposition within bounds), after any
   pre-registered recalibration.
4. **Honesty of presentation:** the product is displayed with explicit uncertainty,
   its validated scope, and the documented limitations (statistical-not-dynamical,
   instantaneous-exceedance proxy, ice-edge caveats).

Products failing the gate are not displayed; the manuscript reports the negative
result, which is itself a valid and useful scientific finding.

---

## 10. Reproducibility and data management

- All analysis scripted and version-controlled on `feat/sst-forecast`; the forecast
  engine lives in `src/mhw/forecast/`.
- Deterministic seeds; archived forecast/outcome datasets; run manifests.
- Configuration-driven parameters (`config/climatology.yml`, `config/datasets.yml`).
- Each WP deliverable is a committed artifact (report + figures + the code that made
  them), enabling end-to-end reproduction of every table and figure.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Baselines show little/no skill in some regions | Pre-committed to publishing negative results; gate prevents deployment; report value of knowing where forecasts fail |
| Warming trend / regime shifts confound the anomaly model | WP3 trend & break testing; trend-aware variant (RQ5) |
| Ice-edge non-Gaussianity miscalibrates probabilities | Empirical predictive distribution + recalibration (WP4/WP6); ice-proximity stratification |
| Multiple-testing inflates apparent skill | FDR + field-significance + block bootstrap (WP6) |
| Scope creep (ML, seasonal, bottom temp) | Those are separate efforts; this study is SST + statistical baselines only |
| Data latency/coverage issues | Documented in WP2; OISST already operational in the project |

---

## 12. Out of scope (explicitly)

- Bottom-temperature / MOM6 forecasting (separate track: `feat/mom6-spike` →
  `feat/bottom-ocean-state`). The engine is built to extend there later.
- Seasonal (1–12 month) dynamical/ensemble forecasting.
- Fish-stock forecasting. Indicators here remain environmental.

---

## 13. Candidate target journals

- *Weather and Forecasting* (AMS) — verification-focused.
- *Progress in Oceanography* / *Fisheries Oceanography* — regional + applied.
- *Communications Earth & Environment* / *Frontiers in Marine Science* — broad.
- *Environmental Data Science* — methods + decision-support.
- *(RQ6)* *Marine Resource Economics* / *ICES Journal of Marine Science* — value-of-
  information.

---

## 14. Key references (to be expanded in WP1)

- Hobday, A. J., et al. (2016). *A hierarchical approach to defining marine
  heatwaves.* Progress in Oceanography.
- Frankignoul, C., & Hasselmann, K. (1977). *Stochastic climate models, Part II.*
  Tellus, 29(4). (AR(1)/red-noise basis for SST anomalies.)
- Jacox, M. G., et al. (2022). *Global seasonal forecasts of marine heatwaves.*
  Nature.
- *Probabilistic extreme SST and marine heatwave forecasts in Chesapeake Bay.*
  Frontiers in Marine Science (2022).
- Verification & inference: Diebold & Mariano (1995); Giacomini & White (2006);
  Wilks — field significance and forecast verification; Benjamini & Hochberg (1995);
  Benjamini & Yekutieli (2001).
- Companion internal docs: `sst-forecast-methodology.md`,
  `sst-forecast-mvp-plan.md`.
