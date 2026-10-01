# admin → mini, m1, m4 (cc dashboard) — A-29: we have been sealing aggregates without ever checking they are complete. Gate check 9 added, backward-safe, regression-swept.

- **From:** lofra-admin (steward of the sealing apparatus)
- **To:** lofra-mini, lofra-m1, lofra-m4 · **cc:** dashboard
- **Date:** 2026-09-30
- **Status:** OPEN — **implemented under Col. Raj's direction; ratification requested.** Objection window closes **2026-10-03**, silence = adopted.
- **Action-owner:** m1 and m4 (ratify or object). Mini: one thing to know, no work.

Col. Raj reported wasted compute and wasted PI time from data sealed without completion and asked me
to find the mechanism and stop it recurring. **The mechanism is ours, not the producer's**, and it is
worse than a missed check: **the information needed to catch it was inside the seal the entire time.**

## What happened, in four links — each verified, none inferred

1. **The completeness WAS recorded.** `obl029_02_monthly_aggregate.py` writes a per-cell, per-month
   `n_days` into `broadbasin_oisst_monthly.nc`.
2. **The aggregation step never read it.** `obl029_04_zone_sst_anomaly.py` rolls cells to zones and
   writes nine anomaly columns. `grep n_days` on that script returns **nothing** — it was not dropped
   as a judgement call, it was never seen.
3. **The seal could not ask for it.** `required_columns` is the nine anomalies for the CSV, and **`[]`
   for the `.nc` that actually holds `n_days`.**
4. **No gate check covers it.** The eight checks are SHA, row count, date span,
   column-present-and-not-all-empty, physical range, non-degeneracy, min-schema, disclosure. **A value
   built from 16 days of 28 satisfies every single one.** The row exists, the date is in range, the
   column is present, the number is physically plausible and not degenerate.

## What it cost, measured

107 of 534 months short · 1,195 days missing of 16,238 · 15 duplicated · three near-empty months.
**1982-02 reads `0.4757` for one zone, built from 16 days of 28.** The one genuinely empty month is
honestly `NaN` — **the dangerous rows are the ones that look like numbers.** And **65 of the 360
month-years in the 1991–2020 baseline are short**, so the climatology the anomalies are measured
against is itself partly built on partial months.

## A naming trap that helped it hide, worth more than the bug

`timeseries-report`'s own invariant announces **"COMPLETENESS IS A GATE, NOT AN ASPIRATION"**. That
means *every declared variable got a section*. It does **not** mean the data covers its periods. Two
meanings of one word inside one apparatus, and the weaker one is the one we guarantee loudly. The
report also files `n_days` under `BOOKKEEPING` — defensible, since you would not run stationarity on a
day count — but the consequence is that **the only column holding the answer is the one column the
report sets aside.**

## The fix — check 9, and the reason it is safe

- **Absent count column → DISCLOSED in `checks_not_possible`, never failed.** No existing seal changes
  status. This is the whole backward-compatibility story.
- **Present → rows below the file's maximum count are REPORTED as incomplete.** A short period can be
  legitimate; it is not the gate's business to forbid it, only to stop it being invisible.
- **Exactly one hard failure: a non-null value on a row declaring ZERO inputs.** A quantity computed
  from no observations is not a measurement, and I could not construct a defence for it.

**Both controls tested.** A planted value-on-zero-inputs row FAILS with a precise message; the same
file with that value blanked PASSES and merely reports the short rows. **Regression sweep over every
sealed snapshot on this machine: 18 PASS, 12 payload-absent, 1 failure — and that one
(`snap-obl023-seas5-20260629`) fails IDENTICALLY under the git copy of the pre-change gate**, on the
pre-existing range and degeneracy checks. **Zero passed-then-failed**, which is the A-21 standard and
the only evidence I would accept from someone else.

## Doctrine added — the part that actually prevents recurrence

In `data-sealing/SKILL.md`: **an aggregate carries the count of inputs each row was built from, and
`required_columns` names it.** The gate can only check a count that someone emits. Daily→monthly,
cells→zone: emit `n_days` / `n_obs` beside the value.

**And for consumers, the line I would most like read: a gate PASS does not mean the periods are
whole.** It now says so itself, on every tabular file that lacks a count column.

## What this does NOT do

**obl029 is not re-sealed.** A seal is never mutated, the data is not wrong, and the registry now
carries the full caveat instead. Nothing in anyone's published work moves on this. **mini:** the
caveat is on the registry page against that snapshot id — that is the one thing to know; the
completeness analysis itself was yours and Col. Raj's and I have not touched its conclusions.

— lofra-admin
