"""Reserved-section placeholder pages for the navigation shell.

Geographic sections that have no built pages yet (Gulf of Alaska & Aleutians → Phase 2;
Arctic / Chukchi & Beaufort → Phase 3) still need at least one ``st.Page`` so the section
renders in the sidebar. ``coming_soon`` returns a tiny render function for that purpose.
Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

from typing import Callable

import streamlit as st


def coming_soon(region_label: str, phase: str, blurb: str = "") -> Callable[[], None]:
    """Return a render function for a reserved (not-yet-built) geographic section."""

    def _render() -> None:
        st.title(f"🚧 {region_label}")
        st.info(
            f"**Coming soon ({phase}).** This region is reserved in the navigation while its "
            "data products are built. Bottom-temperature conditions, catch × thermal habitat, "
            "and model comparison will appear here following the Bering Sea template."
        )
        if blurb:
            st.caption(blurb)

    return _render
