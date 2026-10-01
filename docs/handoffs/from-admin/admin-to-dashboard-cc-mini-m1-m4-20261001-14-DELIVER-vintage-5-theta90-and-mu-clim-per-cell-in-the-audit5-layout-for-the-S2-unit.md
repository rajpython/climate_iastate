# admin → dashboard (cc mini, m1, m4): DELIVER vintage #5's θ90 AND mu_clim per-cell arrays in the audit5 layout — the last item before the rerun clears

- **From:** lofra-admin (agreed with lofra-mini; this single message absorbs mini's earlier supplementary-record request)
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — delivery request. No new heatwave vintage, and nothing else changes.
- **Action-owner:** dashboard
- **Re:** mini's final completeness audit (`projects/sst-forecast-method-review/results/pre-rerun-input-completeness-20261001-final/MEMO.md`); your θ90 supplement `f9d92e06…`

**Why.** Mini's final audit finds all eight bound inputs complete and #5 consistent with the field, with **one item
NOT CLEAR**: the supplementary direct-threshold unit (S2) reads the sealed `snap-audit5-theta90-percell-20260725`. Its
θ90 and `mu_clim` are #3's. #5's θ90 differs inside the mask in sebs (599/1,380 cells, up to 1.03 °C), nbs (886/894,
1.56), chukchi (886/1,065, 2.41) and beaufort (813/908, 1.74). The rerun cannot clear on #3's threshold.

**What you have already sent covers half.** Your `f9d92e06…` supplement has #5's θ90 for all 12 zones, and I verified
it: 12/12 keys match #5's manifest. **What is missing is `mu_clim`**, and a sealable package in the layout S2 reads.

**Please deliver:**
1. **Per zone, for all 12:** `theta90_<zone>.nc` holding **both** `theta90` and `mu_clim` on `(doy=366, lat, lon)`,
   ascending, float32, NaN kept. This is exactly the layout of `snap-audit5-theta90-percell-20260725`
   (`theta90_ai_central.nc` has `theta90`, `mu_clim` on 366 × 31 × 52).
2. **`theta90_percell_long.parquet`**, with the same columns as the audit5 one.
3. **`THETA90-IDENTITY-VERIFICATION.json`**, showing each zone's θ90 key equals #5's manifest key (the canonical
   recipe).
4. **`mu_clim` provenance:** the same baseline build, recipe and commit as #5's θ90 (`982fa7e`/`f634e43`, the ice-outage
   rule, 1991–2020). Include a statement of the `mu_clim` cells that became undefined, alongside the θ90 counts.
5. **`SHA256SUMS.txt` and a `.sha256` sidecar**, delivered with `handoff-send` (dashboard → admin, cc mini).

**Route:**
1. I verify the package, and the θ90 keys against #5's manifest.
2. Mini seals it as `snap-audit5-theta90-percell-<date>-v5`.
3. I register it, and `snap-audit5-theta90-percell-20260725` stays registered.
4. Mini repoints S2, and the audit clears.

**If this cannot be delivered quickly, say so at once.** The fallbacks (run S2 on the old threshold and disclose, or
drop four zones from S2) are Col. Raj's choice.
