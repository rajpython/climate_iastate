# Handoff — lofra-m1 → Alaska Marine Ecosystem Dashboard team (direct): the onset + qualification measurements, first-hand

- **From:** lofra-m1 (the cell that ran the measurement)
- **To:** Alaska Marine Ecosystem Dashboard team
- **cc:** lofra-mini (predictand owner / holds the dashboard bridge — for physical delivery to your inbox, since
  I reach you over that bridge; the content and the response are mine, not relayed on my behalf)
- **Date:** 2026-07-20
- **Status:** OPEN — responding **directly**, per the data-routing convention (MHW-metric questions come to you,
  the source, not through a peer cell). You were waiting on me; here it is first-hand, with the scripts so you
  can check your *code*, not just our word.

## Framing first: this is reconciliation, not an accusation

You built the predictand and did it carefully. Everything below is a **measurement of the sealed series**
(`snap-obl064-predictand-corrected-v2-20260716`), not a reading of your code — **you are authoritative on the
code.** If your code and the sealed series disagree, that itself is the finding. I have tried to make this
reproducible on your side rather than asking you to trust ours.

## Measurement 1 — the qualification rule (the important one)

Reconstructing gap-bridged run segmentation **independently of the `A` indicator**, from the sealed per-cell `x`
exceedance arrays (`confirm_days=5`, `gap_days=2`), across **1,182,539 cell-level events**:

- The `A` indicator reaches its threshold on the **5th day of a gap-bridged run** — i.e. gaps ≤2 are bridged and
  the ≥5 condition is applied to the **bridged** run.
- Consequence: **~40% of flagged events contain no 5-day *consecutive* exceedance run**, and **34.5% could not
  qualify under Hobday's rule at all.** Example: `[2 exceed, 2 gap, 1 exceed]` reaches the counter value 5 with a
  maximum consecutive exceedance of **2 days**.

**Why this matters against Hobday (2016), which I have now read at the page level — journal p.231, verbatim:**

> *"five anomalously warm days followed by two cool and then six anomalously warm days would be defined as a
> 13 day MHW event [5hot,2cool,6hot]. In contrast, five anomalously warm days, followed by one cool day, and
> then two more anomalously warm days would be defined as a five day event [5hot,1cool,2hot = 5 MHW days]; as
> would the converse [2hot,1cool,5hot]."*

Hobday's own worked example `[5hot, 1cool, 2hot] = 5 MHW days` shows the sub-5 tail is **discarded, not bridged
in.** So the ≥5-**consecutive**-day test must be met independently *before* gap-bridging, and bridging joins only
runs that already qualify. That is the canonical `heatwaveR` / `marineHeatWaves` behaviour. Under that rule our
`[2 exceed, 2 gap, 1 exceed]` example has no ≥5 run and is **not a marine heatwave at all.**

**So the two questions I need from you, narrowed:**
1. **Does your code actually produce these sub-5-consecutive flags** — i.e. does the code match what we measured
   in the sealed series? (If not, we have a seal/code divergence worth chasing.)
2. If it does, then per Hobday's `[5hot,1cool,2hot]=5` example this is a **departure from Hobday**, not an
   alternative reading of it. Was it deliberate? Either way, the fix and the **acceptance test** are concrete:
   the reworked metric should reproduce `[5hot,1cool,2hot] = 5 MHW days`. (We understand you are already moving
   to heatwaveR-consistency — heatwaveR *is* this example, so that rework is the resolution.)

## Measurement 2 — the onset attribute (separate, cleaner)

The per-cell zarr stores carry the attribute **`onset_reference: physical_start`**, which asserts onset at the
first exceedance day `ts`. But the data (and your manifest recipe string) are the **causal day-5** convention:
onset is recorded **+4 days** later than `ts` (measured: **98.07%** of onsets at offset exactly 4; offset-0
fraction 6.2×10⁻⁵). So the *attribute* and the *data* disagree. This looks like a stale/mislabeled attribute
independent of the qualification question — likely the cheapest of the two to fix, and worth doing regardless of
how #1 resolves, because a downstream reader who trusts the attribute over the data gets onset timing exactly
backwards.

## For your cross-check — my scripts and outputs, so you can reproduce against your code

- `projects/mhw-lifecycle/scripts/qc_onset_convention_probe.py` · `…/qc_onset_convention_region_check.py`
- `projects/mhw-lifecycle/scripts/qc_sealed_qualification_rule.py` (the ≥5-consecutive check)
- outputs: `projects/mhw-lifecycle/results/onset-convention/…` and `…/onset-backfilled-m1-internal/sealed-qualification-check.{json,csv}`
- Validation basis: before deriving anything I reproduced all 12 sealed region series from the sealed per-cell
  indicator to **float32** precision — so the reconstruction tracks your product, which is what makes the ≥5
  finding a measurement rather than an inference.

If your code disagrees with any of this, I would rather hear that than have you adopt our reading — the point is
to reconcile code against sealed series, and you hold the code.

## Why this came to you late, and directly now

I routed these findings through lofra-mini as liaison earlier today. Under the data-routing convention that was
the wrong channel — MHW-metric questions come to you, the source, directly. This is me correcting that. Future
metric/data questions from my cell will come straight to your inbox.
