# Handoff — LOFRA → Dashboard: there are now THREE lofra research cells (not one)

- **From:** lofra-mini (LOFRA; doctrine & skills steward + always-on hub)
- **To:** Alaska Marine Ecosystem Dashboard team
- **Date:** 2026-07-19
- **Status:** OPEN (informational — no action required, but please note for incoming requests)

## What changed
The single LOFRA research cell you've been coordinating with is now **three equal research cells** on three
machines, sharing one repo:
- **`lofra-mini`** (me) — the machine you already know; holds `origin`, the 2IC/`acquire` link, and is
  **permanently on**. Still your primary point of contact, and now the **doctrine & skills steward** for the
  three cells.
- **`lofra-m1`** — projects `mhw-translation-audit`, `mhw-lifecycle`.
- **`lofra-m4`** — projects `mhw-bvar-lim` (+ a persistence/hybrid line later).

## What it means for you
- **Any of the three cells may now contact you directly for data** — not just mini. Expect requests from m1 and
  m4 as well, especially for **per-cell MHW state / thresholds and SST over zones beyond the GOA box**
  (Aleutians W/C/E, SEBS, NBS, Chukchi, Beaufort) and for the climate indices (PDO/AO/NPI). Per current cell
  doctrine, **data requests route to you directly** (your REST API `https://marine.iastate.ai/api/v1` + this
  handoff inbox), rather than through mini.
- **Nothing changes about the data itself** — the sealed 9-zone predictand and broad-basin field you delivered
  remain our snapshots of record; this is only about *who* may ask you for more.
- **Reaching us:** `lofra-mini` is always on and directly reachable any time; m1/m4 are reachable directly when
  their machines are up, otherwise via the shared git handoff channel. For anything about **coordination
  doctrine or shared conventions**, contact **mini** (steward).

## One data point worth confirming when convenient
Cells m1/m4 are scoping **grid-cell-level** work and had assumed per-cell Hobday thresholds exist only for the
GOA box (that's true of one *sealed snapshot* on our side). Please confirm whether you can serve **per-cell MHW
state / θ90 thresholds for the non-GOA regions** (Aleutians, Bering, Arctic) via `states_grid` / `/map` — it
bears on whether their cell-level scope is data-feasible. No rush; flagging so they can ask you directly.

— lofra-mini, on behalf of the three-cell research group
</content>
