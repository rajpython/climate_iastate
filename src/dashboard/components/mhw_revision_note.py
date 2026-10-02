"""One data-revision note for the marine-heatwave pages (October 2026 input corrections).

Shown on the Operational and Historical MHW pages for the zones the ice-field correction moved most.
"""
from __future__ import annotations

from dashboard.components.bottom_ui import AMBER, callout

ICE_ZONES = {"beaufort", "chukchi", "nbs", "sebs", "ebs"}

NOTE_HTML = (
    "<b>Data revision, October 2026.</b> NOAA's OISST v2.1 sea-surface record omits its sea-ice field on "
    "171 days (for example January–February 2017 and April–June 2016). Ice-covered water on those days "
    "had been counted as open sea, which produced spurious winter heatwaves — the Beaufort Sea showed 26% "
    "of its area in a heatwave in February 2017, against at most 1.5% in any other February. Ice status on "
    "those days is now taken from the days either side, and the Beaufort and Chukchi February 2017 values "
    "are 0%. The same revision restored eight days that were missing from the input and adopted NOAA's "
    "re-issued files for 22–26 April 2024. Heatwave thresholds are no longer extended to days of the year "
    "on which a cell was ice-covered throughout the 1991–2020 baseline. Values in other years can differ "
    "slightly from earlier versions of this page."
)


def render_mhw_revision_note(region: str) -> None:
    """Show the revision note when *region* is one of the ice-affected zones."""
    if region in ICE_ZONES:
        callout(NOTE_HTML, icon="⚠️", tint=AMBER)
