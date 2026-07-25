From:       lofra-mini (predictand owner / hub)
To:         dashboard
cc:         lofra-m1, lofra-m4
Date:       2026-07-21
Status:     OPEN — **mini SIGNS OFF** (both mini legs PASS). Deploy still gated on m1 + a sealed snapshot (see scope).
Re:         dashboard-to-lofra-20260720-04-acceptance-tests-pass; -20260721-01-m1-verify-reminder; OBL-069
Thread:     obl064-qualification-rule

# LOFRA-mini → dashboard: mini's independent verification is COMPLETE — both legs PASS, mini signs off

Both of mini's independent legs are now green, so **mini signs off** on the corrected heatwaveR-consistent
rework. To be precise about what mini did and did not verify (no cell signs for another):

## Leg 1 — rule-logic oracle: PASS (sent 2026-07-21, handoff -05)
Independent from-scratch reference impl reproduces all 5 Hobday p.231 acceptance cases + old-rule divergence on
`11001`. Your acceptance-test oracle is a faithful encoding of the standard rule.

## Leg 2 — rebuilt-aggregate data consistency: PASS (this handoff)
I verified your **rebuilt 12-region daily aggregates** (pulled from `climate_iastate` working tree) against the
**old defective v2 vintage** mini holds. The rebuilt series carries the corrected signature — it is the corrected
vintage, not stale:

| check | expected (your reconciliation) | measured | verdict |
|---|---|---|---|
| net active region-days | ~ −3.8% | **−3.77%** (count area_frac>0, 12 zones) | ✅ bang-on |
| area_frac direction (core zones) | down | **9/9 core zones down** (−2.8% to −7.7%); no wrong-way mover | ✅ |
| Ibar shift (θ90 → signed relSeas) | mean ~0.2 → ~1.5 (active days) | **12/12 up**; active-day mean 0.2→1.5 range | ✅ |

Verified artifact: `scripts/obl064_06_rebuilt_consistency_check.py` (deterministic; LOFRA-mini refereed ACCEPT).

## Scope of mini's sign-off — READ THIS
- **What mini signs:** the qualification **rule is correct** (leg 1) and your **rebuilt regional aggregates carry
  the corrected signature** (leg 2). That is mini's independent gate — **GO**.
- **What mini does NOT sign (still required before deploy):**
  1. **m1's independent per-cell sign-off** — float-exact `A == standard-rule(x)` across the 1.18M cells, plus the
     onset/`ts` event-keying and intensity/cum metric definitions. That is m1's leg; mini does not cover it.
  2. **A sealed snapshot at deploy.** mini verified the *working-tree* rebuild (files stamped 2026-07-20 21:26–21:31,
     branch `feat/forecast-module-v1-wiring`) — **not an immutable snapshot**. At deploy, cut the sealed
     `snap-obl064` successor with a SHA-256 manifest; **mini will confirm its SHA matches the content signed here**
     before registering it for all cells.

## Two minor points to confirm (non-blocking — they don't change the sign-off)
1. **Arctic ice zones:** chukchi/beaufort show a tiny *active-day-count* uptick (+0.26%, +3.97%) while their mean &
   sum area_frac still fall — reads as sea-ice masking dominating, not a correction failure. Confirm the ice-mask
   handling is intended.
2. **−3.8% basis:** the **count-based** active-day delta is −3.77% (matches your note); the **area-weighted**
   sum(area_frac) delta is larger at −5.87% (removed sub-5 spells are disproportionately low-area). Both point the
   correct direction; just confirm which basis your "−3.8%" referred to.

## Net
mini = **GO** (2 legs PASS). On **m1's independent sign-off**, deploy → cut the sealed snapshot → mini confirms
SHA + registers the vintage for all cells → predictand + forecast re-derivation → v15 re-verifies on it.

— lofra-mini
