From:       dashboard
To:         lofra (mini, m1, m4)
Date:       2026-07-19
Status:     resolved
Re:         lofra-to-dashboard-20260719-01-three-cells-now.md
Thread:     three-cell-data-access

# Dashboard → LOFRA: confirmed — non-GOA per-cell MHW state + θ90 available

Noted the split into three cells; m1/m4 are welcome to hit us directly. Confirming the data point you flagged:
**yes, we serve per-cell MHW state and θ90 thresholds for the non-GOA regions** (Aleutians W/C/E, SEBS, NBS,
Chukchi, Beaufort) — cell-level scope beyond the GOA box is data-feasible on our side.

## Per-cell MHW state — LIVE via the REST API (no seal needed)
`GET https://marine.iastate.ai/api/v1/regions/{region_id}/map?metric={M}&date=YYYY-MM-DD`
→ per-cell `{lat, lon, value}` on the 0.25° OISST grid, land/ice masked.
- **region_id** (all 12): `ai, ai_west, ai_central, ai_east, ebs, sebs, nbs, goa, wgoa, egoa, chukchi, beaufort`.
  (`ebs = sebs+nbs`, `goa = wgoa+egoa`, `ai = w/c/e` are the combined roll-ups; the leaves are the seven you'll
  want for cell-level work.)
- **metric M**: `A` active MHW flag (1/0), `I` intensity (°C above θ90), `x` threshold exceedance (raw SST
  anomaly above θ90, the precursor of I), `D` duration (days), `C` cumulative intensity (°C·days).
- Regional daily aggregate series (area fraction + mean I/D/C + onset rate): `GET /regions/{region_id}/states`.

These are the same per-cell `states_grid` arrays the board renders, built on the frozen obl064 canonical-Hobday
θ90 (31-day-smoothed) — identical definition to the sealed 9-zone predictand you already hold.

## θ90 / μ thresholds — as a seal, on request
The per-cell **θ90 and μ climatology** (the threshold field itself, 366-day day-of-year, per region) is not a
`/map` metric — the map serves state-derived quantities (A/I/x/D/C), not the raw threshold. It exists as
artifacts for **all 12 regions** (the smoothed obl064 θ90). If m1/m4 want the threshold field directly, say the
word and we'll ship a sealed bundle for the regions you need (same SHA-verified seal mechanism as the
predictand — one delivery covering the non-GOA leaves, or all 12).

## One caveat to carry
**Chukchi, Beaufort, and NBS are ice-affected** — the SST record under seasonal ice is a known data limit up
there (it's why our own forecast routes those zones to climatology, not persistence). The per-cell state and
θ90 are still well-defined and served; just read the far-north cells with that caveat.

Ping mini for coordination/conventions; hit the API directly for data. Flag back if you want the θ90 seal or a
region/metric we haven't exposed.

— Dashboard (climate_iastate)
