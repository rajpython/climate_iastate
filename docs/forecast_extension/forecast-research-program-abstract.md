# Background Abstract — A Forecasting Research Program for Marine Heatwaves in Sub-Arctic Alaskan Shelf Seas

*Seed background for the research cell. Summarises the project context and the
forecasting problem to be solved; deliberately prescribes no parameters — the
research cell designs the program.*

---

Marine heatwaves (MHWs) are increasingly consequential for high-latitude fisheries,
yet operational forecasting for the shallow, seasonally ice-covered shelves of Alaska
remains underdeveloped. We operate a near-real-time MHW monitoring platform built on
NOAA OISST v2.1 and the Hobday et al. (2016) hierarchical definition — day-of-year
climatology and 90th-percentile threshold, ice-masked — across five regions: the Gulf
of Alaska, the eastern and northern Bering, the Chukchi, and the Beaufort seas.
Motivated by fisheries decision-support needs — annual ecosystem report cards and
management-council briefings for stocks such as snow crab — we seek to extend
monitoring into short-to-medium-lead (days to ~3 months) probabilistic MHW
forecasting.

The central problem is method selection. A spectrum of approaches has been applied to
SST and MHW prediction — persistence and damped persistence; autoregressive models
(AR, ARMA); regression on lagged climate indices (ENSO, PDO, AO); linear inverse
models; analog methods; machine learning; and dynamical or hybrid systems — but their
skill has been established largely in open-ocean, temperate, or low-latitude settings.
Their transferability to ice-affected sub-Arctic shelves, which exhibit strong
seasonal heteroskedasticity, a secular warming trend, ice-edge non-Gaussianity, and
recent regime shifts (the 2014–2016 Blob, the 2018–2019 Bering events, 2023–2024), is
unknown.

This program will identify the appropriate forecast method for these regions: first
through a systematic synthesis of the literature — attending to each method's lag
structure, estimation/training window, out-of-sample validation design, and documented
regional strengths and weaknesses — then through empirical evaluation against
climatology and persistence baselines using leakage-free, calibration-aware,
field-significance-aware verification. A binding principle governs deployment: no
forecast reaches the public dashboard until it is shown, to publication standard, to be
scientifically and econometrically defensible for these specific waters.
