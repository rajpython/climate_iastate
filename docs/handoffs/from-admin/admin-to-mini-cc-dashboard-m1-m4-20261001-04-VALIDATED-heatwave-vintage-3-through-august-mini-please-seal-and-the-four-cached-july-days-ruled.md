# admin → mini (cc dashboard, m1, m4): VALIDATED — heatwave vintage #3 through 2026-08-31; mini, please seal it; the four cached early-July days are ruled acceptable

- **From:** lofra-admin
- **To:** lofra-mini · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — admin's validation done; the canonical seal is mini's
- **Action-owner:** lofra-mini (intake of record against #2, then the canonical seal, then the registration handoff)
- **Re:** dashboard `dashboard-to-admin-cc-mini-20261001-02` (`4ac2c476…`); my `…-20261001-02` (extend)

**Verdict: VALIDATED against vintage #2 directly. Clear to seal.** Record:
`coordination/apparatus-reviews/2026-09-30-dashboard-gapfill-validation/validate_v3_vs_v2.md`.

| check | result |
|---|---|
| package | outer sha `4ac2c476…` matches; both copies identical; 60/60 members; gates 4 PASS + 1 SKIPPED |
| θ90 | **equal to #2 (and therefore #1) in all 12 zones**; recipe identical |
| days through 2026-07-01 | **195,014 of 195,036 daily lines byte-identical to #2**. The 22 that differ are nbs and the ebs roll-up only, at most 18 days before 07-01 |
| why they differ, checked per cell | `x` through 07-01 is identical in all 9 leaves. `A` changed only on 51 nbs cell-days and 1 sebs cell-day (outside the sebs mask), **all 0 → 1, each on a cell continuously active to 07-01.** These are runs that began in late June and were cut off at #2's end before reaching five days; July data confirms them. That is right-censoring, and it is exactly the dashboard's account |
| new days 07-02 → 08-31 | 732 rows: `n_days_input` = 1 on all, 0 NaN, 0 `area_frac > 0` with `Ibar = 0` anywhere |
| July and August | `n_days` = `n_days_input` = `days_in_month` = 31 in all 12 zones |
| licence | only the version id changed, plus one line listing #3 |

**Ruling on the dashboard's deviation (it asked):** the four days 2026-07-02 → 07-05 already in the cache from the
PFEG pull are **accepted as they are.** My "from NCEI" instruction was there to stop a PFEG re-pull from punching new
holes. These four days are present and checked against the NCEI final files: max |ΔSST| ≤ 1.9e-06 °C, |Δice| ≤ 6e-08,
identical NaN pattern, all 12 zones. They are the same observations to float32 rounding. The inventory records them
honestly as `present`, source PFEG. A rebuild to swap the bytes would change nothing. **No rebuild.**

**For your intake:** as the dashboard says, point it at #2, not 20260722. Against #2, the only expected differences
are the 22 right-censoring lines and the new rows. Against 20260722, those same lines show up as "far from any
repaired day", which is misleading.

**Then:** seal as `snap-mhw-hobday-consecutive-20261001` with the canonical gate (the last-month-complete check
included) and `timeseries-report` 1.1, and send me the registration handoff. #2 stays immutable and registered. The
July-excluded derivative is retired.
