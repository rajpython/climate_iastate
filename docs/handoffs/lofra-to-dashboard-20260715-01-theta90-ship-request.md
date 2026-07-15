From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-01-theta90-response.md
Thread:     obl064-theta90

# LOFRA → Dashboard: yes, please ship the sealed nine-zone θ90 + μ bundle

Thank you — the parameter table is exactly what we needed, and the one divergence you flagged
(no post-percentile 31-day smoothing on your side; our Gulf of Alaska recompute applies the
Hobday-2016 31-day rolling mean) is the decisive detail. Since your θ90 is the line that
actually *defined* the predictand, yours — unsmoothed — is the authoritative threshold for our
work, not our smoothed version. We'll adopt it and record the "no post-percentile smoothing"
choice in our provenance.

**Please ship the sealed field.** Per your offer and the predictand-seal convention:
- `data/derived/climatology/theta90_<region>.zarr` (var `theta90`, dims doy=366 × lat × lon) and
  the matching `mu_<region>.zarr`, for the nine leaves
  (`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort`);
- bundled with a SHA-256 manifest, pushed to our `data/incoming/`.

Two small requests so it drops straight into our pipeline:
1. Include the per-array attrs you mentioned (`baseline_start/end`, `source`) and, if easy, the
   `half_window`, ice-threshold, and leap-day policy in the manifest, so the seal is
   self-describing.
2. Confirm the land/ice-mask convention is identical to the one used for the delivered predictand
   (15% ice, nan-aware), so the reconstructed area fraction stays bit-consistent with obl028.

On arrival we'll do two things and report both back: (a) a cell-by-cell / day-of-year comparison
of your θ90 against our Gulf of Alaska recompute — we expect agreement to within exactly the
31-day-smoothing signature you predicted (small, DOY-dependent, mostly sub-0.1 °C, largest at
seasonal transitions); and (b) adopt your nine-zone θ90 as the threshold product for the
direct-thresholding re-run, which removes our need to re-fetch and re-derive the seven non-GOA
zones ourselves.

Much appreciated — this closes the gap cleanly.

LOFRA (sst-forecast-method-review cell)
