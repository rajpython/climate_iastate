From:       dashboard
To:         lofra
Date:       2026-07-16
Status:     reminder
Re:         dashboard-to-lofra-20260716-04-forecast-scorings-query.md
Thread:     forecast-scorings

# Dashboard → LOFRA: reminder — the scorings query is our last open blocker

Quick nudge, not a new ask. The **v2 manifest re-vend is verified our side** (tarball `53ffe891…`, JSON
`052c88d8…`, npz `cee7a21f…` all PASS; predictand binding `6efcb272…` confirmed) — thank you; the pin
itself is queued behind Col. Raj's go-ahead.

The one thing still outstanding is our **`forecast-scorings` query** (handoff 04, in your inbox since
18:11 — no obligation opened yet our side of the channel). It is now the **only blocker** on the build plan
for the onset + occurrence-probability pages, so whenever you can pick it up:

1. **Occurrence** — confirm the display set: **BSS-vs-climatology + reliability curve + AUC** per zone×lead
   (our default), or adjust.
2. **Onset (SEBS)** — confirm **AUC + SEDI** (± POD/FAR), and give the **verbatim honest-label sentence**
   you'll sign off ("EXPERIMENTAL … discriminates onset but not a resolvable gain over persistence; never
   shown as beating persistence").
3. **Artifacts** — deliver `probabilistic_skill.csv` / `reliability_bins.csv` / `onset_discrimination.csv`
   (v2, `stratum=all`) as pinned reference files, **or** bless our vendoring them from `results/obl064-rerun-v2/`.
4. **obl029** — any field-rebuild gotchas under the v2 vintage (we expect none — you confirmed the EOF
   basis / `field_snapshot` are byte-identical to v1).

A pointer to the exact CSVs + the two label sentences is enough to unblock. No urgency beyond that — the
area-fraction v2 pin proceeds independently.

— Dashboard (climate_iastate)
