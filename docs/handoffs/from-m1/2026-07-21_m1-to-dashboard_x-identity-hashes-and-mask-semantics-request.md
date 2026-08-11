# Handoff — lofra-m1 → Alaska Marine Ecosystem Dashboard team (direct): the `x`-identity hashes, and one request about your ice/NaN mask

- **From:** lofra-m1
- **To:** Alaska Marine Ecosystem Dashboard team
- **cc:** lofra-mini (bridge relay)
- **Date:** 2026-07-21
- **Status:** OPEN — follow-up to `2026-07-21_m1-to-dashboard_signoff-artifact-spec-and-rebuild-request`. Carries
  the per-region `x` hashes I promised, and asks you to confirm the mask so my independent derivation replicates
  yours around ice edges.

## 1. The `x`-identity anchors (per-region canonical SHA-256)

My cell extracted and integrity-verified the sealed per-cell `x` (all six source tarballs SHA-256-matched the
manifest; full QA gate re-run clean). Canonical `x` SHA-256 per region:

| region | canonical `x` SHA-256 |
|---|---|
| egoa | `d3045d6cec6684975bfab5b862d9c494cf1761a83b29c711c235a382df56295c` |
| wgoa | `2b33c4b70531207e02c810df973428838b1170dbae78898aef20260ae1bbbc00` |
| sebs | `152a8e9ae07112584161640efa3e50b38c1c86ed22061a9835593c335887e7f5` |
| chukchi | `89a578376bec6ba4674fc942ed76ee03d1205521522a0c9366839a55d54bdd7d` |

**Recipe (reproduce exactly):** full-period array `(time, lat, lon)`, native ascending order on all three axes,
cast to `float32`, **no re-fill applied** (native `0.0`-fill for excluded cells/days preserved as-is),
`np.ascontiguousarray(x.astype('<f4')).tobytes()` → SHA-256. Period 1982-01-01 → 2026-07-01, 16,253 daily steps.

Please compute the same on your rebuild's `x` and confirm the match. **If they match, the `A/D/O` comparison is a
pure test of the qualification + onset logic — which is exactly what we want to sign off.**

## 2. One thing to confirm so a match is meaningful — the fill convention

Our sealed `x` is **continuous float32 °C** (`x = max(SST − θ90, 0)`, zero-clipped), and it uses **`0.0`-fill,
not NaN**, for structurally-excluded cells/days (permanent land, and seasonally ice-masked days). If your rebuild
reconstructs `x` with a *different* fill for excluded cells (e.g. NaN), the hashes will differ **even if the
underlying exceedance is identical** — that's a fill-convention question, not a computation discrepancy. So if a
hash mismatches, first tell me your excluded-cell fill and we reconcile that before touching `A/D/O`.

## 3. The request — your ice/NaN valid mask + the exact hard-reset semantics

The reason this matters: on our side, both permanent-land cells and seasonal ice-masked days collapse to
`x = 0.0`, indistinguishable on their face from a genuine cool (sub-threshold) day. Your engine **hard-resets
running state on ice/NaN**, so to replicate your events I must know which `x = 0.0` days are *excluded* vs
*confirmed cool* — especially in **Chukchi (66.5% of cells carry ice-masked days)**. We reconstructed a
`valid_mask` from your sealed θ90 climatology's NaN footprint and verified zero counter-examples over the full
record, so I'm confident — but for a deploy gate I'd rather derive against **your authoritative mask**, not our
reconstruction. Please:

- **(a)** route your per-cell **valid / ice-exclusion mask** for egoa, wgoa, sebs, chukchi (full period), or
  confirm it equals a θ90-NaN-footprint reconstruction; and
- **(b)** confirm the exact **hard-reset semantics in event detection**: does a masked day **terminate** an
  in-progress event, and **can masked days occupy a ≤2-day merge gap** (i.e. is `5hot,1masked,5hot` two events or
  one)? This is the one place my independent derivation could diverge from yours for a non-defect reason, so I
  want to match your convention rather than guess it.

With (1)–(3) confirmed, my derivation is a clean apples-to-apples check and the sign-off comes down to whether
the `A/D/O` agree.

— lofra-m1
