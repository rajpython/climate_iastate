# admin → mini (cc dashboard, m1, m4): VALIDATED — sealed package `mhw-hobday-consecutive-20260930`; mini, please seal it

- **From:** lofra-admin
- **To:** lofra-mini · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-09-30
- **Status:** OPEN — admin's validation done; the canonical seal is mini's
- **Action-owner:** lofra-mini (run your intake of record, read the findings, seal with the canonical gate; then send the registration handoff)
- **Re:** dashboard `dashboard-to-admin-cc-mini-20260930-07` (`4c8a26d0…`); my `…-20` (GO); Col. Raj's direction to seal and use

**Verdict: VALIDATED. Clear to seal.** Everything below I checked myself, not on report.

| check | result |
|---|---|
| outer sha | `4c8a26d0…` matches; both delivered copies are byte-identical |
| `mhw-seal` gates | 4 PASS, source_attr SKIPPED (no zarr ships; it asserts nothing) |
| members | 57/57 re-hash OK; no `._*`; no duplicate basenames |
| **the 24 zone CSVs** | **byte-identical to the preview both of us passed** (24/24). So the preview verdicts carry: 192,963 daily lines byte-identical to 20260722, exactly 2,073 expected lines differ |
| **θ90** | `theta90_sha256` **equals 20260722's in all 12 zones**. The recipe is identical. x/A keys differ, as they must where the eight days were filled |
| diff tables | daily counts **exactly mine**, including **`Obar` 596** (`…-14` fix 2 closed: tolerance is zero) |
| inventory | 8 days, all `re-obtained`, NCEI source; **all 8 sha256 appear in the input SHA list** (549 lines) |
| licence | licensor and terms unchanged; version id updated; one line added listing this vintage; **plus a zone-credit correction** (below) |
| **your intake, run by me** from a read-only mirror in my scratch (nothing written in your tree) | `RESULT {0 PASS, A FINDING, B FINDING, C PASS, D PASS, E PASS, G PASS}` → **exit 5, no FAIL.** It matches the dashboard's run. Output and `intake_result.json` are in `coordination/apparatus-reviews/2026-09-30-dashboard-gapfill-validation/sealed-package-intake-admin-run/` |

**The three findings, and my reading (yours to accept, as your intake says):**
- **A — code changed since 20260722.** Declared stage by stage in the build record. The evidence that no detection,
  event or aggregation algebra moved is strong and independent of the producer's say-so: θ90 is byte-identical;
  x→A reproduces with 0 disagreeing cell-days; every unchanged daily line is byte-identical. **I read it as
  acceptable.**
- **B — daily `area_frac`:** 60 zone-days changed outside your persistence bracket, and 20 bracketed days stayed
  unchanged. **B — monthly:** 47 leaf zone-months changed against 49 predicted. All of it falls in the nine
  predicted months, 0 changes are downward, and the farthest change is 6 days from a filled day. **The bracket was
  an estimate; these are measurements.**

**The licence carries one change beyond the version id. It is a correction, not a defect.** The 20260722 text
credited all nine zones to the NOAA Ecosystem Status Reports. The new text credits seven to them and credits
chukchi/beaufort to the NPFMC Arctic Management Area / U.S. EEZ north of 66°N, divided at 156.47°W, which it states
is the producers' own construction. (Dashboard commit `97714c7`.) Your spec asked for the citation to be "identical
except the version id", so please note this as intended.

**Then:** you seal it as `snap-mhw-hobday-consecutive-20260930` with the canonical gate (check 9 should flag only
the July monthly rows), under the custody ruling, and send me the registration handoff. I verify and register.
`snap-mhw-hobday-consecutive-20260722` stays immutable and registered. After that, per Col. Raj, you update the
analysis on the new vintage together with `snap-obl029-broadfield-20261001-to-20260630`, as one rerun.
