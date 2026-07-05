"""Groundfish Economic SAFE report registry — the catalog of the AKFIN GFSAFE series.

The board's commercial-economics layer is built from NOAA/AFSC's **Groundfish Economic SAFE**
reports, distributed by AKFIN as interactive Apex reports and exported here to CSV
(``data/raw/akfin_exports/``). This module is the single source of truth describing each report —
its family, dimensions, measures (with units/labels), and confidentiality column — so the ingest,
API, and dashboard all read the same catalog rather than hard-coding report specifics (mirrors how
:mod:`mhw.bottom.sources` / :mod:`mhw.bottom.regions` drive the bottom-ocean layer).

Reports are keyed at **FMP-area** resolution (BSAI / GOA / All Alaska) — the management-area units
economists work in, which do NOT split into the board's Bering/Aleutians ecosystem regions (see
:mod:`mhw.econ.areas`). Series: GFSAFE001–019 (005/006 not issued) = 17 reports. GFSAFE004 is two
CSV files (2003–2009 + 2010–2024) merged into one report on ingest.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

# AKFIN Apex Groundfish Economic SAFE report menu (public, no login).
SAFE_MENU_URL = "https://reports.psmfc.org/akfin/f?p=501:2001"

# Report families (dashboard grouping / phasing).
FAMILIES = ("catch", "value", "price", "share", "wholesale", "effort", "labor", "fleet")


@dataclass(frozen=True)
class Measure:
    """One numeric measure carried by a report (source column → label/units)."""

    col: str            # source column name (upper-snake as exported)
    label: str
    units: str
    kind: str = ""      # catch | value | price | weight | count | weeks | share | length | tonnage


@dataclass(frozen=True)
class EconReport:
    """Descriptor for one Groundfish Economic SAFE report."""

    id: str                          # canonical id, e.g. "gfsafe001"
    code: str                        # AKFIN code, e.g. "GFSAFE001"
    title: str
    family: str
    files: tuple[str, ...]           # source CSV basenames (GFSAFE004 has two)
    dimensions: tuple[str, ...]      # source dimension columns (besides YEAR + FMP_AREA)
    measures: tuple[Measure, ...]
    suppression_col: str = ""        # e.g. "PERCENT_VAL_SUPPRESSED" ("" = none)
    year_span: str = ""
    app_page: str = ""               # AKFIN Apex page id (f?p=501:9NN)
    notes: str = ""

    @property
    def parquet_name(self) -> str:
        return f"{self.id}.parquet"


def _m(col, label, units, kind=""):
    return Measure(col, label, units, kind)


# --- The 17 reports (columns verified live against the exported CSVs) ------------------------
_MT = "metric tons"
_USD = "US$ (nominal)"

SAFE_REPORTS: dict[str, EconReport] = {r.id: r for r in (
    # ---- Catch ----
    EconReport(
        "gfsafe001", "GFSAFE001",
        "Groundfish catch by area and species", "catch",
        ("GFSAFE001-2003-2024.csv",), ("SPECIES_GROUP",),
        (_m("CATCH_MT", "Catch", _MT, "catch"),),
        year_span="2003-2024", app_page="901",
        notes="Total catch (retained + discarded) by FMP area × species group."),
    EconReport(
        "gfsafe002", "GFSAFE002",
        "Retained catch and ex-vessel value by sector and species", "value",
        ("GFSAFE002-2003-2024.csv",), ("HARVEST_SECTOR", "SPECIES_GROUP"),
        (_m("RETAINED_CATCH_MT", "Retained catch", _MT, "catch"),
         _m("EXVESSEL_VALUE", "Ex-vessel value", _USD, "value")),
        year_span="2003-2024", app_page="902",
        notes="Headline catch + ex-vessel value summary by harvest sector × species group."),
    EconReport(
        "gfsafe003", "GFSAFE003",
        "BSAI retained catch by target, gear, sector, and species", "catch",
        ("GFSAFE003-2003-2024.csv",),
        ("GEAR", "SECTOR", "GROUNDFISH_TARGET_SPECIES", "SPECIES"),
        (_m("RETCATCH_MT", "Retained catch", _MT, "catch"),),
        suppression_col="PERCENT_CATCH_SUPPRESSED", year_span="2003-2024", app_page="903",
        notes="BSAI detail: retained catch by gear × sector × target × species."),
    EconReport(
        "gfsafe004", "GFSAFE004",
        "GOA retained catch by target, gear, subarea, and species", "catch",
        ("GFSAFE004-2003-2009.csv", "GFSAFE004-2010-2024.csv"),
        ("GEAR", "SUBAREA", "GROUNDFISH_TARGET_SPECIES", "SPECIES"),
        (_m("RETCATCH_MT", "Retained catch", _MT, "catch"),),
        suppression_col="PERCENT_CATCH_SUPPRESSED", year_span="2003-2024", app_page="904",
        notes="GOA detail: retained catch by gear × subarea × target × species (two-file export)."),
    # ---- Ex-vessel value ----
    EconReport(
        "gfsafe007", "GFSAFE007",
        "BSAI ex-vessel value by species, gear, and sector", "value",
        ("GFSAFE007-2003-2024.csv",), ("GEAR", "SECTOR", "SPECIES"),
        (_m("EXVES_VAL", "Ex-vessel value", _USD, "value"),),
        suppression_col="PERCENT_VAL_SUPPRESSED", year_span="2003-2024", app_page="907"),
    EconReport(
        "gfsafe008", "GFSAFE008",
        "GOA ex-vessel value by species, gear, and subarea", "value",
        ("GFSAFE008-2003-2024.csv",), ("GEAR", "SUBAREA", "SPECIES"),
        (_m("EXVES_VAL", "Ex-vessel value", _USD, "value"),),
        suppression_col="PERCENT_VAL_SUPPRESSED", year_span="2003-2024", app_page="908"),
    EconReport(
        "gfsafe009", "GFSAFE009",
        "Ex-vessel prices by species, gear, and processing sector", "price",
        ("GFSAFE009-2003-2024.csv",), ("GEAR", "PROCESSING_SECTOR", "SPECIES"),
        (_m("EXVES_PRICE_LB", "Ex-vessel price", "US$/lb", "price"),),
        year_span="2003-2024", app_page="909"),
    # ---- Value share / fleet economics ----
    EconReport(
        "gfsafe010", "GFSAFE010",
        "Ex-vessel value share by state of residency, area, and species", "share",
        ("GFSAFE010-2003-2024.csv",), ("SPECIES_GROUP",),
        (_m("ALASKA_EXVESVAL_SHARE", "Alaska-resident share", "%", "share"),
         _m("OTHERSTATE_EXVESVAL_SHARE", "Other-state share", "%", "share")),
        year_span="2003-2024", app_page="910"),
    EconReport(
        "gfsafe011", "GFSAFE011",
        "Ex-vessel value and vessels by fleet", "share",
        ("GFSAFE011-2009-2024.csv",), ("FLEET",),
        (_m("VESSELS", "Vessels", "count", "count"),
         _m("PROCESSING_PERMITS", "Processing permits", "count", "count"),
         _m("EXVES_VAL_M", "Ex-vessel value", "US$ millions", "value"),
         _m("EXVESVALPERVESSEL_K", "Value per vessel", "US$ thousands", "value")),
        year_span="2009-2024", app_page="911"),
    # ---- Wholesale ----
    EconReport(
        "gfsafe012", "GFSAFE012",
        "Wholesale production, value, and prices by product", "wholesale",
        ("GFSAFE012-2003-2024.csv",), ("PROCESSING_SECTOR", "SPECIES", "PRODUCT"),
        (_m("PRODUCT_WEIGHT_MT", "Product weight", _MT, "weight"),
         _m("WHOLESALE_VALUE", "Wholesale value", _USD, "value"),
         _m("PRICE_LB", "Wholesale price", "US$/lb", "price")),
        year_span="2003-2024", app_page="912"),
    EconReport(
        "gfsafe013", "GFSAFE013",
        "Groundfish wholesale unit value", "wholesale",
        ("GFSAFE013-2003-2024.csv",), ("PROCESSING_SECTOR", "SPECIES_GROUP"),
        (_m("WSLPRICE_PERROUNDMT", "Wholesale unit value", "US$/round t", "price"),),
        year_span="2003-2024", app_page="913"),
    EconReport(
        "gfsafe014", "GFSAFE014",
        "First-wholesale value by processor group", "wholesale",
        ("GFSAFE014-2012-2024.csv",), ("FLEET_PORT",),
        (_m("WSVAL_M", "First-wholesale value", "US$ millions", "value"),
         _m("PROCESSING_PERMITS", "Processing permits", "count", "count")),
        year_span="2012-2024", app_page="914"),
    # ---- Effort ----
    EconReport(
        "gfsafe015", "GFSAFE015",
        "Number of vessels by area, sector, and target", "effort",
        ("GFSAFE015-2003-2024.csv",), ("HARVEST_SECTOR", "TARGET"),
        (_m("VESSELS", "Vessels", "count", "count"),),
        year_span="2003-2024", app_page="915"),
    EconReport(
        "gfsafe016", "GFSAFE016",
        "Monthly number of vessels by sector and gear", "effort",
        ("GFSAFE016-2003-2024.csv",), ("HARVEST_SECTOR", "GEAR", "MONTH_NUMBER", "MONTH"),
        (_m("VESSELS", "Vessels", "count", "count"),),
        year_span="2003-2024", app_page="916"),
    EconReport(
        "gfsafe017", "GFSAFE017",
        "Vessel weeks by length, gear, area, and target", "effort",
        ("GFSAFE017-2003-2024.csv",),
        ("GEAR", "GROUNDFISH_TARGET_SPECIES", "HARVEST_SECTOR", "VESSEL_LENGTH_FEET"),
        (_m("VESSEL_WEEKS", "Vessel weeks", "weeks", "weeks"),),
        year_span="2003-2024", app_page="917"),
    # ---- Labor ----
    EconReport(
        "gfsafe018", "GFSAFE018",
        "Crew weeks in the groundfish fisheries", "labor",
        ("GFSAFE018-2009-2024.csv",), ("MONTH_NUMBER", "MONTH"),
        (_m("CV_CREWWEEKS", "Catcher-vessel crew weeks", "weeks", "weeks"),
         _m("ATSEAPROC_CREWWEEKS", "At-sea processor crew weeks", "weeks", "weeks")),
        year_span="2009-2024", app_page="918"),
    # ---- Fleet ----
    EconReport(
        "gfsafe019", "GFSAFE019",
        "Fleet technical characteristics", "fleet",
        ("GFSAFE019-2009-2024.csv",), ("FLEET",),
        (_m("VESSELS", "Vessels", "count", "count"),
         _m("LENGTH_AVG", "Mean length", "feet", "length"),
         _m("LENGTH_MED", "Median length", "feet", "length"),
         _m("NTON_AVG", "Mean net tonnage", "net tons", "tonnage"),
         _m("NTON_MED", "Median net tonnage", "net tons", "tonnage")),
        year_span="2009-2024", app_page="919"),
)}


def get_report(report_id: str) -> EconReport | None:
    """Look up a report by id (case-insensitive; accepts 'gfsafe001' or 'GFSAFE001')."""
    return SAFE_REPORTS.get(report_id.lower())


def reports_by_family(family: str) -> list[EconReport]:
    """All reports in a family, in registry order."""
    return [r for r in SAFE_REPORTS.values() if r.family == family]


def all_families() -> Mapping[str, list[EconReport]]:
    """Family → its reports (registry order)."""
    out: dict[str, list[EconReport]] = {f: [] for f in FAMILIES}
    for r in SAFE_REPORTS.values():
        out.setdefault(r.family, []).append(r)
    return out
