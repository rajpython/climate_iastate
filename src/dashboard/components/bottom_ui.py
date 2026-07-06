"""Shared visual design for the Bering Sea bottom-state pages.

A single CSS injection + small HTML builders (page header with region chip, blue section
titles, colour-accented KPI cards, tinted callouts, footer) so the three pages — Cold Pool &
Bottom Temperature, Model Comparison, Catch × Bottom State — share one consistent, restrained
look with meaningful colour accents (green = position/area, blue = stats/models, red = warm
temperature, amber = caution). Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

GREEN, BLUE, RED, AMBER, PURPLE, SLATE, MUTED = (
    "#2e7d32", "#1565c0", "#c62828", "#b35900", "#6a3d9a", "#1f2a36", "#5f6b7a")

_CSS = """<style>
.bs-title { font-size:2.1rem; font-weight:800; color:#16407a; line-height:1.15; margin:0; }
.bs-subtitle { font-size:1.2rem; font-weight:700; color:#1565c0; margin:0.1rem 0 0.2rem; }
.bs-chip { border:1px solid rgba(130,130,130,0.35); border-radius:0.5rem; padding:0.35rem 0.75rem;
    font-size:0.9rem; color:#2b3a4a; background:rgba(130,130,130,0.06); white-space:nowrap; }
.bs-sec { font-size:0.82rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;
    color:#1565c0; margin-bottom:0.5rem; }
.bs-sec small { font-weight:400; color:#5f6b7a; text-transform:none; letter-spacing:0; }
.bs-grid { display:grid; gap:0.6rem; margin-bottom:0.7rem; }
.bs-kpi { border:1px solid rgba(130,130,130,0.25); border-radius:0.5rem; padding:0.7rem 0.85rem; }
.bs-kpi-label { font-size:0.78rem; font-weight:600; color:#2b3a4a; }
.bs-kpi-label small { font-weight:400; color:#5f6b7a; }
.bs-kpi-val { font-size:1.6rem; font-weight:800; line-height:1.15; margin:0.12rem 0; }
.bs-kpi-sub { font-size:0.74rem; color:#5f6b7a; }
.bs-callout { display:flex; gap:0.8rem; align-items:center; border-radius:0.6rem;
    padding:0.75rem 1rem; margin:0.3rem 0; }
.bs-callout-icon { font-size:1.5rem; }
.bs-callout-txt { font-size:0.95rem; color:#2b3a4a; }
.bs-footer { font-size:0.8rem; color:#7a8694; }
.bs-guidebtn { display:inline-block; border:1px solid rgba(130,130,130,0.4); border-radius:0.5rem;
    padding:0.45rem 0.9rem; color:#1565c0; text-decoration:none; font-weight:600; }
/* Hover tooltip (reliable + immediate, unlike the native title attribute). */
.bs-tip { position:relative; display:inline-block; cursor:help; color:#5f6b7a; }
.bs-tip .bs-tip-box { visibility:hidden; opacity:0; position:absolute; z-index:999;
    top:150%; left:50%; transform:translateX(-50%); width:250px; text-align:left;
    background:#1f2a36; color:#ffffff; padding:0.55rem 0.7rem; border-radius:0.45rem;
    font-size:0.76rem; font-weight:400; line-height:1.4; text-transform:none; letter-spacing:0;
    box-shadow:0 8px 22px rgba(0,0,0,0.28); pointer-events:none; white-space:normal;
    transition:opacity .12s ease; }
.bs-tip .bs-tip-box::after { content:""; position:absolute; bottom:100%; left:50%;
    transform:translateX(-50%); border:6px solid transparent; border-bottom-color:#1f2a36; }
.bs-tip:hover .bs-tip-box { visibility:visible; opacity:1; }
</style>"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str, region_label_text: str,
                caption: str = "") -> None:
    """Title (blue) + region chip (right), optional subtitle and caption."""
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"<div class='bs-title'>{icon} {title}</div>"
                    + (f"<div class='bs-subtitle'>{subtitle}</div>" if subtitle else ""),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='text-align:right; padding-top:0.6rem;'>"
                    f"<span class='bs-chip'>Region: {region_label_text}</span></div>",
                    unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div style='color:#5f6b7a; font-size:0.95rem; margin:0.2rem 0 0.4rem;'>"
                    f"{caption}</div>", unsafe_allow_html=True)


def section_title(title: str, note: str = "") -> None:
    note_html = f" <small>{note}</small>" if note else ""
    st.markdown(f"<div class='bs-sec'>{title}{note_html}</div>", unsafe_allow_html=True)


def kpi_card(label: str, value: str, value_color: str = "", sub: str = "",
             label_note: str = "", tip: str = "") -> str:
    """Return the HTML for one KPI card (compose with :func:`kpi_grid`).

    *tip* adds a native hover tooltip (title attribute) and a small ⓘ after the label.
    """
    note = f" <small>{label_note}</small>" if label_note else ""
    style = f" style='color:{value_color}'" if value_color else ""
    sub_html = f"<div class='bs-kpi-sub'>{sub}</div>" if sub else "<div class='bs-kpi-sub'>&nbsp;</div>"
    info = (f" <span class='bs-tip'>ⓘ<span class='bs-tip-box'>{tip}</span></span>") if tip else ""
    return (f"<div class='bs-kpi'><div class='bs-kpi-label'>{label}{note}{info}</div>"
            f"<div class='bs-kpi-val'{style}>{value}</div>{sub_html}</div>")


def kpi_grid(cards: list[str], cols: int | None = None, template: str | None = None) -> None:
    """Render KPI card HTML strings in a CSS grid (default: one equal column per card)."""
    cols = cols or len(cards)
    tmpl = template or f"repeat({cols}, minmax(0, 1fr))"
    st.markdown(f"<div class='bs-grid' style='grid-template-columns:{tmpl}'>"
                + "".join(cards) + "</div>", unsafe_allow_html=True)


def callout(body_html: str, icon: str = "ℹ️", tint: str = BLUE) -> None:
    st.markdown(
        f"<div class='bs-callout' style='border:1px solid {tint}55; background:{tint}0d;'>"
        f"<div class='bs-callout-icon' style='color:{tint}'>{icon}</div>"
        f"<div class='bs-callout-txt'>{body_html}</div></div>",
        unsafe_allow_html=True)


def footer(left_html: str, guide_url: str = "/bottom_state_guide") -> None:
    """Footer row: data-sources note (left) + 'Learn more in the guide' link (right)."""
    f1, f2 = st.columns([3, 1])
    with f1:
        st.markdown(f"<div class='bs-footer'>{left_html}</div>", unsafe_allow_html=True)
    with f2:
        st.markdown(f"<div style='text-align:right;'><a class='bs-guidebtn' target='_self' "
                    f"href='{guide_url}'>Learn more in the guide →</a></div>",
                    unsafe_allow_html=True)


# Shared table look (dark borders, bold shaded headers) — the single design for every data table
# across the bottom-state pages (catch breakdown, validation skill, model agreement, depth profile).
TABLE_STYLES = [
    {"selector": "", "props": [("border-collapse", "collapse"), ("border", "2px solid #2c3e50")]},
    {"selector": "th", "props": [("border", "1px solid #2c3e50"), ("padding", "9px 18px"),
                                 ("background-color", "#dfe6ee"), ("font-weight", "700"),
                                 ("font-size", "1.05rem"), ("text-align", "center"), ("color", "#1f2a36")]},
    {"selector": "td", "props": [("border", "1px solid #7b8a9a"), ("padding", "9px 18px"),
                                 ("text-align", "right"), ("font-size", "1.05rem")]},
    {"selector": "th.row_heading", "props": [("text-align", "left")]},
]


def when_note(text: str) -> None:
    """Prominent temporal-context line for a card — the date window **and** averaging method, so a
    reader never has to wonder whether a value is January or July. Place right after section_title."""
    st.markdown(
        f"<div style='margin:0.15rem 0 0.55rem 0; padding:0.35rem 0.65rem; background:#eef2f6; "
        f"border-left:3px solid {BLUE}; border-radius:0.25rem; font-size:0.9rem; color:#1f2a36;'>"
        f"🗓 <b>When:</b> {text}</div>", unsafe_allow_html=True)


def styled_table(df: pd.DataFrame, row_bg: dict | None = None, precision: int = 2,
                 na_rep: str = "—") -> str:
    """Render any DataFrame as the shared styled HTML table (dark borders, bold shaded headers).

    Numbers are formatted to ``precision`` decimals (ints keep a thousands separator; already-string
    cells pass through); ``row_bg`` maps an index label → a cell background colour for that row.
    Use as ``st.markdown(styled_table(df), unsafe_allow_html=True)``.
    """
    sty = df.style.format(precision=precision, na_rep=na_rep, thousands=",")
    if row_bg:
        sty = sty.apply(lambda r: [f"background-color:{row_bg.get(r.name, '')}"] * len(r), axis=1)
    return sty.set_table_styles(TABLE_STYLES).to_html()
