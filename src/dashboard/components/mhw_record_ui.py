"""Heatwave-record display layer for the MHW pages: vintage #7 (D1) banner, coverage-aware loaders,
the unknown-share band / hatching / ice band on area charts, and the 2016 SEBS panel.

The rule itself lives in :mod:`mhw.record` (pure, tested); this module only draws it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import AMBER, BLUE, SLATE, callout, kpi_card, kpi_grid, section_title
from mhw import record

UNKNOWN_FILL = "rgba(120,128,140,0.30)"
ICE_FILL = "rgba(120,180,230,0.35)"
HATCH_COLOR = "#5f6b7a"
_PLOTLY_DATE = "%b %d, %Y"


# ---------------------------------------------------------------------------
# Banner + loaders
# ---------------------------------------------------------------------------
def render_record_banner() -> None:
    """The record banner carried on every heatwave page."""
    callout(f"<b>{record.BANNER_TEXT}</b> Days where more than 25&nbsp;% of the zone could not be "
            "assessed are hatched and never shown as zero; the grey band is the unassessed share. "
            "<a href='/marine_heatwave_guide#the-heatwave-record-vintage-7-d1' target='_self'>"
            "What changed</a>.", icon="📌", tint=BLUE)


@st.cache_data(show_spinner="Loading heatwave record …", ttl=3600)
def load_days(zone: str) -> pd.DataFrame | None:
    """Region aggregate joined to its coverage sidecar, every day classified (see mhw.record)."""
    df = record.load_zone(zone)
    if df is None:
        return None
    df["year"] = df["date"].dt.year
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def zone_floor(zone: str) -> float:
    df = record.load_zone(zone)
    return float("nan") if df is None else df.attrs.get("floor", float("nan"))


def as_of_text() -> str:
    return f"as of {record.CERTIFIED_THROUGH_TEXT}"


# ---------------------------------------------------------------------------
# Chart layers
# ---------------------------------------------------------------------------
def _customdata(days: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        days["label"].to_numpy(),
        days["unknown_share"].to_numpy(float),
        days["share_unknown_run_or_regional"].to_numpy(float),
        days["share_unknown_outage"].to_numpy(float),
        days["share_observed_masked_ice"].to_numpy(float),
    ])


AREA_HOVER = (
    f"%{{x|{_PLOTLY_DATE}}}<br><b>%{{customdata[0]}}</b><br>"
    "Heatwave area: %{y:.1%}<br>"
    "Unknown share: %{customdata[1]:.1%} "
    "(ice unknown — run/regional %{customdata[2]:.1%}, outage %{customdata[3]:.1%})<br>"
    "Observed ice: %{customdata[4]:.1%}<extra></extra>"
)


def add_area_with_coverage(fig: go.Figure, days: pd.DataFrame, *, row: int | None = None,
                           col: int | None = None, color: str = "crimson",
                           fill: str | None = "rgba(220,20,60,0.15)") -> None:
    """Area line (gaps on no-coverage days) over the observed-ice band, the grey unknown band and
    the hatching of rejected days (unknown share > 25 %). All four share the zone-fraction axis."""
    rc = {} if row is None else {"row": row, "col": col or 1}
    x = days["date"]
    fig.add_trace(go.Scatter(
        x=x, y=days["share_observed_masked_ice"], mode="lines", line={"width": 0},
        fill="tozeroy", fillcolor=ICE_FILL, name="Observed ice", hoverinfo="skip",
        showlegend=False, legendgroup="ice"), **rc)
    fig.add_trace(go.Scatter(
        x=x, y=days["unknown_share"], mode="lines", line={"width": 0},
        fill="tozeroy", fillcolor=UNKNOWN_FILL, name="Unknown share", hoverinfo="skip",
        showlegend=False, legendgroup="unk"), **rc)
    hatched = days[days["hatched"]]
    if not hatched.empty:
        fig.add_trace(go.Bar(
            x=hatched["date"], y=np.ones(len(hatched)), width=86_400_000,
            marker={"color": "rgba(0,0,0,0)", "line": {"width": 0},
                    "pattern": {"shape": "/", "fgcolor": HATCH_COLOR, "size": 6, "solidity": 0.35}},
            name="Incomplete coverage (> 25 % unknown)", hoverinfo="skip", showlegend=False), **rc)
    fig.add_trace(go.Scatter(
        x=x, y=days["area_plot"], mode="lines", connectgaps=False,
        line={"color": color, "width": 1.6}, fill="tozeroy" if fill else None, fillcolor=fill,
        customdata=_customdata(days), hovertemplate=AREA_HOVER, name="Heatwave area",
        showlegend=False), **rc)
    fig.update_layout(barmode="overlay", bargap=0)


def coverage_legend_html() -> str:
    """Small legend line for the coverage layers (rendered under a chart)."""
    sw = ("<span style='display:inline-block;width:0.9rem;height:0.7rem;margin:0 0.3rem 0 0.8rem;"
          "vertical-align:middle;background:{bg};{extra}'></span>")
    return (
        "<div style='font-size:0.8rem;color:#5f6b7a;'>"
        + sw.format(bg="rgba(220,20,60,0.5)", extra="") + "heatwave area"
        + sw.format(bg=UNKNOWN_FILL, extra="") + "unknown share (not assessed)"
        + sw.format(bg=ICE_FILL, extra="") + "observed ice (a real zero)"
        + sw.format(bg="repeating-linear-gradient(45deg,#5f6b7a 0 2px,transparent 2px 5px)",
                    extra="") + "incomplete coverage (> 25 % unknown); a gap = no coverage"
        + "</div>")


def map_legend_html() -> str:
    sw = ("<span style='display:inline-block;width:0.9rem;height:0.7rem;margin:0 0.3rem 0 0.8rem;"
          "vertical-align:middle;background:{bg};'></span>")
    return ("<div style='font-size:0.8rem;color:#5f6b7a;'>"
            + sw.format(bg="rgba(220,60,40,0.65)") + "in a heatwave (detected)"
            + sw.format(bg=ICE_FILL) + "observed ice"
            + sw.format(bg=UNKNOWN_FILL) + "not assessed (unknown)"
            + "</div>")


def coverage_footnote(zone: str) -> str:
    floor = zone_floor(zone)
    if not np.isfinite(floor) or floor <= 0:
        floor_txt = "Every retained cell of this zone has satellite SST, so a zero here is a plain zero."
    else:
        floor_txt = (f"{floor:.2%} of this zone's retained area never has satellite SST (a constant floor); "
                     "a zero day with more unknown than that reads “none detected in the assessed area”.")
    return (f"Area is the share of the zone's fixed retained domain (142 near-shore cells are excluded "
            f"in every season). {floor_txt}")


# ---------------------------------------------------------------------------
# 2016 SEBS panel (m4's frozen table b7b25fbe; notes 13, 15, 16)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def load_panel2016() -> tuple[pd.DataFrame, pd.DataFrame] | None:
    d = record.panel2016_dir()
    p, o = d / "sebs_2016_panel_daily.csv", d / "sebs_2016_panel_history_overlap.csv"
    if not p.exists() or not o.exists():
        return None
    panel = pd.read_csv(p, parse_dates=["date"])
    keep = ["date", "gap_day", "oec_fills_area_frac", "est_fills_area_frac", "cov_fills_corroborated",
            "cov_fills_estimated_open", "cov_fills_estimated_ice", "cov_fills_unresolved",
            "release_scored_share"]
    return panel[keep], pd.read_csv(o, parse_dates=["date"])


def render_panel2016() -> None:
    """Southeast Bering, 18 April – 30 June 2016: what the evidence shows inside the satellite ice gap."""
    loaded = load_panel2016()
    if loaded is None:
        st.info("The 2016 panel table is not staged.")
        return
    panel, overlap = loaded
    gap = panel[panel["gap_day"]]
    section_title("2016 southeast Bering: inside the satellite ice gap",
                  "18 April – 30 June 2016 · a documented analysis beside the record, not a revision of it")
    callout(
        "OISST has no sea-ice field on these 74 days, so the record keeps them <b>incomplete coverage</b>. "
        "The heatwave is observed on both sides of the gap. Inside it, a separately processed satellite "
        "ice record corroborates open water across much of the zone through May. The panel shows that evidence "
        "beside the record; no fill has been adopted.", icon="🧭", tint=AMBER)
    kpi_grid([
        kpi_card("Observed + corroborated area", f"{gap['oec_fills_area_frac'].mean():.1%}", BLUE,
                 sub=f"gap-day mean · range {gap['oec_fills_area_frac'].min():.0%}–"
                     f"{gap['oec_fills_area_frac'].max():.0%}", label_note="headline"),
        kpi_card("Estimated area", f"{gap['est_fills_area_frac'].mean():.1%}", SLATE,
                 sub="gap-day mean", label_note="sensitivity"),
        kpi_card("Unresolved coverage", f"{gap['cov_fills_unresolved'].mean():.1%}", AMBER,
                 sub="gap-day mean"),
        kpi_card("D1 history-inferred share", f"{gap['release_scored_share'].mean():.1%}", SLATE,
                 sub="an inference, not an observation"),
    ], cols=4)

    fig = go.Figure()
    x = gap["date"]
    # A day with more than 25 % unresolved (4 May, the no-input day) is incomplete coverage, not a
    # zero: the series break there; the table keeps the frozen values.
    unres = gap["cov_fills_unresolved"] > record.HATCH_U
    fig.add_trace(go.Scatter(x=x, y=gap["oec_fills_area_frac"].where(~unres), mode="lines+markers",
                             line={"color": "crimson", "width": 2}, marker={"size": 4},
                             name="Observed + externally corroborated (headline)"))
    fig.add_trace(go.Scatter(x=x, y=gap["est_fills_area_frac"].where(~unres), mode="lines",
                             line={"color": "#7a8694", "width": 1.6, "dash": "dash"},
                             name="Estimated (sensitivity)"))
    fig.add_trace(go.Scatter(x=x, y=gap["cov_fills_unresolved"], mode="lines", line={"width": 0},
                             fill="tozeroy", fillcolor=UNKNOWN_FILL, name="Unresolved coverage"))
    fig.add_trace(go.Bar(x=x, y=np.ones(len(gap)), width=86_400_000, hoverinfo="skip",
                         marker={"color": "rgba(0,0,0,0)",
                                 "pattern": {"shape": "/", "fgcolor": HATCH_COLOR, "size": 6,
                                             "solidity": 0.2}},
                         name="Incomplete coverage (every gap day)"))
    fig.update_layout(height=360, template="plotly_white", barmode="overlay", bargap=0,
                      yaxis={"title": "share of zone", "tickformat": ".0%", "range": [0, 1]},
                      legend={"orientation": "h", "y": -0.2},
                      margin={"l": 55, "r": 20, "t": 20, "b": 40}, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key="panel2016_chart")

    tbl = gap.merge(overlap[["date", "history_inferred_area_also_corroborated_frac"]], on="date", how="left")
    tbl = pd.DataFrame({
        "Date": tbl["date"].dt.strftime("%d %b"),
        "Coverage": "incomplete coverage",
        "Observed + corroborated": tbl["oec_fills_area_frac"].round(3),
        "Estimated (sensitivity)": tbl["est_fills_area_frac"].round(3),
        "Corroborated": tbl["cov_fills_corroborated"].round(3),
        "Estimated open": tbl["cov_fills_estimated_open"].round(3),
        "Estimated ice": tbl["cov_fills_estimated_ice"].round(3),
        "Unresolved": tbl["cov_fills_unresolved"].round(3),
        "D1 history-inferred (inference)": tbl["release_scored_share"].round(3),
        "…of which corroborated": tbl["history_inferred_area_also_corroborated_frac"].round(3),
    })
    with st.expander("Daily table (74 gap days)"):
        st.dataframe(tbl, hide_index=True, use_container_width=True)
    st.caption(
        "How accurate is this kind of reconstruction? In the pre-registered replay for this window "
        "(southeast Bering, spring; 210 trials, verdict **keep unknown**), the estimated series missed "
        "7.7 % of real event-weight and invented 0.0 %, its event-days were 5.1 % short, and it carried "
        "events across the window edge 91 % of the time (daily-area error: median 0, 90th percentile "
        "0.36 points, worst −7.1 points). The headline recovered 65 % of real event-days and withheld 34 %. "
        "In the real 2016 gap, 39 % of the opened area is externally corroborated, 76 % of that directly "
        "supported, and no cell-day is contradicted. *Externally corroborated* means the separately "
        "processed NSIDC G02202 v6 sea-ice record reads low ice, with clean quality flags, at that cell on "
        "that day and the days either side. That record shares sensor heritage with OISST's ice field, and "
        "its weather filter can remove real ice, so a corroborated cell-day is not a certain observation "
        "of open water. "
        "Every gap day is incomplete coverage; the D1 history-inferred share is an inference from the "
        "absence of observed ice, printed beside and never added. On 4 May, the satellite record's "
        "no-input day, 49 % of the zone is unresolved, so the lines break there (the table's 0 is not an "
        "observed zero). "
        "Source: m4's frozen panel table (b7b25fbe), reproduced exactly by the dashboard; "
        "check results: admin's consolidated report of 11 October 2026.")
