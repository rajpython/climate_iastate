"""Page 3 — User Guide.

Renders docs/user_guide.md as a Streamlit page and offers a PDF download.

Run standalone:
    streamlit run src/dashboard/pages/3_Guide.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parents[3]
GUIDE_MD = ROOT / "docs" / "user_guide.md"
GUIDE_PDF = ROOT / "docs" / "user_guide.pdf"

st.set_page_config(page_title="User Guide", layout="wide", page_icon="")
st.markdown("""<style>
[data-testid="stSidebarNavItems"] li:first-child a span {
    font-size: 1.3rem; font-weight: 700;
}
[data-testid="stSidebarNavItems"] img,
[data-testid="stSidebarNavItems"] svg { display: none !important; }
[data-testid="stSidebarNavItems"] li:not(:first-child) a span::before {
    content: "\\2022\\00a0";
}
</style>""", unsafe_allow_html=True)
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
