# Research Proposal — Best-Method Selection for Short-Term Marine Heatwave Forecasting in Sub-Arctic Alaskan Shelf Seas

**A literature-grounded, publication-grade skill assessment.**

*Working title (manuscript):* "What is the best short-term marine-heatwave forecast
method for sub-Arctic Alaskan shelf seas? A literature-grounded probabilistic skill
assessment."

**Status:** governing document for the forecast effort (supersedes
`sst-forecast-mvp-plan.md` as the plan; `sst-forecast-methodology.md` remains the
general-audience method description). No forecast product is displayed on the public
dashboard or API until the deployment gate (§8) is cleared.

---

## 1. Central purpose

One question drives this study:

> **What does the literature say, and what is the best probabilistic short-term
> marine-heatwave (MHW) forecast method for the sub-Arctic Alaskan shelf seas?**

"Best" is defined operationally: the method that delivers the most skillful and
best-calibrated probabilistic MHW forecasts out-of-sample, relative to climatology
and persistence references, while remaining transparent and defensible. The answer
must be earned empirically and survive formal statistical scrutiny — not assumed
from methods validated in other regions.

The deliverable is a first-rate publication that (a) synthesises the evidence and
(b) identifies the best defensible method for these regions, with an explicit,
pre-registered rule for whether that method is good enough to deploy.

---

## 2. Why this question, and why these regions

- **Decision-support need.** A NOAA AFSC collaborator producing annual crab-stock
  ecosystem report cards (NPFMC cycle) has asked for MHW forecasts. A credible short
  lead-time outlook creates a preparation window for survey planning and risk
  communication.
- **Scientific gap.** Published probabilistic MHW skill assessments concentrate on
  open-ocean, temperate, or low-latitude systems. The **Gulf of Alaska, eastern and
  northern Bering, Chukchi, and Beaufort shelves** — shallow, strongly seasonal,
  sea-ice-affected, with recent regime shifts — are underrepresented, and their
  anomaly dynamics plausibly differ from settings where baselines were validated.
- **Methodological gap.** MHW-forecast studies often under-treat the time-series
  econometrics (trend/stationarity, conditional heteroskedasticity, non-Gaussian
  predictive distributions) and forecast inference (field significance across many
  grid cells under spatial dependence). Doing these correctly is part of the
  contribution and is what makes the chosen "best method" defensible.

---

## 3. Research questions

Three questions, with RQ2 as the core. RQ1 bounds the candidate methods; RQ3 bounds
where the answer is usable.

- **RQ1 — Evidence base.** What methods have been applied to short-term MHW/SST
  forecasting, and what does the literature establish about their skill and
  applicability in **high-latitude, seasonally ice-covered shelf seas**? *(Defines
  the candidate method set in §5 and the gap this study fills.)*

- **RQ2 — Best method (core).** Among the candidate methods, which yields the most
  **skillful and best-calibrated** probabilistic MHW forecasts for the five Alaskan
  shelf regions at operationally relevant leads (≈1–4 weeks), evaluated out-of-sample
  against climatology and persistence references?

- **RQ3 — Where it holds.** Under what conditions (**region, season, lead, ice
  proximity**) does the selected method meet a pre-defined skill-and-calibration
  standard sufficient for decision-support deployment?

*Expected direction (to be confirmed or rejected, not assumed):* the literature and
the red-noise nature of SST anomalies suggest damped persistence / AR-type baselines
are competitive at short leads and decay toward climatology by ~1 month, with weaker
and possibly insignificant skill in ice-affected cells and seasons; trend- and
heteroskedasticity-aware variants are expected to help calibration more than point
skill. RQ2 determines whether these expectations hold here.

---

## 4. Contribution (why it is publishable)

1. The first systematic **best-method assessment for probabilistic MHW forecasting in
   sub-Arctic Alaskan shelf seas**, including ice-affected regions usually excluded.
2. A **defensible method-selection template**: literature-bounded candidate set,
   econometric diagnostics that determine which models are warranted, leakage-free
   out-of-sample verification, and **field significance under spatial dependence**.
3. An explicit, pre-registered **deployment-decision rule** linking statistical skill
   and calibration to an operational go/no-go for a public decision-support tool —
   including the scientifically valid outcome that *no* method qualifies in some
   regions.

---

## 5. Candidate forecast methods (the heart of RQ2)

The candidate set is bounded by RQ1 and refined by the diagnostics in §6 (WP3). All
methods produce a **probabilistic** MHW forecast (per-cell exceedance probability vs
θ₉₀, aggregated to regional products), so they are directly comparable.

| Tier | Method | Rationale |
|------|--------|-----------|
| **Reference (must-beat)** | Climatology (day-of-year MHW frequency) | No-information baseline |
| **Reference (must-beat)** | Persistence | "Today continues" |
| **Statistical baseline** | Damped persistence | Physically grounded (red-noise SST) |
| **Statistical baseline** | AR(1) with predictive variance | Closed-form probability; red-noise basis |
| **Diagnostic extension** | Low-order AR(p) / ARMA | Only if residual diagnostics demand it |
| **Diagnostic extension** | Trend-aware variant | Addresses secular warming in the anomaly |
| **Diagnostic extension** | Heteroskedasticity-aware variant (seasonal/periodic variance) | Corrects probability calibration |
| **Diagnostic extension** | Non-Gaussian / empirical predictive distribution | Ice-edge skew/bounding |
| **Predictor-augmented** | Lagged climate-index regression (PDO/ENSO/AO) | Tests whether teleconnections add short-lead skill |
| **Upper-bound reference** | Regularised ML / analog method | Bounds achievable skill; not necessarily for deployment |

The "best method" is whichever tier-appropriate model wins the §7 verification and
clears the §8 gate — favouring the **simplest method that is not significantly worse
than any more complex one** (parsimony as a tie-breaker).

---

## 6. Data and analysis

### Study domain and data
- **Regions (5):** goa, ebs, nbs, chukchi, beaufort.
- **Primary data:** NOAA OISST v2.1, daily, 0.25°, 1982–present (already ingested).
- **Derived inputs (existing):** day-of-year climatology μ and 90th-percentile
  threshold θ₉₀ (Hobday-style, 1991–2020 baseline, 11-day window, ice-masked); region
  masks; cos-latitude weights. See `config/climatology.yml`.
- **Leads:** {7, 14, 30} days (final set fixed at pre-registration).
- **Train/test discipline (pre-registered default):** the **most recent 7 years**
  form the held-out test period, opened only at verification; every forecast estimates
  parameters using an expanding window **strictly prior to its origin** (no leakage).
  A recent-years test set is deliberately the hardest, most honest choice given the
  warming trend. Revisable only at Gate A, and any deviation reported in the paper.

### Diagnostics that determine the candidate set *(this is where the econometrics live)*
The §5 "diagnostic extensions" are included **only if the data justify them**:
- **Trend:** test for and characterise the secular warming trend; deterministic vs
  stochastic-trend distinction; evaluate fixed-baseline vs detrended anomalies.
- **Stationarity / unit roots:** ADF, KPSS, Phillips–Perron; structural-break-aware
  (Zivot–Andrews). Resolves the differencing (d) question empirically.
- **Seasonal heteroskedasticity:** test and, if present, model time-varying anomaly
  variance (periodic variance / periodic-GARCH or equivalent).
- **Memory:** ACF/PACF; AR-order identification (AIC/BIC/HQ); rule long memory in/out.
- **Distribution:** formal non-normality assessment; implications for the Gaussian
  exceedance step and the case for an empirical predictive distribution.

---

## 7. Verification, inference, and method selection (answers RQ2/RQ3)

- **Proper scoring:** Brier score with reliability/resolution/uncertainty
  decomposition; CRPS; ROC/AUC; Brier Skill Score vs climatology and persistence.
- **Calibration:** reliability diagrams and calibration slopes; out-of-sample
  recalibration (e.g. isotonic/logistic) where pre-registered.
- **Predictive-ability inference:** Diebold–Mariano and Giacomini–White tests for
  conditional predictive ability between competing methods and vs references, per
  region/lead/season.
- **Field significance / multiple testing:** FDR control across cells (Benjamini–
  Hochberg / Benjamini–Yekutieli for dependence) plus spatial field-significance
  (Wilks); block bootstrap (respecting temporal autocorrelation) for confidence
  intervals.
- **Stratification:** all results reported by region, season, lead, and ice proximity.
- **Robustness:** sensitivity to baseline period, threshold (θ₉₀ vs θ₉₅), ice masking,
  and instantaneous-vs-5-day MHW definition.
- **Selection rule:** the best method is the one that maximises skill/calibration
  subject to significance, with parsimony breaking statistical ties.

---

## 8. Deployment gate (pre-registered)

No forecast product is shown on the dashboard or served by the public API unless, for
that specific **region × lead × season**, the selected method satisfies **all** of:

1. **Skill:** Brier Skill Score > 0 versus *both* climatology *and* persistence.
2. **Significance:** the advantage is significant after FDR/field-significance
   correction (§7).
3. **Calibration:** reliability within a pre-set tolerance after any pre-registered
   recalibration.
4. **Honest presentation:** displayed with explicit uncertainty, validated scope, and
   documented limitations (statistical-not-dynamical; instantaneous-exceedance proxy;
   ice-edge caveats).

Products failing the gate are not displayed; the negative result is published.

---

## 9. Work packages, roles, and deliverables

| WP | Work | Lead role | Key deliverables |
|----|------|-----------|------------------|
| **WP1** | Literature review (RQ1) + pre-registration | Literature-review assistants (QA: Senior Research Associate) | Annotated bibliography; gap statement; candidate-set justification; signed pre-registration (hypotheses, methods, metrics, test split, gate thresholds) |
| **WP2** | Data assembly + EDA | Data Analyst | Versioned analysis dataset; EDA report (trend, seasonality, ACF, distributions, ice-edge); data-quality memo |
| **WP3** | Econometric diagnostics → refine candidate set | Expert Econometrician (support: Data Analyst) | Diagnostics report (trend, stationarity, heteroskedasticity, memory, distribution) with test tables/maps; recommended anomaly definition, model orders, error model, predictive-distribution form |
| **WP4** | Specify + estimate candidate methods | Expert Econometrician | Estimation report; parameter maps with uncertainty; frozen specifications |
| **WP5** | Forecast generation (leakage-free rolling origin) | Data Analyst (methods: Econometrician; toolkit: `src/mhw/forecast/`) | Reproducible forecast/outcome archive; run manifests + seeds |
| **WP6** | Verification, inference, method selection (RQ2/RQ3) | Expert Econometrician (support: Senior Research Associate) | Verification report (scoring, calibration, significance, robustness); **the selected best method**, with validated scope |
| **WP7** | Synthesis, manuscript, conditional deployment | Senior Research Associate (all contribute) | Submitted manuscript; deployment-decision memo; (conditional) dashboard/API spec limited to gate-passing products |

The Senior Research Associate owns the timeline, pre-registration integrity, the gate
decisions, and AFSC liaison (Erin, a natural co-author for the decision-support
framing).

---

## 10. Timeline and go/no-go gates

Indicative; weeks are effort-relative. Each gate is a stop point with a written,
reviewed deliverable.

| Phase | Weeks | WPs | Gate (exit criterion) |
|-------|-------|-----|-----------------------|
| **P0 — Scoping** | 1–3 | WP1, WP2 | **Gate A:** pre-registration signed; EDA + data report accepted |
| **P1 — Diagnostics & models** | 4–8 | WP3, WP4 | **Gate B:** candidate set refined; frozen specifications |
| **P2 — Forecast & verify** | 9–14 | WP5, WP6 | **Gate C:** verification report; **best method selected; deployment decision** |
| **P3 — Synthesis** | 15–20 | WP7 | **Gate D:** manuscript submitted; (conditional) deployment spec |

**Pre-registration is binding:** hypotheses, candidate methods, metrics, the test
split, and the §8 thresholds are fixed at Gate A; the held-out test period is opened
only at WP6.

---

## 11. Reproducibility, risks, and scope

**Reproducibility.** All analysis scripted and version-controlled on
`feat/sst-forecast`; engine in `src/mhw/forecast/`; deterministic seeds; archived
forecast/outcome datasets; config-driven parameters. Every table and figure
reproducible end-to-end.

**Risks & mitigations.**

| Risk | Mitigation |
|------|-----------|
| Some/all regions show no skillful method | Pre-committed to publishing negative results; gate blocks deployment |
| Warming trend / regime shifts confound the model | WP3 trend & break testing; trend-aware candidate |
| Ice-edge non-Gaussianity miscalibrates probabilities | Empirical predictive distribution + recalibration; ice-proximity stratification |
| Multiple-testing inflates apparent skill | FDR + field significance + block bootstrap |
| Scope creep | SST + short-lead statistical methods only (see below) |

**Out of scope (explicit).** Bottom-temperature / MOM6 forecasting (separate track:
`feat/mom6-spike` → `feat/bottom-ocean-state`; engine designed to extend there);
seasonal (1–12 month) dynamical forecasting; fish-stock forecasting. The
value-of-information / decision-economics analysis is reserved as **future work / a
companion paper**, not part of this study.

---

## 12. Candidate target journals

*Weather and Forecasting* (verification-focused); *Progress in Oceanography* /
*Fisheries Oceanography* (regional, applied); *Communications Earth & Environment* /
*Frontiers in Marine Science* (broad); *Environmental Data Science* (methods +
decision-support).

---

## 13. Key references (to be expanded in WP1)

- Hobday, A. J., et al. (2016). *A hierarchical approach to defining marine
  heatwaves.* Progress in Oceanography.
- Frankignoul, C., & Hasselmann, K. (1977). *Stochastic climate models, Part II.*
  Tellus, 29(4). (AR(1)/red-noise basis for SST anomalies.)
- Jacox, M. G., et al. (2022). *Global seasonal forecasts of marine heatwaves.*
  Nature.
- *Probabilistic extreme SST and marine heatwave forecasts in Chesapeake Bay.*
  Frontiers in Marine Science (2022).
- Verification & inference: Diebold & Mariano (1995); Giacomini & White (2006);
  Wilks (field significance / forecast verification); Benjamini & Hochberg (1995);
  Benjamini & Yekutieli (2001).
- Companion internal docs: `sst-forecast-methodology.md`, `sst-forecast-mvp-plan.md`.
