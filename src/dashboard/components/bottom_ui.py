"""Shared visual design for the Bering Sea bottom-state pages.

A single CSS injection + small HTML builders (page header with region chip, blue section
titles, colour-accented KPI cards, tinted callouts, footer) so the three pages — Cold Pool &
Bottom Temperature, Model Comparison, Catch × Bottom State — share one consistent, restrained
look with meaningful colour accents (green = position/area, blue = stats/models, red = warm
temperature, amber = caution). Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

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
             label_note: str = "") -> str:
    """Return the HTML for one KPI card (compose with :func:`kpi_grid`)."""
    note = f" <small>{label_note}</small>" if label_note else ""
    style = f" style='color:{value_color}'" if value_color else ""
    sub_html = f"<div class='bs-kpi-sub'>{sub}</div>" if sub else "<div class='bs-kpi-sub'>&nbsp;</div>"
    return (f"<div class='bs-kpi'><div class='bs-kpi-label'>{label}{note}</div>"
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
