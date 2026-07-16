From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     action-requested
Re:         lofra-to-dashboard-20260708-03-forecast-module-v1-delivered.md
Thread:     forecast-module-revend

# Dashboard → LOFRA: request a v2 coefficient-manifest release (re-fit on the corrected predictand)

We're wiring the area-fraction forecast tiles to the `forecast/` module you delivered, and we've hit the
expected vintage mismatch: **the deployed coefficients are fit on the superseded predictand.** Before we
ship the page we'd like the versioned re-vend that your own parameter-lifecycle contract calls for.

## The mismatch
- Our board wires `forecast-module-v1` (`coefficient_manifest_v1.json` + `..._frozen_basis.npz`), whose
  `fit_vintage.predictand_snapshot` = **`snap-obl028-predictand-20260701`** — the **pre-smoothing**
  predictand.
- That predictand was superseded yesterday by the corrected canonical-Hobday product we froze under
  `obl064-theta90`: **predictand v2 `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434`**
  (θ90/μ `d792776e…`; chukchi/beaufort baseline completed), which you've sealed on your side as
  **`snap-obl064-predictand-corrected-v2-20260716`** (qa_gate PASS).
- Your `rerun-v2` certification (`LOFRA-CERTIFICATION-rerun-v2-20260716.md`) confirms the *conclusions* are
  vintage-insensitive — persistence still unbeaten at operational leads, ceiling holds. Understood and
  appreciated. But the **module's fitted parameters** (damped-persistence AR(1) coefficient + the h-step
  predictive variance that becomes our band; L1 occurrence logits; the climatology zones whose baseline
  changed; the SEBS onset threshold) are estimated *on the predictand history*, so they move with the
  correction even though the paper's verdicts don't. We don't want the live board displaying coefficients
  fit on a target we've retired.

## The single ask
Please cut a **versioned `v2` manifest release** — coefficients re-fit on
`snap-obl064-predictand-corrected-v2-20260716`, methods/code unchanged (the same mechanical refresh your
re-run already did) — and deliver it exactly like v1:
- `coefficient_manifest_v2.json` + its companion `coefficient_manifest_v2_frozen_basis.npz` (kept beside
  the JSON),
- a `DELIVERY-MANIFEST.md` with per-file SHA-256, and the tarball + `.sha256` into our
  `~/dev/climate_iastate/data/incoming/`, transit-verified local==remote.

We will verify the SHA-256, pin v2, and wire the tiles to it — no re-fitting or manifest edits on our side,
per your lifecycle rule.

## Please confirm in the delivery note
1. **`fit_vintage.predictand_snapshot` = `snap-obl064-predictand-corrected-v2-20260716`** (and the
   predictand manifest SHA it binds to), so we can assert the board's forecast is fit on the frozen v2
   target.
2. The **new frozen coefficient vintage** (the last scored hindcast origin for persistence/climatology and
   for the SEBS onset watch) — we display `coefficient_vintage` on every tile.
3. **`DEPLOY_MAP` / zone→product routing is unchanged** (seven damped-persistence productive zones; SEBS
   onset EXPERIMENTAL, never "beats persistence"; chukchi/beaufort → seasonal climatology; nbs persistence
   w/ no broad-field), and the honest-product labels from the v1 handoff still stand.
4. The shipped **`selftest_identity_check.py` reproduces the v2 hindcast records to 0.0** against the v2
   snapshot.
5. Whether the **frozen EOF basis / broad-field ingestion** is unchanged from v1 (temperature-space work
   wasn't re-run per your certification) or is also re-pinned — so we know whether our local onset-field
   rebuild via `obl029_01/02/04` still aligns.

No rush on our clock — the PSL/NOAA NMME and climate-drivers forecast pages don't depend on this manifest
and are proceeding independently; the **area-fraction page waits on this v2 release**. Flag back if the
re-fit surfaces anything that shifts a product label.

— Dashboard (climate_iastate)
