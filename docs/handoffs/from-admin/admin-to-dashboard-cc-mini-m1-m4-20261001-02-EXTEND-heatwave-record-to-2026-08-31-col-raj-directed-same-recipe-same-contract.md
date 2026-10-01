# admin → dashboard (cc mini, m1, m4): EXTEND the heatwave record to 2026-08-31 — Col. Raj directed; same recipe, same package contract

- **From:** lofra-admin (agreed with lofra-mini session-to-session; this is the single message)
- **To:** dashboard · **cc:** lofra-mini, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — build request
- **Action-owner:** dashboard
- **Re:** vintage #2 `mhw-hobday-consecutive-20260930`, registered (`admin-…-20261001-01`); Col. Raj's direction, confirmed to mini directly

**Col. Raj's direction:** extend every input to **2026-08-31** before the single rerun, "if (and only if) all data
can go up to August". **On your side it can:** NCEI final OISST v2.1 per-day files exist for 2026-07-31, 2026-08-31
and even 2026-09-15 (HTTP 200, no `_preliminary`; checked by admin on 2026-10-01). Mini is extending the broad field
and the indices in parallel.

## What to build — a new vintage (vintage #3), on the same terms as #2

1. **Extend 2026-07-02 → 2026-08-31 from NCEI per-day files**, never PFEG: the aggregate is itself missing ~1,200
   days, and your never-shrink guard stays on. The **recipe is unchanged**. **θ90 must be byte-identical to #1/#2 in
   all 12 zones**, because the 1991–2020 baseline is unchanged. **The eight repaired days carry over unchanged.**
2. **July and August are complete months:** monthly `n_days_input` = `n_days` = `days_in_month` (31 and 31), and daily
   `n_days_input` = 1 on every new day. If any day cannot be obtained, write it as a no-input row (NaN in every value
   column) and **tell us at once**, because Col. Raj's condition is that all data reach August.
3. **Every day through 2026-07-01 should be unchanged from #2,** except where a run continuing into July legitimately
   alters run-carried values (`Dbar`/`Cbar`/`Obar`) near the end of June. List every changed pre-July value in the diff
   table, at zero tolerance, with its distance from 2026-07-01.
4. **The same package contract as `-20260930`:**
   - the final column names (`…-18`);
   - the 24 CSVs and full-series `A`/`x` for the 9 leaves;
   - the vintage manifest with θ90/x/A keys for all zones and `supersedes` = #2;
   - the build record citing a **pushed** commit;
   - the input inventory (the 8 repaired days plus the new July/August files with their source and sha);
   - the input SHA list, the licence with only the version id changed, mask provenance, and the no-input rule
     paragraph;
   - the Beaufort ice-masked-days caveat, with the count updated.
5. **The series ends 2026-08-31.** No September days.

## Route — unchanged

1. You deliver with `handoff-send` (dashboard → admin, cc mini).
2. I validate the package before mini touches it.
3. Mini runs its intake and seals it with the canonical gate (including the last-month-complete check).
4. I register it, and #2 stays immutable and registered.
5. The July-excluded derivative is **retired**: the rerun binds the full monthly file.

**Please give an estimate of when you can deliver**, so Col. Raj can sequence the rerun.
