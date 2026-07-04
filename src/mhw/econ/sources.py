"""Commercial-landings data-source descriptors (the only source-specific config).

Each :class:`LandingsSource` captures everything an ingest CLI needs to turn one source's
raw rows into the board's tidy landings schema — the source column → tidy column map, the
value fields, units, region resolution, and how the data is accessed (live API vs a manually
downloaded export). Adding AKFIN / ADF&G later is a **new descriptor here, not new code**
(mirrors :class:`mhw.bottom.sources.BottomSource`).

Tidy target schema (one parquet per source under ``data/raw/``, gitignored)::

    (year, area_group, area_native, species, species_code,
     landings_t, value_usd, catch_or_landings, collection, source, confidential)

``area_group`` is a board group (``bering`` / ``goa`` / ``ai`` / ``statewide``); ``area_native``
keeps the source's own management-area label (see :mod:`mhw.econ.areas`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

# Pounds → metric tons. Landings are reported in pounds by FOSS; the board shows tons.
LBS_PER_TONNE = 2204.6226218
TONNE_PER_LB = 1.0 / LBS_PER_TONNE


@dataclass(frozen=True)
class LandingsSource:
    """Descriptor for one commercial-landings source."""

    id: str
    label: str                       # user-facing label (dashboard / API)
    base_url: str
    table: str = ""                  # REST table / resource name (api access)
    access: str = "api"              # "api" (live REST) | "export" (manual download → ingest)
    region_resolution: str = "statewide"   # "statewide" | "npfmc_area"
    update_frequency: str = "annual"       # refresh cadence; landings finalise with a lag
    # Source column -> tidy column. Only the mapped columns are carried through.
    field_map: Mapping[str, str] = field(default_factory=dict)
    value_fields: tuple[str, ...] = ()     # tidy columns that are $ values (for labelling)
    units: str = "pounds"            # native quantity unit of the raw feed
    notes: str = ""


# --- NOAA FOSS Commercial Landings — statewide Alaska, live REST -----------------------------
# Verified live 2026-07-03: https://apps-st.fisheries.noaa.gov/ods/foss/landings/ returns AK
# rows with ts_afs_name (species), tsn (taxonomic serial no.), state_name ("ALASKA"),
# region_name, year, pounds, dollars, source ("AKFINHIST" for AK commercial), collection
# ("Commercial" / "Recreational"). Same paged REST infra as the survey tables (limit/offset +
# hasMore); filter on scalars (state_name, collection) — never the WAF-blocked $in operator.
# Region resolution is STATEWIDE Alaska only (no sub-region split); region-wise groundfish is
# the later AKFIN track (E2), not this source.
FOSS_LANDINGS = LandingsSource(
    id="foss_ak",
    label="NOAA FOSS Commercial Landings (statewide Alaska)",
    base_url="https://apps-st.fisheries.noaa.gov/ods/foss",
    table="landings",
    access="api",
    region_resolution="statewide",
    update_frequency="annual (finalised with a lag)",
    field_map={
        "year": "year",
        "ts_afs_name": "species",
        "tsn": "species_code",
        "pounds": "pounds",
        "dollars": "value_usd",
        "region_name": "area_native",
        "collection": "collection",
        "source": "source",
    },
    value_fields=("value_usd",),
    units="pounds",
    notes=(
        "Statewide Alaska only (not sub-region). Ex-vessel value in current (nominal) US$. "
        "Filter collection=Commercial + state_name=ALASKA; landings_t = pounds / 2204.62."
    ),
)

# Registry — id -> descriptor.
LANDINGS_SOURCES: dict[str, LandingsSource] = {
    FOSS_LANDINGS.id: FOSS_LANDINGS,
}
