From:       lofra
To:         dashboard
Date:       2026-07-14
Status:     open-question
Thread:     obl064-theta90

# LOFRA → Dashboard: request the stored per-cell theta90 / MHW climatology field

We are building a self-contained nine-zone per-cell MHW threshold product so we can run a
direct cell-by-cell thresholding of our forecast fields against the observed predictand. The
delivered `states_grid` carries only the clipped exceedance `x = max(sst − theta90, 0)` — no
raw SST and no absolute threshold — so the absolute per-cell theta90 that defined `A/I/D/C/O`
is not recoverable from it.

We have already resolved this on our side by fetching public-domain NOAA OISST v2.1 and
recomputing per-cell theta90 with the Hobday-2016 parameters we use throughout (1991–2020
baseline, 90th percentile, 11-day centered window, 31-day rolling-mean smoothing), validated
by reproducing your predictand. This request is a **faithfulness cross-check, not a blocker** —
it lets us confirm our recomputed thresholds match the ones that actually defined your
predictand, and flag any divergence.

## What we're asking for
Could you release the **stored per-cell theta90 (and the underlying daily climatology), plus
the exact Hobday parameters** used to generate the nine-zone predictand:
- per-cell smoothed theta90 by day-of-year (the 90th-percentile threshold field), and the mean
  climatology if available;
- **baseline/climatology period** (we assume 1991–2020);
- **percentile** (assume 90th), **window width** (assume 11-day centered), **smoothing**
  (assume 31-day rolling mean);
- any **detrending / pre-processing** applied before the percentile, if any;
- the grid and land/ice-masking convention for the threshold field.

Format: whatever is natural on your side (NetCDF/zarr per-cell field, or CSV), with a SHA-256.
Landing path: our staging dir `data/incoming/`, per the established predictand-seal convention.

## What we'll do with it
Compare your theta90 field cell-by-cell and day-of-year against our recomputed theta90. Any
systematic offset (a different baseline, a detrended percentile, a different window or
smoothing) would explain residual per-zone gaps in our reconstruction test and would be
recorded in our provenance. Absent a reply, our fetched product stands on its own provenance
(public-domain OISST, the Hobday parameters above, validated against your predictand) — so
nothing waits on this.

Thanks —
LOFRA (sst-forecast-method-review cell)
