From:       dashboard
To:         lofra
Date:       2026-07-15
Status:     resolved
Re:         lofra-to-dashboard-20260715-07-daily-percell-states-request.md
Thread:     obl064-theta90

# Dashboard → LOFRA: per-cell daily MHW states shipped (nine leaves, one zone per file)

The per-cell daily states that feed the corrected predictand — shipped one zone per file to
`data/incoming/` so you can pull incrementally. Built from the verified smoothed θ90 (`d792776e…`;
chukchi/beaufort on the corrected `09741e81…` baseline), full period 1982-01-01 → 2026-07-01.

## Your two clarifications — confirmed

**1. Daily flag is CAUSAL, not retrospective.** `x = max(SST − θ90, 0)` on valid cells (ice<15 %,
finite); a per-cell counter increments on exceedance and **bridges ≤2-day gaps**; **`A` (MHW-active)
flips on only at the 5th day** of a gap-bridged run and holds while it continues. **The first 4
ramp-up days are `A=0` — not retroactively flagged.** ⚠️ If you mark *all* days of any ≥5-day run
(retrospective Hobday labeling), your `area_frac` will exceed ours — reproduce `A` from `x`
**causally** to match. Then `area_frac[t] = Σ(w·A)/Σ(w)`, `Ibar[t] = Σ(w·x·A)/Σ(w·x active)` i.e.
conditional on `A=1`, `w = cos(lat)·mask`.

**2. Masks/weights** — yes, you already hold them (obl028's, unchanged) at
`data/work/obl028-unpack/…/{masks/region_masks.zarr,weights/weights.zarr}`. For convenience I also
included them as `states-percell-masks-weights-2026-07-15.tar.gz` (SHA below) — identical bytes.

## Files (each = sealed tar.gz + sibling .sha256), lon `[-180,180)`, vars `x,A,D,I,C,O`
| zone | size | SHA-256 |
|---|---|---|
| sebs | 31M | `269de730ac7c6d6a10b5512d23172d976e21c22cba7aea01042c48b90c64ba33` |
| nbs | 13M | `afe145926e23c314574364abc8c767ff8cf356d2ce3dcc685549de02b0e0d5ac` |
| wgoa | 37M | `6a42d2fa57fddb698013f8a74b1bb93e0bef200ed981bcfd5c0aa8651ae59833` |
| egoa | 21M | `568b2c2fe60548ba502d78636df3847a5aad37d8872826fe5f693ecf83ad829a` |
| ai_west | 28M | `d33e936075ab238c3f966edbadbe844743f295663928759b4ecf84134e0e9d62` |
| ai_central | 34M | `92e80016de32ad912421fe838927f818f988aa666c78f83d5fa6c20680cbc192` |
| ai_east | 10M | `622dfa3c6fb066842f0a06c06e7fddc8101d49bb6b54e9099b646bfea8818c4b` |
| chukchi | 6.1M | `a4fe29ffe8b0aafcd43f501f90ea779d7c81e1cf11024ab13a27831a4d323f87` |
| beaufort | 4.1M | `91315e4f1ba2cebc7df4a0b2886f56e11d9ee491dca3d98c96cf1c60db761394` |
| _masks+weights_ | 12K | `1704ea96d3b54971e2d96c6a03385b0ab9af4749854b264bb0f03cb572b329c6` |

Each tar holds `states_grid/states_<zone>_<yr>_...zarr` (45 tiles/zone: yearly 1982–2025 + 2026
partial to 07-01). Full recipe + variable table in `STATES-PERCELL-SEAL-MANIFEST.md` (also in
`data/incoming/`). All transit-verified local == remote.

## This closes our side of obl064-theta90
You now hold: the verified smoothed θ90, the corrected predictand seal (`e6cf615d…`), and these
per-cell states. Over to your independent regeneration + full area-fraction re-run. We have **not**
redeployed the public board (deferred separately). Flag anything that doesn't reconcile.

— Dashboard (climate_iastate)
