"""Research section — a single page describing planned content.

One page (not several empty destinations) so the site reads as intentionally staged rather
than unfinished. As content accumulates, the sections below can be promoted into dedicated
pages. Forecast *development and methodology* are documented here, but forecast indicators
themselves are integrated alongside the relevant ecosystem indicators in the Alaska-wide and
regional sections — Research is not the permanent home of forecasts. Page config / fonts are
owned by the navigation shell.
"""
from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("🔬 Research Resources")
    st.markdown(
        "Literature, summaries, technical notes, methodology, and ongoing work supporting the "
        "Alaska Marine Ecosystem platform. Forecast **development and methodology** are "
        "documented here; the forecast **indicators** themselves will appear alongside the "
        "relevant ecosystem indicators in the Alaska-wide and regional sections as they become "
        "available."
    )
    st.divider()

    st.markdown("### Literature summaries")
    st.write("Curated, plain-language summaries of literature on Alaska marine ecosystems, the "
             "cold pool, bottom conditions, fisheries, and the forecasting of marine heatwaves.")
    st.page_link("pages/literature.py", label="Open Literature Summaries", icon="📚")

    st.markdown("### Forecast development")
    st.write("Methodology and progress on marine-heatwave and ocean-state forecasting, developed "
             "as a separate research programme and held to a validation gate before any product "
             "is shown on the board.")
    st.page_link("pages/forecast_development.py", label="Open Forecast Development", icon="🧭")

    st.markdown("### Technical notes & methodology")
    st.write("Methods, data provenance, validation, and reproducibility details. _In preparation._")

    st.markdown("### Project research")
    st.write("Working notes, presentations, and ongoing analyses from this project. "
             "_In preparation._")
