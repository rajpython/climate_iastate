"""User Guide page — renders docs/user_guide.md and offers a PDF download.

Page config, fonts and sidebar styling are owned by the navigation shell
(Alaska_Dashboard.py); this script just renders the page body.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parents[3]
GUIDE_MD = ROOT / "docs" / "user_guide.md"
GUIDE_PDF = ROOT / "docs" / "user_guide.pdf"

st.title("📖 User Guide")


@st.cache_resource
def _load_guide() -> str:
    """Read user guide markdown once and cache."""
    return GUIDE_MD.read_text(encoding="utf-8")


@st.cache_resource
def _load_pdf() -> bytes | None:
    """Read PDF bytes once and cache, or return None if missing."""
    if GUIDE_PDF.exists():
        return GUIDE_PDF.read_bytes()
    return None


# ── PDF download button (top of page) ──────────────────────────────
pdf_bytes = _load_pdf()
if pdf_bytes:
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name="MHW_Dashboard_User_Guide.pdf",
        mime="application/pdf",
    )

st.divider()

# ── Render guide ────────────────────────────────────────────────────
try:
    guide_text = _load_guide()
    st.markdown(guide_text, unsafe_allow_html=False)
except FileNotFoundError:
    st.error("User guide not found. Expected at docs/user_guide.md")
