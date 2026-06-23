"""Marine Heatwaves hub — the climate indicator under "Alaska-wide Climate".

Streamlit's ``st.navigation`` is two-level (section → pages), so the third level —
Marine Heatwaves → Operational / Historical — lives here: the section "Alaska-wide Climate"
holds this single hub page, and the hub offers the Operational and Historical views via a
sidebar sub-selector. Only the selected view renders, so its sidebar controls are not
duplicated. Future Alaska-wide climate indicators (SST anomalies, climate modes, outlooks)
become sibling pages under the same section. Page config / fonts are owned by the nav shell.
"""
from __future__ import annotations

import streamlit as st

from dashboard.pages.historical import render as _historical_render
from dashboard.pages.operational import render as _operational_render

_VIEWS = {
    "Operational": _operational_render,
    "Historical": _historical_render,
}


def render() -> None:
    view = st.sidebar.radio(
        "Marine Heatwaves", list(_VIEWS), key="mhw_view",
        captions=["Live & recent state", "1982–present analysis"],
    )
    st.sidebar.divider()
    _VIEWS[view]()
