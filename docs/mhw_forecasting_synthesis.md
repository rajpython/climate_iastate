# Forecasting Marine Heatwaves in Alaska Shelf Seas: Methods, Predictability, and Validation Challenges

*Synthesis review · June 2026*

**Abstract.** Despite rapid progress in global and regional marine-heatwave (MHW) forecasting,
there is little direct evidence on forecast skill for the Gulf of Alaska and the Bering, Chukchi,
and Beaufort shelves. The methodological approaches available for such forecasts — coupled
dynamical seasonal systems, machine-learning and hybrid models, linear inverse models, and
statistical baselines — are mature in open-ocean, temperate, and tropical systems, and the
principal physical mechanisms governing high-latitude sea-surface temperature (SST) persistence
have been extensively investigated. The principal gap is the absence of region-specific
evaluation. The central scientific problem is not the absence of forecasting methods; it is the
absence of validated, benchmarked, trend-aware, probabilistic forecast evaluation for Alaska shelf
systems. This synthesis is organized around the distinction between forecasting methodology,
forecast validation, and physical predictability: it distinguishes existing forecast methodologies
from the evidence on their forecast skill, the mechanisms that may confer predictability, and the
outstanding methodological challenges specific to Alaska shelf seas, and closes with the elements
of a credible regional evaluation design. The focus is the North Pacific high latitudes; sub-Arctic
Atlantic systems are considered only for comparison, and the distinct physical regimes of the
deeper, open-ocean-influenced Gulf of Alaska and the shallow, seasonally ice-affected Bering and
Arctic shelves are treated as separate problems.

---

## 1. The predictand and the evaluation problem

Forecast evaluation begins with the definition of the predictand (the quantity to be predicted),
and the relevant studies do not share a common predictand. Five distinct targets appear in the
literature and should not be conflated: (i) SST anomaly forecasting, a continuous prediction; (ii)
MHW binary occurrence, a threshold-exceedance event; (iii) MHW intensity and duration, including
onset, decline, and cumulative magnitude; (iv) probabilistic event forecasting, the calibrated
probability of an MHW; and (v) shelf and bottom thermal-state forecasting, addressing subsurface or
near-bottom temperature as distinct from the surface. These predictands are not interchangeable. A
method validated for one does not automatically transfer to another, and calibrated probabilistic
occurrence skill in particular is not implied by a low SST-anomaly root-mean-square error.

The evaluation criterion matters as much as the predictand. For a climate-econometrics readership
the relevant question is whether a model demonstrates superior out-of-sample probabilistic skill
relative to persistence and climatology, under a transparent treatment of trend and regime change.
Persistence and climatology are therefore not minor baselines but the central benchmarks; a model
that does not improve upon persistence is of limited operational value. This standard is exacting at
high latitudes precisely because oceanic thermal inertia makes persistence strong: at subsurface and
high-heat-content scales, simple persistence frequently outperforms dynamical models (Smith &
Spillman 2024; McAdam et al. 2023), and damped-persistence and persistence-transformation schemes
are competitive benchmarks in their own right (Lee & Tzeng 2012; Ross & Stock 2022). Any claim of
skill for an Alaska shelf system must be stated relative to these benchmarks and under an explicit
treatment of the warming trend (Section 5).

## 2. Existing forecast methodologies

The methodological repertoire is well developed and spans five families, each typically oriented
toward a particular predictand.

- **Coupled dynamical seasonal systems** — NMME (Jacox et al. 2022), ECMWF SEAS5 (de Boisséson &
  Balmaseda 2024; Liu et al. 2025), ACCESS-S2 (Spillman et al. 2021; Smith & Spillman 2024),
  CMCC-SPS3.5 (McAdam et al. 2023), and NUIST-CFS1.0 (Zhang et al. 2023; Tang et al. 2024) are the
  principal operational approach at lead times of one to three months, primarily for MHW occurrence
  and probabilistic event forecasts. Their documented predictive skill is robust but strongly
  modulated by ENSO phase and concentrated outside the sub-Arctic.
- **Machine-learning and deep-learning methods** — long short-term memory networks, random forests,
  and convolutional architectures (Bonino et al. 2024; Giamalaki et al. 2022), U-Net models (Taylor
  & Feng 2022; Parasyris et al. 2025; Howard et al. 2026), and the MHWUNet model (Sun et al. 2024) —
  target SST anomalies and event occurrence and perform best at lead times of one day to two weeks;
  the available evidence is dominated by the Mediterranean and Indian Ocean.
- **Hybrid (machine-learning-corrected dynamical) approaches** — a neural correction applied to a
  subseasonal-to-seasonal (S2S) dynamical forecast (Sun et al. 2024), or a statistical SST model
  forced by a numerical-weather ensemble (Ross & Stock 2022) — are most advantageous at subseasonal
  lead times, at which purely data-driven models tend to lose spatial structure beyond approximately
  ten days.
- **Linear inverse models** (Wang et al. 2023) provide a parsimonious representation of MHW
  predictability and an interpretable connection to autoregressive state-space representations widely
  used in econometrics.
- **Statistical baselines** — climatology, persistence, damped persistence, and
  persistence-transformation preprocessing (Lee & Tzeng 2012) — together with analogue methods (Walsh
  et al. 2021, for air temperature in Alaska rather than SST) constitute the benchmark set against
  which the foregoing must be judged.

Illustrative results include dynamical SST anomaly correlations exceeding 0.8 in the tropics and far
northern Pacific at the initial month (Smith & Spillman 2024) and day-one root-mean-square errors of
0.11–0.19 °C across Mediterranean sub-basins for deep-learning models (Bonino et al. 2024).
Calibrated probabilistic verification — Brier skill scores, the symmetric extremal dependence index
(SEDI), relative operating characteristic (ROC) analysis, and reliability diagrams — is now standard
practice (Jacox et al. 2022; Liu et al. 2025; Smith & Spillman 2024).

## 3. Evidence on forecast skill

The nearest well-studied analogue to a Gulf-of-Alaska target is the northeast Pacific "Blob" region:
Tang et al. (2024) employ NUIST-CFS1.0 with ensemble-Kalman data assimilation; Liu et al. (2025)
apply SEAS5 across the northeast Pacific, including a Gulf-of-Alaska sub-region; and Taylor & Feng
(2022) reproduce the 2014–2015 and 2019 events with a deep-learning model. These results pertain to
the open northeast Pacific and, at most, the deeper Gulf of Alaska; none addresses the shallow,
seasonally ice-covered Bering, Chukchi, or Beaufort shelves, where bottom thermal conditions and sea
ice define the relevant predictand.

The Alaska shelf itself remains substantially unstudied. A structured review of a large high-latitude
literature corpus (approximately 2,255 records) identified abundant fisheries, ecology, sea-ice, and
impacts research but few studies reporting out-of-sample SST or MHW forecast skill relative to a
benchmark. The recent review of machine-learning methods for MHW prediction by Welandawe et al.
(2025) corroborates this independently: none of the studies it surveys falls within the sub-Arctic
Alaska, Bering, or Barents domain. The direct high-latitude forecasting evidence is limited to a
small number of studies, two of which are conference abstracts without quantitative verification
(Langehaug et al. 2024 for the Barents Sea; de Boisséson et al. 2022 for a northeast Pacific
precursor), together with Walsh et al. (2021), which addresses air temperature rather than SST.

## 4. Why high-latitude predictability might exist

In contrast to the paucity of methodological studies, the mechanisms underlying predictability in
this region are comparatively well characterized, through two partly competing accounts.

The first is **atmospheric teleconnection sequencing.** The 2013–2014 onset of the northeast Pacific
anomaly is attributed to anomalous atmospheric ridging and reduced ocean heat loss rather than to El
Niño (Bond et al. 2015). Di Lorenzo & Mantua (2016) attribute the multi-year persistence of the
2014–2015 event not to static ocean memory but to a sequence of atmospheric forcing: an NPGO-like
North Pacific pattern in 2014, linked through an extratropical–tropical teleconnection to a weak El
Niño and returning as a PDO-like pattern in 2015, with modulation of the Aleutian Low forming part of
the sequence. On this account, predictability resides in the atmosphere and in ENSO.

The second is **subsurface ocean memory and re-emergence.** Scannell et al. (2020) document subsurface
anomalies preceding the 2019 event from 2017, insulated from the surface by a shallow mixed layer; Xu
et al. (2026) relate ocean heat content to MHW persistence through seasonal re-emergence; and Amaya et
al. (2021) provide the mechanistic basis, whereby a shoaling mixed layer amplifies the SST response
per unit heat content (∂T/∂t ≈ Q/ρcₚh), accompanied by observed mixed-layer shoaling in the northeast
Pacific and a record minimum in 2019. These accounts are not fully reconciled, and the forecasting
evidence bears directly on the question: Tang et al. (2024) show that subsurface data assimilation is
required to capture a Blob-scale event and that surface nudging alone is insufficient, indicating that
the subsurface-memory channel should be represented in any operational system for the Gulf of Alaska.

The status of large-scale atmospheric precursors is more provisional. The Pacific Decadal Oscillation
is well established as a pattern of persistence and forcing, but the Arctic Oscillation has not been
established as a usable multi-year SST precursor: in the studies surveyed here it appears, at most, as
a candidate atmospheric covariate, and the Aleutian Low appears principally within the teleconnection
mechanism of Di Lorenzo & Mantua (2016) rather than as a predictor in its own right. Whether an
upstream Arctic Oscillation–Aleutian Low–PDO chain confers genuine multi-year predictive skill for
Gulf-of-Alaska SST, beyond the contributions of ENSO and of the subsurface ocean state, is an open
research question rather than a settled result.

## 5. Outstanding methodological challenges

Four issues separate the validated literature from a credible Alaska shelf forecast.

First, **the Alaska shelf seas are not one system.** The Gulf of Alaska is deeper and more
open-ocean-influenced, so that surface SST and MHW occurrence are the natural predictands; the
Bering, Chukchi, and Beaufort shelves are shallow, strongly seasonal, ice-affected, and
bottom-condition dependent, so that bottom thermal state and ice-conditioned occurrence matter more.
Treating these as one "high-latitude North Pacific" problem obscures the fact that the relevant
predictand, predictors, and benchmarks differ between them.

Second, **trend and forecastable interannual variability must be separated.** The distinction is sharp
and consequential: undetrended skill may partly reflect secular warming, whereas detrended skill
measures interannual predictive ability; both are useful, but they answer different questions. Zhang
et al. (2023) provide the clearest illustration — in their system trend-only skill extends to
approximately nine months, whereas the detrended interannual signal in the basin mean is significant
only to approximately three months. Treatment of the trend is nonetheless inconsistent across the
literature; some studies detrend, some report both treatments, and at least one (Smith & Spillman
2024) does not detrend and notes the resulting inflation of skill estimates. In a warming sub-Arctic
record, conflating the two overstates genuine forecast skill.

Third, **the treatment of sea ice is unresolved.** Masking of ice-affected grid cells is not addressed
in the assembled forecasting literature and is the least-developed requirement for any application to
the Bering, Chukchi, or Beaufort shelves.

Fourth, **robustness across regime shifts is unestablished** for sub-Arctic shelves; Welandawe et al.
(2025) identify rare-event and post-regime-shift performance as an unresolved, field-wide limitation.

## 6. Research-design implications

These limitations motivate a structured evaluation framework. A credible evaluation of MHW
forecasting for Alaska shelf seas should compare a common set of methods — climatology, persistence,
damped persistence, autoregressive and vector-autoregressive models, linear inverse models, dynamical
seasonal forecasts, and hybrid machine-learning corrections — over common hindcast periods, under
identical event definitions (a fixed MHW threshold and baseline climatology), and with probabilistic
verification (the Brier skill score and its decomposition, SEDI, ROC, and reliability diagrams). Trend
should be handled explicitly and reported both ways, distinguishing undetrended skill from the
detrended interannual component. The Gulf of Alaska and the Bering, Chukchi, and Beaufort shelves
should be evaluated as separate systems, with predictands appropriate to each — surface SST and MHW
occurrence for the former, bottom thermal state and ice-conditioned occurrence for the latter. Such a
design would convert the present descriptive literature into a benchmarked, regionally specific
evidence base. The central scientific problem is not the absence of forecasting methods; it is the
absence of validated, benchmarked, trend-aware, probabilistic forecast evaluation for Alaska shelf
systems.

---

## Basis and limitations

This is a focused synthesis rather than a systematic review, intended to characterize the current
state of the field and the evaluation problem it poses. It draws from a set of contemporary SST and
MHW forecasting studies and a peer-reviewed review of machine-learning methods, together with a
targeted reading of the North Pacific marine-heatwave mechanism literature. A small number of
supporting points (for example, Scannell et al. 2020; Xu et al. 2026; the two conference abstracts)
rest on abstract-level rather than full-text reading and are identified accordingly in the text. The
principal limitation warrants emphasis: there is at present essentially no direct evidence on SST or
MHW forecast methods for the Gulf-of-Alaska or Bering shelf, so every methodological recommendation
here is an argument from transfer, and transfer to a shallow, strongly seasonal, ice-affected, and
regime-shifting shelf remains an open question.

## References

- Amaya DJ, Alexander MA, Capotondi A, Deser C, Karnauskas KB, Miller AJ, Mantua NJ. 2021. Are
  long-term changes in mixed layer depth influencing North Pacific marine heatwaves? *Bulletin of the
  American Meteorological Society* 102(1):S59–S66. doi:10.1175/BAMS-D-20-0144.1
- Bond NA, Cronin MF, Freeland H, Mantua N. 2015. Causes and impacts of the 2014 warm anomaly in the
  NE Pacific. *Geophysical Research Letters* 42(9):3414–3420. doi:10.1002/2015GL063306
- Bonino G, Galimberti G, Masina S, McAdam R, Clementi E. 2024. Machine learning methods to predict
  sea surface temperature and marine heatwave occurrence: a case study of the Mediterranean Sea.
  *Ocean Science* 20:417–432. doi:10.5194/os-20-417-2024
- de Boisséson E, Balmaseda MA. 2024. Predictability of marine heatwaves: assessment based on the
  ECMWF seasonal forecast system. *Ocean Science* 20:265–278. doi:10.5194/os-20-265-2024
- de Boisséson E, Balmaseda M, Mayer M, Zuo H. 2022. Monitoring and predictions of marine heatwave
  events in the North East Pacific from ocean reanalyses and seasonal forecasts. *EGU General Assembly
  2022*, Vienna, EGU22-4079. doi:10.5194/egusphere-egu22-4079
- Di Lorenzo E, Mantua N. 2016. Multi-year persistence of the 2014/15 North Pacific marine heatwave.
  *Nature Climate Change* 6(11):1042–1047. doi:10.1038/nclimate3082
- Giamalaki K, Beaulieu C, Prochaska JX. 2022. Assessing predictability of marine heatwaves with random
  forests. *Geophysical Research Letters* 49:e2022GL099069. doi:10.1029/2022GL099069
- Howard L, Subramanian AC, Nadimpalli JR, Giglio D, Hoteit I. 2026. Skillful subseasonal Indian Ocean
  marine heatwave forecasts using a neural network. *Environmental Data Science* 5:e6.
  doi:10.1017/eds.2026.10033
- Jacox MG, Alexander MA, Amaya D, Becker E, Bograd SJ, Brodie S, Hazen EL, Pozo Buil M, Tommasi D.
  2022. Global seasonal forecasts of marine heatwaves. *Nature* 604:486–490.
  doi:10.1038/s41586-022-04573-9
- Langehaug HR, Sandø AB, Hordoir R, Counillon F, Chiu P-G, Raj R. 2024. Marine heatwaves: can we
  predict them in the Barents Sea? *EGU General Assembly 2024*, Vienna, EGU24-5667.
  doi:10.5194/egusphere-egu24-5667
- Lee Y-A, Tzeng R-Y. 2012. Persistence neutralization transformation: an effective way to improve
  short-lead forecast skill. *Journal of Geophysical Research* 117:D23109. doi:10.1029/2012JD018198
- Liu Z, Wang B, Shan H. 2025. Predictability assessment of marine heatwaves in the Northeast Pacific
  based on SEAS5. *Weather and Climate Extremes* 48:100773. doi:10.1016/j.wace.2025.100773
- McAdam R, Masina S, Gualdi S. 2023. Seasonal forecasting of subsurface marine heatwaves.
  *Communications Earth & Environment* 4:225. doi:10.1038/s43247-023-00892-5
- Parasyris A, Metheniti V, Kampanis N, Darmaraki S. 2025. Marine heatwaves in the Mediterranean Sea: a
  convolutional neural network study for extreme event prediction. *Ocean Science* 21:897–912.
  doi:10.5194/os-21-897-2025
- Ross AC, Stock CA. 2022. Probabilistic extreme SST and marine heatwave forecasts in Chesapeake Bay: a
  forecast model, skill assessment, and potential value. *Frontiers in Marine Science* 9:896961.
  doi:10.3389/fmars.2022.896961
- Scannell HA, Johnson GC, Thompson L, Lyman JM, Riser SC. 2020. Subsurface evolution and persistence of
  marine heatwaves in the Northeast Pacific. *Geophysical Research Letters* 47(23):e2020GL090548.
  doi:10.1029/2020GL090548
- Smith GA, Spillman CM. 2024. Global ocean surface and subsurface temperature forecast skill over
  subseasonal to seasonal timescales. *Journal of Southern Hemisphere Earth Systems Science* 74:ES23020.
  doi:10.1071/ES23020
- Spillman CM, Smith GA, Hobday AJ, Hartog JR. 2021. Onset and decline rates of marine heatwaves: global
  trends, seasonal forecasts and marine management. *Frontiers in Climate* 3:801217.
  doi:10.3389/fclim.2021.801217
- Sun D, Jing Z, Liu H. 2024. Deep learning improves sub-seasonal marine heatwave forecast.
  *Environmental Research Letters* 19:064035. doi:10.1088/1748-9326/ad4616
- Tang T, He J, Sun H, Luo J. 2024. Impact of ocean data assimilation on the seasonal forecast of the
  2014/15 marine heatwave in the Northeast Pacific Ocean. *Atmospheric and Oceanic Science Letters*
  18:100498. doi:10.1016/j.aosl.2024.100498
- Taylor J, Feng M. 2022. A deep learning model for forecasting global monthly mean sea surface
  temperature anomalies. *Frontiers in Climate* 4:932932. doi:10.3389/fclim.2022.932932
- Walsh JE, Brettschneider B, Kettle NP, Thoman RL. 2021. An analog method for seasonal forecasting in
  northern high latitudes. *Atmosphere and Climate Sciences* 11:469–485. doi:10.4236/acs.2021.113028
- Wang Y, Holbrook NJ, Kajtar JB. 2023. Predictability of marine heatwaves off Western Australia using a
  linear inverse model. *Journal of Climate* 36. doi:10.1175/JCLI-D-22-0692.1
- Welandawe S, Priyadarshana YHPP, Senanayake N, Silva ENS. 2025. Machine learning techniques for marine
  heatwave prediction: a comprehensive review. *Intelligent Marine Technology and Systems* 3:28.
  doi:10.1007/s44295-025-00076-1
- Xu T, et al. 2026. Persistent Northeast Pacific marine heatwaves are sensitive to the seasonality of
  tropical and North Pacific dynamics. *Communications Earth & Environment* (online first).
  doi:10.1038/s43247-026-03442-x
- Zhang T, Xu H, Ma J, Deng J. 2023. Predictability of Northwest Pacific marine heatwaves in summer
  based on NUIST-CFS1.0 hindcasts. *Weather and Climate Extremes* 42:100617.
  doi:10.1016/j.wace.2023.100617
