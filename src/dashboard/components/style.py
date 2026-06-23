"""Shared dashboard styling.

Streamlit multipage has no global CSS hook, so each page calls
:func:`apply_explanatory_font` right after ``st.set_page_config`` to enlarge the
descriptive prose (paragraphs + captions) by ~1/3 for readability. Headings and the
data tables are unaffected (those carry their own sizing).
"""
from __future__ import annotations

import streamlit as st

_EXPLANATORY_CSS = """
<style>
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { font-size: 1.30rem; line-height: 1.5; }
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p { font-size: 1.15rem; }
</style>
"""


def apply_explanatory_font() -> None:
    """Enlarge descriptive paragraph + caption text on the current page (~1/3 larger)."""
    st.markdown(_EXPLANATORY_CSS, unsafe_allow_html=True)
