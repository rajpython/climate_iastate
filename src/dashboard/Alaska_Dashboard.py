"""Alaska Marine Ecosystem Dashboard — entry point / navigation shell.

Run:
    streamlit run src/dashboard/Alaska_Dashboard.py

Hybrid navigation (``st.navigation``, **top-positioned**): cross-cutting Alaska-wide products
(marine heatwaves) and region-specific ecosystems (Bering Sea, Gulf of Alaska, …) are grouped
into a horizontal top bar; this keeps the **left sidebar dedicated to the active page's own
controls** (region/model/threshold selectors) so they sit at the top of the sidebar instead of
below a tall navigation list. Research and guides are separate platform sections. New
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
# Current-coverage cards (one per platform section) — answers "what is this?" before "what
# pages exist?". Not an ecosystem-status index (deliberately deferred). Each card leads with
# the section, then the concept it covers. (icon, section, concept, description, under_dev).
_COVERAGE = [
    ("🌊", "Marine Heatwaves", "Operational & historical monitoring",
     "Marine heatwave conditions across Alaska shelf ecosystems.", False),
    ("🧊", "Bering Sea", "Bottom Conditions & Climate–Fisheries Relationships",
     "Cold-pool indicators, bottom-temperature assessments, model validation, model "
     "comparison, and catch–environment relationships.", False),
    ("🌀", "Gulf of Alaska", "Regional Ecosystem Indicators", "", True),
    ("🌋", "Aleutian Islands", "Regional Ecosystem Indicators", "", True),
    ("❄️", "Arctic", "Chukchi and Beaufort Ecosystems", "", True),
    ("🔬", "Research", "Research Resources",
     "Literature summaries, technical notes, forecast development, and project research.", False),
    ("📖", "Guides", "Documentation",
     "Documentation, methodology, and background material.", False),
]


def home() -> None:
    st.title("🌊 Alaska Marine Ecosystem Dashboard")
    st.subheader("Climate • Ocean • Ecosystems • Fisheries")
    st.markdown(
        "Climate, ocean, ecosystem, and fisheries indicators for Alaska's shelf ecosystems, "
        "derived from observed surveys and regional ocean models."
    )
    st.markdown("#### Current Coverage")
    cols = st.columns(3)
    for i, (icon, section, concept, desc, under_dev) in enumerate(_COVERAGE):
        with cols[i % 3].container(border=True):
            st.markdown(f"##### {icon}  {section}")
            if concept:
                st.markdown(f"**{concept}**")
            if desc:
                st.write(desc)
            if under_dev:
                st.caption("🚧 Under development")
    st.caption(
        "Current coverage emphasizes observed and modelled ecosystem state. Forecast indicators "
        "will be integrated into Alaska-wide and regional sections as they become available."
    )


# --- Page registry: geography-first hybrid navigation -------------------------------------
# Top-positioned: each section is a top-bar menu, leaving the sidebar for page controls.
# Gulf of Alaska, Aleutian Islands, and Arctic are distinct ecosystems and get distinct
# sections from the start (avoids future restructuring); each holds one concise placeholder
# until its indicators are built (Phase 2/3), reusing the group-aware render()s.
nav = {
    "Overview": [
        st.Page(home, title="Overview", icon="🏠", default=True),
    ],
    "Marine Heatwaves": [
        st.Page("pages/operational.py", title="Operational", icon="🌊"),
        st.Page("pages/historical.py", title="Historical", icon="📊"),
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
                title="Under development", icon="🚧", url_path="goa_under_development"),
    ],
    "Aleutian Islands": [
        st.Page(coming_soon("Aleutian Islands", phase="Phase 2"),
                title="Under development", icon="🚧", url_path="ai_under_development"),
    ],
    "Arctic": [
        st.Page(coming_soon("Arctic — Chukchi & Beaufort", phase="Phase 3"),
                title="Under development", icon="🚧", url_path="arctic_under_development"),
    ],
    "Research": [
        st.Page(research_render, title="Research", icon="🔬", url_path="research"),
    ],
    "Guides": [
        st.Page("pages/user_guide.py", title="User Guide", icon="📖"),
        st.Page(cold_pool_guide_render, title="Cold-Pool Guide", icon="❄️", url_path="cold_pool_guide"),
    ],
}

pg = st.navigation(nav, position="top")
pg.run()
