"""Shared data loaders + helpers for the commercial-economics (Economic SAFE) pages.

Reads the tidy parquets built by ``mhw-ingest-econ-safe`` (``data/raw/econ_safe/<id>.parquet``)
directly, and exposes the report registry + FMP-area labels so the pages stay thin. Mirrors
``components/coldpool_data.py`` for the bottom-ocean layer.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mhw.econ import areas
from mhw.econ.safe_reports import SAFE_REPORTS, get_report  # noqa: F401 (re-exported)

ROOT = Path(__file__).resolve().parents[3]
SAFE_DIR = ROOT / "data" / "raw" / "econ_safe"

# FMP-area display order for selectors.
FMP_ORDER = ("bsai", "goa", "ak")

# A high-contrast categorical palette. Colours are assigned to categories by *identity*
# (see category_colors), so a species/stock/fleet keeps the same colour across pages and
# regardless of how many are selected — never "always blue for the first one". Deliberately ONE
# colour per hue family (a single blue, green, purple, …) so two co-shown series never look alike.
ECON_PALETTE = ["#1565c0", "#ef6c00", "#2e7d32", "#c62828", "#8e24aa", "#00838f",
                "#c2185b", "#6d4c41", "#f9a825", "#455a64", "#9e9d24", "#5e35b1"]


def category_colors(categories) -> dict[str, str]:
    """Stable {category → colour}, assigned in the given order.

    Colours are handed out in the order *categories* are passed (first-seen, de-duplicated), so
    pass the full vocabulary **ordered by importance** (e.g. total landings/value, largest first).
    The most significant categories — the ones actually shown — then get the distinct leading
    palette colours, and only the negligible long tail can wrap onto a repeat. Each category's
    colour is fixed by identity (a single selection shows its own colour, not "always blue").
    """
    out: dict[str, str] = {}
    for c in categories:
        c = str(c)
        if c not in out:
            out[c] = ECON_PALETTE[len(out) % len(ECON_PALETTE)]
    return out


@st.cache_data(show_spinner=False, ttl=3600)
def load_safe_report(report_id: str) -> pd.DataFrame | None:
    """Load one Economic SAFE report's tidy parquet (None if not ingested)."""
    p = SAFE_DIR / f"{report_id}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def fmp_label(code: str) -> str:
    """Full FMP-area label for a code (e.g. 'goa' → 'Gulf of Alaska')."""
    return areas.fmp_area_label(code)


def year_slider(label: str, y0: int, y1: int, key: str,
                default: tuple[int, int] | None = None) -> tuple[int, int]:
    """A sidebar year-range slider that echoes the current selection in its own label.

    The narrow sidebar sometimes clips the blue value labels above the slider handles, so the
    selected span is repeated in the label text (always visible) — e.g. "Year range · 2000–2020".
    """
    default = default if default is not None else (y0, y1)
    cur = st.session_state.get(key, default)
    return st.sidebar.slider(f"{label}: {int(cur[0])}–{int(cur[1])}", y0, y1, default, key=key)


def by_total(df: pd.DataFrame, cat_col: str, val_col: str) -> list[str]:
    """Categories ordered by summed *val_col* (largest first) — the importance order for colours."""
    if df.empty or cat_col not in df.columns:
        return []
    return df.groupby(cat_col)[val_col].sum().sort_values(ascending=False).index.astype(str).tolist()


def available_areas(df: pd.DataFrame) -> list[str]:
    """FMP-area codes present in *df*, in display order."""
    if df is None or "area_code" not in df.columns:
        return []
    present = set(df["area_code"].dropna().unique())
    return [a for a in FMP_ORDER if a in present]


def stacked_bar(df: pd.DataFrame, cat_col: str, val_col: str, y_title: str,
                hover_fmt: str = ",.0f", colors: dict[str, str] | None = None,
                height: int = 400) -> None:
    """Stacked bar per year — for **additive** quantities (they sum to a meaningful total).

    Each category is a coloured segment; the full bar height is the total across the selected
    categories, so composition *and* total read at a glance. Use for landings, catch, value,
    harvest, wholesale value, effort-weeks — NOT for prices/shares/means (those don't sum).

    Behaviour:
    - **Colour follows identity.** Pass *colors* (from :func:`category_colors` over the full
      vocabulary) so each category keeps its own colour; falls back to a stable per-selection map.
    - **Largest at the bottom.** Segments are stacked by total magnitude over the shown years,
      biggest on the bottom and decreasing upward.
    - Hover shows the category name (bold) + year + value in a readable font.
    """
    if df.empty:
        return
    years = list(range(int(df["year"].min()), int(df["year"].max()) + 1))
    order = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False).index.tolist()
    cmap = colors or category_colors(order)
    fig = go.Figure()
    for cat in order:  # add largest first → it sits at the bottom of the stack
        s = df[df[cat_col] == cat].groupby("year")[val_col].sum().reindex(years)
        fig.add_trace(go.Bar(
            x=years, y=s.values, name=str(cat),
            marker_color=cmap.get(str(cat), ECON_PALETTE[0]),
            hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:" + hover_fmt + "}<extra></extra>"))
    fig.update_layout(
        barmode="stack", template="plotly_white", height=height,
        margin=dict(l=10, r=10, t=30, b=10), bargap=0.15,
        yaxis_title=y_title, xaxis_title="Year", font=dict(size=13),
        hovermode="closest", hoverlabel=dict(font_size=14, namelength=-1),
        legend=dict(orientation="h", y=1.14, font=dict(size=11)))
    fig.update_xaxes(dtick=5, tickformat="d")
    st.plotly_chart(fig, use_container_width=True)
