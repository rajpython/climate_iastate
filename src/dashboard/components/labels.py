"""Shared display-name mappings for MHW metrics.

Import from here in every dashboard component and page to ensure
consistent, user-friendly metric labels across the UI.
"""
from __future__ import annotations

# Internal column name -> user-friendly label
DISPLAY_NAMES: dict[str, str] = {
    "area_frac": "Area Fraction",
    "Ibar":      "Mean Intensity",
    "Dbar":      "Mean Duration",
    "Cbar":      "Cumul. Intensity",
    "Obar":      "Onset Rate",
}

# Internal column name -> unit string
DISPLAY_UNITS: dict[str, str] = {
    "area_frac": "",
    "Ibar":      "°C",
    "Dbar":      "days",
    "Cbar":      "°C·days",
    "Obar":      "°C/day",
}

# Percentile-column renames for the risk table
PCT_COLUMN_NAMES: dict[str, str] = {
    "area_frac_pct": "Area Frac. %ile",
    "Ibar_pct":      "Intensity %ile",
    "Dbar_pct":      "Duration %ile",
    "Cbar_pct":      "Cumul. Int. %ile",
}


def display_label(col: str, with_unit: bool = False) -> str:
    """Return friendly name, optionally with unit in parentheses."""
    name = DISPLAY_NAMES.get(col, col)
    if with_unit:
        unit = DISPLAY_UNITS.get(col, "")
        return f"{name} ({unit})" if unit else name
    return name


def metric_legend() -> str:
    """One-line caption suitable for st.caption() at the bottom of any tab."""
    return (
        "**Metrics:** Area Fraction = share of grid cells in MHW · "
        "Mean Intensity = °C above threshold · "
        "Mean Duration = days · "
        "Cumul. Intensity = °C·days · "
        "Onset Rate = °C/day"
    )
