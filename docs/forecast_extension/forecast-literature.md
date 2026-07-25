# Where forecast science stands for high-latitude SSTs — a North Pacific orientation scan

- **For:** Col. Raj (director, ACFR) · **By:** Advisor (acting LOFRA) · **Date:** 2026-06-24
- **Type:** orientation briefing — synthesizes *existing* ACFR/cell intelligence; no new search, no spawn
- **Frame:** North Pacific high latitude (Gulf of Alaska + Bering / NE Pacific); Barents/Nordic used only as transfer comparison
- **Grade:** internal — inherits the preliminary, revisitable posture of the sources it draws on
- **Grounding tags:** `[FT]` full-text-verified · `[ABS]` abstract-verified · `[META]` metadata-only (no content claim rests on `[META]`)

**In one paragraph.** High-latitude SST/MHW *forecasting* exists today mostly as **skill borrowed from
elsewhere**: the method families are mature in open-ocean, temperate, and tropical systems, and the
nearest well-studied case to us is the NE Pacific "Blob," but the Gulf of Alaska / Bering shelf *itself*
is a documented near-blank for forecast methods. By contrast, the **predictability basis** for our
region — why high-latitude SST anomalies persist long enough to be forecastable — is comparatively
well-characterized, through two partly-competing accounts (atmospheric teleconnection sequencing vs.
subsurface ocean memory). The practical state of play: a defensible GOA system would transfer a proven
method in, not build on local precedent, with that transfer as the load-bearing risk.

---

## Page 1 — State of forecast methods and skill

**1. The method families that exist (and where they're proven).** The forecast-method corpus (23
papers full-text-extracted into a method × region matrix) covers the full toolkit `[FT]`:

- **Coupled dynamical seasonal systems** — NMME (Jacox 2022), SEAS5 (de Boisséson 2024; Liu 2025),
  ACCESS-S2 (Spillman 2021; Smith 2024), CMCC-SPS3.5 (McAdam 2023), NUIST-CFS1.0 (Zhang 2023; Tang
  2024). The workhorse for **1–3-month-lead** MHW prediction; skill is real but **ENSO-modulated** and
  concentrated outside the sub-Arctic `[FT]`.
- **Pure ML / deep learning** — LSTM/RF/CNN (Bonino 2024), U-Net variants (Taylor 2022; Parasyris 2025;
  Howard 2026), MHWUNet (Sun 2024). Strongest at **1-day–2-week** leads; the matrix's pool is
  Mediterranean- and Indian-Ocean-dominated `[FT]`.
- **Hybrid ML-corrects-dynamical** (Sun 2024 over UKMO S2S; Ross 2022) — the sub-seasonal sweet spot,
  since pure DL tends to freeze spatial patterns past ~10 days `[FT]`.
- **LIM / inverse** (Wang 2023), **analog** (Walsh 2021, Alaska, but for *air* temperature), and
  **persistence-transform** (Lee 2012) — baselines and niche tools `[FT]`.

Headline skill where it's been shown: dynamical SST anomaly correlation r > 0.8 in tropics and the far
northern Pacific at month 0 (Smith 2024 `[FT]`); DL day-1 RMSE 0.11–0.19 °C in Mediterranean sub-basins
(Bonino 2024 `[FT]`); calibrated probabilistic verification (BSS, SEDI, ROC, reliability) is now the
field norm (Jacox 2022, Liu 2025, Smith 2024 `[FT]`).

**2. Where high-latitude skill is established — and where it is absent.** The nearest well-studied case
to us is the **NE Pacific Blob region**: Tang 2024 (NUIST-CFS1.0 + EnKF data assimilation), Liu 2025
(SEAS5 over the NEP including a GOA sub-region), and Taylor 2022 (U-Net tracking the 2014/15/19 events)
all sit immediately adjacent to our target `[FT]`. But the **GOA / Bering shelf itself is a documented
gap**: a dedicated regional-gap memo found the direct-sub-Arctic pool of 2,255 records to be rich in
fisheries, ecology, sea-ice, and impacts work but **essentially empty of SST/MHW forecast-method papers
that report skill against a baseline** `[FT]`. The Welandawe 2025 ML-for-MHW review corroborates from
outside the corpus: **zero** of its reviewed studies fall in the sub-Arctic/Alaska/Bering/Barents
envelope `[FT]`. Direct sub-Arctic forecast evidence amounts to three rows — two of them EGU conference
abstracts without quantitative skill (Langehaug 2024 Barents; de Boisséson 2022 NEP precursor) and
Walsh 2021, which targets air temperature, not SST `[ABS]`.

**3. The high-latitude-specific hard parts.** Four issues make transfer non-trivial:

- **Trend vs. forecastable interannual signal.** Zhang 2023's decomposition is the cleanest warning:
  trend-only skill extends ~9 months, but the **detrended interannual** basin-mean signal is significant
  only to **~3 months** `[FT]`. Much apparent long-lead skill in a warming sub-Arctic record is trend,
  not a forecastable signal. Trend handling across the corpus is inconsistent (Jacox detrends both ways;
  Smith 2024 deliberately doesn't and says so) `[FT]`.
- **Persistence is a strong baseline, not a floor.** At subsurface and high-thermal-inertia scales,
  persistence often beats the dynamical model (Smith 2024, McAdam 2023) `[FT]`; it must be reported, not
  assumed beaten.
- **Ice-masking is unaddressed** anywhere in the matrix — the least-served criterion for any
  Bering/Chukchi/Beaufort application `[FT]`.
- **Regime-shift robustness is unestablished** for a sub-Arctic shelf; Welandawe 2025 flags rare-event /
  post-regime-shift performance as an open field-wide gap `[FT]`.

---

## Page 2 — The predictability basis and the frontier

**4. Why high-latitude SST is forecastable at all.** Unlike the method gap, the *source-of-skill*
question for our region is comparatively well-mapped — through **two partly-competing accounts**:

- **Atmospheric teleconnection sequencing.** Di Lorenzo & Mantua 2016 `[FT]` is explicit that the
  2014/15 multi-year persistence was **not** static ocean memory but a *serial atmospheric* chain: an
  NPGO-like GOA forcing in 2014 → a weak El Niño via extratropical–tropical teleconnection → a PDO-like
  pattern in 2015, **mediated by Aleutian-Low modulation**. Persistence here lives in the atmosphere and
  ENSO, not the ocean.
- **Subsurface ocean memory / re-emergence.** Scannell 2020 `[ABS]` documents 2019 subsurface anomalies
  developing from 2017, insulated by a shallow mixed layer; Xu 2026 `[ABS]` ties OHC to MHW persistence
  via seasonal re-emergence; Amaya 2021 `[FT]` supplies the physics — a shoaling mixed layer amplifies
  the SST response per unit heat content (∂T/∂t ≈ Q/ρcₚh), with observed NE Pacific MLD shoaling and a
  2019 record minimum.

These accounts are in productive tension, and the forecast literature already adjudicates part of it:
**Tang 2024 `[FT]` shows subsurface data assimilation (EnKF) is required to capture the Blob-class
signal — SST-nudging alone fails** — which is the strongest practical argument that the subsurface-memory
channel must be in any GOA system, whatever its share of total predictability.

**5. Teleconnection precursors — honestly calibrated.** The PDO is well-developed in the existing
intelligence as a persistence/forcing pattern `[FT/ABS]`. The **Arctic Oscillation as a developed
predictability channel is, by contrast, essentially absent** from what the cell assembled: AO appears
only as a candidate atmospheric driver in the GOA-SST regression work, not as a demonstrated multi-year
SST precursor, and the **Aleutian Low** surfaces only *inside* the Di Lorenzo teleconnection mechanism
— never as a forecast handle in its own right. So the upstream `AO → Aleutian Low → PDO` precursor chain
is a **genuine open question, not a settled result** — which is precisely why it is the subject of the
new `lit-intel/` teleconnection `[SCOPE]` rather than something this scan can report on. Stated plainly:
the field gives us the PDO end of the chain and a glimpse of the Aleutian-Low mediator; the Arctic front
end is unexamined here.

**6. Net orientation.** For a North Pacific high-latitude target today, the defensible path the existing
synthesis converges on is a **coupled dynamical seasonal system with subsurface data assimilation**
(Tang 2024 / Liu 2025 lineage), made **trend-explicit** (Zhang 2023 decomposition), and verified
**probabilistically against a real persistence baseline** (Liu 2025 / Smith 2024) — *transferred in*
from where it was proven, with the absence of direct GOA-shelf validation stated as the load-bearing
risk. The predictability basis to lean on is dual (atmospheric teleconnection + subsurface memory), and
the subsurface channel is the one the forecast evidence says you cannot omit. The AO/Aleutian-Low
precursor question is open and worth its own pull — but it is not yet evidence you can build on.

---

### Grounding note
- **Full-text `[FT]`:** the 23-paper forecast extraction matrix and its method-family/skill claims;
  Di Lorenzo & Mantua 2016; Amaya 2021; Tang/Liu/Zhang/Smith forecast specifics; the regional-gap and
  Welandawe-2025 findings. **Abstract `[ABS]`:** Scannell 2020, Xu 2026, the two EGU conference rows.
- **Central honest caveat:** there is essentially **no direct GOA/Bering-shelf SST/MHW forecast-method
  evidence**; every method recommendation here is a *transfer* argument, and transfer to a shallow,
  strongly seasonal, ice-affected, regime-shifting shelf is the open risk. This briefing inherits the
  internal, preliminary grade of its sources and is not a fresh adjudication of the field.
- **Sources:** ACFR `projects/sst-forecast-method-review/` (preliminary literature review, sub-Arctic
  regional-gap memo, direction bridge, extraction matrix, full-text bodytexts) and cell-runtime
  `gulf-of-alaska-sst/` (positioning memo, post-Stage-8 literature-integration synthesis, dossiers:
  Di Lorenzo–Mantua 2016, Scannell 2020, Amaya 2021, Xu 2026, Bond 2015). Read-only; nothing in the cell
  runtime was altered.
