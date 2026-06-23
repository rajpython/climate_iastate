"""Alaska Marine Ecosystem Dashboard — entry point / navigation shell.

Run:
    streamlit run src/dashboard/Alaska_Dashboard.py

Hybrid navigation (``st.navigation``): cross-cutting Alaska-wide products (marine heatwaves)
stay top-level; region-specific products (bottom state, catch) are organised geographically
(one section per ecosystem); research and guides are separate platform sections. New
regions/products slot into a section here rather than lengthening a flat page list. This shell
owns the single ``set_page_config``, the explanatory-font CSS, and the page registry; the page
modules just render their bodies.
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
# pages are plain callables. Importing them here is safe — these modules define functions only.
from dashboard.pages.bottom_observed import render as bottom_observed_render  # noqa: E402
from dashboard.pages.bottom_models import render as bottom_models_render  # noqa: E402
from dashboard.pages.catch import render as catch_render  # noqa: E402
from dashboard.pages.cold_pool_guide import render as cold_pool_guide_render  # noqa: E402
from dashboard.pages.research import render as research_render  # noqa: E402
from dashboard.pages._placeholders import coming_soon  # noqa: E402


# --- Overview front door ------------------------------------------------------------------
# Module cards (one per platform section) — answers "what is this?" before "what pages exist?".
# Not an ecosystem-status index (deliberately deferred). (icon, title, description, under_dev).
_MODULES = [
    ("🌊", "Alaska-wide Climate",
     "Marine heatwave monitoring across Alaska shelf ecosystems through operational and "
     "historical products.", False),
    ("🧊", "Bering Sea",
     "Bottom-state indicators, cold-pool conditions, model validation, model comparison, and "
     "climate–fisheries relationships.", False),
    ("🌀", "Gulf of Alaska",
     "Regional ecosystem products under development.", True),
    ("🌋", "Aleutian Islands",
     "Regional ecosystem products under development.", True),
    ("❄️", "Arctic",
     "Chukchi and Beaufort ecosystem products under development.", True),
    ("🔬", "Research",
     "Research summaries, forecast development, technical notes, and project research.", False),
    ("📖", "Guides",
     "Documentation, methodology, and background material.", False),
]


def home() -> None:
    st.title("🌊 Alaska Marine Ecosystem Dashboard")
    st.subheader("Climate • Ocean • Ecosystems • Fisheries")
    st.markdown(
        "Climate, ocean, ecosystem, and fisheries indicators for Alaska's shelf ecosystems, "
        "derived from observed surveys and regional ocean models."
    )
    st.markdown("#### Modules")
    cols = st.columns(3)
    for i, (icon, title, desc, under_dev) in enumerate(_MODULES):
        with cols[i % 3].container(border=True):
            st.markdown(f"##### {icon}  {title}")
            st.write(desc)
            if under_dev:
                st.caption("🚧 Under development")
    st.caption(
        "Products are observed and modelled ecosystem **state** — annual and lagged "
        "(recent-historical), not near-real-time. Forecast products are under development and "
        "will be surfaced through the Research section as they become available."
    )


# --- Page registry: geography-first hybrid navigation -------------------------------------
# Gulf of Alaska, Aleutian Islands, and Arctic are distinct ecosystems and get distinct
# top-level sections from the start (avoids future restructuring); each holds one concise
# placeholder until its products are built (Phase 2/3), reusing the group-aware render()s.
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
    "Gulf of Alaska": [
        st.Page(coming_soon("Gulf of Alaska", phase="Phase 2"),
                title="Coming soon", icon="🚧", url_path="goa_coming_soon"),
    ],
    "Aleutian Islands": [
        st.Page(coming_soon("Aleutian Islands", phase="Phase 2"),
                title="Coming soon", icon="🚧", url_path="ai_coming_soon"),
    ],
    "Arctic": [
        st.Page(coming_soon("Arctic — Chukchi & Beaufort", phase="Phase 3"),
                title="Coming soon", icon="🚧", url_path="arctic_coming_soon"),
    ],
    "Research": [
        st.Page(research_render, title="Research", icon="🔬", url_path="research"),
    ],
    "Guides": [
        st.Page("pages/user_guide.py", title="User Guide", icon="📖"),
        st.Page(cold_pool_guide_render, title="Cold-Pool Guide", icon="❄️", url_path="cold_pool_guide"),
    ],
}

pg = st.navigation(nav)
pg.run()
