"""Cold-Pool Guide page — renders docs/cold_pool_user_guide.md.

Plain-language explainer for the cold-pool / bottom-state products. Page config and fonts are
owned by the navigation shell (Alaska_Dashboard.py); this module just renders the body.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
GUIDE_MD = ROOT / "docs" / "cold_pool_user_guide.md"


@st.cache_resource
def _load_guide() -> str:
    return GUIDE_MD.read_text(encoding="utf-8")


def render() -> None:
    st.title("❄️ Cold-Pool Guide")
    try:
        st.markdown(_load_guide(), unsafe_allow_html=False)
    except FileNotFoundError:
        st.error("Cold-pool guide not found. Expected at docs/cold_pool_user_guide.md")
