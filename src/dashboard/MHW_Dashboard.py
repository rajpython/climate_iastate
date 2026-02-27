"""MHW State Dashboard — entry point.

Run:
    streamlit run src/dashboard/MHW_Dashboard.py
"""
import streamlit as st

st.set_page_config(
    page_title="MHW State Dashboard",
    page_icon="🌊",
    layout="wide",
)

# -- Sidebar cosmetics (injected on every page for persistence) --
_SIDEBAR_CSS = """<style>
/* Larger, bolder app name in sidebar */
[data-testid="stSidebarNavItems"] li:first-child a span {
    font-size: 1.3rem;
    font-weight: 700;
}
/* Hide page-icon images (emoji bullets) in sidebar nav */
[data-testid="stSidebarNavItems"] img,
[data-testid="stSidebarNavItems"] svg {
    display: none !important;
}
/* Add bullet before subpage names */
[data-testid="stSidebarNavItems"] li:not(:first-child) a span::before {
    content: "\\2022\\00a0";
}
</style>"""
st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

st.title("🌊 Marine Heatwave State Dashboard")
st.markdown(
    """
    Gulf of Alaska (GOA) and adjacent high-latitude North Pacific and Arctic regions.
    **Select a page from the sidebar.**

    ---

    ### Page 1 — Operational
    | Panel | Description |
    |---|---|
    | 🗺️ **Live MHW Map** | Spatial heatmap of intensity, duration, cumulative intensity, onset speed, and active flag for any date |
    | 📈 **Event Metrics** | Time series of Area Fraction, Mean Intensity, Mean Duration, Cumul. Intensity, Onset Rate |
    | 🌐 **Predictability** | AO/PDO indices alongside MHW event metrics |
    | 🚦 **Risk Gauge** | Composite percentile-based risk score with 30-day trend |

    ### Page 2 — Historical (1982–2024)
    | Panel | Description |
    |---|---|
    | 📊 **Annual Burden** | Year-by-year MHW activity bar chart with Blob annotation |
    | 🔍 **Event Explorer** | Year selector → detailed event timeline and stats |
    | 📉 **Distributions** | Metric histograms with percentile rulers |
    | 🌊 **Regime Analysis** | AO± × PDO± box plots over full backfill |
    """
)

st.info("Navigate with the **sidebar** (← left) — use ▸ to expand if hidden.")

st.sidebar.success("Select a page above.")
