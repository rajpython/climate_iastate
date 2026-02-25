"""Panel 4 — Risk Gauge.

Displays a Green/Yellow/Red composite risk gauge built from percentile ranks
of area_frac, Ibar, Dbar, and Cbar, plus a 30-day trend sparkline.

Run:
    streamlit run src/dashboard/components/risk_gauge.py

Prerequisite:
    mhw-compute-risk --region goa
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from mhw.states.risk import RISK_THRESHOLDS, RISK_WEIGHTS, compute_risk_table

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).parents[3]
AGG_DIR = ROOT / "data" / "derived" / "aggregates_region"
RISK_DIR = ROOT / "data" / "derived" / "risk"

# Gauge colour bands (threshold, bar_color, bg_color)
GAUGE_STEPS = [
    {"range": [0,  33],  "color": "rgba(60,179,113,0.25)"},   # green
    {"range": [33, 66],  "color": "rgba(255,165,0,0.25)"},    # orange
    {"range": [66, 100], "color": "rgba(220,20,60,0.25)"},    # red
]
GAUGE_THRESHOLD_COLOR = {"green": "#2ecc40", "orange": "#ff851b", "red": "#ff4136"}

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading aggregates …", ttl=3600)
def load_aggregates(region: str) -> pd.DataFrame | None:
    p = AGG_DIR / f"region_daily_{region}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner="Loading risk table …", ttl=3600)
def load_risk_table(region: str) -> pd.DataFrame | None:
    p = RISK_DIR / f"risk_{region}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def list_regions() -> list[str]:
    return sorted(p.stem.replace("region_daily_", "") for p in AGG_DIR.glob("region_daily_*.parquet"))


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------
def _make_gauge(score: float, risk_level: str) -> go.Figure:
    bar_color = GAUGE_THRESHOLD_COLOR.get(
        {"Normal": "green", "Elevated": "orange", "High Risk": "red"}.get(risk_level, "green"),
        "gray"
    )
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            number={"suffix": "", "font": {"size": 42}},
            delta={"reference": 33, "valueformat": ".1f"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": bar_color, "thickness": 0.25},
                "steps": GAUGE_STEPS,
                "threshold": {
                    "line": {"color": bar_color, "width": 3},
                    "thickness": 0.85,
                    "value": score,
                },
            },
            title={"text": f"Composite Risk Score<br><span style='font-size:18px;color:{bar_color}'>{risk_level}</span>",
                   "font": {"size": 16}},
        )
    )
    fig.update_layout(height=280, margin={"l": 20, "r": 20, "t": 20, "b": 20})
    return fig


def _make_pct_bars(row: pd.Series) -> go.Figure:
    """Horizontal bar chart of individual metric percentile ranks."""
    labels  = list(RISK_WEIGHTS.keys())
    weights = list(RISK_WEIGHTS.values())
    pct_cols = [f"{c}_pct" for c in labels]
    values  = [float(row.get(c, 0)) for c in pct_cols]
    colors  = ["#2ecc40" if v <= 33 else "#ff851b" if v <= 66 else "#ff4136" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=[f"{lbl} (w={w:.0%})" for lbl, w in zip(labels, weights)],
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}th" for v in values],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f}th percentile<extra></extra>",
        )
    )
    fig.update_layout(
        title="Metric Percentile Ranks",
        xaxis={"range": [0, 110], "title": "Percentile rank"},
        yaxis={"autorange": "reversed"},
        height=220,
        margin={"l": 130, "r": 40, "t": 40, "b": 30},
        template="plotly_white",
    )
    fig.add_vline(x=33, line_dash="dot", line_color="green",  line_width=1)
    fig.add_vline(x=66, line_dash="dot", line_color="orange", line_width=1)
    return fig


def _make_sparkline(risk_df: pd.DataFrame, agg_df: pd.DataFrame, n_days: int = 30) -> go.Figure:
    """30-day composite risk trend + area_frac overlay."""
    r = risk_df.tail(n_days)
    a = agg_df.tail(n_days)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Risk score line
    fig.add_trace(
        go.Scatter(
            x=r["date"], y=r["composite_risk"],
            mode="lines+markers", marker_size=4,
            line={"color": "crimson", "width": 2},
            name="Risk score",
            hovertemplate="%{x|%Y-%m-%d}: risk = %{y:.1f}<extra></extra>",
        ),
        secondary_y=False,
    )

    # area_frac bar (secondary axis)
    fig.add_trace(
        go.Bar(
            x=a["date"], y=a["area_frac"],
            marker_color="rgba(70,130,180,0.35)",
            name="area_frac",
            hovertemplate="%{x|%Y-%m-%d}: frac = %{y:.4f}<extra></extra>",
        ),
        secondary_y=True,
    )

    # Risk level bands
    for lo, hi, step in [(0, 33, "rgba(60,179,113,0.08)"),
                         (33, 66, "rgba(255,165,0,0.08)"),
                         (66, 100, "rgba(220,20,60,0.08)")]:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=step, line_width=0, secondary_y=False)

    fig.update_layout(
        title=f"Risk Score Trend (last {n_days} days)",
        height=240,
        template="plotly_white",
        showlegend=True,
        legend={"x": 0.01, "y": 0.99},
        margin={"l": 50, "r": 50, "t": 40, "b": 30},
    )
    fig.update_yaxes(title_text="Composite risk (0–100)", range=[0, 105], secondary_y=False)
    fig.update_yaxes(title_text="area_frac", range=[0, 0.5], secondary_y=True)
    return fig


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="MHW Risk Gauge", layout="wide", page_icon="🚦")
    st.title("🚦 MHW Risk Gauge")

    # ---- Sidebar ----
    st.sidebar.header("Controls")

    regions = list_regions()
    if not regions:
        st.error("No aggregates found. Run: `mhw-aggregate --region goa ...`")
        return

    region = st.sidebar.selectbox("Region", regions, format_func=str.upper)

    # Auto-run risk computation if parquet is missing
    risk_path = RISK_DIR / f"risk_{region}.parquet"
    if not risk_path.exists():
        st.info("Risk table not found — running `mhw-compute-risk` …")
        result = subprocess.run(
            [sys.executable, "-m", "mhw.states.risk", "--region", region],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            st.error(f"mhw-compute-risk failed:\n{result.stderr}")
            return
        st.success("Risk table computed.")
        load_risk_table.clear()

    if st.sidebar.button("♻️ Recompute risk scores"):
        load_risk_table.clear()
        load_aggregates.clear()

    # ---- Load data ----
    risk_df = load_risk_table(region)
    agg_df  = load_aggregates(region)

    if risk_df is None or agg_df is None:
        st.error("Failed to load data.")
        return

    # Date selector (default: last available)
    min_date = risk_df["date"].dt.date.min()
    max_date = risk_df["date"].dt.date.max()
    selected_date = st.sidebar.date_input(
        "Reference date", value=max_date, min_value=min_date, max_value=max_date
    )

    row = risk_df[risk_df["date"].dt.date == selected_date]
    if row.empty:
        st.warning(f"No risk data for {selected_date}.")
        return
    row = row.iloc[0]

    score      = float(row["composite_risk"])
    risk_level = str(row["risk_level"])

    # ---- Layout: gauge + percentile bars ----
    left_col, right_col = st.columns([1, 1.6])

    with left_col:
        st.plotly_chart(_make_gauge(score, risk_level), use_container_width=True)

        # Key metric values for the selected date
        agg_row = agg_df[agg_df["date"].dt.date == selected_date]
        if not agg_row.empty:
            agg_row = agg_row.iloc[0]
            st.markdown(f"**{selected_date}**")
            mc1, mc2 = st.columns(2)
            mc1.metric("area_frac",  f"{agg_row['area_frac']:.4f}")
            mc2.metric("Ī (°C)",     f"{agg_row['Ibar']:.2f}")
            mc3, mc4 = st.columns(2)
            mc3.metric("D̄ (days)", f"{agg_row['Dbar']:.1f}")
            mc4.metric("C̄ (°C·days)", f"{agg_row['Cbar']:.2f}")

    with right_col:
        st.plotly_chart(_make_pct_bars(row), use_container_width=True)

        # Legend
        st.markdown(
            "**Risk levels:** "
            ":green[🟢 Normal (0–33)]  "
            ":orange[🟠 Elevated (33–66)]  "
            ":red[🔴 High Risk (66–100)]"
        )
        st.caption(
            f"Weights: area_frac {RISK_WEIGHTS['area_frac']:.0%}, "
            f"Ibar {RISK_WEIGHTS['Ibar']:.0%}, "
            f"Dbar {RISK_WEIGHTS['Dbar']:.0%}, "
            f"Cbar {RISK_WEIGHTS['Cbar']:.0%}.  "
            "Reference: 2023 test-year distribution (proxy until full backfill)."
        )

    # ---- 30-day sparkline ----
    st.markdown("---")
    st.plotly_chart(_make_sparkline(risk_df, agg_df, n_days=30), use_container_width=True)

    # ---- Yearly summary table ----
    with st.expander("Full risk table"):
        disp = risk_df[["date", "area_frac_pct", "Ibar_pct", "Dbar_pct",
                         "Cbar_pct", "composite_risk", "risk_level"]].copy()
        disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
        for col in ["area_frac_pct", "Ibar_pct", "Dbar_pct", "Cbar_pct", "composite_risk"]:
            disp[col] = disp[col].round(1)
        st.dataframe(disp, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
