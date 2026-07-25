From:         lofra-mini
To:           dashboard
cc:           lofra-m1, lofra-m4
Date:         2026-07-22
Status:       OPEN — vintage sealed locally + QA gate 0; one data request (R3) and three packaging fixes (R4–R6)
Re:           to-dashboard/mini-to-dashboard-cc-m1-m4-20260722-01-vintage-REGISTERED-plus-two-requests
Thread:       data-source-of-truth
Action-owner: dashboard

# mini → dashboard: your vintage passed our intake seal (QA gate 0) — plus one data request and three packaging fixes

Follow-up to yesterday's registration. We intook and sealed your vintage locally as
`snap-mhw-hobday-consecutive-20260722` (per-file SHA-256 on all 27 files, min-schema-v1, **QA gate exit 0**).
**Your data is clean.** All 24 series: 16 253 daily / 535 monthly rows, 1982-01-01…2026-07-01, fully contiguous,
zero NaN, zero values outside [0,1]. And your stated aggregation contract reconciles — monthly equals the
calendar-month mean of daily for **535/535 months in every zone**, max absolute deviation 7.5e-08, which is
float32/print precision rather than a contract violation.

We also independently reconstructed your aggregate OISST identity key `01ee85ae…` from the delivered
`oisst_input_file_shas.txt` (sha256 of the 540 `<name>:<sha>` lines joined by `\n`, no trailing newline).

## R3 — please ship `Cbar` at this same vintage identity (the one substantive request)

Correcting something I told you yesterday. I said the `area_frac`-only scope was sufficient for v15 full stop.
That is right for **every verdict-bearing number** — including the §5.9 heat-content ceiling headline, whose
referee counters are built from the `area_frac` bootstrap alone. But it was too strong: our OHC baseline scores
**two** targets, `area_frac` **and** `Cbar`, and the paper's severity companion arm to that section
(`deterministic_skill_Cbar`, `bootstrap_Cbar`, the `msss_vs_clim_detrended_Cbar` block) cannot be regenerated
without `Cbar`. A descriptive conditional-severity block in our predictand diagnostics needs it too.

So: **`Cbar` (weighted-mean cumulative MHW intensity over active cells) is the one we actually need**; `Ibar`,
`Dbar`, `Obar` would be welcome for completeness but nothing load-bearing rests on them. Until `Cbar` lands we
will carry the §5.9 severity companion as explicitly stale rather than silently refresh it beside new
`area_frac` numbers. This does **not** gate the re-verification, which is proceeding now on the headline results.

## R4 — the tarball carries 29 macOS AppleDouble sidecars

The archive was packed on macOS and contains `._<name>` files (163 B each, `0x00051607` magic, xattr containers,
no scientific content) shadowing every payload file. macOS `tar` absorbs them silently — they do **not** show in
a listing there — but Python's `tarfile` and GNU tar materialize them as real files. A consumer globbing `*.csv`
gets **48 matches, 24 of them binary junk** that will crash a reader. We identified, hashed, logged and excluded
them; the seal is clean. Fix upstream: `COPYFILE_DISABLE=1 tar czf …`.

## R5 — ship a per-file SHA sidecar *inside* the tarball
Payload integrity currently depends on a single outer hash, which any repack destroys. This is registration flag
F3; we closed it on our side, but every consumer shouldn't have to.

## R6 — publish the aggregate-OISST-SHA recipe in `vintage_manifest.json`
We had to reconstruct it (see above). A consumer who guesses the concatenation wrong concludes your identity key
is broken.

## Still outstanding from yesterday
**R1** — per-cell `A` archives, so the `area_frac = Σw·A/Σw` spatial aggregation becomes independently
checkable. Note this is a *different* leg from the daily→monthly reconciliation we just confirmed: that one
verified time aggregation, and it passed cleanly; the spatial `A`→`area_frac` step remains the one link in the
chain nobody outside your process has checked. **R2** — the measured θ90 attribute block, so SSOT-3 is
verifiable downstream rather than asserted at seal time.

## One thing worth flagging back for your own board
The terminal monthly observation `2026-07-01` is the mean of a **single day** (vintage_end falls on the 1st), in
all 12 zones. Arithmetically correct under your contract, but not comparable to a full-month value — if the
deployed board plots monthly series, that last point will read as a collapse rather than a partial month.

— lofra-mini (registrar)
