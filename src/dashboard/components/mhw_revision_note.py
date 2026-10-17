"""Record banner + data-revision note for the marine-heatwave pages (vintage #7, D1).

Every heatwave page carries the record banner; the zones D1 moved most also get a short note on
what changed. Shown on the Operational and Historical MHW pages.
"""
from __future__ import annotations

from dashboard.components.bottom_ui import AMBER, callout
from dashboard.components.mhw_record_ui import render_record_banner

ICE_ZONES = {"beaufort", "chukchi", "nbs", "sebs", "ebs"}

NOTE_HTML = (
    "<b>What changed in vintage #7 (D1).</b> NOAA's OISST v2.1 omits its sea-ice field on 171 days "
    "(for example April–June 2016 and January–February 2017). The previous version filled the ice on "
    "those days from the days either side. D1 no longer fills it: where ice cannot be known, that part "
    "of the zone is <b>unknown</b>, drawn as the grey band, and a day with more than 25 % unknown is "
    "hatched and never shown as zero. Observed ice counts as a real zero, so Arctic winter days mostly "
    "read “ice-covered”. 142 cells whose satellite ice record is inconsistent over time (for example, "
    "never ice-covered before 2005 but routinely after) are excluded in every season. Values differ "
    "from earlier versions of this page, most in spring 2016 in the southeast Bering and in the "
    "pre-2005 Arctic."
)


def render_mhw_revision_note(region: str) -> None:
    """Record banner on every zone; the D1 change note on the ice-affected zones."""
    render_record_banner()
    if region in ICE_ZONES:
        callout(NOTE_HTML, icon="⚠️", tint=AMBER)
