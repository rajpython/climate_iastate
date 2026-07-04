"""Fishery economics layer — commercial landings & ex-vessel value (fishery-*dependent*).

The board's existing layers describe ecosystem *state* from the fishery-**independent** AFSC
survey (CPUE, bottom temperature, the cold pool). This package adds the **commercial harvest**
layer economists work with: region/statewide landings (tons) and ex-vessel value ($) by species
and year — always labelled *fishery-dependent (commercial harvest)* to keep it distinct from the
survey. Source config lives in :mod:`mhw.econ.sources` (a descriptor per source), so adding a
source is data, not code (mirrors :mod:`mhw.bottom.sources`).

Scope boundary (firm): aggregated, non-confidential area × species × year only; no forecasting;
no confidential (vessel/processor-level) ingest. See ``docs/commercial_economics_plan.md``.
"""
