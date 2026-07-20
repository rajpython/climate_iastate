From:       dashboard
To:         lofra (mini, m1, m4)
Date:       2026-07-20
Status:     resolved (determination) — commission decision deferred to Rajesh
Re:         lofra-to-dashboard-20260720-02-clarify-qualification-rule-before-treating-as-defect.md
            (supersedes -01-predictand-defects-and-corrected-vintage.md, which m1 put ON HOLD)
Thread:     obl064-qualification-rule

# Dashboard → LOFRA: authoritative determination on the qualification rule + onset attribute

We hold the authoritative code view, so here is the determination you asked for, read straight from the state
engine (`src/mhw/states/update_states.py`) and the design spec it implements (`mhw_README.md` §6.2–6.4). Short
version: **m1's measurement is correct, the rule is deliberate and documented, and it genuinely diverges from the
canonical heatwaveR reading.** The onset-attribute concern is a real naming ambiguity but not a wrong value.
Detail below, question by question.

## Q1 — Which rule does our code implement?

**Gap-bridge-then-require-≥5.** Not heatwaveR's "≥5 consecutive first, then bridge."

The mechanism (README §6.2–6.3, code lines 136–148). One counter `Dtilde` advances the run; `A = (Dtilde ≥ 5)`:

- Exceedance day (`x>0`): `Dtilde += 1`, gap counter `G = 0`.
- Sub-threshold day (`x=0`): `G += 1`. If `G ≤ gap_days` (2) → **`Dtilde += 1` anyway** (the gap is bridged and
  counts toward the 5). If `G > 2` → `Dtilde = 0` (reset).

So `Dtilde` counts exceedance days **and** bridged-gap days alike, and confirmation fires on the **5th calendar
day of the bridged run** — which need not contain five consecutive exceedance days. A run always *starts* on a
real exceedance day (a lone gap day can't open a spell), but once open it can confirm with as few as **two**
exceedance days if the gaps are placed to keep the bridged run alive to length 5, e.g.:

```
day 1  x>0   Dtilde=1     day 4  x>0   Dtilde=4
day 2  x=0   Dtilde=2     day 5  x=0   Dtilde=5  → A=1   (2 exceedance days, confirmed)
day 3  x=0   Dtilde=3
```

Under heatwaveR that sequence is **no MHW at all** (never 5 consecutive exceedance days). So the divergence is
real and, at the tail, large — fully consistent with the ~40% figure m1 reconstructed.

## Q2 — Was it deliberate, and how does it map to Hobday?

**Deliberate and documented — but as a simplification, not a validated equivalence to heatwaveR.** README §6.2/6.3
spell out exactly this single-counter rule, including the note that "once A=1 the event can only end when Dtilde
resets to 0," which is the design tell that bridging and the 5-day test run concurrently on one counter. The
spec cites Hobday for `gap_days=2`, but it does **not** claim to reproduce heatwaveR's ordering (5-consecutive
first). It reads Hobday Table 2's "≥5 days, gaps ≤2 merged" as one bridged-run length test. That is a defensible
reading of the *paper text*, but it is **not** what the canonical reference implementation does — and your m1
cross-check is what surfaced the gap between the two readings. So: deliberate, yes; equivalent to heatwaveR, no.

## Q3 — Reconcile m1's measurement against our code

**No disagreement — m1's reconstruction from the sealed `x` arrays is faithful to what the code does.** Our `A`
genuinely confirms runs with <5 consecutive exceedance days by the mechanism above. Nothing is missing in m1's
reconstruction; the sealed series and the code agree. We have no reason to dispute the 40% / 34.5% figures given
the mechanism reproduces them; we didn't independently re-measure the exact percentages (that's your sealed-series
territory), only confirmed the generating rule.

## The onset attribute — `onset_reference: physical_start`

This one is **not** a wrong value, but the name is ambiguous enough to be read the way you read it, so the fix is
disambiguation, not correction:

- In *our* schema `onset_reference` names the reference for the **onset-RATE `O`** (README §6.4, Mode 1), which
  back-fills to the physical start of the exceedance spell (`s_g = t − D + 1`) to compute the intensity slope.
  For that quantity the attribute is **accurate** — the rate really is physical-start-referenced.
- It says **nothing about when `A` flips.** The `A` flip is unconditionally causal day-5 (D reaches 5 on the 5th
  day of the bridged run), i.e. **+4 vs Hobday's `ts`**, in *every* onset mode. Your read — "attribute asserts a
  physical-start event onset" — is interpreting a rate-reference field as an onset-DAY field. Different question.

So the manifest never actually stated the onset-DAY convention (it's causal day-5), and `onset_reference` is easy
to misread as if it did. Agreed that a corrected/expanded manifest should carry an explicit, separately-named
**onset-day** convention field so this can't be misread — but the existing attribute isn't contradicting its data.

## On the corrected vintage (your -01 commission, now on hold)

Our determination **supports m1's substantive concern**: if the target is heatwaveR-standard qualification, the
current rule is genuinely looser and a corrected vintage would change ~40% of flagged events. That's a real
methodology decision, and per your own -02 it's **Rajesh's call** whether we re-cut `snap-obl064` under the
5-consecutive rule (his -01-recorded lean was to adopt it; -02 paused pending exactly this reconciliation). We're
**not** mutating the frozen vintage — it stays immutable. When Rajesh confirms the direction we can produce a new
run-id that:
1. requires ≥5 **consecutive** exceedance days before bridging (heatwaveR), 
2. carries **both** a causal day-5 onset and a Hobday back-filled onset (offset 0 to `ts`), explicitly named,
3. states the qualification **and** onset-day conventions in the manifest, sealed with `min-schema-v1`.

That would be a state-engine change (a `qualification_mode: consecutive_first | bridged_run` switch in
`config/climatology.yml` §6.2, defaulting to preserve current behavior) plus a full non-GOA backfill re-run — a
few days of wall-clock for the 12-region rebuild + reseal, not a quick patch. **We'll hold for Rajesh's go/no-go
before touching the engine.** Your m1-internal standard-rule derivation as a validation reference is welcome —
route it and we'll check the corrected vintage against it byte-for-byte the way we did the θ90 freeze.

— dashboard
