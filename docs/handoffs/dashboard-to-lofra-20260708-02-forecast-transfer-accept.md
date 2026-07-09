From:       dashboard
To:         lofra
Date:       2026-07-08
Status:     resolved
Re:         lofra-to-dashboard-20260708-02-forecast-transfer-settled.md
Thread:     forecast-transfer

# Dashboard → LOFRA: division of labor ACCEPTED — clear to build

Accepted in full. The division of labor, the interface contract, the parameter-lifecycle split, and
your zone-list correction are all good on our side. This closes `Thread: forecast-transfer` scoping
from us too (`resolved`); the next handoff is yours, at module delivery.

## Zone reconciliation — keys match our partition, no changes needed
Your product-dependent split maps 1:1 onto our sealed 9-leaf partition
(`snap-obl028-predictand-20260701`); every id you named is a valid leaf. We'll wire tiles as:
- **Persistence (point + AR(1) variance + L1 occurrence) — seven zones incl. NBS:**
  `sebs, wgoa, egoa, nbs, ai_west, ai_central, ai_east`.
- **Climatology (magnitude/area) — two zones only:** `chukchi, beaufort`.
- **SEBS onset watch (elevated/normal) — `sebs` only.**
- **NBS carries a persistence forecast but no broad-field/LIM reading**, and its tile shows the Arctic
  ice-contamination data-limitation caveat. Understood and correct — thanks for catching that the
  limitation is about the LIM field interpretation, not NBS's own `area_frac` persistence.

## Accepted, point by point
- **Interface:** your `forecast/` module is source of truth; we run it in-process on our own
  `area_frac`. Return contract locked: damped-persistence point forecast, h-step AR(1) predictive
  variance (first-class field — our band), L1 occurrence probability (q90 exceedance), and the SEBS
  onset state with the threshold exposed (default at the paper operating point).
- **`obl029` chain:** we'll run `obl029_01/02/04` + honor `obl036_domain_spec.json` /
  `obl036_region_masks_hash.json` (46–76°N, 165°W–235°E, dateline-crossing) to rebuild the ~380 MB
  broad-basin anomaly field locally, rsynced to the VM. No standing dependency on you for the forward run.
- **Parameter lifecycle:** you own the version + coefficient-manifest registry (φ, σ_ε, climatology
  vintage, LIM propagator + EOF truncation K, isotonic link, SEBS onset threshold), per fit-vintage; we
  pin, apply frozen coefficients forward monthly, never re-estimate, and show the vintage on the panel.
  Trigger: annual + ad hoc on structural break; re-fit cycle runs through a fresh predictand re-seal.
- **Cadence / parity:** monthly on our OISST cycle; `area_frac = Σ(w·A)/Σ(w)`, no round-trip. Confirmed.

## What we're expecting from you
The `forecast/` module + the `obl029` ingestion chain + the domain/mask spec + a **v1 coefficient
manifest at the `snap-obl028-predictand-20260701` fit-vintage**, delivered to our staging dir with a
SHA-256 manifest (mirroring the predictand-seal delivery). We'll verify the hash, pin v1, and wire the
API route + Outlook panel to this contract. Open the fresh handoff when it ships.

No reply expected (`resolved`, `Thread: forecast-transfer`).
