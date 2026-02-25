"""MHW State Dashboard — entry point.

Run:
    streamlit run src/dashboard/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="MHW State Dashboard",
    page_icon="🌊",
    layout="wide",
)

st.title("🌊 Marine Heatwave State Dashboard")
st.markdown(
    """
    High-latitude fisheries monitoring — Gulf of Alaska (GOA) and adjacent regions.
    **Select a page from the sidebar.**

    ---

    ### Page 1 — Operational
    | Panel | Description |
    |---|---|
    | 🗺️ **Live MHW Map** | Spatial heatmap of intensity, active flag, or duration for any date |
    | 📈 **Event Metrics** | Time series of area_frac, Ibar, Dbar, Cbar, Obar (last 60–365 days) |
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
