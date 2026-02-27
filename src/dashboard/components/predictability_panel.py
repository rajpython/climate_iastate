"""Panel 3 — Predictability Context (AO / PDO).

Shows AO daily index, PDO monthly index, and MHW event metrics (area_frac,
Ibar) on a shared time axis so analysts can assess large-scale conditioning.

Run:
    streamlit run src/dashboard/components/predictability_panel.py
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
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).parents[3]
RAW_DIR = ROOT / "data" / "raw"
AGG_DIR = ROOT / "data" / "derived" / "aggregates_region"

_cfg = yaml.safe_load((ROOT / "config" / "climatology.yml").read_text())
AREA_THRESH = float(_cfg["regional_events"]["area_frac_threshold"])

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading AO index …", ttl=3600)
def load_ao() -> pd.DataFrame | None:
    p = RAW_DIR / "ao_daily.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner="Loading PDO index …", ttl=3600)
def load_pdo() -> pd.DataFrame | None:
    p = RAW_DIR / "pdo_monthly.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner="Loading aggregates …", ttl=3600)
def load_aggregates(region: str) -> pd.DataFrame | None:
    p = AGG_DIR / f"region_daily_{region}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def list_regions() -> list[str]:
    return sorted(p.stem.replace("region_daily_", "") for p in AGG_DIR.glob("region_daily_*.parquet"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _zero_line(fig, row: int, col: int = 1) -> None:
    fig.add_hline(y=0, line_width=0.8, line_dash="dot", line_color="gray", row=row, col=col)


def _add_event_shading(fig, dates: pd.Series, active: np.ndarray, n_rows: int) -> None:
    """Add salmon shading over MHW event periods across all subplots."""
    in_span = False
    for d, flag in zip(dates, active):
        if flag and not in_span:
            s = d
            in_span = True
        elif not flag and in_span:
            for r in range(1, n_rows + 1):
                fig.add_vrect(x0=s, x1=d, fillcolor="salmon", opacity=0.12,
                              layer="below", line_width=0, row=r, col=1)
            in_span = False
    if in_span:
        for r in range(1, n_rows + 1):
            fig.add_vrect(x0=s, x1=dates.iloc[-1], fillcolor="salmon",
                          opacity=0.12, layer="below", line_width=0, row=r, col=1)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Predictability Context", layout="wide", page_icon="🌐")
    st.title("🌐 Predictability Context — AO / PDO")

    # ---- Sidebar ----
    st.sidebar.header("Controls")

    regions = list_regions()
    region  = st.sidebar.selectbox("Region", regions or ["goa"], format_func=str.upper)

    window_options = {"90 days": 90, "180 days": 180, "1 year": 365, "All": 9999}
    window_label   = st.sidebar.selectbox("Display window", list(window_options.keys()), index=1)
    window         = window_options[window_label]

    show_pdo = st.sidebar.checkbox("Show PDO", value=True)
    show_mhw = st.sidebar.checkbox("Show MHW metrics", value=True)

    # ---- Load data ----
    ao_df  = load_ao()
    pdo_df = load_pdo()
    agg_df = load_aggregates(region) if show_mhw else None

    if ao_df is None:
        st.error("AO parquet not found. Run: `mhw-fetch-indices --ao-years 2 --pdo-years 5`")
        return

    # ---- Determine shared time window ----
    # Anchor on MHW aggregates when available (so AO/PDO align to the event period).
    # Fall back to recent AO window when no MHW data is loaded.
    if agg_df is not None and not agg_df.empty:
        agg_all = agg_df.tail(min(window, len(agg_df))).reset_index(drop=True)
        t_start = agg_all["date"].iloc[0]
        t_end   = agg_all["date"].iloc[-1]
        agg_win = agg_all
    else:
        ao_win  = ao_df.tail(min(window, len(ao_df))).reset_index(drop=True)
        t_start = ao_win["date"].iloc[0]
        t_end   = ao_win["date"].iloc[-1]
        agg_win = None

    # Filter AO and PDO to the same window
    ao_win  = ao_df[(ao_df["date"] >= t_start) & (ao_df["date"] <= t_end)].reset_index(drop=True)
    pdo_win = pdo_df[(pdo_df["date"] >= t_start) & (pdo_df["date"] <= t_end)] if pdo_df is not None and show_pdo else None

    # If no AO data in MHW window, fall back to latest AO and note the gap
    if ao_win.empty:
        n_ao = min(window, len(ao_df))
        ao_win = ao_df.tail(n_ao).reset_index(drop=True)
        st.info(f"AO data not available for the MHW period ({t_start.strftime('%b %d, %Y')} → "
                f"{t_end.strftime('%b %d, %Y')}). Showing most recent {n_ao} AO days instead.")

    # ---- Build figure ----
    row_titles = ["AO (daily)"]
    if show_pdo and pdo_win is not None:
        row_titles.append("PDO (monthly)")
    if show_mhw and agg_win is not None:
        row_titles += ["Area Fraction", "Mean Intensity (°C)"]

    n_rows = len(row_titles)
    row_heights = [1.0] * n_rows

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        subplot_titles=row_titles,
        vertical_spacing=0.07,
        row_heights=row_heights,
    )

    current_row = 1

    # -- AO --
    ao_colors = np.where(ao_win["ao"].values >= 0, "steelblue", "tomato")
    fig.add_trace(
        go.Bar(
            x=ao_win["date"], y=ao_win["ao"],
            marker_color=ao_colors.tolist(),
            name="AO",
            hovertemplate="%{x|%b %d, %Y}: AO = %{y:.3f}<extra></extra>",
        ),
        row=current_row, col=1,
    )
    _zero_line(fig, current_row)
    fig.update_yaxes(title_text="AO index", row=current_row, col=1, title_font={"size": 10})
    current_row += 1

    # -- PDO --
    if show_pdo and pdo_win is not None and not pdo_win.empty:
        pdo_colors = np.where(pdo_win["pdo"].values >= 0, "darkorange", "royalblue")
        fig.add_trace(
            go.Bar(
                x=pdo_win["date"], y=pdo_win["pdo"],
                marker_color=pdo_colors.tolist(),
                name="PDO",
                hovertemplate="%{x|%b %Y}: PDO = %{y:.3f}<extra></extra>",
            ),
            row=current_row, col=1,
        )
        _zero_line(fig, current_row)
        fig.update_yaxes(title_text="PDO index", row=current_row, col=1, title_font={"size": 10})
        current_row += 1

    # -- MHW metrics --
    active_flag = None
    if show_mhw and agg_win is not None and not agg_win.empty:
        active_flag = agg_win["area_frac"].values > AREA_THRESH

        # area_frac
        fig.add_trace(
            go.Scatter(
                x=agg_win["date"], y=agg_win["area_frac"],
                mode="lines", line={"color": "tomato", "width": 1.8},
                fill="tozeroy", fillcolor="rgba(255,99,71,0.15)",
                name="Area Fraction",
                hovertemplate="%{x|%b %d, %Y}: Area Fraction = %{y:.4f}<extra></extra>",
            ),
            row=current_row, col=1,
        )
        fig.add_hline(y=AREA_THRESH, line_dash="dash", line_color="darkred", line_width=1,
                      annotation_text="threshold", annotation_font_size=8,
                      row=current_row, col=1)
        fig.update_yaxes(title_text="fraction", row=current_row, col=1, title_font={"size": 10})
        current_row += 1

        # Ibar
        fig.add_trace(
            go.Scatter(
                x=agg_win["date"], y=agg_win["Ibar"],
                mode="lines", line={"color": "orangered", "width": 1.8},
                name="Mean Intensity (°C)",
                hovertemplate="%{x|%b %d, %Y}: Mean Intensity = %{y:.3f} °C<extra></extra>",
            ),
            row=current_row, col=1,
        )
        fig.update_yaxes(title_text="°C", row=current_row, col=1, title_font={"size": 10})

    # Event shading across all rows
    if active_flag is not None and agg_win is not None:
        _add_event_shading(fig, agg_win["date"], active_flag, n_rows)

    fig.update_layout(
        title=dict(text=f"Predictability Context — {region.upper()}  ({t_start.strftime('%b %d, %Y')} → {t_end.strftime('%b %d, %Y')})",
                   font={"size": 14}),
        height=220 * n_rows,
        showlegend=False,
        template="plotly_white",
        bargap=0.05,
        margin={"l": 60, "r": 20, "t": 70, "b": 40},
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---- Index summary ----
    st.subheader("Index summary")
    c1, c2, c3, c4 = st.columns(4)
    latest_ao = ao_win["ao"].iloc[-1]
    c1.metric("Latest AO", f"{latest_ao:.3f}", delta=None,
              help="Positive: strong polar vortex (cooler Arctic, milder mid-latitudes)")

    mean_ao = ao_win["ao"].mean()
    c2.metric("Mean AO (window)", f"{mean_ao:.3f}")

    if pdo_win is not None and not pdo_win.empty:
        latest_pdo = pdo_win["pdo"].iloc[-1]
        c3.metric("Latest PDO", f"{latest_pdo:.3f}",
                  help="Positive: warm NE Pacific; Negative: cool NE Pacific")
    else:
        c3.metric("Latest PDO", "—")

    if agg_win is not None and not agg_win.empty:
        mhw_event_days = int((agg_win["area_frac"] > AREA_THRESH).sum())
        c4.metric("MHW event days (window)", mhw_event_days)

    # ---- Regime annotation ----
    if pdo_win is not None and not pdo_win.empty:
        latest_pdo_val = float(pdo_win["pdo"].iloc[-1])
        ao_phase  = "AO+" if latest_ao  >= 0 else "AO−"
        pdo_phase = "PDO+" if latest_pdo_val >= 0 else "PDO−"
        regime = f"{ao_phase} / {pdo_phase}"
        color  = "red" if "PDO+" in regime else "blue"
        st.markdown(f"**Current regime:** :{color}[{regime}]  "
                    f"(PDO+ favours warm NE Pacific → elevated MHW risk)")


if __name__ == "__main__":
    main()
