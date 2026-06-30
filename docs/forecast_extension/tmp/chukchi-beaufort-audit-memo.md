# Technical memorandum — Chukchi vs Beaufort bottom temperature: follow-up audit

**Date:** 2026-06-28 · scope: the six remaining-uncertainty questions only.
**Data:** MOM6 NEP, Jul–Sep, 1993–2024; area-weighted (cos-lat) on the 0.25° analysis grid;
2014–2024 climatology. Evidence files in this folder: `annual_series.csv`,
`chukchi_beaufort_cells.csv`, `chukchi_beaufort_depthbins.csv`, `cb_annual_bands.png`, `cb_maps.png`,
`chukchi_beaufort_Tbz.png`.

## Bottom line
The **primary conclusion stands and is strengthened**: the whole-shelf "Beaufort ≳ Chukchi" is a
**depth-composition (Simpson) artifact**, now quantified and binning-robust. But the audit
**corrects three narrative claims** from the first memo:
1. 2024 was **not** an "atypically cold Chukchi year" — it was a *moderately* cool Chukchi **and** a
   warm Beaufort *simultaneously* (the coincidence, amplified by an Aug-only first cut, drove it).
2. The matched-depth ordering is **not** "Chukchi warmer at 0–100 m." The crossover is **~60 m**:
   Chukchi warmer in the **upper shelf (<~60 m)**, Beaufort warmer in the **deeper shelf (>60 m)**.
3. The deep-bin reversal is **"Chukchi is anomalously cold," not "Beaufort has warm Atlantic water"**
   — the Atlantic-Water attribution is **not supported** by the data.

---

## Q1 — Was 2024 anomalous? (evidence, not narrative)

Jul–Sep area-weighted, anomaly vs 2014–2024 clim, rank of 32 yrs (1 = coldest):

| Series | Chukchi 2024 / anom / rank | Beaufort 2024 / anom / rank |
|---|---|---|
| whole shelf | +0.93 / **−0.55** / **13/32** | +1.92 / **+0.25** / **25/32** |
| 0–30 m | +4.50 / −1.41 / 11/32 | +3.99 / +0.07 / 23/32 |
| 30–100 m | +0.31 / −0.40 / 14/32 | +0.90 / +0.43 / 26/32 |
| 100–200 m | −1.24 / −0.13 / 18/32 | −0.17 / +0.13 / 27/32 |

**Finding:** 2024 was only *modestly* cool for the Chukchi (rank 13/32, ~median; not extreme) but
distinctly *warm* for the Beaufort (rank 25/32). The original single-year confusion came from the
**coincidence of a cool Chukchi + warm Beaufort**, not an extreme Chukchi cold year — and was further
exaggerated by the first cut using **August only** rather than Jul–Sep. The two series have high,
largely independent interannual variability and cross frequently (`cb_annual_bands.png`).
→ **Revises** the first memo's "atypically cold Chukchi year."

## Q2 — Simpson decomposition (does composition *explain most* of the gap?)

Whole-shelf Δ(Beaufort − Chukchi) = **+0.18 °C**. Symmetric shift-share, **robust to binning**:

| Binning | Composition (depth dist.) | Within-bin temperature | Sum |
|---|---|---|---|
| 6 bins | **+0.96** | **−0.77** | +0.18 |
| 10 m bins | **+1.00** | **−0.81** | +0.18 |

Counterfactuals: Beaufort temps on the **Chukchi** depth distribution → **+0.90 °C** (0.6 °C *colder*
than Chukchi); Chukchi temps on the **Beaufort** distribution → **+2.63 °C** (warmer than Beaufort).

**Finding:** composition is **not "merely present" — it is the dominant driver**, ~5× the net
difference, and it **overwhelms** an opposing within-bin temperature effect (−0.8 °C: on an
area-weighted basis the Chukchi is *warmer* at matched depth, because the high-area upper/mid shelf
favours it). → **Confirms and strengthens** the composition explanation.

## Q3 — The shallow 0–10 m bin: broad or localized?

| | n cells | % shelf **area** | mean T | dist-to-coast (mean / max) | top-3 cells = % of bin area |
|---|---|---|---|---|---|
| Chukchi | 20 | **2.3 %** | +8.6 °C | 32 / 63 km | 16 % |
| Beaufort | 22 | **10.2 %** | +6.9 °C | 56 / 84 km | 14 % |

**Finding:** the warmth is **not** dominated by a few cells (top-3 ≈ 14–16 %) and is **not** a
lagoon/river-mouth signature — cells sit ~1–2 grid cells (30–80 km) off the coast: a **broad
near-coastal shallow band**. It is **negligible by area in the Chukchi (2.3 %)** but **material in the
narrow Beaufort (10.2 %)**. Mean is 7–9 °C (the earlier "up to ~13 °C" was an unrepresentative max).
Plausible summer near-coastal warming; realism vs in-situ **not** verified. → **Revises** the
"lagoon/river-mouth, ~13 °C" wording.

## Q4 — Sensitivity to bin definition (the consequential check)

Sign of (Chukchi − Beaufort), area-weighted T per bin:
- **10 m bins:** Chukchi warmer 0–60 m (+0.1 to +3.2), Beaufort warmer 60–200 m (−0.3 to −1.9; one
  small +0.2 blip at 90–100). Crossover ≈ **55–60 m**.
- **20 m bins:** Chukchi warmer 0–60 m, Beaufort warmer 60–200 m.
- **Quantile bins** (edges 0/17/39/47/54/200 m): +2.05, +1.70, +0.04, +0.49, −0.04 — Chukchi warmer
  in the shallow four, ~equal in the deepest.

**Finding:** the matched-depth ordering is **depth-dependent**, with a **~60 m crossover** — robust
across 10 m, 20 m and quantile bins. The first memo's 6-bin "**Chukchi warmer at 50–100 m**" was a
**coarse-bin artifact**: within that wide bin the two regions' depths differ (Chukchi concentrated at
50–55 m, where it *is* warmer), masking the ~60 m sign flip. → **Revises** the headline to: *Chukchi
warmer in the upper shelf (<~60 m); Beaufort warmer in the deeper shelf (>60 m).* (The area-weighted
*aggregate* still favours the Chukchi because the upper/mid shelf carries most area — consistent with
Q2's −0.8 within-bin term.)

## Q5 — The 100–200 m reversal

| | 100–150 m | 150–200 m |
|---|---|---|
| Chukchi | −0.98 °C (0.9 % area, n=10) | −1.35 °C (0.5 % area, n=6) |
| Beaufort | −0.27 °C (8.8 % area, n=20) | −0.36 °C (4.8 % area, n=11) |

**Finding:**
- Concentrated near **neither 100 nor 200 m specifically** — the Beaufort 150–200 m is *slightly
  colder* than its 100–150 m, i.e. temperature **does not increase with depth** toward 200 m.
- **Geographically localized:** Chukchi deep cells are the small NW canyon corner (Herald/Barrow
  drainage; `cb_maps.png`); Beaufort deep cells are the offshore shelf-break strip.
- **Not consistent with warm Atlantic Water:** both regions are **near-freezing** at 100–200 m
  (Beaufort −0.3 °C, not warm); the Atlantic-Water core is **deeper than our 200 m cap**. The
  reversal is because the **Chukchi is anomalously cold** there (dense winter water draining the
  canyons, −1.0 to −1.35 °C), **not** because the Beaufort is warm. → **Revises** the Atlantic-Water
  attribution to *unsupported*.
- **Contribution to shelf means is small:** Chukchi 100–200 m is only 1.4 % of area (≈ −0.016 °C);
  Beaufort 13.6 % (≈ −0.040 °C). The deep bin is *not* what drives the whole-shelf comparison.

## Q6 — Validation vs plausibility (tightened language)

- **(a) Direct evidence — from MOM6 only.** The T_b(z) shape, the ~60 m crossover, the decomposition,
  the band time series, the near-coastal shallow-warm band. These are **internally consistent
  properties of the model**, not of the ocean.
- **(b) Agreement with known circulation.** The **upper-shelf Chukchi-warmer** signal is consistent
  with Pacific Summer Water transiting the Chukchi (literature). This is **consistency, not
  validation**.
- **(c) Observational validation.** **None performed** — no in-situ Arctic bottom temperatures were
  used.

**Observationally supported:** nothing directly. **Consistent-with-circulation (hypothesis-grade):**
the shallow/upper-shelf Chukchi-warm pattern. **Unsupported / revised:** the deep-reversal
"Atlantic-Water" mechanism (data favour "Chukchi-cold," not Atlantic warmth). **Open / needs data:**
realism of the 7–9 °C shallow warming (possible model over-mixing), and any absolute-bias check of
MOM6 Arctic — both require in-situ or an independent reanalysis, out of current scope.

---

## Verdict — archive the primary finding; correct the narrative; flag the rest as model-only

- **Archive:** the whole-shelf "Beaufort ≳ Chukchi" is a **depth-composition artifact** —
  quantified (composition +1.0 °C vs net +0.18 °C), binning-robust, explained by the broad-cold
  Chukchi shelf vs the narrow-shallow Beaufort shelf. **Robust enough to close.**
- **Correct** the first memo / investigation doc on three points: 2024 framing (Q1); the ~60 m
  crossover, not 0–100 m (Q4); the Atlantic-Water attribution is unsupported (Q5).
- **Do not** apply a min-depth floor (Q2/Q4 confirm it would mask a composition effect).
- **Still genuinely open** (model-only / unvalidated, needs observations): shallow-warming realism
  and absolute MOM6 Arctic bias. These do **not** block archiving the composition conclusion but keep
  the dashboard's "Arctic = model-only, unvalidated in-region" caveat in force.
