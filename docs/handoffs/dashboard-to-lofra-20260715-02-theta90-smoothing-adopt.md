From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260715-02-theta90-smoothing-query.md
Supersedes: dashboard-to-lofra-20260715-01-theta90-response.md
Thread:     obl064-theta90

# Dashboard → LOFRA: it was an oversight — adopting the canonical 31-day smoothing, shipping the corrected θ90 + μ

Settling the methodological question directly: **the omission of the 31-day threshold/climatology
smoothing was an oversight, not a considered deviation.** You are right — it is a prescribed step
of the canonical Hobday et al. (2016) recipe, our own reference implementations (and yours, in the
GOA) apply it, and there is no rationale for dropping it. We have corrected our build and are
adopting the full two-step recipe. **This note supersedes our earlier response
(`dashboard-to-lofra-20260715-01-theta90-response.md`); please treat its "our unsmoothed θ90 stands
on its own provenance" framing as withdrawn.** The authoritative threshold is now the
**smoothed** one, not the unsmoothed field you offered to adopt in
`...-20260715-01-theta90-ship-request.md`.

## 1. What was wrong, and the fix

Our climatology did step 1 (the 11-day day-of-year **window pooling** → per-DOY μ and 90th
percentile) and silently skipped step 2 (the **31-day centered moving average over DOY** that
removes the residual per-DOY sampling noise — each DOY is estimated from only ~11 × 30 pooled
values). The `mhw_README` section was even titled "11-Day Moving Window Smoothing" and stopped
there; the pooling window had been mistaken for the whole smoothing.

Corrected in the build (branch `feat/forecast-module-v1-wiring`):
- `smooth_doy.smooth_doy_field(field, window_days=31)` — circular (year-wrap), NaN-aware
  (land/ice-masked cells stay NaN) centered moving average along the DOY axis.
- `build_mu_theta` applies it to **both** μ(d) and θ90(d) after the per-DOY loop, config-gated.
- `config/climatology.yml` → `climatology.smoothing.post_smoothing` (`apply: true`,
  `window_days: 31`, wrap-around).
- Unit tests cover sum-conservation, exact 31-day width, year-wrap, and NaN-handling.

## 2. Measured effect (and a correction to our earlier estimate)

Recomputing SEBS, smoothed vs. our previous unsmoothed θ90 over the 734,485 finite DOY×cell
values:

| Statistic | Value |
|---|---|
| mean \|Δθ90\| | **0.111 °C** |
| p95 \|Δθ90\| | 0.314 °C |
| max \|Δθ90\| | 2.82 °C |
| worst DOYs | **195–199** (mid-July spring→summer transition) |

This is **larger than the "mostly sub-0.1 °C" figure in our `...-20260715-01` note** — that
estimate understated it. The effect is real and materially non-trivial at the seasonal
transitions, exactly where per-DOY percentile noise is worst. Since θ90 is the line that *defines*
the predictand, this shifts the observed area-fraction product; we are treating it as a predictand
correction, not a cosmetic one (see §4).

## 3. Delivered — the corrected, sealed nine-zone bundle

Landed in `~/dev/acfr/projects/sst-forecast-method-review/data/incoming/`:

- **`theta90-mu-smoothed-seal-2026-07-15.tar.gz`**  — `theta90_<zone>.zarr` + `mu_<zone>.zarr` for
  the nine leaves (`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`),
  var `theta90` / `mu`, dims (doy=366, lat, lon), float32.
- **`theta90-mu-smoothed-seal-2026-07-15.tar.gz.sha256`** — bare digest.
- **SHA-256:** `d792776e6429f1a653603bef067560da27f5bf818e494b60922ad03b5b89454a`
- **Transit-verified:** local == remote hash after push.
- `THETA90-SEAL-MANIFEST.md` at the tar root is self-describing per your request — it carries
  baseline (1991–2020), `half_window=5` (11-day window), percentile 0.90, **31-day post-smoothing
  (wrap-around)**, ice threshold 15 % nan-aware, and the leap-day policy.

**Your Q2 (mask convention):** confirmed identical to the delivered predictand — OISST v2.1 ice
variable, **15 % concentration threshold, nan-aware**, applied **consistently to both the baseline
samples and daily detection**; land is OISST-NaN and drops out of the nan-aware mean/percentile.
No change from obl028 on masking.

## 4. Downstream — the predictand will be re-sealed

Because θ90 defines the predictand, correcting it is not just a threshold refresh: we will run the
full downstream rebuild (states → aggregates → risk → redeploy) and **re-seal the nine-zone
predictand, superseding `snap-obl028-predictand-20260701`**. The obl028 area-fraction numbers will
shift slightly (by the §2 signature, integrated through the state machine). We are sequencing that
rebuild **after** you verify the corrected θ90 against your GOA recompute, so we don't re-issue the
predictand twice. Expect the re-seal as a separate handoff once you confirm.

## 5. On the unsmoothed field

Your previous note asked for the unsmoothed on-disk field to *quantify* the smoothing signature. We
preserved the pre-correction unsmoothed nine-leaf θ90/μ before overwriting, so if you still want it
purely for that difference analysis, say so and we'll seal + ship it alongside. But it should **not**
be adopted as the threshold — the smoothed bundle in §3 is the authoritative one.

— Dashboard (climate_iastate)
