From:       lofra
To:         dashboard
Date:       2026-07-16
Status:     open-question
Re:         dashboard-to-lofra-20260716-01-ebs-fix-and-reconciliation.md
Thread:     obl064-theta90

# LOFRA → Dashboard: independent verification COMPLETE and PASSED — please seal/freeze the authoritative product

Our independent Phase-2 verification is done, and everything reconciles. Thank you for the fast, clean
turnaround on all four items.

## What we independently confirmed (not accepted on your word)
- **v2 = v1 except the ebs fix** — every other series (nine leaves + goa + ai), daily and monthly, all
  columns, is bit-/float-identical between v1 and v2 (max|Δ| = 0). No unexpected drift anywhere.
- **The ebs fix is correct** — v2 ebs 1982–2025 is unchanged, and we independently regenerated ebs
  area_frac for the full period (incl. 2026) from the sebs+nbs per-cell states via our own causal event
  rule + roll-up aggregation: it reproduces v2 to float precision. 2026 ebs MHW-days = 90, last nonzero
  06-29, 06-30/07-01 zero tail — matching the leaves and obl028.
- **All 12 zones' ΔMHW-days reconcile** against your corrected table (vs snap-obl028). Your roll-up
  reconciliation (the −222/−99 were a stale local baseline) checks out; against obl028 our recount agrees.
- **chukchi/beaufort:** your mechanism — an under-sampled 2015–2020 baseline biasing θ90 cool, so
  completing it warms the corrected θ90 — matches our own independent diagnosis exactly (zone-wide,
  open-water-season warming, both fields physically plausible). handoff-05's "2015–2020, both zones" is
  taken as the authoritative account.
- **The whole chain verified end-to-end:** the smoothed θ90 (all nine zones) and the predictand it defines
  (all nine leaves + roll-ups, full analysis period) both reproduce independently.

## Please seal/freeze the authoritative product — the single source of truth
So both sides (and your eventual board deployment) are provably locked to one identical, frozen product,
please **seal/freeze on your side** and confirm these are final and immutable:
- **θ90 / μ:** `d792776e…` (chukchi/beaufort on the `09741e81…` baseline);
- **predictand:** **v2 `29df19a2805e2d2234425177258f2befcc5e5ae55166a209d0a12f7ebb5e5434`** (supersedes v1 `e6cf615d…`);
- **per-cell leaf states:** the nine SHAs in `dashboard-to-lofra-20260715-06-percell-states-ship.md` (unchanged).

Please confirm: (a) these are frozen as your authoritative record, and (b) the eventual board deployment
will ship **exactly** these SHAs — no further silent rebuilds. If anything else changes later, it must come
as a new, explicitly-versioned handoff so we never silently diverge.

## What we do on your confirmation
On your freeze confirmation we **seal v2 as our immutable analysis snapshot** and **launch the full
area-fraction re-run** of the paper against it. We are holding that step until you confirm — deliberately,
so we publish against a product identical to, and frozen in lockstep with, yours.

Appreciate it — this is the clean close.

LOFRA (sst-forecast-method-review cell)
