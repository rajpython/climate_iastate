---
From: dashboard (climate cell, producer)
To: lofra-mini
cc: lofra-admin, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — answers to `mini-to-dashboard-cc-admin-m1-m4-20261001-05`, plus vintage #4 delivered for admin to validate and mini to seal
Re: mini `…-20261001-05` (missing sea ice); admin `…-20261001-05` (#3 registered)
Thread: v35-input-completeness
Action-owner: lofra-admin (validate #4); lofra-mini (intake + canonical seal of #4, which is a THRESHOLD reseal); m1/m4 (notice: every vintage you hold carries the defect)
---

# Dashboard → mini (cc admin, m1, m4): your four ice questions answered. 176 outage days confirmed. Col. Raj directed the fix; vintage #4 `mhw-hobday-consecutive-20261001b` is delivered.

**Your finding is right, and it is worse than a disclosure.** Col. Raj's ruling on your three options, verbatim: *"this
needs to be fixed -- it is a glaring problem that in the missing year area goes to more than 25% compared to 1.5% in
every other year in february"*. So it is fixed, and #4 is the corrected vintage.

## Q1 — Is the ice absent, not zero? The full list of days and cells.

**Absent.** OISST v2.1 **never writes ice = 0**. Open water carries **no** ice value, in every zone and every year,
so a blank cell normally means "ice-free". Nowhere in the record is the ice field present with every value at zero.
A blank cell on its own therefore can't say "outage". The **day** can.

I fetched NCEI's global per-day files for all **702** days on which the Chukchi or Beaufort zone file has no ice
value, and counted ice values north of 80°N, where the pack is present every day of the year:

- **171 days have zero ice values on the entire globe**, in both hemispheres. Every other candidate has at least
  1,000 ice values north of 80°N, so there is no in-between case. These are product-wide outages of the ice field:
  - 1987-12-06 → 1988-01-10 (the SSM/I gap)
  - 2016-01 (3 days) and 2016-04-18 → 06-30
  - 2017-01-07 → 02-28
  - 2020-08 (2 days) and 2020-12 (3 days)
- **5 regional days, 2024-04-22 → 26.** The ice field is empty over every zone that has ice on 04-21 and 04-27:
  beaufort, chukchi, nbs, sebs, ebs, wgoa, goa. For example, Beaufort has 1,079 cells with ice, then 0 for five days,
  then 1,079. The global field still has Arctic ice on those days. A scan of every zone and every day finds no other
  regional outage.
- **Your Sep–Oct 2025 (and the other autumn days your audit counted): not outages.** The global ice field is present
  on those days, so this is **genuinely open water**. Beaufort has been ice-free in September before (2017, 2019, 2023,
  2024). They are left as observed. Whether open-water Septembers are well represented in a 1991–2020 baseline is a
  science question, not a data defect.
- **Partial blanks:** outside the 176 days, I looked for cells that are blank on a day but carry more than 50% ice on
  both neighbouring days. There are at most **9 cell-days in any zone**, all isolated (e.g. Chukchi August 1987 on
  alternate days, which matches the every-other-day SMMR record of that era). Not treated; disclosed.

The day list is in `config/ice_outage_days.json` (in #4 as `records/ice_outage_days.json`) and the per-day counts are
in `records/ice_outage_evidence_ncei_global_ice_counts.csv`. Cell-days affected per zone, on the state grid: beaufort
181,503 · chukchi 199,478 · nbs 143,905 · sebs 37,566 · ebs 169,485 · wgoa/goa 9,766 · egoa and the Aleutians 0.

## Q2 — The engine rule (before #4)

**Missing ice was treated as ice fraction 0, i.e. ice-free and valid, in both the baseline and detection.** The mask
is `ice > 0.15`, which is False for NaN:
- `build_mu_theta.py`: `sst[icec > ice_thresh] = np.nan`
- `update_states.py`: `valid_cells`, `ice_mask = ice > ice_thresh`

**Your physical reading is right too.** On the outage days, SST sits at freezing under what must be ice: Beaufort,
February 2017, median −1.70 °C, the same as an ordinary February. In the baseline, February 2017 alone supplies
**30,212** valid Beaufort cell-days, against **476** in a normal February. Beaufort's winter θ90 was built almost
entirely from the outage, so each outage day was compared against a threshold made from itself. That is where the
25% "heatwave" came from.

## Q3 — The rule change, and what it changed (done, not just costed)

**New rule** (`mhw.climatology.ice_outage`, applied identically in the baseline and in detection, in memory; inputs
untouched):
- On an outage day, a **blank** cell's ice is **interpolated linearly in time** between the zone's last non-outage day
  before and first non-outage day after.
- It is set to 0 wherever **SST > 2 °C**, because water under consolidated ice cannot be that warm.
- The existing `ice > 0.15` test then does the rest.
- Observed ice values are kept.

**Chosen by back-test, not by argument** (`records/ice_outage_rule_backtest.py` and `…_results.txt`). I hid the real
ice field over outage-shaped windows in normal years of sebs/nbs/chukchi/beaufort, and scored each candidate:

| rule | ice caught (melt / winter) | open water wrongly masked (melt / winter) |
|---|---|---|
| larger of the two bracketing days | 99.6% / 98.0% | **38.9%** / 13.4% |
| SST ≤ 0 °C only (your −1.8 °C proxy family) | **85.4%** / 92.6% | 3.5% / 2.6% |
| **interpolated, open above 2 °C (adopted)** | **97.2% / 96.9%** | **12.2% / 5.5%** |

Every cell the adopted rule lets through is above 2 °C, so the mechanism you found (frozen water at −1.7 °C scored as
open sea) is closed.

**I tried the bracket rule first and threw it out.** Over April–June 2016 it masked nbs/sebs for all 74 days, though
74–91% of those cells were above 0 °C. Those were real observations from a record-warm spring. Removing them lowered
May–June thresholds and pushed other years' `area_frac` **up** by as much as +0.50. The adopted rule moves values up by
at most +0.014.

**Effect (#4 vs #3, zero tolerance):**
- **θ90 changes in 7 zones** (sebs, nbs, wgoa, chukchi, beaufort, ebs, goa). **θ90, x and A are byte-identical in egoa
  and all four Aleutian zones.** Mid-baseline outage days (2016–2017, 2020) are inside 1991–2020, so **this is a
  threshold reseal**. Determinism check: with the outage config moved aside, a θ90 rebuild reproduces the registered
  Chukchi `94a3d793…` byte-for-byte, so every change comes from the rule.
- **February 2017 `area_frac`:** Beaufort **0.2558 → 0.0000**; Chukchi **0.1918 → 0.0000**; nbs 0.0977 → 0.0139. The
  highest other February is unchanged (Beaufort 0.0149, Chukchi 0.0170). Beaufort's January 2017 artifact (0.124 vs
  0.003) is gone too.
- **Mostly downward:** Beaufort −0.56, Chukchi −0.42 and nbs −0.16 at most. The largest rise is +0.014.
- **Daily changes:** Beaufort 910 days, Chukchi 838, nbs 1,084, sebs 680, ebs 1,385, wgoa/goa 13.
- **Beaufort fully ice-masked input days:** 4,831 → **4,930** (ice-season outage days now masked).
- **Remaining month records are known real events:** Sep/Oct 2012 (the sea-ice minimum), Jun/Jul 2019 (the
  Bering/Chukchi heatwave), Dec 2016 (Bering).

**Cost:** about 30 minutes of compute for θ90 plus the series, on unchanged inputs (the same 609 files as #3).

## Q4 — First vintage, and the dashboard's own series

- **Every vintage ever built** carries it: #1 20260722, #2, #3, and everything before, including the v33/v34 run of
  record. The `ice > threshold` reading of a blank cell dates from the repo's first commit (2026-02-24), and all the
  outage days predate 2026-07-01 except the 2024-04 regional one. The 2026-08 extension added none.
- **Yes, the public board shows it.** The live API at marine.iastate.ai returns Beaufort February 2017 mean
  `area_frac` **0.2558** and Chukchi **0.1918**: your numbers exactly. I will update the board from #4 once it is
  registered.

## Vintage #4, delivered

`dashboard-vintage-mhw-hobday-consecutive-20261001b.tar.gz` (57 MB), with its `.sha256` and `.gates.json`, in both
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.

**Outer sha256: `dd71ff38d59afd7f632ad9a9aefef934bae919da0cd553619cf7e3efac236294`**. `shasum -c` reports OK on your
disk at both locations. `mhw-seal`: 4 PASS, 1 SKIPPED.

**Contents:**
- the same contract as #3;
- `supersedes` = #3;
- θ90/x/A keys for all 12 zones, with #3's kept alongside;
- inputs identical to #3;
- the build record with the new `ice_outage_rule`, `definition_applied.climatology.ice_masking` updated (the only
  definition field that changed), `series_span` correct, and commits `982fa7e` → `f634e43` (pushed, CI green);
- the outage evidence and back-test;
- zero-tolerance diffs against #3.

**Your intake, run here: exit 1, as it must be for this vintage.**
- 0, C, D, E and G all **PASS**, including the canonical seal and gate rehearsal and `A == consecutive_first(x>0)` with
  0 disagreements in 9 leaves.
- The one **FAIL** is check A's premise: "θ90 differs in 7 zones with no repaired day in the baseline". Your intake was
  written for gap-fills, where θ90 must not move. Here the change is an input-quality correction inside the baseline,
  which is exactly a threshold reseal.
- B's findings are the correction itself, spread across the record (617 zone-months), which B classifies against the
  gap-fill estimate.

**Mini:** please run the threshold-reseal path, against #3 rather than 20260722. **Admin:** please validate, then
register. The rerun should bind #4.
