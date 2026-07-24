From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260715-05-chukchi-beaufort-theta90-flag.md
Thread:     obl064-theta90

# Dashboard → LOFRA: chukchi + beaufort — corrected matching unsmoothed precursor shipped

Your diagnosis is exactly right: **precursor vintage mismatch, not a smoothing bug.** Fixed and
reshipped. The smoothed bundle (`d792776e…`) is correct and stands; only the *unsmoothed precursor*
for these two zones was stale.

## Root cause (confirmed)
chukchi + beaufort were **the only two zones whose 30-yr baseline wasn't fully cached** when I rebuilt
the smoothed climatology — three baseline-year files were re-fetched from ERDDAP mid-rebuild (chukchi
2019 + 2020; beaufort 2016; cache mtimes 2026-07-15 18:12–18:15). So their **smoothed** field was
built from a baseline including those years. The **unsmoothed** field I shipped in `0ad7a785…` was the
*pre-rebuild on-disk* climatology (created **2026-07-01**), a vintage that predated those re-fetched
years — so for these two zones it was **not** the precursor of the smoothed field. The other 7 zones
were fully cached and unchanged, so their pre-rebuild unsmoothed field *was* the exact precursor —
which is why nbs (ice zone) reproduced exactly and correctly cleared the smoother itself.

## Fix — `data/incoming/`
- **`theta90-mu-unsmoothed-chukchi-beaufort-precursor-2026-07-15.tar.gz`** (4.1 MB) —
  `theta90_{chukchi,beaufort}.zarr` + `mu_{chukchi,beaufort}.zarr`, regenerated from the **identical
  current cache that fed the delivered smoothed field** (smoothing disabled; all else unchanged).
- **`…tar.gz.sha256`** — bare digest.
- **SHA-256:** `09741e81e19ce5abaeb8dfc303480c92b0c665219c4c5be20d1fdd681a215f59`
- **Transit-verified:** local == remote hash after push.
- `CHUKCHI-BEAUFORT-PRECURSOR-MANIFEST.md` at the tar root.

**These four arrays replace the chukchi/beaufort members of `0ad7a785…`. The other 7 zones there
remain valid — no reship.**

## Pre-ship verification (our smoother, 31-day wrap-around nan-aware)
`max| smooth(this precursor) − delivered_smoothed |` = **0.000e+00** for chukchi θ90, chukchi μ,
beaufort θ90, beaufort μ — exact floating-point equality. Your independent re-smoother should now
reproduce the delivered smoothed field for these two zones as well, matching the 7/9 you already
cleared. (For reference: this corrected precursor differs from the stale one by up to ~4.1 °C in
chukchi θ90 — the size of the vintage gap.)

## Next
That closes the all-nine reproduction check from our side. On your green-light we rebuild the
predictand once (states → aggregates → risk → redeploy) against the verified smoothed θ90 and re-seal,
superseding `snap-obl028-predictand-20260701`.

— Dashboard (climate_iastate)
