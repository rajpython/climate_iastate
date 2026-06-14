# Short-Term Marine Heatwave Forecast — Methodology

*For fisheries scientists, ecosystem analysts, and managers. Technical, but written
to be read end-to-end without a statistics background. Every modelling choice is
stated, along with its assumptions and limitations.*

**Status:** development (branch `feat/sst-forecast`). The forecast products
described here are experimental.

---

## 1. What this forecast is — and is not

**Is:** a short-term, *probabilistic* outlook for sea-surface marine heatwave (MHW)
conditions. For each location and each lead time it answers one question:

> *How likely is the sea surface to be in marine-heatwave conditions 2 weeks (or
> 1 month) from now?*

The answer is a **probability** (e.g. "65% chance"), not a yes/no call, and it
comes with an explicit, growing uncertainty.

**Is not:**

- It is **not a dynamical ocean/atmosphere model.** It does not simulate winds,
  currents, or El Niño. It is a *statistical* forecast built from the recent and
  historical behaviour of sea temperature itself.
- It is **not a fish forecast.** It forecasts an *ocean state* (temperature),
  which is an input to ecological risk — not stock size, recruitment, or catch.
- It is **not a long-range forecast.** Useful skill from these methods lives in the
  days-to-~one-month range. Seasonal (1–12 month) forecasting is a separate,
  later effort using operational climate models.

The guiding philosophy is honesty over sophistication: start with simple, well-
understood baselines, measure their skill openly, and let that skill be the bar any
future, fancier method must clear.

---

## 2. Background: what a marine heatwave is here

We use the widely adopted Hobday et al. (2016) definition, already implemented in
the monitoring dashboard (see `mhw_README.md`). In brief:

- For every calendar day-of-year and every 0.25° grid cell we know the
  **climatological mean** temperature, written **μ** (mu), and a **warm threshold**,
  the **90th percentile** of historical temperature for that day, written **θ₉₀**
  (theta-90).
- A cell is in MHW conditions on a day when its temperature exceeds **θ₉₀**.
  (The full monitoring definition also requires the warm spell to last ≥5 days; see
  §9 for how the forecast relates to that.)

Two facts that matter for the forecast:

1. Because θ₉₀ is the **90th percentile**, on any random day the *climatological*
   chance of exceeding it is about **10%**. So "10%" is the natural no-information
   baseline a useful forecast should beat or move away from.
2. The threshold and climatology are **day-of-year specific and ice-aware**, so the
   forecast inherits the same seasonally-varying, ice-masked definition the
   dashboard already uses — no separate or inconsistent thresholds.

---

## 3. Data used

Everything the forecast needs already exists in the project — **no new data is
ingested for this MVP.**

| Input | What it is | Source / location |
|-------|-----------|-------------------|
| Daily sea-surface temperature | NOAA OISST v2.1, 0.25° grid, daily, 1982–present, ~24 h latency | OISST cache (`mhw.climatology.build_mu_theta`) |
| Climatological mean **μ**(day-of-year) | Hobday baseline mean per cell | `data/derived/climatology/mu_<region>.zarr` |
| Warm threshold **θ₉₀**(day-of-year) | 90th-percentile threshold per cell | `data/derived/climatology/theta90_<region>.zarr` |
| Region masks + area weights | Which cells belong to each region; cos-latitude area weighting | `mhw.regions.masks`, `mhw.regions.weights` |
| Sea-ice mask | OISST internal ice fraction (>15% excluded) | applied as in monitoring |

**Climatology details (from `config/climatology.yml`):** baseline period
**1991–2020**, an **11-day window** centred on each day-of-year, **90th percentile**
threshold, ice-masked. The forecast uses these exact products so it is consistent
with the live monitoring numbers.

**Regions:** Gulf of Alaska (goa), Eastern Bering Sea (ebs), Northern Bering Sea
(nbs), Chukchi Sea (chukchi), Beaufort Sea (beaufort).

---

## 4. The core idea in one paragraph

Sea temperature has *memory*: an unusually warm patch of ocean tends to stay
unusually warm for a while before fading back toward normal. We measure how warm
things are *right now* relative to normal, project that anomaly forward at the rate
the ocean historically "forgets" it, attach an honest uncertainty that grows with
lead time, and then compute the probability that the projected temperature lands
above the marine-heatwave threshold. We do this at every grid cell, producing a
**map of MHW probability**, and then summarize each region.

---

## 5. The method, step by step

### Step 1 — Measure today's anomaly

For each cell we compute the **anomaly**: how far today's temperature is from the
day-of-year normal.

```
anomaly(today) = SST(today) − μ(day-of-year)
```

A positive anomaly means warmer than normal. The forecast is built entirely in
anomaly space, which removes the seasonal cycle and lets us treat all times of year
on a common footing.

### Step 2 — Project the anomaly forward (the forecast "engine")

We use three standard baselines. All three say the anomaly decays toward zero
(normal) over time; they differ in how, and in whether they carry uncertainty.

- **Persistence** — "tomorrow looks like today." The projected anomaly stays equal
  to today's. Simplest possible forecast; a baseline every method must beat.

- **Damped persistence** — today's anomaly, but fading toward normal at the speed
  the ocean historically fades:
  ```
  anomaly(lead h) = φ^h × anomaly(today)
  ```
  Here **φ** (phi) is the **lag-1 autocorrelation** — a number between 0 and 1 that
  measures memory. φ near 1 = long memory (anomalies persist for weeks); φ near 0 =
  short memory (anomalies vanish in days). φ is estimated **separately for each
  cell** from its own history, so regions with deep mixed layers or persistent
  circulation get the slow decay they deserve.

- **AR(1)** — the same decaying mean as damped persistence, **plus an explicit,
  growing uncertainty**. This is the primary probabilistic method. It models the
  anomaly as a "first-order autoregressive" process and gives, at each lead, both a
  best estimate and a spread:
  ```
  mean(h)     = φ^h × anomaly(today)
  variance(h) = σ²_ε × (1 − φ^(2h)) / (1 − φ²)
  ```
  **σ_ε** (sigma-epsilon) is the typical size of week-to-week random "shocks,"
  again estimated per cell. The variance formula has an important, physically
  sensible behaviour: at short leads the spread is small; as the lead grows the
  spread **saturates** at the historical (climatological) spread of anomalies — the
  forecast never claims to know more than climatology at long range.

**Where φ and σ_ε come from.** Both are fit per cell from the historical anomaly
record (the same multi-decade series behind the monitoring climatology), using a
simple lag-1 regression. Fitting uses only past data; see §8 on avoiding leakage.

### Step 3 — Turn the projected anomaly into an MHW probability

The marine-heatwave threshold, expressed in anomaly space, is:

```
threshold = θ₉₀(day-of-year) − μ(day-of-year)      (always positive)
```

The AR(1) forecast says the future anomaly is centred on `mean(h)` with spread
`σ(h) = √variance(h)`. We treat that uncertainty as a bell curve (Gaussian) and ask
what fraction of it sits above the threshold:

```
P(MHW at lead h) = probability( forecast anomaly > threshold )
                 = Φ( ( mean(h) − threshold ) / σ(h) )
```

where Φ is the standard normal cumulative function. In words: **if the projected
warmth is well above the heatwave line relative to the forecast uncertainty, the
probability is high; if it is well below, the probability is low.** This is the same
construction used in published seasonal MHW forecasts (Jacox et al. 2022).

A useful sanity check falls out of the math: at long leads, `mean → 0` and
`σ → climatological spread`, so the probability returns to roughly the
climatological **~10%**. The forecast adds value precisely when it departs from that
10% because current conditions and ocean memory justify it.

### Step 4 — From cells to regions

The per-cell probabilities form the primary product: a **spatial MHW-probability
map**. From that map we derive the regional summaries, using the same area weights
as the monitoring dashboard:

- **Regional MHW probability / expected area fraction** — the area-weighted average
  of the cell probabilities, i.e. the expected fraction of the region in MHW at that
  lead. (This is the forecast analogue of the monitored `area_frac`.)

Note the deliberate direction: we forecast the *primitive* (temperature) at the
grid and **derive** the area/regional numbers. We do not forecast the regional
aggregate directly — that would throw away the spatial structure that makes the map
useful.

---

## 6. Forecast horizons

Three outlooks are produced:

| Horizon | Lead | Intended use |
|---------|------|--------------|
| Nowcast | current | situational awareness, consistent with monitoring |
| Short-range | **2 weeks** | the headline outlook; where statistical skill is strongest |
| Extended | **1 month** | early signal; expect skill to approach the climatology floor |

We stop near one month because beyond that, statistical persistence has typically
decayed to climatology and genuine skill requires dynamical seasonal models (a
later, separate effort).

---

## 7. The products

- **MHW probability map** per region per lead — the main deliverable, and the most
  informative artefact for an ecosystem report card.
- **Regional outlook** — a single probability / expected-area-fraction number per
  region per lead, suitable for a dashboard gauge or a one-line risk statement.
- **Uncertainty is always shown**, never hidden behind a point estimate.

---

## 8. How we know whether it works (verification)

A forecast is only worth showing if it beats the cheap alternatives. We verify with
a **rolling-origin ("walk-forward") backtest**:

1. Pick many historical forecast dates.
2. For each, fit φ and σ_ε using **only data before that date** (no peeking at the
   future — this avoids "leakage" that would inflate apparent skill).
3. Forecast 2 weeks and 1 month ahead.
4. Compare the forecast probability against what actually happened (MHW or not).

We score with the **Brier score** (mean squared error of the probability against
the 0/1 outcome) and summarize as a **Brier Skill Score** relative to two
references:

- **Climatology** — always predicting the day-of-year MHW frequency (~10%).
- **Persistence** — "today's state continues."

A positive skill score means the forecast beats that reference; zero means no
improvement; negative means worse. **We will report skill honestly per region and
lead, and only promote products that beat both baselines** — and we will say plainly
where they do not.

---

## 9. Assumptions and limitations (read this section)

- **Statistical, not dynamical.** The forecast extrapolates temperature's own
  memory. It cannot anticipate a new event driven by winds, a marine cold/warm
  intrusion, or an El Niño that has not yet shown up in the temperature record.
- **Gaussian uncertainty.** We approximate forecast spread as a bell curve. Real
  anomalies have some skew, especially near sea ice; probabilities near 0 or 1
  should be read as "very unlikely / very likely," not literal precision.
- **Stationarity of memory.** φ and σ_ε are assumed roughly stable through time and
  estimated per cell. A long-term warming trend is partly absorbed into the
  climatology baseline (1991–2020) and partly not; very warm recent years can push
  baseline-relative anomalies high.
- **Threshold inherits monitoring choices.** The 90th-percentile, 1991–2020,
  11-day-window, 15%-ice definition is a defensible convention, not a unique truth.
- **Instantaneous exceedance vs the 5-day rule.** The forecast estimates the
  probability that conditions *exceed the threshold* at a given lead. The full
  Hobday MHW also requires a ≥5-day warm spell. The forecast probability is
  therefore a close proxy for "in MHW conditions," not a literal probability of a
  confirmed 5-day event; this is stated wherever the product is presented.
- **Edges and ice.** Near the ice edge and in seasonally ice-covered cells,
  data gaps and masking reduce reliability; those cells are handled with the same
  ice mask as monitoring.

---

## 10. Why these methods (and not something more complex)

Damped persistence and AR(1) are the **standard low-cost baselines** in the
marine-heatwave forecasting literature precisely because they are hard to beat at
short range and trivial to understand and reproduce. Building them first gives us:

1. A genuinely useful product quickly, on data we already hold.
2. An honest, quantified **skill bar** that any future dynamical or seasonal product
   must clear to justify its added complexity.

---

## 11. How this fits the bigger picture

The forecast is built as a **variable- and source-agnostic engine**: it forecasts
*an anomaly field* against *a threshold field*. That means the very same machinery
will later forecast **bottom-temperature** marine heatwaves (swap in MOM6 bottom
temperature and its threshold) and ingest **seasonal climate-model ensembles**, with
no change to the core math — only the data adapter changes. Today's SST forecast is
therefore both a deliverable and the foundation for the fisheries-relevant forecasts
to come.

---

## 12. Reproducibility — where the method lives

| Component | Location |
|-----------|----------|
| Forecast engine (math) | `src/mhw/forecast/baselines.py`, `exceedance.py`, `regional.py` |
| Data adapters | `src/mhw/forecast/io.py` |
| Verification | `src/mhw/forecast/backtest.py` |
| Command-line tool | `mhw-forecast` (`src/mhw/forecast/cli.py`) |
| Engineering plan | `docs/forecast_extension/sst-forecast-mvp-plan.md` |
| This methodology | `docs/forecast_extension/sst-forecast-methodology.md` |
| Definitions / parameters | `config/climatology.yml`, `config/datasets.yml` |

When the dashboard panel and API endpoint ship, a plain-language version of this
document will feed the dashboard **User Guide** and the **API docs**, so external
users see the same methodology described here.

Intended invocation (once data wiring is complete):

```
mhw-forecast --region ebs --leads 14,30 --method ar1
```

---

## 13. Glossary

- **Anomaly** — temperature minus the day-of-year normal (μ). Positive = warmer.
- **μ (mu)** — climatological mean temperature for a cell and day-of-year.
- **θ₉₀ (theta-90)** — the 90th-percentile warm threshold; the marine-heatwave line.
- **φ (phi)** — lag-1 autocorrelation; how strongly the ocean "remembers" anomalies.
- **σ_ε (sigma-epsilon)** — typical size of random week-to-week temperature shocks.
- **Lead time** — how far ahead the forecast looks (e.g. 14 days).
- **Brier score / skill score** — measures of how good a probability forecast is.
- **Climatology baseline** — always predicting the historical average frequency.

---

## 14. References

- Hobday, A. J., et al. (2016). *A hierarchical approach to defining marine
  heatwaves.* Progress in Oceanography.
- Jacox, M. G., et al. (2022). *Global seasonal forecasts of marine heatwaves.*
  Nature. (Source of the anomaly → exceedance-probability construction.)
- NOAA OISST v2.1 — Optimum Interpolation Sea Surface Temperature.
