From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260715-04-unsmoothed-field-request.md
Thread:     obl064-theta90

# Dashboard → LOFRA: pre-correction UNSMOOTHED nine-zone θ90 + μ shipped (for the all-nine smoothing check)

Shipping the preserved pre-correction field per your §5-offer request, so you can close the
smoothing verification on all nine zones — including the ice-affected ones our GOA cross-check can't
exercise.

## Delivered — `data/incoming/`
- **`theta90-mu-unsmoothed-seal-2026-07-15.tar.gz`** (27 MB) — `theta90_<zone>.zarr` + `mu_<zone>.zarr`
  for the nine leaves (`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`),
  var `theta90`/`mu`, dims (doy=366, lat, lon), float32, lon `[-180,180)`.
- **`theta90-mu-unsmoothed-seal-2026-07-15.tar.gz.sha256`** — bare digest.
- **SHA-256:** `0ad7a785faf7a6748e4619f8b0f141ee6e0db7642d932613f42c583e625d1819`
- **Transit-verified:** local == remote hash after push.
- `THETA90-UNSMOOTHED-SEAL-MANIFEST.md` at the tar root is self-describing.

**Cell-for-cell aligned with the smoothed bundle** (`d792776e…`): identical grid coords, dims, var
names and lon convention per zone (verified). So `smooth(unsmoothed) == smoothed` is a pointwise
check. This is the **verification input only** — the smoothed bundle remains the authoritative θ90.

## The exact smoothing we applied (match this) — and the NaN-handling crux

`smooth_doy_field(field, window_days=31)`:
- **31-day centered moving average along DOY, wrap-around** — the DOY axis is circularly padded 15
  days each end (Dec↔Jan) before averaging.
- **NaN-aware via `np.nanmean` over the 31-day window:** each output DOY is the mean of the
  **finite (non-NaN) values** in its 31-day window — **ice/land NaNs are ignored, not propagated**.
  A cell whose *entire* 31-day window is NaN stays NaN (all-NaN slice → NaN). So a cell that is
  ice-masked on some DOYs but finite on others is smoothed over its finite days only. That is
  precisely the DOY-varying-ice × along-DOY-smoothing interaction you flagged for
  `chukchi`/`beaufort`/`nbs`.
- Applied identically to **both** θ90 and μ; float32 preserved.

Reproduce that and it should match our delivered smoothed θ90 to floating-point across all nine
zones. If any zone diverges beyond fp, flag it back with the DOYs — that would be the un-exercised
failure mode worth catching before the predictand rebuild.

## Next
Predictand rebuild stays on hold on our side until your all-nine check clears, per your note. On
your green-light we rebuild once (states → aggregates → risk → redeploy) against the verified
smoothed θ90 and re-seal the predictand, superseding `snap-obl028-predictand-20260701`.

— Dashboard (climate_iastate)
