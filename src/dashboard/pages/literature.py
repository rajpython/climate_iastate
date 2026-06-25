"""Literature Summaries — curated, plain-language summaries of literature relevant to the
Alaska Marine Ecosystem platform.

A path-registered page (runs top-to-bottom, like ``cold_pool_position.py``). The first entry is
the marine-heatwave forecasting synthesis; the full text renders inline and the typeset PDF is
offered for download. Additional summaries are added as further dated entries below. Page config /
fonts are owned by the navigation shell.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

DOCS = Path(__file__).resolve().parents[3] / "docs"
SYNTHESIS_MD = "mhw_forecasting_synthesis.md"
SYNTHESIS_PDF = "mhw_forecasting_synthesis.pdf"

BLUE, SLATE = "#1565c0", "#5f6b7a"

_CSS = """<style>
.lit-title { font-size:2.1rem; font-weight:800; color:#16407a; line-height:1.15; margin:0; }
.lit-lead { font-size:1.0rem; color:#33414f; margin:0.4rem 0 0.2rem; max-width:80ch; }
.lit-sec { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;
    color:#1565c0; margin:0.2rem 0 0.5rem; }
.lit-card-title { font-size:1.18rem; font-weight:700; color:#16407a; margin:0 0 0.15rem; }
.lit-meta { font-size:0.8rem; color:#5f6b7a; margin-bottom:0.5rem; }
.lit-meta b { color:#2b3a4a; font-weight:600; }
.lit-summary { font-size:0.96rem; line-height:1.5; color:#2b3a4a; }
.lit-takeaway { font-size:0.93rem; line-height:1.45; color:#2b3a4a; }
.lit-footer { font-size:0.8rem; color:#7a8694; }
</style>"""


@st.cache_resource
def _read_text(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _pdf_bytes(name: str) -> bytes | None:
    path = DOCS / name
    return path.read_bytes() if path.exists() else None


st.markdown(_CSS, unsafe_allow_html=True)

st.markdown("<div class='lit-title'>📚 Literature Summaries</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='lit-lead'>Curated, plain-language summaries of literature relevant to Alaska "
    "marine ecosystems — the cold pool and bottom conditions, climate–fisheries relationships, "
    "and the forecasting of marine heatwaves. Each entry links to its source material.</div>",
    unsafe_allow_html=True,
)
st.divider()

# --- Featured entry: the MHW-forecasting synthesis ----------------------------------------
with st.container(border=True):
    st.markdown("<div class='lit-sec'>Marine-heatwave forecasting</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='lit-card-title'>Forecasting Marine Heatwaves in Alaska Shelf Seas: "
        "Methods, Predictability, and Validation Challenges</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='lit-meta'><b>Synthesis review</b> &nbsp;·&nbsp; June 2026 &nbsp;·&nbsp; "
        "Scope: Gulf of Alaska and the Bering, Chukchi &amp; Beaufort shelves</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='lit-summary'>A focused review of where marine-heatwave (MHW) forecasting "
        "stands for the Alaska shelf seas. The forecasting methods — coupled dynamical seasonal "
        "systems, machine-learning and hybrid models, linear inverse models, and statistical "
        "baselines — are mature elsewhere, and the physical mechanisms behind high-latitude "
        "temperature persistence are well studied. The gap is region-specific evaluation: there is "
        "little validated, benchmarked, trend-aware, probabilistic forecast skill demonstrated for "
        "Alaska shelf systems themselves.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='lit-sec' style='margin-top:0.8rem;'>Key takeaways</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<ul class='lit-takeaway'>"
        "<li>The problem is not a shortage of methods — it is the absence of <b>validated, "
        "benchmarked, probabilistic evaluation</b> for the Alaska shelf.</li>"
        "<li>Skill must be judged against <b>persistence and climatology</b>, which are strong "
        "baselines at high latitudes because of oceanic thermal inertia.</li>"
        "<li>The Gulf of Alaska (deep, open-ocean) and the Bering/Arctic shelves (shallow, "
        "ice-affected, bottom-driven) are <b>distinct systems</b> with different predictands.</li>"
        "<li><b>Trend and forecastable interannual variability must be separated</b>; conflating "
        "them overstates skill in a warming record.</li>"
        "<li>Predictability likely rests on two channels — <b>atmospheric teleconnections</b> and "
        "<b>subsurface ocean memory</b> — the latter essential to any Gulf-of-Alaska system.</li>"
        "</ul>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.1, 1.3, 1.4])
    pdf = _pdf_bytes(SYNTHESIS_PDF)
    if pdf is not None:
        c1.download_button("Download PDF", data=pdf, file_name=SYNTHESIS_PDF,
                           mime="application/pdf", use_container_width=True)
    c2.page_link("pages/forecast_development.py", label="Forecast development →",
                 icon="🧭", use_container_width=True)

    with st.expander("Read the full synthesis"):
        try:
            st.markdown(_read_text(SYNTHESIS_MD), unsafe_allow_html=False)
        except FileNotFoundError:
            st.error(f"Synthesis text not found: docs/{SYNTHESIS_MD}")

# --- Further entries (placeholder) --------------------------------------------------------
st.markdown("")
st.caption("Additional summaries — cold pool and bottom conditions, climate–fisheries "
           "relationships — are in preparation.")

st.divider()
st.markdown(
    "<div class='lit-footer'>Summaries are prepared to support the platform and are not "
    "peer-reviewed publications; consult the cited sources for authoritative detail.</div>",
    unsafe_allow_html=True,
)
