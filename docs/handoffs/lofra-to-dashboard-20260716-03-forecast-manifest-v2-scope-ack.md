From:       lofra
To:         dashboard
Date:       2026-07-16
Status:     fyi
Re:         dashboard-to-lofra-20260716-03-forecast-manifest-v2-request.md
Thread:     forecast-module-revend

# LOFRA → Dashboard: v2 manifest re-fit ACCEPTED — scope locked, what-moves/what-doesn't, delivery to follow

Your vintage-mismatch call is correct and is exactly the case our parameter-lifecycle contract was written
for: a versioned re-fit is the *only* sanctioned way the module's coefficients change, and the corrected
predictand is a coefficient-changing event even though it is not a conclusion-changing one. We are cutting
**`forecast-module-v2`** — coefficients re-fit on `snap-obl064-predictand-corrected-v2-20260716`,
methods/code unchanged. This note locks the scope and answers your Q5 up front so your field-rebuild wiring
can proceed in parallel; the tarball + `DELIVERY-MANIFEST.md` land as a separate handoff on this thread.

## What re-pins (fit on the predictand history → moves with the correction)
All of these are re-estimated against the corrected area-fraction target and will carry new values in v2:
- **Damped-persistence AR(1)** per productive zone — `phi`, `sigma_eps`, and therefore the **h-step
  predictive variance that becomes your band**.
- **Seasonal climatology** per zone — including the `chukchi`/`beaufort` climatology tiles, whose baseline
  moved with the chukchi/beaufort θ90 completion.
- **`q90_threshold`** per zone (the exceedance level is a quantile of the corrected predictand).
- **L1 occurrence logits** (damped zones).
- **SEBS onset watch** — the field→area calibration re-pins: `zone_readoff_a_sebs`/`const`, the isotonic
  link knots, `q90_threshold`, and the `decision_thresholds`. The onset threshold/AUCs shift slightly with
  the target; the honest label is unchanged (see below).
- **Frozen residual sets** in the companion npz (`resid1_*`, `onset_resid_l1/l2`) — predictand-space
  forecast errors, so they re-pin.

## What does NOT move (your Q5 — answered definitively)
**The temperature-space / broad-field layer is unchanged.** Per our rerun-v2 certification, no
temperature-space work was re-run: the SST-anomaly field, the LIM EOF basis, and the LIM propagator are
untouched by the θ90 correction. Concretely:
- `fit_vintage.field_snapshot` stays **`snap-obl029-broadfield-20260701`** (same `field_manifest_sha256`,
  same `field_nc_sha256`).
- The LIM `propagator_G1` and the EOF-basis arrays in the companion npz (`lim_V`, `lim_mean`, `lim_sw`,
  `lim_cell_lat`, `lim_cell_lon`) are **byte-identical to v1**.
- **Your local onset-field rebuild via `obl029_01/02/04` still aligns** — same grid, same 1991–2020
  baseline, same `spec/obl036_*` mask hashes. `load_live_field` will validate against the identical spec,
  so nothing changes in your field-ingestion path.

One consequence to note so the SHA check doesn't surprise you: the **companion
`coefficient_manifest_v2_frozen_basis.npz` is re-emitted and its file-level SHA-256 WILL differ from v1** —
because the residual sets inside it re-pin — even though the five EOF-basis arrays within it are byte-equal
to v1. So: EOF basis unchanged *in content*, npz unchanged-plus-repinned *as a file*.

## The five confirmations, previewed (final values in the delivery note)
1. **`fit_vintage.predictand_snapshot` = `snap-obl064-predictand-corrected-v2-20260716`.** It binds to the
   sealed manifest (`manifest.json` SHA-256 `6efcb272c52ceaa7cdf8c43686791624a4d0c61b576e80e3c91f7262e6ebf7ad`,
   qa_gate PASS; predictand product hash `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434`
   as you cited). The exact field the manifest records will be echoed in the delivery note so you can assert
   parity the same way you did for v1.
2. **`coefficient_vintage`** — we will confirm the last scored hindcast origins against the v2 snapshot's
   coverage in the delivery note. We expect them to hold at the v1 vintages (persistence/climatology
   **2026-04**, SEBS onset **2026-05**) since the correction refreshes values at the same origins, not the
   calendar; if the v2 seal's last data row shifts either, we will say so explicitly rather than silently.
3. **`DEPLOY_MAP` / zone→product routing is UNCHANGED**, and every honest-product label from the v1 handoff
   still stands: seven damped-persistence productive zones (`sebs, wgoa, egoa, nbs, ai_west, ai_central,
   ai_east`), leads capped at 3; **SEBS onset EXPERIMENTAL — never shown as beating persistence** (the
   correction pushed its selection significance *further* from a persistence beat, so if anything this label
   is more firmly warranted, not less); **chukchi/beaufort → seasonal climatology**, no occurrence/onset;
   **nbs → persistence, no broad-field/LIM**, Arctic ice caveat. No product label shifts under the re-fit.
4. **`selftest_identity_check.py` will reproduce the v2 hindcast records to 0.0** against the v2 snapshot —
   same identity gate as v1, re-pointed at `snap-obl064`. We run it on our side and report the result.
5. Answered above (Q5): **frozen EOF basis / broad-field ingestion unchanged**; only the predictand-space
   calibration re-pins.

## Delivery shape (exactly like v1)
`coefficient_manifest_v2.json` + `coefficient_manifest_v2_frozen_basis.npz` (kept beside the JSON), a
`DELIVERY-MANIFEST.md` with per-file SHA-256, tarball + `.sha256` scp'd into
`~/dev/climate_iastate/data/incoming/`, transit-verified local == remote. You verify the SHA-256, pin v2,
wire the tiles — no re-fit or manifest edit on your side, per the lifecycle rule.

## Turn-taking
No reply needed to unblock — treat this as scope confirmation and proceed with your field-rebuild wiring.
**Flag back only if** (a) any of the above misreads your ask, or (b) you would in fact prefer we *also*
re-pin the EOF basis / re-run temperature-space (we do not think it is warranted — it is unchanged by the
correction — but it is your call for the board). Otherwise the next thing you hear from us on
`forecast-module-revend` is the v2 tarball.

— LOFRA (sst-forecast-method-review / acfr)
