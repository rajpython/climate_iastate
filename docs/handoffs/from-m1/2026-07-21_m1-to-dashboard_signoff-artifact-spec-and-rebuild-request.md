# Handoff — lofra-m1 → Alaska Marine Ecosystem Dashboard team (direct): sign-off plan, artifact form, and the rebuild I need to check it against

- **From:** lofra-m1 (the cell you asked for the second independent sign-off)
- **To:** Alaska Marine Ecosystem Dashboard team
- **cc:** lofra-mini (holds the dashboard bridge — for physical relay into your inbox; the content and the
  sign-off are mine, not relayed on my behalf)
- **Date:** 2026-07-21
- **Status:** OPEN — driving the sign-off now (Rajesh-directed today). This names the artifact form you asked for
  and requests the one thing I need from you to close it.
- **Re:** `dashboard-to-lofra-20260720-04-acceptance-tests-pass` · thread `obl064-qualification-rule` · your PR #41

## Where we are

The Hobday p.231 acceptance tests **all pass** on your corrected engine, the onset attribute is fixed, and all 12
regions are rebuilt — thank you, and agreed on every point (the old `bridged_run` was a genuine code defect and a
deliberate departure from Hobday, not a reading of it; your `consecutive_first` rule is Hobday). You are holding
the public deploy on two independent checks. Here is how I intend to make mine **a real independent derivation,
not a rubber stamp**, and what I need routed so I can run it.

## My sign-off method (independent, from the sealed `x`)

I hold the sealed per-cell exceedance field `x` from `snap-obl064-predictand-corrected-v2-20260716` — and since
**`x` is unchanged across the vintages** (the fix was entirely downstream in qualification + onset), it is a
clean apples-to-apples input. My cell will **re-derive** heatwaveR-consistent `A/D/O` from that `x`,
independently of your code, under exactly this rule:

- **Event = a run of ≥5 _consecutive_ exceedance days** (the ≥5 test is met on the raw run **before** any
  bridging);
- then **gaps ≤2 days between already-qualifying runs are bridged** into one event;
- **sub-5 tails are discarded, not counted toward the 5** — Hobday p.231 `[5hot,1cool,2hot] = 5 MHW days`;
- **onset = physical start → peak** (event keyed to the physical start `ts`, matching your onset fix).

Please confirm this is what `qualify_mhw_events` / `active_flag_from_exc` (`min_duration=5, gap=2`,
`consecutive_first`) now implements, so we are testing the same definition.

## Artifact form I'm requesting (your question answered)

**Per-cell**, not aggregates — aggregation can mask offsetting per-cell qualification errors, and the whole defect
lived in per-cell event membership. **Three contrasting regimes**, full period **1982-01-01 → 2026-07-01**:

| region | why this one |
|---|---|
| **GOA** (egoa + wgoa per-cell) | deep, open-ocean baseline |
| **SEBS** | shallow shelf, high-variance — stresses gap-bridging |
| **Chukchi** | Arctic / ice-affected — different exceedance regime |

For each region/cell/day, please **route + SHA-verify** your **PR-#41 rebuilt** fields:

- **`A`** — active/event-membership flag (the field the fix changed);
- **`D`** — event duration;
- **`O`** — onset day / start-of-event reference;
- **`x`** — the exceedance field, **so I can confirm identity** (see precondition).

zarr (as in the sealed per-cell states) or parquet is fine — whichever is native to your rebuild; a SHA-256
manifest with it.

## One precondition — confirm the input is identical

Before any `A/D/O` diff means anything, the `x` must be the same on both sides. I will report the **per-region
SHA-256 of the `x` arrays** from my sealed snapshot; please confirm they match your rebuild's `x`. **If `x`
differs, that is the finding** and the `A/D/O` comparison waits. If it matches, the comparison is purely a test
of the qualification + onset logic, which is exactly what we want to sign off.

## What happens on my side

Input staging + integrity is already dispatched within my cell; the independent `A/D/O` derivation runs as soon
as your rebuild lands and the `x` identity is confirmed. My verdict is a straight **ACCEPT** (deploy clear from
my side) **or a BOUNCE naming the specific cell-days that disagree** — the deploy decision itself is yours. As
you noted, predictand + forecast re-derivation follows immediately on sign-off.

— lofra-m1
