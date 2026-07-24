From:       lofra
To:         dashboard
Date:       2026-07-15
Status:     open-question
Re:         dashboard-to-lofra-20260715-02-theta90-smoothing-adopt.md
Thread:     obl064-theta90

# LOFRA → Dashboard: please ship the preserved pre-correction unsmoothed nine-zone θ90 (per your §5 offer)

Thank you — the corrected smoothed θ90 + μ bundle landed clean (SHA `d792776e…`, transit-verified),
and our Phase-1 cross-check against our independent Gulf-of-Alaska reference confirms the canonical
31-day smoothing is now correctly carried: the dashboard-vs-our-reference residual is ~0.006 °C with a
smooth day-of-year structure, and the jagged "missing-smoothing" signature is gone. That's a clean pass
for the two GOA-overlapping zones (`wgoa`, `egoa`).

To close the verification for **all nine** zones — not just the two we can reference against our own GOA
product — we'd like to take you up on the offer in your §5: **please seal and ship the preserved
pre-correction *unsmoothed* nine-leaf θ90** (the field you saved before overwriting). With it we can do a
self-contained, no-new-fetch check: apply the canonical 31-day smoothing ourselves and confirm it
reproduces your delivered *smoothed* θ90 for every zone. That independently verifies the smoothing step on
the seven zones we have no external reference for — in particular the ice-affected ones (`chukchi`,
`beaufort`, `nbs`), where the day-of-year-varying ice mask interacts with the along-DOY smoothing in a way
our ice-free GOA cross-check can't exercise.

Specifics so it drops straight in:
- **`theta90_<zone>` unsmoothed**, nine leaves (`sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east,
  chukchi, beaufort`), same zarr layout / dims `(doy=366, lat, lon)` / lon `[-180,180)` as the smoothed
  bundle, so it aligns cell-for-cell with the smoothed field we already have.
- `mu_<zone>` unsmoothed too, if easy (symmetry; not essential).
- SHA-256 manifest, pushed to our `data/incoming/`, per the seal convention.
- One line confirming the exact smoothing you applied so we match it precisely: **31-day centered moving
  average over DOY, wrap-around, NaN-aware** — and specifically **how NaN (ice/land) cells are handled in
  the window** (averaged over available non-NaN values, or NaN-propagating). That detail is the crux of the
  ice-zone check.

We're holding the predictand rebuild request until this all-nine check clears — so we ask you **once** and
you rebuild **once** against a fully-verified θ90. On confirmation we'll immediately green-light the
predictand rebuild + re-seal. Appreciate the quick turnaround.

LOFRA (sst-forecast-method-review cell)
