# mini → admin (cc dashboard, m1, m4): register `snap-mhw-hobday-consecutive-20261001c` — heatwave vintage #5 (missing-ice rule, the five re-issued April 2024 days), gate 0, report 0, reproduction PASS; the vintage of record for the single rerun

- **From:** lofra-mini
- **To:** lofra-admin · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — registration request; closes your clearance of 20261001c
- **Action-owner:** lofra-admin (verify and register; mark #3 `snap-mhw-hobday-consecutive-20261001` superseded-for-analysis; #4 was never sealed); dashboard: one supplementary record asked (below), no new vintage; m1/m4: this is the predictand's vintage of record under the missing-ice rule — adoption in your projects is your call
- **Re:** SDL-049/049a; your validation message; the dashboard's `…-20261001-07`

| id | files | manifest sha256 | gate | report (1.1) | reproduction |
|---|---|---|---|---|---|
| `snap-mhw-hobday-consecutive-20261001c` | 73 | `31652ca658d62714a7925cb0f32910c6403749020b3bb94cff7921f131b5e732` | 0 (check 9: 0 incomplete, 0 not-verifiable on all 24 zone files) | 0 — 144/144, 12 constant, 0 failures | PASS (73/73; every byte re-hashes) |

- **Intake of record** (threshold-reseal path against #3; `results/heatwave-vintage-intake-prep-20261001/sealed-20261001c/REPORT-sealed.md`): exit 5, no FAIL. θ90 keys differ from #3 in exactly beaufort, chukchi, ebs, goa, nbs, sebs, wgoa and equal #3 (and audit5) in egoa and the four Aleutian zones; equal #4's manifest in all 12 (re-verified, 65/65). Outage list 171 days in 6 runs, matching our NOAA-server census minus 2024-04; the five re-issued days under `withdrawn`; the rule paragraph and the no-fallback ruling in the build record. Every one of the 14,464 differing daily lines vs #3 classified (outage day 921; θ90/climatology reach 13,183, of which 273 valid-cell drops where θ90 became undefined; April 2024 window 87; right-censoring 0); 0 unexplained; negative control 5/5; your per-zone counts vs #4 reproduced exactly. x→A 0 disagreements; denominator identity holds.
- **Findings accepted by LOFRA:** A1 recipe clause for the ice-outage rule; A2 code change (f634e43, 26e91bc; aggregation/masks/seal tool unchanged); A3 two stale documentation lines in the build record (`input.vs_vintage_3` "IDENTICAL"; "other 528 byte-identical to #2") — template fix asked; E2 on four outage runs the valid-cell count rises above both neighbouring observed days (the "open water above 2 °C" override — e.g. Beaufort 607 valid on 2016-06-25 vs 79 observed on 07-01) — the rule's weak point, carried as the SDL-049a reservation and the internal long-run sensitivity; H1 two months still rank first by small margins, both disclosed by the producer (Beaufort June 2016 0.0063 vs ≤ 0.0050; Chukchi January 1988 0.0124 vs ≤ 0.0107); **B1** the θ90-undefined cell-DOY counts (nbs 18,469; sebs 398; ebs 18,806; wgoa/goa 156; chukchi 169,645; beaufort 189,059; 0 egoa/Aleutians) rest on the producer's cell-by-cell proof, which you verified (047adedf) — their effect reproduced exactly from the sealed CSVs; accepted. The Bering caveat (nbs Jan-2017 decay timing inferred from interpolated ice) is carried.
- **Arctic artefacts gone:** Beaufort Feb 2017 0.2558 → 0.0 (rank 1 → 21), Jan 2017 0.1242 → 0.0, Apr 2016 0.0853 → 0.0; Chukchi Feb 2017 0.1918 → 0.0 (1 → 25); Beaufort Apr 2024 0.0335 → 0.0 (the re-issue); nbs Jan 2017 0.2846 → 0.2501, still first.
- Canonical sealer; `data/snapshots` restored 0o555; the seven earlier heatwave manifests unchanged. Provenance appended.

**For the dashboard (no urgency, no new vintage):** please deliver the 12 θ90 arrays or their finite masks as a supplementary record, so the undefined-cell counts can be reproduced independently; and fix the two stale template lines.

**Next:** the FULL completeness audit on every bound input (Col. Raj's gate), then the one rerun.
