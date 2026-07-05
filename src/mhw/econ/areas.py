"""Management-area ↔ board-group crosswalk for the commercial-landings layer.

Commercial-harvest data uses **NPFMC / ADF&G management areas**, which do NOT match the AFSC
survey regions the rest of the board is keyed on (BSAI bundles the Bering Sea *and* the
Aleutians; the GOA splits into Western/Central/West-Yakutat/Southeast-Outside). This module is
the crosswalk from a source's native management area to a board group (``bering`` / ``goa`` /
``ai``), so region-wise pages can aggregate without silently relabelling management areas as
survey regions.

E1 (FOSS) is **statewide** — it exercises no crosswalk yet (``area_group="statewide"``). This
table is the E2 foundation (AKFIN region-wise groundfish); the authoritative crosswalk is locked
against an NPFMC management reference at E2, so treat this as a first draft (per plan §6).
"""
from __future__ import annotations

# Board groups the crosswalk maps into (aligns with the dashboard's geography-first nav).
BOARD_GROUPS = ("bering", "goa", "ai")

# Native management area (lower-cased key) -> board group. NPFMC groundfish reporting areas plus
# the coarse BSAI/GOA/AI subarea labels. Extend as AKFIN/ADF&G native labels are confirmed at E2.
_AREA_TO_GROUP: dict[str, str] = {
    # Bering Sea (groundfish BS subarea; crab BS districts) ≈ EBS/NBS survey regions.
    "bering sea": "bering",
    "bs": "bering",
    "ebs": "bering",
    "eastern bering sea": "bering",
    # Aleutian Islands — BSAI bundles BS + AI, so AI must be split back out.
    "aleutian islands": "ai",
    "ai": "ai",
    # Gulf of Alaska reporting areas (610 / 620 / 630 / 640 / 650) → one GOA group.
    "gulf of alaska": "goa",
    "goa": "goa",
    "western goa": "goa",
    "central goa": "goa",
    "west yakutat": "goa",
    "southeast outside": "goa",
    "610": "goa",
    "620": "goa",
    "630": "goa",
    "640": "goa",
    "650": "goa",
}


def crosswalk(area: str) -> str | None:
    """Return the board group for a native management *area*, or None if unmapped.

    Case/space-insensitive on the native label. ``None`` means "not yet crosswalked" — the
    caller should keep the native label and leave ``area_group`` unset rather than guess.
    """
    if area is None:
        return None
    return _AREA_TO_GROUP.get(str(area).strip().lower())


def board_groups() -> tuple[str, ...]:
    """The board groups the crosswalk can map into."""
    return BOARD_GROUPS


# ---------------------------------------------------------------------------
# FMP-area normalization (Economic SAFE / GFSAFE reports)
# ---------------------------------------------------------------------------
# The Groundfish Economic SAFE reports are keyed at **FMP-area** resolution, whose only values
# are the three below. FMP area is the management unit economists use; it does NOT split into the
# board's Bering/Aleutians ecosystem regions — "Bering Sea and Aleutian Islands" (BSAI) bundles
# both, so `bsai` maps to NO single survey region. `ak` = the statewide total row. Codes are the
# stable ids used in parquet/API/dashboard; labels are for display.
FMP_AREAS = ("bsai", "goa", "ak")

_FMP_LABELS: dict[str, str] = {
    "bsai": "Bering Sea & Aleutian Islands",
    "goa": "Gulf of Alaska",
    "ak": "All Alaska",
}

_FMP_STRING_TO_CODE: dict[str, str] = {
    "bering sea and aleutian islands": "bsai",
    "bsai": "bsai",
    "gulf of alaska": "goa",
    "goa": "goa",
    "all alaska": "ak",
    "alaska": "ak",
}


def fmp_area_code(area: str) -> str | None:
    """Normalize an FMP_AREA string (e.g. 'Gulf of Alaska') to a code ('goa'); None if unknown."""
    if area is None:
        return None
    return _FMP_STRING_TO_CODE.get(str(area).strip().lower())


def fmp_area_label(code: str) -> str:
    """Full display label for an FMP-area code (falls back to the upper-cased code)."""
    return _FMP_LABELS.get(str(code).strip().lower(), str(code).upper())
