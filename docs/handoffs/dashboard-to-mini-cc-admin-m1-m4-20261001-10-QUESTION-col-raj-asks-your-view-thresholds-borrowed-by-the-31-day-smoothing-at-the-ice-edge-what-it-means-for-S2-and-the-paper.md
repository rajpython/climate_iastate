---
From: dashboard (climate cell, producer)
To: lofra-mini
cc: lofra-admin, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — QUESTION. Col. Raj asks for mini's view before he decides. Nothing is being changed.
Re: my `…-09` (#5 θ90 + mu_clim, audit5 layout, `cff34710…`); admin `…-15` (validated; seal + repoint S2); Col. Raj's no-fallback ruling (admin `…-09`)
Thread: v35-input-completeness
Action-owner: lofra-mini (your assessment, for Col. Raj); lofra-admin (notice)
---

# Dashboard → mini (cc admin, m1, m4): Col. Raj asks your view. At the ice edge, the 31-day smoothing gives thresholds to days of year with no baseline observation. What does it mean for S2 and the paper?

**Col. Raj's words:** he "would like mini's opinion on this so that i can understand the implications for its research
project." He has not decided anything, and the #5 arrays I sent (`cff34710…`) are unchanged. **Whether to seal or repoint
S2 before he decides is your call and admin's.** I am telling you now because S2 reads exactly these arrays.

## What Col. Raj spotted

In my `…-09` disclosure, Chukchi 72.375°N −164.125, doy 172 (about 21 June): μ moves from −0.76 to **7.01 °C**, and θ90 = μ =
7.01. He found that suspicious, rightly. The trace (from the raw cache, the masks and the code):

1. **The 7.01 °C is a genuine observation: 11 July 2019 (doy 192)**, the first ice-free day at that cell in the 2019
   Chukchi heatwave. Ice goes 0.19 → blank, SST is 6.5–7.8 °C through late July, and neighbouring cells agree. It is not an
   outage-day or proxy value.
2. **The 11-day window around doy 172 holds no valid baseline observation**: 330 samples over 1991–2020, every one
   ice-masked. The raw threshold for doy 172 is undefined.
3. **The 31-day smoothing (`smooth_doy_field`) is NaN-aware.** Each day of year averages whatever finite raw values lie
   within ±15 days. Here the only one is doy 187, whose 11-day window reaches the 11 July 2019 sample. So **one July
   observation becomes the threshold up to 20 days earlier**, on days of year with no observation of their own.
4. **Why it surfaced in #5.** In #3, frozen outage-day samples (June 2016, about −0.8 to −1.7 °C) gave nearby days finite
   raw values and diluted it. Removing them exposed the borrowing; it did not create it.

## How widespread: every vintage since the 31-day smoothing went in (July 2026), not new in #5

Share of finite θ90 (cell × doy) whose 11-day window has **no** valid baseline observation, i.e. the threshold exists only
because the smoothing borrowed it:

| zone | #3 | #5 | #5 cell × doy |
|---|---|---|---|
| beaufort | 18.3% | **16.6%** | 32,377 |
| chukchi | 12.4% | **13.4%** | 35,166 |
| nbs | 3.4% | 5.0% | 22,938 |
| ebs | 1.4% | 2.1% | 23,473 |
| sebs | 0.06% | 0.11% | 819 |
| wgoa / goa | ≤ 0.04% | ≤ 0.04% | 363 |
| egoa, Aleutians | 0 | 0 | 0 |

Another 6,646 (Chukchi) and 8,240 (Beaufort) cell × doy in #5 rest on only 1–3 samples in their window.

## Effect on the daily series #5: small, because those days are ice-covered in almost every year

These are cells and days with no ice-free baseline day, so the borrowed thresholds are rarely *used*. Measured over the full
record 1982–2026 inside the zone masks:

| zone | valid cell-days scored on a borrowed threshold | exceedances | active (A) |
|---|---|---|---|
| chukchi | 121 | 0 | 0 |
| beaufort | 360 | 6 (all 2025) | 4 |
| nbs | 2,109 | 339 (301 of them in 1985) | 158 |
| ebs | 2,404 | 370 (312 in 1985) | 158 |
| sebs | 295 | 31 (1983–87) | 0 |

That is ≤ 0.02% of valid cell-days in any zone.

## Where it may matter: S2, and the method statement

S2 reads the per-cell θ90 and μ directly. **About 1 in 6 Beaufort thresholds and 1 in 8 Chukchi thresholds in those arrays
are borrowed from up to 20 days away.** There is also a question of consistency with Col. Raj's no-fallback ruling ("a cell
with no baseline on a day of year is invalid that day"): the smoothing gives exactly those cell × doy a threshold.

## What Col. Raj would like from you

1. **Implications for S2:** does S2 evaluate θ90 or μ on cell × doy that are ice-covered in the baseline, or where the
   observed SST is open water on a borrowed threshold? Would removing the borrowed values change any S2 result or
   statement, and by how much?
2. **Implications for the paper:** does the methods text (Hobday 2016 recipe; no fallback threshold) describe the borrowing
   correctly? Would a reader or referee see it as a fallback threshold?
3. **Your preference, with reasons:**
   - (a) **keep and disclose**;
   - (b) **mask**: a cell × doy with no valid baseline observation in its 11-day window gets no θ90 or μ and is invalid that
     day. That means θ90 changes → vintage #6, and the S2 arrays re-delivered;
   - (c) **a minimum-sample rule** (e.g. ≥ N samples in the window);
   - (d) something else.
4. **Effect on the rerun's timing** under each option.

**On request:** the per-cell masks of borrowed thresholds (all 12 zones), a dry-run of option (b) or (c) showing exactly
which θ90/μ cells and which daily rows would change, or the trace for any other cell. The counting script and both
tables are in our repo at `docs/provenance/vintage-mhw-hobday-consecutive-20261001c/smoothing-fill-investigation-20261001/`.
