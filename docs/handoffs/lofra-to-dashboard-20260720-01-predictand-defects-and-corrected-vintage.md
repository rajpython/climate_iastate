# Handoff — LOFRA → Dashboard: two confirmed defects in obl064, and a commission for one corrected authoritative vintage

- **From:** lofra-mini (LOFRA; predictand owner + dashboard liaison)
- **To:** Alaska Marine Ecosystem Dashboard team
- **Date:** 2026-07-20
- **Status:** OPEN — action requested (correct at source in a new vintage; existing freeze never mutated)

## Context
Reading Hobday et al. (2016) in full for the first time surfaced two defects in `snap-obl064` (your frozen
9-zone predictand). Both were **measured against the sealed series** (lofra-m1, verified independently across
1.18M cell-events), not inferred from code. We escalated to Rajesh; his decision is below.

## Defect 1 — onset metadata contradicts the data
The per-cell zarr attribute `onset_reference: physical_start` **asserts a physical-start (back-filled) onset**,
but the data (and the manifest recipe string) are the **causal day-5** convention: `A` flips on at the 5th day
of a gap-bridged run, first 4 days `A=0`. So onset is **+4 days vs Hobday's `ts`**, and the attribute states the
opposite. (A checksum can't catch a file that misdescribes its own semantics — hence a manifest field must never
contradict the data.)

## Defect 2 — qualification rule is looser than Hobday (larger, upstream)
The counter reaches 5 on the **5th calendar day of a gap-bridged run** — i.e. gaps ≤2 are bridged **then** ≥5 is
required. The standard reference implementation (`heatwaveR` / Hobday's `marineHeatWaves`) requires **≥5
*consecutive* exceedance days *before* bridging**. Consequence on the sealed series: **40% of flagged events
have no 5-day consecutive exceedance run; 34.5% would not qualify as a MHW under Hobday at all.** The manifest
`confirm_days=5` reads as Hobday-standard, but the implemented rule is looser.

## Rajesh's decision → commission
**Adopt the standard Hobday rule.** Please produce **one corrected authoritative vintage** (new run-id; the
existing freeze is immutable):
1. **Qualification:** ≥5 *consecutive* exceedance days *before* gap-bridging (heatwaveR-standard).
2. **Onset:** carry **both** a causal day-5 onset **and** a Hobday-standard back-filled onset (offset 0 to `ts`),
   clearly named.
3. **Metadata:** correct the onset attribute, and **state the qualification *and* onset conventions explicitly**
   in the manifest — no attribute may contradict the data.
4. **Seal** with the shared `min-schema-v1` tooling (`size_bytes`, `dims`, `lon_is_contiguous`, `source`,
   `schema_version`); QA gate exit 0.

**Cross-check available:** lofra-m1 has an *m1-internal* derivation from your sealed `x` exceedance arrays
(standard rule + back-fill) that **reproduced the 12 obl064 region series to float32** before applying the
correction — happy to route it as a validation reference so your corrected vintage can be checked against it.

**One question:** was gap-bridging-before-5 a deliberate design choice on your side? You hold the authoritative
code view. Either way the corrected vintage adopts the standard rule per Rajesh.

**Why the priority:** this gates mini's return to the v15 paper (v15 re-verifies on the corrected predictand),
and it's the shared target all three cells build on — so it's first in the queue. **What's your timeline?**

— lofra-mini
</content>
