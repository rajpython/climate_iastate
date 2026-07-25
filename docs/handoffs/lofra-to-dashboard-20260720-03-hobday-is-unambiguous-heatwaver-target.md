# Handoff — LOFRA → Dashboard: correcting my own framing — Hobday is NOT ambiguous; the target is heatwaveR-consistent (Rajesh-directed)

- **From:** lofra-mini (LOFRA; predictand owner + dashboard liaison)
- **To:** Alaska Marine Ecosystem Dashboard team
- **Date:** 2026-07-20
- **Status:** OPEN — **supersedes the "may be a legitimate reading of Hobday" premise in
  `lofra-to-dashboard-20260720-02`. Please answer on this sharper premise, not that one.**

## I over-hedged, and I'm correcting it against my own record
My previous note asked you to reconcile on the premise that gap-bridge-then-≥5 *might be a valid reading of
Hobday*. **It isn't, and I verified it against the paper myself** (read Hobday et al. 2016 p.231 directly, not
relayed). The worked examples on that page foreclose the ambiguity that Table 2's terse formula (`te−ts ≥ 5,
gap ≤ 2`) leaves open when quoted alone:

> *"five anomalously warm days, followed by one cool day, and then two more anomalously warm days would be
> defined as a **five day event [5hot,1cool,2hot = 5 MHW days]**; as would the converse [2hot,1cool,5hot]."*
> — and `[5hot,4cool,6hot]` → **two separate events** (a 4-day gap isn't bridged).

So Hobday requires **≥5 *consecutive* exceedance days per run, independently — and gap-bridging joins only runs
that already qualify.** A sub-5 run is never added in. That is exactly the `heatwaveR` / `marineHeatWaves`
behaviour Hobday co-authored. The paper is not ambiguous; one line of one table, lifted out, is terse.

## The resolution is already set: heatwaveR-consistent (Rajesh-directed)
Rajesh has directed the corrected metric to be **heatwaveR-consistent** — which, per the above, *is* Hobday.
So this is not a reading for us to adjudicate; it's a target to hit. Two concrete anchors for your rework:
- **Acceptance test:** the corrected metric must reproduce `[5hot,1cool,2hot] = 5-day event` (trailing 2-day run
  discarded), and must flag `[2hot,2cool,1hot]` (max 2 consecutive) as **not a MHW**. The current sealed series
  does the opposite (m1 measured it flags with a 2-day max run) — that's the behaviour to change.

## Two things I'd still value from you (for understanding, not to adjudicate)
1. **Does your *code* actually produce the sub-5-consecutive flags we measured in the sealed series** — i.e.
   does the code match the series? If code and sealed series disagree, that's its own finding worth knowing.
2. **Was the gap-bridge-then-≥5 behaviour deliberate** ("event continues through a short gap")? Either way it's
   labelled *a departure from Hobday* in the record, not *a reading of Hobday* — but knowing the intent helps.

## Separately — the onset attribute (unchanged by any of this)
`onset_reference: physical_start` in the per-cell zarr contradicts the causal day-5 data (onset +4 vs `ts`). It's
a plain label/data mismatch, independent of the qualification question — please correct it in the same reworked
vintage and state the onset convention explicitly in the manifest.

**Why the priority:** this predictand gates mini's return to v15 and all three cells build on it. **What's your
timeline for the heatwaveR-consistent rework?** m1 holds a heatwaveR-consistent derivation from your sealed `x`
arrays (float32-reproducing) that you're welcome to use as a cross-check.

— lofra-mini
</content>
