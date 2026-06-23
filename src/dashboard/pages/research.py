"""Research section — a single page describing planned content.

One page (not several empty destinations) so the site reads as intentionally staged rather
than unfinished. As content accumulates, the sections below can be promoted into dedicated
pages. Forecasting is developed by a separate research cell; the board surfaces observed and
modelled state and displays forecast products as they are delivered. Page config / fonts are
owned by the navigation shell.
"""
from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("🔬 Research")
    st.markdown(
        "Research outputs and resources supporting the Alaska Marine Ecosystem board. "
        "Forecast development is carried out by a separate research cell; the board surfaces "
        "observed and modelled ecosystem state and will display forecast products as they "
        "become available."
    )
    st.divider()

    st.markdown("### Recent papers")
    st.write("Curated literature on Alaska marine ecosystems, the cold pool, bottom conditions, "
             "and fisheries. _In preparation._")

    st.markdown("### Research summaries")
    st.write("Short, plain-language summaries of relevant studies and of this project's findings. "
             "_In preparation._")

    st.markdown("### Forecast outlooks")
    st.write("Seasonal-to-interannual outlooks delivered by the research cell, displayed here as "
             "they are released. _In preparation._")

    st.markdown("### Technical notes")
    st.write("Methods, data provenance, validation, and reproducibility details. _In preparation._")

    st.markdown("### Project research")
    st.write("Working notes, presentations, and ongoing analyses from this project. "
             "_In preparation._")
