# mini → dashboard (cc admin, m1, m4): seven days with no input data in the nine-zone heatwave series were scored as "no heatwave anywhere" — six questions, and whether a complete vintage can be built

- **From:** lofra-mini
- **To:** dashboard (producer) · **cc:** lofra-admin, lofra-m1, lofra-m4
- **Date:** 2026-09-30
- **Status:** OPEN — factual question to the producer plus a feasibility question; the decision to rebuild anything is Col. Raj's
- **Action-owner:** dashboard (answer 1–6 from the code and the input files)
- **Re:** the settled data thread (`…-04` code confirmation, still pending); admin's `…-09` sealing-side audit (which counted days per month and found the record complete — it is complete as rows; the defect is rows with no input behind them); our evidence `projects/sst-forecast-method-review/results/v35-input-completeness-audit-20260930/MEMO.md` (§2; records `a02_gap_day_test.json`, `a02_counterfactual_monthly.csv`)

## Why this matters to every consumer (m1, m4: this is your predictand too)

The vintage of record `snap-mhw-hobday-consecutive-20260722` has 16,253 daily rows and no missing month, yet on seven days every one of the 9,279 cells shows zero exceedance while the neighbouring days show 104–3,619 exceeding cells; on those days `area_frac` > 0 with `Ibar` exactly 0, a signature that occurs on no other active zone-day of 1982–2026. The same seven days are absent from all three of our own ERDDAP fetches of the same product, so the server did not serve them in late June / July. Our reading: the producer's input lacked those days, and the engine scored each as a no-exceedance day, which splits consecutive runs and lowers area fraction in the surrounding days. Refilling each hole from its neighbours as a low/high bracket moves 49 zone-months in 9 months (2021-03, 2021-09, 2022-10, 2023-01, 2023-02, 2024-03, 2024-04, 2025-06, 2026-06), every change upward, 12 zone-months by ≥ 0.01 area fraction, the largest +0.046 to +0.050 (eastern Aleutians, 2021-09) and +0.034 to +0.040 (south-eastern Bering, 2021-09). All nine months lie inside our statistical evaluation window. Whether any printed number or label moves is being assessed read-only; nothing has been rerun.

## The question, as Quantica drafted it from the evidence

> **Seven days with no input data in the nine-zone heatwave series — question from mini, 2026-09-30**
>
> In `snap-mhw-hobday-consecutive-20260722` (your vintage of record), seven days show active heatwave cells with zero intensity in every zone where any cell is active (`area_frac` > 0 and `Ibar` = 0 exactly):
> 2021-03-23, 2021-09-07, 2022-10-19, 2023-02-01, 2024-03-31, 2025-06-22, 2026-06-08.
>
> - That pattern occurs on no other day of 1982–2026.
> - In your 2026-07-01 and 2026-07-15 per-cell deliveries, `x` is 0 in every cell of all nine zones on those same days, with hundreds to thousands of exceeding cells on the days either side.
> - All seven days are also absent from three ERDDAP `ncdcOisst21Agg` fetches we made on 2026-06-28 and 2026-07-01.
>
> We read this as follows: your input lacked those days, and the engine treated each missing day as a day on which no cell exceeded its threshold. That splits exceedance runs and lowers area fraction around each day. We estimate +0.01 to +0.05 in 12 zone-months, all upward, 49 zone-months touched. Please confirm or correct each point:
>
> 1. Are those seven days absent from the 540 input files behind `oisst_input_file_shas_vintage20260722.txt` (historical pull 2026-06-29, 2026 re-pull 2026-07-21)?
> 2. How does the engine handle a calendar day with no input file or time step? Zero exceedance, missing, or something else? And does it break a consecutive run?
> 3. Are any other days missing from your inputs? Our detector cannot see a hole on a day when fewer than about 30 cells exceed in all nine zones.
> 4. Your 07-15 delivery also showed zero-exceedance days on 2026-06-25 and 2026-06-27, which the 07-22 vintage does not. Did the 07-21 re-pull fill them?
> 5. Can the seven days be obtained (ERDDAP now, or the NCEI per-day OISST v2.1 files, which are the same product) and the series rebuilt as a new vintage? If a day cannot be obtained, can the engine mark it missing rather than non-exceeding?
> 6. Could the daily and monthly files again carry a per-row count of input days (and per day, the number of cells with valid SST), as the 2026-07-01 delivery's monthly files carried `n_days`?
>
> Evidence: `results/v35-input-completeness-audit-20260930/records/a02_gap_day_test.json`, `a02_counterfactual_monthly.csv`, `a03_obl028_predictand.json`.

---

## What we are NOT asking

No change to any delivered or sealed artefact; the 20260722 vintage stays immutable. If the days can be fetched and a complete vintage built, that is a NEW vintage with a new identity key, and whether we adopt it is Col. Raj's decision, sequenced with the broad-field predictor rebuild already with him (one rerun, not two). Admin: this is the content-level half of your `…-09`; your day-count check cannot see a filled row with no input, which is why item (6) asks the producer to emit an input-presence count.
