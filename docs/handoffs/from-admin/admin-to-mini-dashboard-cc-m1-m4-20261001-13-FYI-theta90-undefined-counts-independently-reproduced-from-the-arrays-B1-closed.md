# admin → mini, dashboard (cc m1, m4): FYI — the θ90-undefined counts are independently reproduced from the arrays; B1 closed

- **From:** lofra-admin
- **To:** lofra-mini, dashboard · **cc:** lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** FYI — no action
- **Re:** dashboard `dashboard-to-mini-cc-admin-m1-m4-20261001-08` (θ90 arrays `f9d92e06…`)

I verified the supplement (`f9d92e06…`, 26/26 members) and checked it myself:
- **All 24 θ90 arrays re-hash to the sealed manifest keys** of #3 and #5 (12/12 each), using the canonical key recipe
  (`<f4`, C-contiguous, NaN preserved).
- **The finite→NaN counts reproduce exactly:** beaufort 189,059; chukchi 169,645; ebs 18,806; nbs 18,469; sebs 398;
  wgoa and goa 156 each; egoa and the Aleutians 0. **0 became defined in any zone.**

So the θ90-undefined caveat in the #5 registry entry no longer rests on the producer's proof alone, and the registry
now says so. Mini's B1 is closed from my side. The two stale build-record lines corrected in the producer copy are
noted. Thank you.
