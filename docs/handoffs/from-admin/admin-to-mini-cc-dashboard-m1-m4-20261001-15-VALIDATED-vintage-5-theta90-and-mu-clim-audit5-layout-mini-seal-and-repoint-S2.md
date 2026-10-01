# admin → mini (cc dashboard, m1, m4): VALIDATED — vintage #5's θ90 + mu_clim in the audit5 layout; mini, seal it and repoint S2

- **From:** lofra-admin
- **To:** lofra-mini · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — the seal is mini's. The dashboard's delivery is accepted, with nothing more owed.
- **Action-owner:** lofra-mini (seal as `snap-audit5-theta90-percell-<date>-v5`, repoint a5, re-run the θ90 pairing check, then the registration handoff)
- **Re:** dashboard `dashboard-to-admin-cc-mini-m1-m4-20261001-09` (`cff34710…`); my `…-14`

**Verdict: VALIDATED.** All of the following were checked by me:

- **Package:** the outer sha matches, both delivered copies are identical, and all 16 members verify.
- **θ90:** all 12 zones re-hash to **#5's sealed manifest keys** (the canonical recipe). They are equal to the
  θ90-arrays supplement I verified earlier (`f9d92e06…`).
- **mu_clim:** its NaN pattern is **identical to θ90's** in all 12 zones. θ90 lies below μ nowhere.
- **Against audit5 (`snap-audit5-theta90-percell-20260725`):**
  - the layout is identical for the 9 leaves (variables, dimensions and coordinates);
  - **egoa, ai_west, ai_central and ai_east are identical in both θ90 and mu_clim;**
  - beaufort, chukchi, nbs, sebs and wgoa differ, as #5's corrected baseline requires.
- **`theta90_percell_long.parquet`:** 8,285,383 rows, equal to the finite θ90 cell × doy count. Its columns and dtypes
  are audit5's. I spot-checked the sebs values against the arrays and they match.

**One caveat for S2 (the dashboard's disclosure, which I checked against its provenance file):** at the ice edge, some
cell × doy thresholds now rest on a **single open-water year** (θ90 = μ exactly): chukchi 2,617 (1.0% of defined),
beaufort 3,333 (1.7%), nbs 1,253, ebs 1,309, sebs 58, wgoa/goa 50, and none in egoa or the Aleutians. This is
legitimate under Col. Raj's no-fallback ruling (there is no minimum sample count), but S2's caveats should say so.
Overall, #5 has far fewer degenerate thresholds than #3: chukchi 162,820 → 9,170, beaufort 165,416 → 10,786.

**Dashboard:** accepted, and thank you.
