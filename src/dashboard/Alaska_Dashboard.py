"""Alaska Marine Ecosystem Dashboard — entry point / navigation shell.

Run:
    streamlit run src/dashboard/Alaska_Dashboard.py

Hybrid navigation (``st.navigation``): cross-cutting Alaska-wide products (marine heatwaves)
stay top-level; region-specific products (bottom state, catch) are grouped geographically;
research and guides are separate platform sections. New regions/products slot into a section
here rather than lengthening a flat page list. This shell owns the single ``set_page_config``,
the explanatory-font CSS, and the page registry; the page modules just render their bodies.
"""
import streamlit as st

st.set_page_config(
    page_title="Alaska Marine Ecosystem Dashboard",
    page_icon="🌊",
    layout="wide",
)

# set_page_config must be the first Streamlit call, so all dashboard imports are deferred
# below it (E402 is expected and intentional for a Streamlit entrypoint).
from dashboard.components.style import apply_explanatory_font  # noqa: E402
apply_explanatory_font()

# Region-specific bottom-state pages are group-aware callables; the placeholder + research
# stubs are plain callables. Importing them here is safe — these modules define functions only.
from dashboard.pages.bottom_observed import render as bottom_observed_render  # noqa: E402
from dashboard.pages.bottom_models import render as bottom_models_render  # noqa: E402
from dashboard.pages.catch import render as catch_render  # noqa: E402
from dashboard.pages.cold_pool_guide import render as cold_pool_guide_render  # noqa: E402
from dashboard.pages import research as rsch  # noqa: E402
from dashboard.pages._placeholders import coming_soon  # noqa: E402


def home() -> None:
    """Overview — the front door (simple MVP; not an ecosystem-status index yet)."""
    st.title("🌊 Alaska Marine Ecosystem Dashboard")
    st.subheader("Climate • Ocean • Ecosystems • Fisheries")
    st.markdown(
        """
        A friendly, honest, regionally-organised window onto public Alaska-shelf ocean and
        fisheries data — observed surveys and ocean models, surfaced for the scientists and
        managers who can use them. Pick a section from the sidebar.

        ### Current modules
        | Section | What's there |
        |---|---|
        | 🌊 **Alaska-wide Climate** | Marine-heatwave monitoring across all Alaska shelves — live **Operational MHW** state and **Historical MHW** analysis (1982–present), region-selectable |
        | 🧊 **Bering Sea** | **Bottom State — Observed & Validation** (the cold-pool index + survey-replicated model skill), **Model Comparison** (Bering10K ROMS vs CEFI MOM6 NEP), and **Catch × Bottom State** (snow crab & co. vs thermal habitat) |
        | 🚧 **Gulf of Alaska & Aleutians** · **Arctic** | Reserved — bottom-temperature conditions + catch, coming as the data products are built |
        | 🔬 **Research** | Recent papers, summaries, forecast outlooks (delivered by the research cell), technical notes, project research |
        | 📖 **Guides** | User Guide and the plain-language Cold-Pool Guide |

        ---
        *Bottom-state and catch products are **lagged** (recent-historical), not near-real-time.
        Forecasting is owned by a separate research cell — this board surfaces **state**.*
        """
    )
    st.info("Navigate with the **sidebar** (← left).  Prefer dark mode? **top-right ⋮ → Settings → Theme**.")


# --- Page registry: geography-first hybrid navigation -------------------------------------
# Future "Gulf of Alaska & Aleutians" and "Arctic" sections become real pages in Phase 2/3;
# for now they hold a single reserved placeholder so the section renders.
nav = {
    "Overview": [
        st.Page(home, title="Overview", icon="🏠", default=True),
    ],
    "Alaska-wide Climate": [
        st.Page("pages/operational.py", title="Operational MHW", icon="🌊"),
        st.Page("pages/historical.py", title="Historical MHW", icon="📊"),
    ],
    "Bering Sea": [
        st.Page(lambda: bottom_observed_render(group="bering"),
                title="Bottom State — Observed & Validation", icon="🧊",
                url_path="bering_bottom_observed"),
        st.Page(lambda: bottom_models_render(group="bering"),
                title="Bottom State — Model Comparison", icon="🌡️",
                url_path="bering_bottom_models"),
        st.Page(lambda: catch_render(group="bering"),
                title="Catch × Bottom State", icon="🎣",
                url_path="bering_catch"),
    ],
    "Gulf of Alaska & Aleutians": [
        st.Page(coming_soon("Gulf of Alaska & Aleutians", phase="Phase 2"),
                title="Coming soon", icon="🚧", url_path="goa_ai_coming_soon"),
    ],
    "Arctic": [
        st.Page(coming_soon("Arctic — Chukchi & Beaufort", phase="Phase 3"),
                title="Coming soon", icon="🚧", url_path="arctic_coming_soon"),
    ],
    "Research": [
        st.Page(rsch.research_home, title="Research Home", icon="🔬", url_path="research_home"),
        st.Page(rsch.recent_papers, title="Recent Papers", icon="📄", url_path="recent_papers"),
        st.Page(rsch.research_summaries, title="Research Summaries", icon="📝", url_path="research_summaries"),
        st.Page(rsch.forecast_outlooks, title="Forecast Outlooks", icon="🔭", url_path="forecast_outlooks"),
        st.Page(rsch.technical_notes, title="Technical Notes", icon="🛠️", url_path="technical_notes"),
        st.Page(rsch.project_research, title="Project Research", icon="📁", url_path="project_research"),
    ],
    "Guides": [
        st.Page("pages/user_guide.py", title="User Guide", icon="📖"),
        st.Page(cold_pool_guide_render, title="Cold-Pool Guide", icon="❄️", url_path="cold_pool_guide"),
    ],
}

pg = st.navigation(nav)
pg.run()
