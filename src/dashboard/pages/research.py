"""Research section — minimal stub pages.

The structure is created now so the platform reads as a research-backed ecosystem board; the
content is curated by the separate research cell (`docs/forecast_extension/`) and filled in
later. Forecasting is owned by that cell — the board only *displays* products it delivers.
Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

import streamlit as st

_COMING = "_Coming soon — curated by the research cell._"


def research_home() -> None:
    st.title("🔬 Research")
    st.markdown(
        "The research home for the Alaska Marine Ecosystem board: recent papers, short research "
        "summaries, forecast outlooks, technical notes, and the project's own research outputs.\n\n"
        "Forecasting is owned by a separate research cell; the board surfaces observed and modelled "
        "*state* and will display forecast products the cell delivers — it does not build forecasts."
    )
    st.info("This section is being assembled. Use the items under **Research** in the sidebar.")


def recent_papers() -> None:
    st.title("📄 Recent Papers")
    st.markdown("Curated recent literature on Alaska marine ecosystems, cold pool, and fisheries.")
    st.caption(_COMING)


def research_summaries() -> None:
    st.title("📝 Research Summaries")
    st.markdown("Short plain-language summaries of relevant studies and the project's findings.")
    st.caption(_COMING)


def forecast_outlooks() -> None:
    st.title("🔭 Forecast Outlooks")
    st.markdown(
        "Seasonal / interannual outlooks **delivered by the research cell** and displayed here. "
        "The board does not generate forecasts."
    )
    st.caption(_COMING)


def technical_notes() -> None:
    st.title("🛠️ Technical Notes")
    st.markdown("Methods, data provenance, validation notes, and reproducibility details.")
    st.caption(_COMING)


def project_research() -> None:
    st.title("📁 Project Research")
    st.markdown("Outputs from this project: working notes, presentations, and ongoing analyses.")
    st.caption(_COMING)
