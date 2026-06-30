"""Panel 2 — Event Characterization Time Series.

Displays a multi-metric time series of region-level aggregated MHW metrics:
area_frac, Ibar, Dbar, Cbar, Obar with event shading.

Run:
    streamlit run src/dashboard/components/ts_event_metrics.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Shared MHW chart/table styling — bigger, bolder axis fonts + darker table numbers.
# ---------------------------------------------------------------------------

def mhw_plot(fig, **kwargs) -> None:
    """Render an MHW Plotly chart with enlarged, bold x/y axis fonts (~+30% over the default 12 px)
    for readability on the climate pages. Applies to every cartesian axis in the figure."""
    fig.update_xaxes(tickfont={"size": 15, "weight": "bold"},
                     title_font={"size": 14, "weight": "bold"})
    fig.update_yaxes(tickfont={"size": 15, "weight": "bold"},
                     title_font={"size": 14, "weight": "bold"})
    st.plotly_chart(fig, **kwargs)


def mhw_table(df, **kwargs) -> None:
    """Render an MHW dataframe with darker, bolder cell text (more legible numbers)."""
    sty = df.style.set_properties(**{"color": "#10243f", "font-weight": "600"})
    st.dataframe(sty, **kwargs)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).parents[3]
AGG_DIR = ROOT / "data" / "derived" / "aggregates_region"

_cfg = yaml.safe_load((ROOT / "config" / "climatology.yml").read_text())
AREA_THRESH = float(_cfg["regional_events"]["area_frac_threshold"])

METRIC_DEFS = [
    ("area_frac", "Area Fraction",      "fraction",  "steelblue"),
    ("Ibar",      "Mean Intensity",     "°C",        "orangered"),
    ("Dbar",      "Mean Duration",      "days",      "mediumpurple"),
    ("Cbar",      "Cumul. Intensity",   "°C·days",   "seagreen"),
    ("Obar",      "Onset Rate",         "°C/day",    "darkorange"),
]

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading aggregates …", ttl=3600)
def load_aggregates(region: str) -> pd.DataFrame | None:
    path = AGG_DIR / f"region_daily_{region}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


#: Canonical region ordering — south to north (sub-arctic Pacific → Arctic).
#: GOA leads as the largest U.S. fisheries footprint among the five.
#: Matches the order in config/regions.geojson; any unknown region falls to the end.
# ESR ecosystem regions, grouped: each combined area immediately followed by its subareas,
# then the Arctic shelves. Bering: ebs (= sebs+nbs); GOA: goa (= wgoa+egoa); AI: ai (= W+C+E).
REGION_ORDER = ["ebs", "sebs", "nbs", "goa", "wgoa", "egoa",
                "ai", "ai_west", "ai_central", "ai_east", "chukchi", "beaufort"]

REGION_NAMES = {
    "ebs": "Eastern Bering Sea", "sebs": "Southeastern Bering Sea", "nbs": "Northern Bering Sea",
    "goa": "Gulf of Alaska", "wgoa": "Western Gulf of Alaska", "egoa": "Eastern Gulf of Alaska",
    "ai": "Aleutian Islands", "ai_west": "Western Aleutians",
    "ai_central": "Central Aleutians", "ai_east": "Eastern Aleutians",
    "chukchi": "Chukchi Sea", "beaufort": "Beaufort Sea",
}
_COMBINED_REGIONS = {"ebs", "goa", "ai"}            # ESR ecosystem-area rollups (= sum of subareas)
_SUBAREA_REGIONS = {"sebs", "nbs", "wgoa", "egoa",  # ESR subareas (indented under their area)
                    "ai_west", "ai_central", "ai_east"}


def _region_key(r: str) -> tuple:
    """Sort regions by canonical grouped order; unknowns fall to the end alphabetically."""
    return (REGION_ORDER.index(r), r) if r in REGION_ORDER else (len(REGION_ORDER), r)


def region_menu_label(rid: str) -> str:
    """Dropdown label grouping an ecosystem area with its subareas (combined = '— all';
    subareas indented). Used by the MHW region selectors."""
    name = REGION_NAMES.get(rid, rid.upper())
    if rid in _COMBINED_REGIONS:
        return f"{name} — all"
    if rid in _SUBAREA_REGIONS:
        return f"   · {name}"
    return name


@st.cache_data(show_spinner=False, ttl=3600)
def list_regions() -> list[str]:
    return sorted(
        (p.stem.replace("region_daily_", "") for p in AGG_DIR.glob("region_daily_*.parquet")),
        key=_region_key,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _active_spans(dates: pd.Series, active: np.ndarray) -> list[tuple]:
    """Return list of (start_date, end_date) for contiguous active periods."""
    spans = []
    in_span = False
    for d, flag in zip(dates, active):
        if flag and not in_span:
            s = d
            in_span = True
        elif not flag and in_span:
            spans.append((s, d))
            in_span = False
    if in_span:
        spans.append((s, dates.iloc[-1]))
    return spans


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="MHW Event Metrics", layout="wide", page_icon="📈")
    st.title("📈 Event Characterization Time Series")

    # ---- Sidebar ----
    st.sidebar.header("Controls")

    regions = list_regions()
    if not regions:
        st.error(f"No region_daily parquet files found in {AGG_DIR}.\n"
                 "Run: `mhw-aggregate --region goa --start 2023-01-01 --end 2023-12-31`")
        return

    region = st.sidebar.selectbox("Region", regions, format_func=str.upper)
    df = load_aggregates(region)
    if df is None or df.empty:
        st.error(f"No data for region '{region}'.")
        return

    # Window selector
    n_days_total = len(df)
    window_options = {
        "30 days":  30,
        "60 days":  60,
        "90 days":  90,
        "180 days": 180,
        "1 year":   365,
        "Full period": n_days_total,
    }
    window_label = st.sidebar.selectbox("Display window", list(window_options.keys()), index=4)
    window = window_options[window_label]
    df_win = df.tail(window).reset_index(drop=True)

    # Metric toggles
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Metrics to show**")
    show = {col: st.sidebar.checkbox(label, value=True)
            for col, label, *_ in METRIC_DEFS}

    active_metrics = [(col, label, ylabel, color)
                      for col, label, ylabel, color in METRIC_DEFS if show[col]]
    if not active_metrics:
        st.warning("Select at least one metric.")
        return

    # ---- Build figure ----
    n_rows = len(active_metrics)
    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        subplot_titles=[m[1] for m in active_metrics],
        vertical_spacing=0.07,
    )

    active_flag = df_win["area_frac"].values > AREA_THRESH
    spans = _active_spans(df_win["date"], active_flag)

    for row, (col, label, ylabel, color) in enumerate(active_metrics, start=1):
        fig.add_trace(
            go.Scatter(
                x=df_win["date"], y=df_win[col],
                mode="lines",
                name=label,
                line={"color": color, "width": 1.8},
                hovertemplate=f"%{{x|%b %d, %Y}}: %{{y:.3f}} {ylabel}<extra></extra>",
            ),
            row=row, col=1,
        )
        fig.update_yaxes(title_text=ylabel, row=row, col=1, title_font={"size": 10})

        # Event shading
        for span_start, span_end in spans:
            fig.add_vrect(
                x0=span_start, x1=span_end,
                fillcolor="salmon", opacity=0.15,
                layer="below", line_width=0,
                row=row, col=1,
            )

        # Threshold line on area_frac panel
        if col == "area_frac":
            fig.add_hline(
                y=AREA_THRESH,
                line_dash="dash", line_color="red", line_width=1,
                annotation_text="event threshold",
                annotation_font_size=9,
                row=row, col=1,
            )

    fig.update_layout(
        title=dict(
            text=f"MHW Event Metrics — {region.upper()}  (last {window} days)",
            font={"size": 15},
        ),
        height=220 * n_rows,
        showlegend=False,
        template="plotly_white",
        margin={"l": 60, "r": 20, "t": 60, "b": 40},
    )

    mhw_plot(fig, use_container_width=True)

    # ---- Summary table ----
    st.subheader("Event summary")
    active_days  = int((df_win["area_frac"] > 0).sum())
    event_days   = int((df_win["area_frac"] > AREA_THRESH).sum())
    inactive_days = int((df_win["area_frac"] == 0).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Window",         f"{window} days")
    c2.metric("Event Days", event_days)
    c3.metric("Any-active days",    active_days)
    c4.metric("Inactive days",      inactive_days)

    if event_days > 0:
        peak = df_win.loc[df_win["area_frac"].idxmax()]
        st.markdown(
            f"**Peak event day:** {peak['date'].strftime('%b %d, %Y')} — "
            f"Area Fraction = **{peak['area_frac']:.4f}**, "
            f"Mean Intensity = {peak['Ibar']:.2f} °C, "
            f"Mean Duration = {peak['Dbar']:.1f} days, "
            f"Cumul. Intensity = {peak['Cbar']:.2f} °C·days"
        )

    # Recent tail table
    with st.expander("Last 14 days (data table)"):
        tail14 = df_win.tail(14).copy()
        tail14["date"] = tail14["date"].dt.strftime("%b %d, %Y")
        for col in ["area_frac", "Ibar", "Dbar", "Cbar", "Obar"]:
            tail14[col] = tail14[col].round(4)
        from dashboard.components.labels import DISPLAY_NAMES
        tail14 = tail14.rename(columns=DISPLAY_NAMES)
        st.dataframe(tail14, use_container_width=True, hide_index=True)

    from dashboard.components.labels import metric_legend
    st.caption(metric_legend())


if __name__ == "__main__":
    main()
