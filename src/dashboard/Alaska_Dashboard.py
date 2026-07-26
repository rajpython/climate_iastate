"""Alaska Marine Ecosystems Dashboard — entry point / navigation shell.

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
    page_title="Alaska Marine Ecosystems Dashboard",
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
    /* Trim the oversized default gap between the top nav bar and page content. */
    [data-testid="stMainBlockContainer"] { padding-top: 2.5rem; }
    /* Narrow the sidebar — it carries only page-level controls (region / year range),
       so Streamlit's ~336px default wastes horizontal space. */
    [data-testid="stSidebar"] { width: 250px !important; min-width: 250px !important;
        max-width: 250px !important; }
    [data-testid="stSidebar"] > div:first-child { width: 250px !important; }
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"] { padding-bottom: 0.25rem; }
    </style>""",
    unsafe_allow_html=True,
)

# Region-specific bottom-state pages are group-aware callables; the placeholder + research
# pages are plain callables. Importing them here is safe — these modules define functions only.
from dashboard.pages.marine_heatwaves import render as marine_heatwaves_render  # noqa: E402
from dashboard.pages.mhw_forecast import render as mhw_forecast_render  # noqa: E402
from dashboard.pages.bottom_observed import render as bottom_observed_render  # noqa: E402
from dashboard.pages.bottom_models import render as bottom_models_render  # noqa: E402
from dashboard.pages.catch import render as catch_render  # noqa: E402
from dashboard.pages.ocean_health import render as ocean_health_render  # noqa: E402
from dashboard.pages.commercial_landings import render as commercial_landings_render  # noqa: E402
from dashboard.pages.eco_econ import render as eco_econ_render  # noqa: E402
from dashboard.pages.econ_safe import (  # noqa: E402
    render_catch_value as econ_catch_value_render,
    render_crab as econ_crab_render,
    render_effort_labor as econ_effort_render,
    render_fleet_ownership as econ_fleet_render,
    render_prices as econ_prices_render,
    render_wholesale as econ_wholesale_render,
)
from dashboard.pages.guides import (  # noqa: E402
    bottom_state_guide,
    dashboard_guide,
    econ_safe_guide,
    marine_heatwave_guide,
)
from dashboard.pages.research import render as research_render  # noqa: E402


# --- Overview front door ------------------------------------------------------------------
# Current-coverage cards (one per platform section). Restrained, equal-height grid; emoji kept
# only in the page title. (title, concept, description, under_dev, links) where links is a list
# of (label, url_path) for that section's pages — revealed on hover (see _HOME_CSS) so a visitor
# can jump straight to a related page. url_paths must match the st.navigation registry below.
_COVERAGE = [
    ("Marine Heatwaves", "Operational, historical &amp; forecast",
     "Marine heatwave conditions across Alaska shelf ecosystems — live monitoring, the historical "
     "record, and a short-term outlook.", False,
     [("Operational", "marine_heatwaves"),
      ("Historical", "marine_heatwaves"),
      ("Forecast", "marine_heatwaves"),
      ("MHW Forecast (NOAA PSL)", "mhw_forecast")]),
    ("Bering Sea", "Bottom Conditions &amp; Climate–Fisheries Relationships",
     "Cold-pool indicators, bottom-temperature assessments, model validation, and "
     "climate–fisheries relationships.", False,
     [("Cold Pool & Bottom Temperature", "bering_bottom_observed"),
      ("Model Comparison", "bering_bottom_models"),
      ("Cold-Pool Position", "bering_cold_pool_position"),
      ("Ocean Conditions", "bering_ocean_health"),
      ("Catch × Bottom State", "bering_catch")]),
    ("Gulf of Alaska", "Bottom Conditions &amp; Climate–Fisheries Relationships",
     "Bottom-temperature conditions and catch–environment relationships for the Gulf shelf "
     "(survey index + MOM6 validation; no cold pool).", False,
     [("Bottom Temperature", "goa_bottom_observed"),
      ("Model Comparison", "goa_bottom_models"),
      ("Ocean Conditions", "goa_ocean_health"),
      ("Catch × Bottom State", "goa_catch")]),
    ("Aleutian Islands", "Bottom Conditions &amp; Climate–Fisheries Relationships",
     "Bottom-temperature conditions and catch–environment relationships for the Aleutian "
     "shelf (survey index + MOM6 validation; no cold pool).", False,
     [("Bottom Temperature", "ai_bottom_observed"),
      ("Model Comparison", "ai_bottom_models"),
      ("Ocean Conditions", "ai_ocean_health"),
      ("Catch × Bottom State", "ai_catch")]),
    ("Arctic", "Chukchi and Beaufort Shelf Ecosystems",
     "Modelled bottom-temperature conditions for the Arctic shelf (MOM6; model-only — no "
     "in-region survey or validation).", False,
     [("Bottom Temperature", "arctic_bottom_observed")]),
    ("Fishery Economics", "Commercial Harvest, Value &amp; Fleet",
     "Statewide landings plus groundfish and crab catch, ex-vessel &amp; wholesale value, price, "
     "effort, and fleet from the Economic SAFE (fishery-dependent — distinct from the survey).", False,
     [("Commercial Landings", "commercial_landings"),
      ("Catch & Ex-Vessel Value", "econ_catch_value"),
      ("Ex-Vessel Prices", "econ_prices"),
      ("Wholesale Production & Value", "econ_wholesale"),
      ("Fishing Effort & Labor", "econ_effort"),
      ("Fleet & Ownership", "econ_fleet"),
      ("Crabonomics", "econ_crab"),
      ("Cold Pool × Crabonomics", "eco_econ")]),
    ("Research", "Research Resources",
     "Literature summaries, technical notes, forecast development, and project research.", False,
     [("Overview", "research"),
      ("Literature Summaries", "literature"),
      ("Forecast Development", "forecast_development")]),
    ("Guides", "Documentation",
     "Documentation, methodology, and background material.", False,
     [("Dashboard Guide", "dashboard_guide"),
      ("Marine Heatwave Guide", "marine_heatwave_guide"),
      ("Bottom-State Guide", "bottom_state_guide"),
      ("Groundfish Economics Guide", "econ_safe_guide")]),
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
/* Resting look is unchanged; the lift + link panel only appear on hover. A solid background
   (matches the page) lets a hovered card float cleanly above its neighbours. */
.amed-card { border: 1px solid rgba(130,130,130,0.28); border-radius: 0.5rem;
    padding: 1.05rem 1.2rem; display: flex; flex-direction: column; position: relative;
    background: var(--background-color, #ffffff);
    transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
.amed-card:hover { transform: translateY(-8px) scale(1.02); z-index: 10;
    border-color: rgba(130,130,130,0.55);
    box-shadow: 0 18px 38px rgba(0,0,0,0.20), 0 6px 12px rgba(0,0,0,0.12); }
.amed-card-title { font-size: 1.12rem; font-weight: 700; margin-bottom: 0.3rem; }
.amed-card-sub { font-size: 0.97rem; font-weight: 600; opacity: 0.95; margin-bottom: 0.35rem; }
.amed-card-desc { font-size: 0.92rem; line-height: 1.45; opacity: 0.7; }
/* Related-page links: an ABSOLUTE dropdown anchored to the card's bottom edge, so revealing it on
   hover never changes the card's box. That is what keeps the grid from reflowing (rows are equal-
   height via grid-auto-rows) — otherwise a growing card would push every row and the hovered card
   would jitter out from under the cursor. */
.amed-card-links { position: absolute; left: 0; right: 0; top: 100%; z-index: 11;
    display: flex; flex-direction: column; gap: 0.18rem; padding: 0 1.2rem;
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(130,130,130,0.55); border-top: none; border-radius: 0 0 0.5rem 0.5rem;
    box-shadow: 0 18px 34px rgba(0,0,0,0.18);
    max-height: 0; overflow: hidden; opacity: 0;
    transition: max-height .25s ease, opacity .2s ease, padding .2s ease; }
.amed-card:hover .amed-card-links { max-height: 340px; opacity: 1; padding: 0.5rem 1.2rem 0.85rem; }
.amed-card-links a { font-size: 0.86rem; font-weight: 600; line-height: 1.5;
    color: var(--primary-color, #1f77b4); text-decoration: none; }
.amed-card-links a:hover { text-decoration: underline; }
.amed-card-tag { margin-top: auto; padding-top: 0.7rem; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.09em; text-transform: uppercase; opacity: 0.5; }
.amed-rule { border: none; border-top: 1px solid rgba(130,130,130,0.25); margin: 1.0rem 0 0.6rem; }
.amed-footer { font-size: 0.85rem; opacity: 0.6; }
@media (max-width: 1000px) { .amed-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .amed-grid { grid-template-columns: 1fr; } }
/* Featured Ask Deckhand banner — the assistant's front door. */
.amed-featured { display:flex; align-items:center; gap:1rem; border:1px solid rgba(21,101,192,0.35);
    border-radius:0.6rem; padding:1.05rem 1.3rem; margin:0.2rem 0 1.7rem;
    background:linear-gradient(180deg, rgba(21,101,192,0.07), rgba(21,101,192,0.02)); }
.amed-featured-icon { font-size:1.7rem; line-height:1; }
.amed-featured-body { flex:1; min-width:0; }
.amed-featured-title { font-size:1.2rem; font-weight:800; color:var(--primary-color,#1f77b4); }
.amed-featured-sub { font-size:0.98rem; opacity:0.82; margin-top:0.15rem; }
.amed-featured-cta a { display:inline-block; background:#1565c0; color:#fff !important; font-weight:700;
    font-size:0.95rem; text-decoration:none; padding:0.5rem 1.15rem; border-radius:0.5rem;
    white-space:nowrap; }
.amed-featured-cta a:hover { background:#0f4c99; }
</style>"""


def _card_html(title: str, concept: str, desc: str, under_dev: bool,
               links: list[tuple[str, str]] | None = None) -> str:
    parts = [f'<div class="amed-card-title">{title}</div>']
    if concept:
        parts.append(f'<div class="amed-card-sub">{concept}</div>')
    if desc:
        parts.append(f'<div class="amed-card-desc">{desc}</div>')
    if links:
        anchors = "".join(
            f'<a href="/{path}" target="_self">→ {label}</a>' for label, path in links
        )
        parts.append(f'<div class="amed-card-links">{anchors}</div>')
    if under_dev:
        parts.append('<div class="amed-card-tag">Under development</div>')
    return f'<div class="amed-card">{"".join(parts)}</div>'


def home() -> None:
    st.markdown(_HOME_CSS, unsafe_allow_html=True)
    st.title("🌊 Alaska Marine Ecosystems Dashboard")
    st.markdown('<div class="amed-subtitle">Climate • Ocean • Ecosystems • Fisheries</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="amed-intro">Climate, ocean, ecosystem, and fisheries indicators for '
        'Alaska marine ecosystems.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="amed-featured">'
        '<div class="amed-featured-icon">💬</div>'
        '<div class="amed-featured-body">'
        '<div class="amed-featured-title">Ask Deckhand</div>'
        '<div class="amed-featured-sub">Combine any indicators on this dashboard into charts, '
        'tables, or a slide deck.</div></div>'
        '<div class="amed-featured-cta"><a href="/assistant" target="_self">Try it →</a></div>'
        '</div>',
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
        '<hr class="amed-rule"><div class="amed-footer">Developed using NOAA observational '
        "and modelling products.</div>",
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
    # Front-door reference: the 12 ecosystem zones (one annotated map + cited provenance) that
    # every mask/aggregation/map/forecast on the board is built on. Path-registered docs page.
    "Study Regions": [
        st.Page("pages/study_regions.py", title="Study Regions", url_path="study_regions"),
    ],
    "Ask Deckhand": [
        st.Page("pages/assistant.py", title="Ask Deckhand", url_path="assistant"),
    ],
    # Two-level nav limit: the third level (Marine Heatwaves → Operational / Historical) lives
    # inside the hub page. Future climate indicators (SST anomalies, climate modes, outlooks)
    # become sibling pages here.
    "Alaska-wide Climate": [
        st.Page(marine_heatwaves_render, title="Marine Heatwaves", url_path="marine_heatwaves"),
        st.Page(mhw_forecast_render, title="MHW Forecast (NOAA PSL)", url_path="mhw_forecast"),
        st.Page("pages/driver_correlations.py", title="Climate Driver Links",
                url_path="driver_correlations"),
    ],
    "Bering Sea": [
        st.Page(lambda: bottom_observed_render(group="bering"),
                title="Cold Pool & Bottom Temperature", url_path="bering_bottom_observed"),
        st.Page(lambda: bottom_models_render(group="bering"),
                title="Model Comparison", url_path="bering_bottom_models"),
        st.Page("pages/cold_pool_position.py",
                title="Cold-Pool Position", url_path="bering_cold_pool_position"),
        st.Page(lambda: ocean_health_render(group="bering"),
                title="Ocean Conditions", url_path="bering_ocean_health"),
        st.Page(lambda: catch_render(group="bering"),
                title="Catch × Bottom State", url_path="bering_catch"),
    ],
    # GOA has no cold pool and only MOM6 covers it (Bering10K is out of domain), so it carries
    # the bottom-temperature + catch pages — not the Bering's model-comparison / cold-pool-
    # position pages (which need two models / a cold pool).
    "Gulf of Alaska": [
        st.Page(lambda: bottom_observed_render(group="goa"),
                title="Bottom Temperature", url_path="goa_bottom_observed"),
        st.Page(lambda: bottom_models_render(group="goa"),
                title="Model Comparison", url_path="goa_bottom_models"),
        st.Page(lambda: ocean_health_render(group="goa"),
                title="Ocean Conditions", url_path="goa_ocean_health"),
        st.Page(lambda: catch_render(group="goa"),
                title="Catch × Bottom State", url_path="goa_catch"),
    ],
    # Like the Gulf, the Aleutians have no cold pool and are MOM6-only — observed bottom-temperature,
    # a model-comparison page (continuous record + survey-replicated skill), and catch.
    "Aleutian Islands": [
        st.Page(lambda: bottom_observed_render(group="ai"),
                title="Bottom Temperature", url_path="ai_bottom_observed"),
        st.Page(lambda: bottom_models_render(group="ai"),
                title="Model Comparison", url_path="ai_bottom_models"),
        st.Page(lambda: ocean_health_render(group="ai"),
                title="Ocean Conditions", url_path="ai_ocean_health"),
        st.Page(lambda: catch_render(group="ai"),
                title="Catch × Bottom State", url_path="ai_catch"),
    ],
    # Arctic (Chukchi & Beaufort) is MODEL-ONLY — no AFSC survey, so no catch / cold-pool /
    # validation pages; just the modelled bottom-temperature conditions, clearly labelled.
    "Arctic": [
        st.Page(lambda: bottom_observed_render(group="arctic"),
                title="Bottom Temperature", url_path="arctic_bottom_observed"),
    ],
    # Commercial harvest (fishery-DEPENDENT) — statewide Alaska landings + ex-vessel value. Its
    # own top-level section because the FOSS feed resolves to statewide Alaska, not a survey
    # region; region-wise groundfish (NPFMC areas via AKFIN) would add pages here later.
    "Fishery Economics": [
        st.Page(commercial_landings_render, title="Commercial Landings",
                url_path="commercial_landings"),
        st.Page(econ_catch_value_render, title="Catch & Ex-Vessel Value",
                url_path="econ_catch_value"),
        st.Page(econ_prices_render, title="Ex-Vessel Prices", url_path="econ_prices"),
        st.Page(econ_wholesale_render, title="Wholesale Production & Value",
                url_path="econ_wholesale"),
        st.Page(econ_effort_render, title="Fishing Effort & Labor", url_path="econ_effort"),
        st.Page(econ_fleet_render, title="Fleet & Ownership", url_path="econ_fleet"),
        st.Page(econ_crab_render, title="Crabonomics", url_path="econ_crab"),
        st.Page(eco_econ_render, title="Cold Pool × Crabonomics", url_path="eco_econ"),
    ],
    "Research": [
        st.Page(research_render, title="Overview", url_path="research"),
        st.Page("pages/literature.py", title="Literature Summaries", url_path="literature"),
        st.Page("pages/forecast_development.py", title="Forecast Development",
                url_path="forecast_development"),
    ],
    "Guides": [
        st.Page(dashboard_guide, title="Dashboard Guide", url_path="dashboard_guide"),
        st.Page(marine_heatwave_guide, title="Marine Heatwave Guide",
                url_path="marine_heatwave_guide"),
        st.Page(bottom_state_guide, title="Bottom-State Guide",
                url_path="bottom_state_guide"),
        st.Page(econ_safe_guide, title="Groundfish Economics Guide",
                url_path="econ_safe_guide"),
    ],
}

pg = st.navigation(nav, position="top")
pg.run()
