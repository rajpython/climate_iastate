"""Alaska Marine Ecosystem Dashboard — entry point / navigation shell.

Run:
    streamlit run src/dashboard/Alaska_Dashboard.py

Hybrid navigation (``st.navigation``, **top-positioned**): cross-cutting Alaska-wide products
(climate / marine heatwaves) and region-specific ecosystems (Bering Sea, Gulf of Alaska, …)
are grouped into a horizontal top bar; this keeps the **left sidebar dedicated to the active
page's own controls** (region/model/threshold selectors) so they sit at the top of the sidebar
instead of below a tall navigation list. Research and guides are separate platform sections.
New regions/products slot into a section here rather than lengthening a flat page list. This
shell owns the single ``set_page_config``, the page CSS, and the page registry; the page
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

# Modestly enlarge the top navigation (~+14%) for a research-portal feel. Applies on every
# page since the top bar is global.
st.markdown(
    """<style>
    [data-testid="stTopNavSection"], [data-testid="stTopNavSection"] a,
    [data-testid="stTopNavDropdownButton"], [data-testid="stTopNav"] a { font-size: 1.0rem; }
    </style>""",
    unsafe_allow_html=True,
)

# Region-specific bottom-state pages are group-aware callables; the placeholder + research
# pages are plain callables. Importing them here is safe — these modules define functions only.
from dashboard.pages.marine_heatwaves import render as marine_heatwaves_render  # noqa: E402
from dashboard.pages.bottom_observed import render as bottom_observed_render  # noqa: E402
from dashboard.pages.bottom_models import render as bottom_models_render  # noqa: E402
from dashboard.pages.catch import render as catch_render  # noqa: E402
from dashboard.pages.cold_pool_guide import render as cold_pool_guide_render  # noqa: E402
from dashboard.pages.research import render as research_render  # noqa: E402
from dashboard.pages._placeholders import coming_soon  # noqa: E402


# --- Overview front door ------------------------------------------------------------------
# Current-coverage cards (one per platform section). Restrained, equal-height grid; emoji kept
# only in the page title. (title, concept, description, under_dev).
_COVERAGE = [
    ("Marine Heatwaves", "Operational &amp; historical monitoring",
     "Marine heatwave conditions across Alaska shelf ecosystems.", False),
    ("Bering Sea", "Bottom Conditions &amp; Climate–Fisheries Relationships",
     "Cold-pool indicators, bottom-temperature assessments, model validation, model "
     "comparison, and catch–environment relationships.", False),
    ("Gulf of Alaska", "Regional Ecosystem Indicators", "", True),
    ("Aleutian Islands", "Regional Ecosystem Indicators", "", True),
    ("Arctic", "Chukchi and Beaufort Ecosystems", "", True),
    ("Research", "Research Resources",
     "Literature summaries, technical notes, forecast development, and project research.", False),
    ("Guides", "Documentation",
     "Documentation, methodology, and background material.", False),
]

# Custom-class divs (not <p>) so the explanatory-font p-rule does not override these sizes.
# Neutral / monochrome only — colour comes from the figures, not the home page.
_HOME_CSS = """<style>
.amed-subtitle { font-size: 1.45rem; font-weight: 400; letter-spacing: 0.04em; opacity: 0.6;
    margin: -0.4rem 0 1.0rem; }
.amed-intro { font-size: 1.08rem; line-height: 1.5; max-width: 74ch; opacity: 0.9;
    margin-bottom: 1.7rem; }
.amed-section { font-size: 1.2rem; font-weight: 700; opacity: 0.92; margin: 0.2rem 0 0.3rem; }
.amed-context { font-size: 1.0rem; line-height: 1.5; opacity: 0.72; max-width: 84ch;
    margin-bottom: 1.1rem; }
.amed-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem;
    grid-auto-rows: 1fr; margin-bottom: 1.4rem; }
.amed-card { border: 1px solid rgba(130,130,130,0.28); border-radius: 0.5rem;
    padding: 1.05rem 1.2rem; display: flex; flex-direction: column; }
.amed-card-title { font-size: 1.12rem; font-weight: 700; margin-bottom: 0.3rem; }
.amed-card-sub { font-size: 0.97rem; font-weight: 600; opacity: 0.95; margin-bottom: 0.35rem; }
.amed-card-desc { font-size: 0.92rem; line-height: 1.45; opacity: 0.7; }
.amed-card-tag { margin-top: auto; padding-top: 0.7rem; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.09em; text-transform: uppercase; opacity: 0.5; }
.amed-rule { border: none; border-top: 1px solid rgba(130,130,130,0.25); margin: 1.0rem 0 0.6rem; }
.amed-footer { font-size: 0.85rem; opacity: 0.6; }
@media (max-width: 1000px) { .amed-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .amed-grid { grid-template-columns: 1fr; } }
</style>"""


def _card_html(title: str, concept: str, desc: str, under_dev: bool) -> str:
    parts = [f'<div class="amed-card-title">{title}</div>']
    if concept:
        parts.append(f'<div class="amed-card-sub">{concept}</div>')
    if desc:
        parts.append(f'<div class="amed-card-desc">{desc}</div>')
    if under_dev:
        parts.append('<div class="amed-card-tag">Under development</div>')
    return f'<div class="amed-card">{"".join(parts)}</div>'


def home() -> None:
    st.markdown(_HOME_CSS, unsafe_allow_html=True)
    st.title("🌊 Alaska Marine Ecosystem Dashboard")
    st.markdown('<div class="amed-subtitle">Climate • Ocean • Ecosystems • Fisheries</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="amed-intro">Climate, ocean, ecosystem, and fisheries indicators for '
        "Alaska's shelf ecosystems, derived from observed surveys and regional ocean "
        'models.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="amed-section">Current Coverage</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="amed-context">Current coverage emphasizes observed and modelled ecosystem '
        "state across Alaska shelf ecosystems. Additional regional indicators and forecast "
        'capabilities are under development.</div>',
        unsafe_allow_html=True,
    )
    cards = "".join(_card_html(*m) for m in _COVERAGE)
    st.markdown(f'<div class="amed-grid">{cards}</div>', unsafe_allow_html=True)
    st.markdown(
        '<hr class="amed-rule"><div class="amed-footer">Developed at Iowa State University '
        "using NOAA observational and modelling products.</div>",
        unsafe_allow_html=True,
    )


# --- Page registry: geography-first hybrid navigation -------------------------------------
# Top-positioned: each section is a top-bar menu, leaving the sidebar for page controls.
# "Alaska-wide Climate" is the cross-cutting climate section (marine heatwaves today; SST
# anomalies, climate modes, outlooks later). Gulf of Alaska, Aleutian Islands, and Arctic are
# distinct ecosystems and get distinct sections from the start (avoids future restructuring);
# each holds one concise placeholder until its indicators are built (Phase 2/3).
nav = {
    "Overview": [
        st.Page(home, title="Overview", default=True),
    ],
    # Two-level nav limit: the third level (Marine Heatwaves → Operational / Historical) lives
    # inside the hub page. Future climate indicators (SST anomalies, climate modes, outlooks)
    # become sibling pages here.
    "Alaska-wide Climate": [
        st.Page(marine_heatwaves_render, title="Marine Heatwaves", url_path="marine_heatwaves"),
    ],
    "Bering Sea": [
        st.Page(lambda: bottom_observed_render(group="bering"),
                title="Bottom State — Observed & Validation", url_path="bering_bottom_observed"),
        st.Page(lambda: bottom_models_render(group="bering"),
                title="Bottom State — Model Comparison", url_path="bering_bottom_models"),
        st.Page(lambda: catch_render(group="bering"),
                title="Catch × Bottom State", url_path="bering_catch"),
    ],
    "Gulf of Alaska": [
        st.Page(coming_soon("Gulf of Alaska", phase="Phase 2"),
                title="Under development", url_path="goa_under_development"),
    ],
    "Aleutian Islands": [
        st.Page(coming_soon("Aleutian Islands", phase="Phase 2"),
                title="Under development", url_path="ai_under_development"),
    ],
    "Arctic": [
        st.Page(coming_soon("Arctic — Chukchi & Beaufort", phase="Phase 3"),
                title="Under development", url_path="arctic_under_development"),
    ],
    "Research": [
        st.Page(research_render, title="Research", url_path="research"),
    ],
    "Guides": [
        st.Page("pages/user_guide.py", title="User Guide"),
        st.Page(cold_pool_guide_render, title="Cold-Pool Guide", url_path="cold_pool_guide"),
    ],
}

pg = st.navigation(nav, position="top")
pg.run()
