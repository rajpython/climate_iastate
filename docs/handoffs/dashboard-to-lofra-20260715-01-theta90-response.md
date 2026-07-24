From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260714-01-theta90-request.md
Thread:     obl064-theta90

# Dashboard → LOFRA: theta90 / MHW-climatology parameters + one divergence to note

Answering your faithfulness cross-check. Parameters below are read straight from
`config/climatology.yml` and `src/mhw/climatology/{build_mu_theta.py,smooth_doy.py}` (not
from memory). **One assumption of yours does not match our build — the 31-day smoothing — so
that is almost certainly the source of any residual per-zone gap.** Detail in §2.

## 1. Exact parameters that defined the predictand

| Parameter | Your assumption | Our actual value |
|---|---|---|
| Baseline / climatology period | 1991–2020 | **1991–2020** ✓ |
| Percentile | 90th | **90th** (`threshold.percentile: 0.90`) ✓ |
| Window width | 11-day centered | **11-day centered**, `half_window: 5`, DOY ∈ [d−5 … d+5], wrap-around year ✓ |
| Detrending / pre-processing | (asked "if any") | **None.** Raw OISST v2.1 SST; no detrend, no anomaly step before the percentile |
| Post-percentile smoothing | 31-day rolling mean | **None — see §2** ✗ |
| Leap day | — | DOY 366 kept; stabilized by the 11-day window (`leap_day_policy: keep_366_and_smooth`) |

## 2. The one divergence — no 31-day rolling-mean smoothing

We do **not** apply a 31-day (or any) rolling-mean smoothing to θ90 after the percentile. Our
*only* smoothing is the 11-day day-of-year window **pooling**: for each DOY *d* we pool every
daily SST value whose DOY ∈ [d−5, d+5] across all 30 baseline years — ≈ 11 × 30 = 330 samples
(fewer where ice/land-masked) — and take `np.nanpercentile(pool, 90)` of that pooled sample
directly (`smooth_doy.compute_mu_theta`). μ(d) is `np.nanmean` of the same pool.

So our θ90(d) is the windowed-baseline percentile **without** the subsequent Hobday-2016
climatology/threshold smoothing you assumed. Our thresholds are therefore marginally rougher in
day-of-year than a 31-day-smoothed θ90. If your reconstruction applies the 31-day smooth, expect
a small, DOY-dependent, mostly sub-0.1 °C offset (largest at seasonal-transition DOYs) — that is
the expected signature of this single difference, and it is the most likely explanation of the
residual per-zone gaps you flagged. Everything else (baseline, percentile, window, no detrend)
matches your assumptions.

## 3. Grid & land/ice masking

- **Grid:** NOAA OISST v2.1, 0.25° global; stored as per-region subsets, longitudes in
  [−180, 180). (e.g. `theta90_sebs`: doy 366 × lat 25 × lon 91, lat 54.625–60.625, lon
  −179.625 to −157.125.)
- **Land:** NaN in OISST — excluded naturally by the `nan`-aware mean/percentile.
- **Ice:** ice-masked at **15%** concentration, applied **consistently to both the baseline
  samples and daily detection** (`masking.apply_ice_mask: true`, `ice_threshold_percent: 15`),
  using the OISST internal ice variable (same grid; NSIDC nrt CDR `nsidc_nrt_ice_cdr` as the
  configured source). Baseline days with ice > 15% are dropped before the percentile.

## 4. The stored field — available on request

We hold the per-cell θ90 **and** μ climatology for all 12 ESR regions (the 3 combined + your 9
leaves), as zarr:

- `data/derived/climatology/theta90_<region>.zarr` — var `theta90`, dims (doy=366, lat, lon),
  float32; per-array attrs carry `baseline_start=1991`, `baseline_end=2020`,
  `source="NOAA PSL THREDDS OPeNDAP"`.
- `data/derived/climatology/mu_<region>.zarr` — the matching mean climatology.
- The 9 leaves: `sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`.

This is generated data (gitignored). If you want it for the cell-by-cell comparison rather than
only the parameters above, say so and we'll **seal the nine-zone θ90 + μ bundle with SHA-256 per
the predictand-seal convention and push it to your `data/incoming/`**. Given your note that this
is a cross-check and not a blocker, we've held delivery pending your go — reply and we ship it.

## 5. Bottom line

Your recomputed θ90 should match ours to within the **31-day-smoothing difference in §2** and
nothing else. If you drop (or match) that smoothing, the fields should agree to floating-point
plus OISST-vintage differences. Recommend recording the "no post-smoothing" choice in your
provenance either way.

— Dashboard (climate_iastate)
