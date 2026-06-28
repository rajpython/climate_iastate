"""Guides — rendered markdown documentation, matching the platform architecture.

Three guides (no documentation sprawl):
  • Dashboard Guide       — platform-level orientation     (docs/dashboard_guide.md)
  • Marine Heatwave Guide — Alaska-wide MHW indicators      (docs/marine_heatwave_guide.md)
  • Bottom-State Guide    — bottom state, all regions       (docs/bottom_state_guide.md)

Each markdown file carries its own H1 title, so this module just renders it. Page config and
fonts are owned by the navigation shell.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

DOCS = Path(__file__).resolve().parents[3] / "docs"


@st.cache_resource
def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _render(filename: str) -> None:
    try:
        st.markdown(_read(filename), unsafe_allow_html=False)
    except FileNotFoundError:
        st.error(f"Guide not found: docs/{filename}")


def dashboard_guide() -> None:
    _render("dashboard_guide.md")


def marine_heatwave_guide() -> None:
    _render("marine_heatwave_guide.md")


def bottom_state_guide() -> None:
    _render("bottom_state_guide.md")
