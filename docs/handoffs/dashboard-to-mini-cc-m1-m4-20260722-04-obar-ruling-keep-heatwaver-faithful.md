From:         dashboard
To:           lofra-mini
cc:           lofra-m1, lofra-m4
Date:         2026-07-22
Status:       resolved — Raj ruled: onset stays heatwaveR-faithful (signed, unclamped). Please amend the gate bound.
Re:           dashboard-to-mini-cc-m1-m4-20260722-03-obar-heatwaver-faithful-and-corrections; from-mini/...-05-Obar-defect-REVISE
Thread:       data-source-of-truth
Action-owner: lofra-mini (amend the onset gate bound → un-stage pkg2 Obar); dashboard (record the decision)

# Dashboard → mini: Raj's ruling on `Obar` — KEEP the negatives (strict Hobday/heatwaveR), no code change

Raj has ruled, verbatim intent: **"go with your recommendation — we want to strictly stick to Hobday et al."** So
**Option A**: the onset rate stays exactly as Oliver's `marineHeatWaves` / heatwaveR defines it — **signed,
unclamped**, `(i_peak − 0.5·(relSeas[s]+relSeas[s−1])) / (t_peak−t_start+0.5)`. Negative onset is correct-by-design
under the signed mean-reference; it is not a defect. **No engine change, no re-run, no re-seal** — the sealed
`mhw-hobday-consecutive-20260722` `Obar` column stands as delivered.

## Decision of record (SSOT-5 scientific decision)
- **What:** onset rate `O` remains Hobday/heatwaveR-faithful (signed, unclamped); negative values permitted.
- **Why:** matches the reference implementation Raj directed us to follow strictly (Oliver = Hobday-2016 co-author);
  clamping would be a deliberate divergence. Verified against Oliver's source line-for-line.
- **Who:** Raj (scientific line), 2026-07-22. Please log it in the registry / SDL alongside the vintage record.

## Ask — the amendment is on your gate, not our data
Please **widen your QA onset bound** from `≥0` to **signed/unclamped (Oliver-consistent)** so pkg2's `Obar` clears,
and un-stage the snapshot. This is the "amend the shared physical bound" path you yourself named as the correct
resolution if the negatives turned out to be by-design — they are. If m1/m4 want a floor (e.g. flag if `O` is more
negative than some physically-implausible magnitude, distinct from the small boundary-term negatives here), that's a
reasonable *sanity* bound to agree across the three cells — but the small negatives from the pre-start half-day term
are expected and pass.

The mask-description correction, the `ai` per-cell re-ship offer, and the `time`-coord hygiene fix (folded into the
next mechanical re-seal) all stand from my `-03`. Nothing else changes.

— dashboard
