# Groundfish Economics Guide (Economic SAFE)

This guide documents the **commercial groundfish economics** layer of the dashboard — the
fishery-*dependent* counterpart to the survey and model ecosystem pages.

## What this is

The data come from NOAA/AFSC's **Economic Status of the Groundfish Fisheries off Alaska**
("Economic SAFE"), distributed by the **Alaska Fisheries Information Network (AKFIN)** as public
Apex reports. The board ingests the **Groundfish Economic SAFE report series (GFSAFE001–019)** —
17 reports covering catch, ex-vessel value and price, wholesale production and value, fishing
effort, crew labor, and fleet characteristics.

These are **aggregated, non-confidential** statistics. Where a cell aggregates too few
vessels/processors to be fully public (NOAA's "rule of three"), the published value is retained
and accompanied by a **suppression band** telling you how much of the cell was confidential — the
board surfaces that band rather than hiding the number.

## Spatial units: FMP area, not survey region

Economic SAFE data is keyed to **Fishery Management Plan (FMP) areas**:

| Code | FMP area |
|---|---|
| `BSAI` | Bering Sea & Aleutian Islands |
| `GOA` | Gulf of Alaska |
| `AK` | All Alaska (statewide total) |

These are **management areas, not the survey ecosystem regions** used elsewhere on the board.
Importantly, **BSAI bundles the Bering Sea *and* the Aleutian Islands** and cannot be split into
them — so the economics pages are organized by FMP area (BSAI / GOA), deliberately separate from
the Bering Sea / Aleutian Islands ecosystem sections. Some reports add a GOA `SUBAREA` (Western /
Central Gulf).

## Catch vs. value vs. price vs. wholesale

Different reports measure different things — read each panel by its label:

- **Catch (t)** — retained (and, in GFSAFE001, total) groundfish weight, in metric tons.
- **Ex-vessel value ($)** — what harvesters were paid at the dock (nominal, not inflation-adjusted).
- **Ex-vessel price ($/lb)** — dock price per pound.
- **First-wholesale value ($) / price** — value of processed products leaving the primary processor.

All dollar figures are **nominal** (current-year dollars), not adjusted for inflation.

## The report series

| Family | Reports | Content |
|---|---|---|
| Catch | 001, 003, 004 | Catch / retained catch by area, species, gear, sector, target, subarea |
| Value | 002, 007, 008 | Retained catch + ex-vessel value by species, gear, sector |
| Price | 009 | Ex-vessel price ($/lb) by species, gear, processing sector |
| Value share | 010, 011 | Value by state of residency; by fleet |
| Wholesale | 012, 013, 014 | Wholesale production, value, unit price; by processor group |
| Effort | 015, 016, 017 | Vessel counts (annual & monthly); vessel-weeks |
| Labor | 018 | Crew-weeks (catcher-vessel & at-sea processor) |
| Fleet | 019 | Fleet technical characteristics (length, tonnage) |

## Currency and refresh

- **Coverage:** most reports 2003–2024; a few begin 2009 or 2012.
- **Refresh:** annual. The Economic SAFE finalizes with a lag; the board re-downloads the AKFIN
  Apex CSV exports and re-runs the ingest (`mhw-ingest-econ-safe`).
- **Source:** AKFIN Groundfish Economic SAFE Apex reports — `reports.psmfc.org/akfin`.

## Not included

Confidential vessel/processor-level records, and any inflation adjustment, are out of scope.
Crab economics (ADF&G) and joins to survey biomass / bottom temperature are separate, later layers.
