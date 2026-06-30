# Chukchi vs Beaufort modelled bottom temperature — investigation

> **UPDATE 2026-06-28 — superseded in part by `chukchi-beaufort-audit-memo.md`.** A follow-up audit
> (annual 1993–2024 series, formal Simpson decomposition, bin-sensitivity, shallow- and deep-bin
> spatial detail) **confirms the core composition finding** but **corrects three claims below**:
> (1) 2024 was *not* an atypically cold Chukchi year (rank 13/32) — it was a *moderately cool Chukchi
> + warm Beaufort* coincidence (amplified by an Aug-only first cut); (2) the matched-depth crossover
> is **~60 m**, not 100 m — Chukchi warmer only in the **upper shelf (<~60 m)**, Beaufort warmer
> **>60 m** (the 6-bin "50–100 m Chukchi warmer" was a coarse-bin artifact); (3) the 100–200 m
> reversal is **"Chukchi is anomalously cold" (canyon winter water), not warm Atlantic Water** — the
> Atlantic attribution is **unsupported** (both regions near-freezing there; no warming toward
> 200 m). See the memo for evidence.

**Date:** 2026-06-28 · scratch/side investigation (not a dashboard deliverable).
**Question:** the modelled Arctic *shelf-mean* bottom temperature came out **Beaufort ≳ Chukchi**,
which looks wrong — the Chukchi receives warm Pacific inflow, so why would the Beaufort be warmer?

## Methodology checks demanded (and why they mattered)

1. **Cell counts ≠ area.** The first explanation leaned on "% of cells" and depth *percentiles*.
   The shelf mean must be area-weighted: T̄ = Σ Aᵢ Tᵢ / Σ Aᵢ, not (1/N) Σ Tᵢ.
2. **The depth-floor experiment can mislead (Simpson's paradox).** If warm cells are shallow and
   cold cells deeper, raising a depth floor lowers the mean regardless of whether the shallow
   warmth is physical. The right diagnostic is **T_b(z)** — bottom temperature *by depth bin* for
   **both regions** side by side.

### Verification of the area question
- Grid is regular 0.25° (rectilinear NEP `regrid` product → block-averaged to 0.25°); cells are
  cos-lat weighted (~15–18% smaller at the northern edge of each region).
- The regional **means were already area-weighted** (`cell_area_km2` in `wmean`). ✓
- Within each small region, **area-weighted ≈ cell-count** weighting — depth percentiles identical
  both ways (Chukchi 39/47/53 m; Beaufort 20/40/58 m). So cell-counting wasn't distorting the
  *depth distribution*; the real issue was (2), the composition/Simpson effect.

## Result — Jul–Sep climatology 2014–2024, area-weighted

Whole-shelf area-weighted mean bottom temperature:
- **Chukchi +1.49 °C** (259,070 km²) · **Beaufort +1.67 °C** (57,981 km²) — *nearly equal* (not the
  −0.10 vs +1.86 single-year 2024 figures; **2024 was an atypically cold Chukchi year** — the
  single-year comparison was the original error).

**T_b(z) — Chukchi is WARMER at matched depths (except the deepest):**

| Depth bin | Chukchi T_b (°C) | Beaufort T_b (°C) | Chukchi area % | Beaufort area % |
|---|---|---|---|---|
| 0–10 m   | **8.62** | 6.87 | 2.3  | 10.2 |
| 10–20 m  | **6.65** | 3.43 | 6.1  | 15.2 |
| 20–30 m  | **4.40** | 2.10 | 7.1  | 12.4 |
| 30–50 m  | **1.02** | 0.81 | 48.6 | 28.7 |
| 50–100 m | **0.26** | −0.02| 34.5 | 19.9 |
| 100–200 m| −1.12    | **−0.30** | 1.5 | 13.6 |

(Plot: `chukchi_beaufort_Tbz.png`; per-bin: `chukchi_beaufort_depthbins.csv`; per-cell:
`chukchi_beaufort_cells.csv`.)

## Conclusion — the original "Beaufort warmer" was a composite of two artifacts

1. **At matched depths the Chukchi is warmer than the Beaufort** at 0–100 m — consistent with the
   user's intuition. The whole-shelf *mean* comes out ~equal only because of **depth composition**
   (Simpson's paradox): the broad Chukchi is dominated by its **cold mid-shelf** (83% of area at
   30–100 m), while the narrow Beaufort has a much larger **warm shallow** fraction (38% < 30 m).
   Averaging across two different depth distributions makes the Beaufort *look* equal/warmer.
2. **The single-year (Aug 2024) comparison was misleading** — it showed Beaufort warmer at all
   depths; the 2014–2024 climatology reverses it. High Chukchi interannual variability.
3. The **depth-floor "fix" would have been wrong** — it lowers the mean by chopping warm shallow
   cells, masking a composition effect rather than correcting an artifact.

## Literature grounding

- **Pacific Summer Water (PSW)** — warm — flows over the **Chukchi** shelf warming surface *and*
  bottom, then exits via Herald Valley / Barrow Canyon as shelf-break jets; the Beaufort gets only
  diluted downstream intrusions. So the Chukchi being warmer at matched (0–100 m) depths is
  expected. ([Nature Sci. Rep. 2024](https://www.nature.com/articles/s41598-024-81994-8);
  [UAF Chukchi–Beaufort study](http://research.cfos.uaf.edu/chukchi-beaufort/))
- **Atlantic water at depth** intrudes onto the Beaufort outer shelf/slope (warm, ~100–200 m+),
  while the Chukchi's 100–200 m is cold dense winter water draining the canyons — matching the one
  bin (100–200 m) where the Beaufort is warmer. ([Bourke 1976](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/GL003i010p00629))
- Representative *cold* shelf bottom water (winter water, −0.4 to −1.6 °C) sits at the mid/deep
  shelf — our 50–200 m bins (Chukchi 0.26 / −1.12; Beaufort −0.02 / −0.30) are consistent; the
  shallow bins are summer-warmed. ([Pacini et al. 2019](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019JC015261))

**So the model's cross-shelf structure is physically sensible** (PSW-warm Chukchi at depth,
Atlantic-warm Beaufort at depth) — a weak validation-by-physics for the otherwise-unvalidated MOM6
Arctic. The shallow summer warmth (8–9 °C at <10 m) is plausible for nearshore August but should
still be treated cautiously (coarse model, possible over-mixing — not verified against in-situ).

## Implications for the dashboard
- **Do NOT apply a min-depth floor** — it would mask a composition effect, not fix an artifact.
- The dashboard shows each Arctic region's series **separately** (no head-to-head), so no false
  cross-region comparison is presented. The per-region continuous series are fine.
- If a cross-region or interpretive note is ever added: compare **at matched depths** (T_b(z)), and
  state that whole-shelf means reflect each region's depth distribution.
- Caveat unchanged: Arctic bottom is **model-only / unvalidated in-region**; the matched-depth
  agreement with PSW/Atlantic physics is reassuring but not a substitute for observations.
