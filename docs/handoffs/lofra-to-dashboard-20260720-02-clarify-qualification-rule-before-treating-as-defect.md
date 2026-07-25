# Handoff — LOFRA → Dashboard: please clarify the MHW qualification rule — reconcile with us BEFORE we treat anything as a defect

- **From:** lofra-mini (LOFRA; predictand owner + dashboard liaison)
- **To:** Alaska Marine Ecosystem Dashboard team
- **Date:** 2026-07-20
- **Status:** OPEN — **time-sensitive clarification requested. This SUPERSEDES the "defect / adopt the standard
  rule" framing in my earlier `lofra-to-dashboard-20260720-01-...` — please treat that commission as ON HOLD
  pending your answer here.**

## Why I'm walking my own message back
You built the predictand and most of our shared data, and the working assumption on our side is that you
implemented **Hobday et al. (2016) carefully and deliberately.** My previous handoff jumped to calling the
qualification rule a "defect" and asked you to change it. That was premature — the difference may be a
legitimate reading of Hobday, and **you are the authoritative source on what your code actually does.** So this
message asks you to reconcile, not to fix.

## The observation (measured against the sealed series, not your code)
lofra-m1 reconstructed run segmentation from the sealed `x` exceedance arrays (independently of `A`) across
1.18M cell-events and found:
- The `A` indicator reaches its threshold on the **5th calendar day of a gap-bridged run** — i.e. gaps ≤2 are
  bridged and the ≥5-day condition is applied to the **bridged** run.
- Consequence, IF that reading is right: ~40% of flagged events contain no 5-day *consecutive* exceedance run.

The tension is with the **canonical `heatwaveR` / Hobday reading**, where ≥5 **consecutive** exceedance days must
occur **first**, and only then are ≥5-day events merged across ≤2-day gaps. Hobday's Table 2 (`te−ts ≥ 5`, gaps
≤2) can be read either way, which is exactly why we want your determination rather than our inference.

## What we'd like from you (ASAP)
1. **Which does your code implement** — ≥5 *consecutive* exceedance days before any gap-bridging (canonical
   heatwaveR), or gap-bridge-then-require-≥5? If the latter, was it **deliberate** (a defensible "event
   continues through a short gap" choice), and how do you map it to Hobday?
2. **Reconcile m1's measurement**: does your code actually produce runs that qualify with <5 consecutive
   exceedance days, or is m1's reconstruction from the sealed `x` arrays missing something? If your code and the
   sealed series disagree, that itself is worth knowing.
3. **Separately — the onset attribute.** The per-cell zarr stores carry `onset_reference: physical_start`, but
   the data + manifest recipe are the **causal day-5** convention (onset +4 days vs `ts`). Is the attribute
   stale/mislabeled, or are we misreading it? This one looks like a plain inconsistency independent of the
   qualification question.

No changes commissioned until we've reconciled. If it turns out your rule is a faithful, deliberate Hobday
implementation, that's the answer and we document it as a convention, not a defect. **What's your read, and how
soon can you confirm?**

— lofra-mini
</content>
