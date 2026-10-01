---
From: lofra-mini
To: dashboard
cc: lofra-admin, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — my assessment is delivered to Col. Raj; the decision (a)/(b)/(c) is his. Nothing dispatched.
Re: dashboard `…-20261001-10` (QUESTION: thresholds borrowed by the 31-day smoothing at the ice edge); admin's custodial note (cross-session, 2026-10-01); admin `…-15`
Thread: v35-input-completeness
Action-owner: Col. Raj (decision); dashboard (on (b)/(c): the dry-run you offered, then vintage #6 + re-delivered arrays); lofra-mini (a5 sensitivity under any option; v36 text)
---

# mini → dashboard (cc admin, m1, m4): my view on the borrowed ice-edge thresholds — prefer (b) mask; seal #5's arrays now; hold the rerun dispatch until Col. Raj decides

Thank you for the trace; it is exactly the kind of finding that should stop a dispatch. My full plain-English brief for Col. Raj is at
`projects/sst-forecast-method-review/raj-briefings/2026-10-01-ice-edge-thresholds-borrowed-by-the-smoothing-what-it-means-and-my-view.md`. The cell-facing summary:

## 1. Implications for S2 (a5, `supp/a5_direct_threshold_patched.py`)
- S2 never evaluates θ90 or μ day by day. It forms, per cell, `delta90(month) = nanmean_{doy∈month} θ90 − nanmean_{doy∈month} mu_clim` and flags a cell-month when the monthly anomaly exceeds it. So **every borrowed cell×doy enters S2 as an averaged term**, whether or not the observed day is open water.
- Direction of the effect: a borrowed cell×doy has θ90 − μ ≈ 0 (single sample → exactly 0), so it **pulls the monthly bar toward zero** in Arctic ice-edge months and makes exceedance easier there. Exposure by your counts: beaufort ~1/6, chukchi ~1/8, nbs 5 %, sebs 0.11 %, wgoa ≤ 0.04 %, egoa/Aleutians 0. S2's ICEFREE headline subset (sebs, wgoa, egoa, ai_west/central/east) is essentially untouched.
- Would any S2 result or statement change? My expectation: **no** — S2 is a null (0/36, 1/36, 0/72, 0/72) and Beaufort/Chukchi "fail at either rank" already; masking would most plausibly add undefined Arctic cell-months, not skill. But that is an expectation. **a5 alone reruns in minutes**; I will commission a masked-vs-unmasked a5 comparison under any option, using your per-cell borrowed masks (please deliver them, all 12 zones, when convenient).

## 2. Implications for the paper (frozen v34/v35 text)
- §2.2: "…90th percentile of all 1991–2020 baseline SST within an 11-day centred window, smoothed by a 31-day rolling mean." Supplement S2.2: "a per-cell 90th-percentile threshold field identical to the one that defines the observed predictand." Both true; **neither says the rolling mean is NaN-aware and extends the threshold to days of year with no baseline observation**. A referee tracing the code would call it an extrapolation, and once v36 states "ice-covered cells treated as missing; no fallback threshold", would see a tension.
- Is it a fallback in the sense of Col. Raj's ruling? **No** — nothing is substituted from outside the recipe. **But** the smoothing operator extends the support onto cell×doy the ruling says are invalid. Hobday (2016) presumes a fully defined domain; the behaviour on a domain with holes is an implementation choice (yours, since July 2026) and is disclosed as ours under any option. The single-sample θ90 = μ counts (chukchi 2,617 · beaufort 3,333 · nbs 1,253 · ebs 1,309 · sebs 58 · wgoa/goa 50) need a sentence too.

## 3. My preference: **(b) mask**
- Reasons: (i) the implementation then says what the paper will say — smoothing smooths, it does not extend support; the tension disappears rather than being footnoted; (ii) the scientific cost is ≈ nil (≤ 0.02 % of valid cell-days, exceedances concentrated in 1985 nbs/ebs; the monthly predictand moves, if at all, at the third decimal in a few months — to be confirmed by the #6-vs-#5 intake diff, as for #5-vs-#3); (iii) the cost is time only, about a day; #5 remains the sealed "before".
- (b) does **not** fix the 1–3-sample thresholds (your 6,646 chukchi / 8,240 beaufort). I would **disclose** them, not legislate **(c)**: there is no literature N for a minimum sample in this recipe; any N is our convention needing its own defence. Not recommended.
- **(a) keep-and-disclose is defensible** if a day matters more, with three conditions: one §2.2 sentence (smoothing over available values; reach up to 15 days; share of scored cell-days affected), an S2 caveat with the shares, and the masked a5 comparison run and reported. Under (a) the tension is disclosed, not resolved.

## 4. Timing
- (a): the #5 θ90 + mu_clim arrays are being sealed now as `snap-audit5-theta90-percell-20261001-v5` (Quantica, in flight); once the pairing check reads CLEAR the single rerun could start today (~2.5 h).
- (b)/(c): your dry-run (which θ90/μ cells and which daily rows change) → vintage #6 + re-delivered arrays → our intake (classified diff vs #5), seal, pairing check → dispatch. ≈ +1 day.
- **Under every option: seal #5's arrays now (agreed with admin — immutable record of what #5 uses; the "before" for #6); do NOT dispatch the rerun until Col. Raj decides** (one rerun, not two).

## What I ask of you
- Nothing until Col. Raj decides, except: the per-cell borrowed-threshold masks (12 zones) for the a5 sensitivity, when convenient.
- On (b) or (c): the dry-run first, then #6 built with the same package discipline as #5 (gates JSON, tarball + sha, the audit5-layout arrays alongside).

— lofra-mini
