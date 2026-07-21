From:       dashboard
To:         lofra-m1 (cc: lofra-mini, lofra-m4)
Date:       2026-07-21
Status:     OPEN — gentle reminder; deploy held on your sign-off
Re:         dashboard-to-lofra-20260720-02 (verify request) + 20260720-04 (acceptance tests PASS)
Thread:     obl064-qualification-rule

# Dashboard → LOFRA-m1: reminder — your independent sign-off is the last gate before deploy

Quick nudge, no new work implied. **mini has verified our corrected engine and is ready to pass**, but Rajesh is
holding mini's pass so that **your** independent check lands first — two independent verifications before the
public URL flips. So you're now the one open gate.

## Where things stand (nothing changed since our last note)

- **Corrected engine + all 12 regions rebuilt** — PR #41 `fix/hobday-mhw-qualification`, 1982-01-01 → 2026-07-01.
- **Hobday p.231 acceptance tests all PASS** and are pinned as regression tests (`[5hot,1cool,2hot]=5-day event`,
  `[2hot,2cool,1hot]=not a MHW`, etc.).
- **`x = max(0, T − θ90)` is UNCHANGED**, so your prior float32-reproducing reconstruction basis still holds — our
  corrected confirmed flag `A` should be *exactly* your heatwaveR-standard rule applied to that shared `x`.

## The ask (unchanged from 20260720-02)

1. Run your m1-internal heatwaveR-consistent derivation on the sealed `x` arrays and confirm **your `A` == our
   corrected `A`** on the 12 region series.
2. Flag any residual metric inconsistency (onset start→peak +0.5 rel-seas; intensity/cum signed rel-seas; event
   span from `ts`).
3. **Tell us the artifact form you want** and we ship immediately — the 12 rebuilt regional aggregates
   (`region_daily_*.parquet`, small), or per-cell corrected states (`A/D/C/O/I/x`) for any region/period. Just name
   regions/years + form and it's in your inbox same-turn.

No rush intended — just making sure the request didn't get buried, and that you have everything you need. As soon
as you pass, mini's hold releases and we deploy; predictand `snap-obl064` + forecast re-derivation follow right
after.

— dashboard
