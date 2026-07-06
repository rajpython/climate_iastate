"""Ecosystem × Economics — exploratory joins between ecosystem state and commercial value.

The board's two halves meet here: the **ecosystem indicators** (cold-pool area, bottom
temperature, survey abundance) and the **commercial economics** (ex-vessel value, harvest). This
page overlays a chosen economic series with an ecosystem indicator and shows their relationship.

**These are descriptive, exploratory associations — NOT causal.** Fisheries economics depends on
management (quotas, closures), markets, and stock dynamics well beyond the plotted indicator; a
correlation here is a starting point for questions, not an effect estimate.

Reads existing board artifacts directly: cold-pool index (``data/raw/coldpool_index_observed_sebs``),
crab & groundfish Economic SAFE (``data/raw/econ_safe/*``), and survey CPUE
(``data/raw/catch_bottom_state_*``).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    PURPLE,
    SLATE,
    callout,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
    section_title,
)
from dashboard.components.econ_data import load_safe_report

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"

# Ecosystem indicators (from the observed EBS cold-pool index).
_ECO = {
    "EBS cold-pool area (≤ 2 °C)": ("area_lte2_km2", "Cold-pool area (km²)", ",.0f"),
    "EBS mean bottom temperature": ("mean_bottom_temp", "Mean bottom temp (°C)", ".2f"),
}

# Economic series: (kind, key, column, axis title, hover fmt). kind drives the loader.
_ECON = {
    "Snow crab — ex-vessel value": ("crab", "BERING SEA SNOW CRAB", "hpy_exv_nom",
                                    "Ex-vessel value (US$)", "$,.0f"),
    "Snow crab — harvest": ("crab", "BERING SEA SNOW CRAB", "hpy_soldmt",
                            "Harvest (metric tons)", ",.0f"),
    "Bristol Bay red king crab — ex-vessel value": ("crab", "BRISTOL BAY RED KING CRAB",
                                                    "hpy_exv_nom", "Ex-vessel value (US$)", "$,.0f"),
    "BSAI groundfish — ex-vessel value": ("gf", "All Groundfish", "exvessel_value",
                                          "Ex-vessel value (US$)", "$,.0f"),
}


# ---------------------------------------------------------------------------
# Annual series loaders (year → value)
# ---------------------------------------------------------------------------

def _eco_series(col: str) -> pd.DataFrame:
    p = RAW / "coldpool_index_observed_sebs.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["year", "value"])
    d = pd.read_parquet(p)[["year", col]].rename(columns={col: "value"})
    return d.dropna().sort_values("year").reset_index(drop=True)


def _econ_series(label: str) -> pd.DataFrame:
    kind, key, col, _, _ = _ECON[label]
    if kind == "crab":
        d = load_safe_report("crsafeexec01")
        if d is None:
            return pd.DataFrame(columns=["year", "value"])
        d = d[d["fishery_name"] == key][["year", col]].rename(columns={col: "value"})
    else:  # groundfish GFSAFE002 — BSAI, all sectors
        d = load_safe_report("gfsafe002")
        if d is None:
            return pd.DataFrame(columns=["year", "value"])
        d = d[(d["area_code"] == "bsai") & (d["harvest_sector"] == "All Sectors")
              & (d["species_group"] == key)][["year", col]].rename(columns={col: "value"})
    return d.dropna().sort_values("year").reset_index(drop=True)


def _survey_cpue(species_code: int, region: str = "EBS") -> pd.DataFrame:
    p = RAW / f"catch_bottom_state_{species_code}.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["year", "value"])
    d = pd.read_parquet(p)
    d = d[d["region"] == region]
    g = d.groupby("year", as_index=False)["cpue_kgkm2"].mean().rename(columns={"cpue_kgkm2": "value"})
    return g.dropna().sort_values("year").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def _pearson(a: pd.DataFrame, b: pd.DataFrame) -> tuple[float | None, int, pd.DataFrame]:
    """Inner-join two (year,value) frames; return (Pearson r, n, joined)."""
    j = a.merge(b, on="year", suffixes=("_x", "_y")).dropna()
    if len(j) < 3:
        return None, len(j), j
    r = float(np.corrcoef(j["value_x"], j["value_y"])[0, 1])
    return r, len(j), j


def _overlay(econ: pd.DataFrame, eco: pd.DataFrame, econ_title: str, eco_title: str,
             econ_fmt: str, eco_fmt: str) -> None:
    """Economic series as bars (left axis) + ecosystem indicator as a line (right axis)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=econ["year"], y=econ["value"], name=econ_title, marker_color=AMBER,
                         opacity=0.85, hovertemplate="%{x}: %{y:" + econ_fmt + "}<extra></extra>"))
    fig.add_trace(go.Scatter(x=eco["year"], y=eco["value"], name=eco_title, yaxis="y2",
                             mode="lines+markers", line=dict(color=BLUE, width=3),
                             marker=dict(size=6),
                             hovertemplate="%{x}: %{y:" + eco_fmt + "}<extra></extra>"))
    fig.update_layout(
        template="plotly_white", height=420, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Year", yaxis=dict(title=econ_title),
        yaxis2=dict(title=eco_title, overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.14, font=dict(size=11)), font=dict(size=13))
    st.plotly_chart(fig, use_container_width=True)


def _scatter(joined: pd.DataFrame, x_title: str, y_title: str) -> None:
    """Ecosystem (x) vs economic (y), points coloured by year."""
    fig = go.Figure(go.Scatter(
        x=joined["value_y"], y=joined["value_x"], mode="markers+text",
        text=joined["year"].astype(str), textposition="top center", textfont=dict(size=9),
        marker=dict(size=10, color=joined["year"], colorscale="Viridis", showscale=True,
                    colorbar=dict(title="Year")),
        hovertemplate="%{text}: (" + "%{x:.0f}, %{y:,.0f})<extra></extra>"))
    fig.update_layout(
        template="plotly_white", height=440, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=x_title, yaxis_title=y_title, font=dict(size=13))
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render() -> None:
    inject_css()
    st.sidebar.header("Controls")
    econ_label = st.sidebar.selectbox("Economic series", list(_ECON), index=0, key="ee_econ")
    eco_label = st.sidebar.selectbox("Ecosystem indicator", list(_ECO), index=0, key="ee_eco")

    page_header("🔗", "Ecosystem × Economics", "Eastern Bering Sea",
                "Eastern Bering Sea",
                caption=("Where the board's two halves meet — commercial value set against the "
                         "ecosystem indicators that describe the shelf it comes from."))
    callout(
        "These are <b>exploratory, descriptive</b> associations — <b>not causal</b>. Ex-vessel "
        "value is driven by management (quotas, closures), markets, and stock dynamics far beyond "
        "any single ecosystem indicator. Read a correlation here as a question to pursue, not an "
        "effect. Cold-pool &amp; temperature come from the "
        "<a target='_self' href='/bering_bottom_observed'>Bering Cold Pool</a> pages; economics "
        "from the Economic SAFE.",
        icon="🔎", tint=SLATE)

    econ = _econ_series(econ_label)
    eco = _eco_series(_ECO[eco_label][0])
    econ_axis, econ_fmt = _ECON[econ_label][3], _ECON[econ_label][4]
    _eco_col, eco_axis, eco_fmt = _ECO[eco_label]

    if econ.empty or eco.empty:
        st.warning("Underlying data not built. Run `mhw-ingest-econ-safe` / `mhw-fetch-coldpool`.")
        return

    r, n, joined = _pearson(econ, eco)

    with st.container(border=True):
        section_title("Overlay", note=f"{econ_label} vs {eco_label.lower()}")
        kpi_grid([
            kpi_card("Correlation (r)", f"{r:+.2f}" if r is not None else "—", PURPLE,
                     sub=f"n = {n} overlapping years"),
            kpi_card("Economic series", econ_label.split(" — ")[0], AMBER,
                     sub=econ_label.split(" — ")[-1] if " — " in econ_label else ""),
            kpi_card("Ecosystem indicator", eco_label.replace("EBS ", ""), BLUE,
                     sub="observed survey index"),
        ], cols=3)
        _overlay(econ, eco, econ_axis, eco_axis, econ_fmt, eco_fmt)

    with st.container(border=True):
        section_title("Relationship", note="each point is a year (colour = year)")
        if r is not None:
            _scatter(joined, eco_axis, econ_axis)
            callout(
                f"Across {n} overlapping years, {econ_label.lower()} and {eco_label.lower()} have a "
                f"Pearson correlation of <b>r = {r:+.2f}</b>. Association only — see the caveat above.",
                icon="📈", tint=SLATE)
        else:
            st.info("Too few overlapping years to show a relationship.")

    _harvest_vs_survey_panel()

    footer("Sources: AFSC observed cold-pool index; NOAA Economic SAFE (via AKFIN); AFSC "
           "bottom-trawl survey CPUE. Exploratory / non-causal.", guide_url="/econ_safe_guide")


def _harvest_vs_survey_panel() -> None:
    """Fixed spotlight: snow-crab commercial harvest vs its fishery-independent survey index."""
    harvest = _econ_series("Snow crab — harvest")
    cpue = _survey_cpue(68580, "EBS")
    if harvest.empty or cpue.empty:
        return
    r, n, _ = _pearson(harvest, cpue)
    with st.container(border=True):
        section_title("Commercial harvest vs. survey abundance",
                      note="snow crab: what was landed vs the fishery-independent index")
        callout(
            "<b>Two independent measures of the same stock.</b> Commercial <b>harvest</b> "
            "(fishery-dependent, Economic SAFE) and <b>survey CPUE</b> (fishery-independent, AFSC "
            f"bottom-trawl). Their raw correlation over {n} years is <b>weak (r = {r:+.2f})</b> — "
            "and that is the point: harvest is <b>quota-managed</b>, so it does not freely track "
            "abundance, whereas the survey measures the population directly. That is exactly why "
            "the <b>survey</b>, not landings, is the abundance index managers rely on.",
            icon="🦀", tint=PURPLE)
        _overlay(harvest, cpue, "Commercial harvest (metric tons)", "Survey CPUE (kg/km²)", ",.0f", ",.1f")
