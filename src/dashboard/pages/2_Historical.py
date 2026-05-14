"""Page 2 — Historical Analysis (1982–present).

Four panels in tabs:
  📊  Annual MHW Burden bar chart
  🔍  Event Explorer — year selector + event timeline
  📉  Metric Distributions — histograms with percentile rulers
  🌊  Regime Analysis — AO± × PDO± box plots

Run standalone:
    streamlit run src/dashboard/pages/2_Historical.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml
from plotly.subplots import make_subplots

ROOT    = Path(__file__).parents[3]
AGG_DIR = ROOT / "data" / "derived" / "aggregates_region"
RAW_DIR = ROOT / "data" / "raw"

_cfg = yaml.safe_load((ROOT / "config" / "climatology.yml").read_text())
AREA_THRESH  = float(_cfg["regional_events"]["area_frac_threshold"])
REGIME_ORDER = ["AO+ / PDO+", "AO+ / PDO−", "AO− / PDO+", "AO− / PDO−"]
REGIME_COLOR = {
    "AO+ / PDO+": "#e74c3c",
    "AO+ / PDO−": "#3498db",
    "AO− / PDO+": "#e67e22",
    "AO− / PDO−": "#2ecc71",
}
_PLOTLY_DATE = "%b %d, %Y"        # e.g. "Feb 24, 2024"

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading aggregates …", ttl=3600)
def _load_agg(region: str) -> pd.DataFrame | None:
    p = AGG_DIR / f"region_daily_{region}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner="Loading AO …", ttl=3600)
def _load_ao() -> pd.DataFrame | None:
    p = RAW_DIR / "ao_daily.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner="Loading PDO …", ttl=3600)
def _load_pdo() -> pd.DataFrame | None:
    p = RAW_DIR / "pdo_monthly.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M")
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def _list_regions() -> list[str]:
    # South-to-north canonical order; see ts_event_metrics.REGION_ORDER for rationale.
    from dashboard.components.ts_event_metrics import _region_key
    return sorted(
        (p.stem.replace("region_daily_", "") for p in AGG_DIR.glob("region_daily_*.parquet")),
        key=_region_key,
    )


@st.cache_data(show_spinner="Building annual summary …", ttl=3600)
def _annual_summary(region: str) -> pd.DataFrame:
    df = _load_agg(region)
    if df is None:
        return pd.DataFrame()
    return df.groupby("year").agg(
        rows       =("date",      "count"),
        max_af     =("area_frac", "max"),
        mean_af    =("area_frac", "mean"),
        event_days =("area_frac", lambda x: (x > AREA_THRESH).sum()),
        max_Ibar   =("Ibar",      "max"),
        max_Dbar   =("Dbar",      "max"),
        max_Cbar   =("Cbar",      "max"),
    ).reset_index()


@st.cache_data(show_spinner="Joining regime data …", ttl=3600)
def _regime_df(region: str) -> pd.DataFrame:
    df  = _load_agg(region)
    ao  = _load_ao()
    pdo = _load_pdo()
    if df is None or ao is None or pdo is None:
        return pd.DataFrame()

    merged = df.merge(ao[["date", "ao"]], on="date", how="inner")
    merged["year_month"] = merged["date"].dt.to_period("M")
    merged = merged.merge(pdo[["year_month", "pdo"]], on="year_month", how="left")
    merged = merged.dropna(subset=["ao", "pdo"])

    merged["ao_phase"]  = np.where(merged["ao"]  >= 0, "AO+", "AO−")
    merged["pdo_phase"] = np.where(merged["pdo"] >= 0, "PDO+", "PDO−")
    merged["regime"]    = merged["ao_phase"] + " / " + merged["pdo_phase"]
    return merged

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Historical Analysis", layout="wide", page_icon="")
st.markdown("""<style>
[data-testid="stSidebarNavItems"] li:first-child a span {
    font-size: 1.3rem; font-weight: 700;
}
[data-testid="stSidebarNavItems"] img,
[data-testid="stSidebarNavItems"] svg { display: none !important; }
[data-testid="stSidebarNavItems"] li:not(:first-child) a span::before {
    content: "\\2022\\00a0";
}
</style>""", unsafe_allow_html=True)
st.title("📊 Historical Analysis — 1982–present")


@st.cache_data(show_spinner=False, ttl=3600)
def _data_through_dates() -> dict:
    """Latest date present in each data source the dashboard reads."""
    out: dict = {}
    goa = AGG_DIR / "region_daily_goa.parquet"
    if goa.exists():
        out["agg"] = pd.to_datetime(
            pd.read_parquet(goa, columns=["date"])["date"]
        ).max()
    ao_path = RAW_DIR / "ao_daily.parquet"
    if ao_path.exists():
        out["ao"] = pd.to_datetime(
            pd.read_parquet(ao_path, columns=["date"])["date"]
        ).max()
    pdo_path = RAW_DIR / "pdo_monthly.parquet"
    if pdo_path.exists():
        out["pdo"] = pd.to_datetime(
            pd.read_parquet(pdo_path, columns=["date"])["date"]
        ).max()
    return out


_dates = _data_through_dates()
_parts = []
if "agg" in _dates:
    _parts.append(f"📅 **MHW data through {_dates['agg'].strftime('%b %d, %Y')}**")
if "ao" in _dates:
    _parts.append(f"AO through {_dates['ao'].strftime('%b %d, %Y')}")
if "pdo" in _dates:
    _parts.append(f"PDO through {_dates['pdo'].strftime('%b %Y')}")
if _parts:
    st.caption(" · ".join(_parts))

# ---------------------------------------------------------------------------
# Shared sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("Controls")

regions = _list_regions()
if not regions:
    st.error("No aggregates parquet found. Run the backfill first.")
    st.stop()

region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="hist_region")

ann = _annual_summary(region)
if ann.empty:
    st.error(f"No data for region '{region}'.")
    st.stop()

min_year = int(ann["year"].min())
max_year = int(ann["year"].max())

year_range = st.sidebar.slider(
    "Year range", min_year, max_year, (min_year, max_year), key="hist_years"
)
y_start, y_end = year_range

ann_f = ann[(ann["year"] >= y_start) & (ann["year"] <= y_end)]

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_burden, tab_explorer, tab_dist, tab_regime = st.tabs([
    "📊 Annual Burden",
    "🔍 Event Explorer",
    "📉 Distributions",
    "🌊 Regime Analysis",
])

# ============================================================
# TAB 1 — Annual Burden
# ============================================================
with tab_burden:
    st.subheader(f"Annual MHW Burden — {region.upper()}  ({y_start}–{y_end})")

    bar_metric = st.radio(
        "Bar metric", ["Peak Area Fraction", "Mean Area Fraction", "Event Days"],
        horizontal=True, key="burden_metric"
    )
    col_map = {
        "Peak Area Fraction":  ("max_af",      "Annual peak area fraction"),
        "Mean Area Fraction":  ("mean_af",     "Annual mean area fraction"),
        "Event Days":          ("event_days",  "Event days (area fraction > 5%)"),
    }
    col, ylabel = col_map[bar_metric]

    # Quantile-based, year-neutral coloring on the displayed metric.
    # Cutoffs are computed against the region's full historical distribution
    # (`ann`), not the year-filtered slice (`ann_f`), so colors always reflect
    # each year's true historical rank:
    #   top 10% (≥ 90th pct) → red, 50th–90th pct → orange, bottom 50% → blue.
    q50 = float(np.quantile(ann[col].values, 0.50))
    q90 = float(np.quantile(ann[col].values, 0.90))
    bar_colors = [
        "#e74c3c" if v >= q90 else        # top 10%
        "#f39c12" if v >= q50 else        # 50th–90th percentile
        "#3498db"                         # bottom 50%
        for v in ann_f[col].values
    ]

    fig_b = go.Figure()
    # Main bar trace — colored, not in legend
    fig_b.add_trace(go.Bar(
        x=ann_f["year"], y=ann_f[col],
        marker_color=bar_colors, width=0.7,
        hovertemplate="Year %{x}: %{y:.4f}<extra></extra>",
        showlegend=False,
    ))
    # Dummy traces purely for legend swatches (off-canvas x values)
    legend_entries = [
        ("#e74c3c", f"Top 10% (≥ {q90:.3g})"),
        ("#f39c12", f"50th–90th pct ({q50:.3g} ≤ x < {q90:.3g})"),
        ("#3498db", f"Bottom 50% (< {q50:.3g})"),
    ]
    for color, name in legend_entries:
        fig_b.add_trace(go.Bar(
            x=[None], y=[None],
            marker_color=color, name=name,
            hoverinfo="skip",
        ))
    if col in ("max_af", "mean_af"):
        fig_b.add_hline(y=AREA_THRESH, line_dash="dash", line_color="red",
                        line_width=1.2, annotation_text="event threshold",
                        annotation_font_size=10)

    # Text-only historical-context annotation: the 2014–2016 "Pacific Blob"
    # marine heatwave. Does NOT affect bar coloring — colors remain quantile-
    # based per the legend above. On regions where the Blob barely registered
    # (e.g., Chukchi, Beaufort), the arrow lands on small bars — which is
    # itself informative: it shows the Blob period wasn't extreme there.
    BLOB_YEARS = {2014, 2015, 2016}
    blob_in_range = BLOB_YEARS & set(ann_f["year"])
    if blob_in_range:
        mid_blob = sorted(blob_in_range)[len(blob_in_range) // 2]
        fig_b.add_annotation(
            x=mid_blob,
            y=ann_f.loc[ann_f["year"] == mid_blob, col].values[0],
            text="Pacific Blob",
            showarrow=True,
            arrowhead=2,
            yshift=12,
            font={"color": "#c0392b", "size": 11},
        )

    fig_b.update_layout(
        yaxis_title=ylabel,
        xaxis_title="Year",
        xaxis={"tickmode": "linear", "dtick": 2},
        height=440,
        template="plotly_white",
        showlegend=True,
        legend={
            "title": {"text": f"<b>{bar_metric} — rank in {region.upper()} history</b>",
                       "font": {"size": 11}},
            "orientation": "h",
            "x": 0.0, "xanchor": "left",
            "y": 1.10, "yanchor": "bottom",
            "bgcolor": "rgba(255,255,255,0.85)",
            "bordercolor": "#cccccc", "borderwidth": 1,
            "font": {"size": 10},
        },
        margin={"t": 90},
    )
    st.plotly_chart(fig_b, use_container_width=True)
    st.caption(
        "Colors are quantile-based against this region's full 1982–present "
        "history of the displayed metric. Cutoffs update automatically when you "
        "change region or metric."
    )

    # Summary table (top 10 years)
    top10 = ann_f.nlargest(10, "max_af")[
        ["year", "max_af", "mean_af", "event_days", "max_Ibar", "max_Cbar"]
    ].round(4)
    top10 = top10.rename(columns={
        "max_af": "Peak Area Frac.", "mean_af": "Mean Area Frac.",
        "event_days": "Event Days", "max_Ibar": "Peak Intensity (°C)",
        "max_Cbar": "Peak Cumul. Int. (°C·days)",
    })
    st.subheader("Top 10 Years by Peak Area Fraction")
    st.dataframe(top10, use_container_width=True, hide_index=True)

# ============================================================
# TAB 2 — Event Explorer
# ============================================================
with tab_explorer:
    df_full = _load_agg(region)

    years_avail = sorted(ann_f["year"].tolist(), reverse=True)
    sel_year = st.selectbox("Select year", years_avail, key="explorer_year")

    df_yr = df_full[df_full["year"] == sel_year].reset_index(drop=True)
    yr_ann = ann[ann["year"] == sel_year].iloc[0]

    # Year header metrics
    hc1, hc2, hc3, hc4, hc5 = st.columns(5)
    hc1.metric("Event Days",              int(yr_ann["event_days"]))
    hc2.metric("Peak Area Frac.",         f"{yr_ann['max_af']:.4f}")
    hc3.metric("Peak Intensity (°C)",     f"{yr_ann['max_Ibar']:.3f}")
    hc4.metric("Peak Duration (days)",    f"{yr_ann['max_Dbar']:.1f}")
    hc5.metric("Peak Cumul. Int.",        f"{yr_ann['max_Cbar']:.2f}")

    # Year time series — area_frac + Ibar + Dbar
    fig_yr = make_subplots(rows=3, cols=1, shared_xaxes=True,
                           subplot_titles=["Area Fraction", "Mean Intensity (°C)",
                                           "Mean Duration (days)"],
                           vertical_spacing=0.08)

    active_yr = df_yr["area_frac"].values > AREA_THRESH

    for row, (col, color) in enumerate(
        [("area_frac", "crimson"), ("Ibar", "orangered"), ("Dbar", "mediumpurple")],
        start=1
    ):
        fig_yr.add_trace(go.Scatter(
            x=df_yr["date"], y=df_yr[col],
            mode="lines", line={"color": color, "width": 1.6},
            fill="tozeroy" if row == 1 else None,
            fillcolor="rgba(220,20,60,0.15)" if row == 1 else None,
            hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}}<extra></extra>",
        ), row=row, col=1)

        # Event shading
        in_span, span_s = False, None
        for d, flag in zip(df_yr["date"], active_yr):
            if flag and not in_span:
                span_s  = d
                in_span = True
            elif not flag and in_span:
                fig_yr.add_vrect(x0=span_s, x1=d, fillcolor="salmon",
                                 opacity=0.15, layer="below", line_width=0,
                                 row=row, col=1)
                in_span = False
        if in_span:
            fig_yr.add_vrect(x0=span_s, x1=df_yr["date"].iloc[-1],
                             fillcolor="salmon", opacity=0.15,
                             layer="below", line_width=0, row=row, col=1)

    if "area_frac" in df_yr:
        fig_yr.add_hline(y=AREA_THRESH, line_dash="dash",
                         line_color="red", line_width=1, row=1, col=1)

    fig_yr.update_layout(
        title=f"{sel_year} — {region.upper()} MHW Timeline",
        height=540, showlegend=False, template="plotly_white",
        margin={"l": 55, "r": 20, "t": 60, "b": 40},
    )
    st.plotly_chart(fig_yr, use_container_width=True)

    # Monthly stats table
    df_yr2 = df_yr.copy()
    df_yr2["month"] = df_yr2["date"].dt.month_name()
    month_order = list(pd.date_range(f"{sel_year}-01-01",
                                     periods=12, freq="MS").month_name())
    monthly = (
        df_yr2.groupby("month")
        .agg(event_days=("area_frac", lambda x: (x > AREA_THRESH).sum()),
             max_area_frac=("area_frac", "max"),
             max_Ibar=("Ibar", "max"),
             max_Dbar=("Dbar", "max"))
        .reindex([m for m in month_order if m in df_yr2["month"].values])
        .round(4)
    )
    monthly = monthly.rename(columns={
        "event_days": "Event Days", "max_area_frac": "Peak Area Frac.",
        "max_Ibar": "Peak Intensity (°C)", "max_Dbar": "Peak Duration (days)",
    })
    st.subheader(f"Monthly summary — {sel_year}")
    st.dataframe(monthly, use_container_width=True)

# ============================================================
# TAB 3 — Metric Distributions
# ============================================================
with tab_dist:
    df_full = _load_agg(region)

    df_range = df_full[(df_full["year"] >= y_start) & (df_full["year"] <= y_end)]

    metrics_hist = [
        ("area_frac", "Area Fraction",      "fraction",  "steelblue",  False),
        ("Ibar",      "Mean Intensity",     "°C",        "orangered",  True),
        ("Dbar",      "Mean Duration",      "days",      "mediumpurple",True),
        ("Cbar",      "Cumul. Intensity",   "°C·days",   "seagreen",   True),
        ("Obar",      "Onset Rate",         "°C/day",    "darkorange", True),
    ]

    st.subheader(f"Metric Distributions — {region.upper()}  ({y_start}–{y_end})")

    n_bins = st.slider("Histogram bins", 20, 100, 50, key="dist_bins")

    for col, label, unit, color, cond_only in metrics_hist:
        vals = df_range[col].values
        plot_vals = vals[vals > 0] if cond_only else vals
        n_plot  = len(plot_vals)
        n_zero  = len(vals) - n_plot

        if n_plot == 0:
            st.info(f"{label}: no non-zero values in selected range.")
            continue

        p10 = np.percentile(plot_vals, 10)
        p50 = np.percentile(plot_vals, 50)
        p90 = np.percentile(plot_vals, 90)

        fig_h = go.Figure()
        fig_h.add_trace(go.Histogram(
            x=plot_vals, nbinsx=n_bins,
            marker_color=color, opacity=0.75, name=label,
        ))
        for pv, pn, pc in [(p10, "p10", "navy"), (p50, "p50", "black"),
                            (p90, "p90", "crimson")]:
            fig_h.add_vline(x=pv, line_dash="dash", line_color=pc,
                            line_width=1.5,
                            annotation_text=f"{pn}={pv:.3f}",
                            annotation_font_size=9,
                            annotation_position="top right")

        title_suffix = f"(non-zero: {n_plot:,}  zero: {n_zero:,})" if cond_only else f"(n={n_plot:,})"
        fig_h.update_layout(
            title=f"{label} — {unit}  {title_suffix}",
            xaxis_title=unit, yaxis_title="Days",
            height=280, template="plotly_white",
            margin={"l": 50, "r": 20, "t": 40, "b": 40},
            showlegend=False,
        )
        st.plotly_chart(fig_h, use_container_width=True)

    # Composite risk distribution
    risk_path = ROOT / "data" / "derived" / "risk" / f"risk_{region}.parquet"
    if risk_path.exists():
        risk_df = pd.read_parquet(risk_path)
        risk_df["year"] = pd.to_datetime(risk_df["date"]).dt.year
        risk_range = risk_df[(risk_df["year"] >= y_start) & (risk_df["year"] <= y_end)]
        if not risk_range.empty:
            st.subheader("Composite Risk Score Distribution")
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Histogram(
                x=risk_range["composite_risk"], nbinsx=60,
                marker_color="slategray", opacity=0.8,
            ))
            for lo, hi, clr, lbl in [(0, 33, "rgba(46,204,113,0.12)", "Normal"),
                                      (33, 66, "rgba(255,165,0,0.12)", "Elevated"),
                                      (66, 100, "rgba(220,20,60,0.12)", "High Risk")]:
                fig_risk.add_vrect(x0=lo, x1=hi, fillcolor=clr, line_width=0)
                n = ((risk_range["composite_risk"] >= lo) & (risk_range["composite_risk"] < hi)).sum()
                fig_risk.add_annotation(
                    x=(lo + hi) / 2, y=0, yref="paper", yanchor="bottom",
                    text=f"<b>{lbl}</b><br>{n:,} days", showarrow=False,
                    font={"size": 10},
                )
            fig_risk.add_vline(x=33, line_dash="dot", line_color="green",  line_width=1.5)
            fig_risk.add_vline(x=66, line_dash="dot", line_color="orange", line_width=1.5)
            fig_risk.update_layout(
                xaxis_title="Composite risk score (0–100)", yaxis_title="Days",
                height=300, template="plotly_white",
                margin={"l": 50, "r": 20, "t": 20, "b": 40},
                showlegend=False,
            )
            st.plotly_chart(fig_risk, use_container_width=True)

# ============================================================
# TAB 4 — Regime Analysis
# ============================================================
with tab_regime:
    regime_df = _regime_df(region)

    if regime_df.empty:
        st.warning("Not enough overlapping AO/PDO/aggregates data for regime analysis. "
                   "Run `mhw-fetch-indices --ao-years 43 --pdo-years 43` first.")
    else:
        # Filter by year range
        regime_df = regime_df[(regime_df["year"] >= y_start) & (regime_df["year"] <= y_end)]

        st.subheader(f"AO / PDO Regime Analysis — {region.upper()}  ({y_start}–{y_end})")

        # Regime counts
        rc = regime_df["regime"].value_counts()
        st.caption("Days per regime: " + "   ".join(
            f"**{r}**: {rc.get(r, 0):,}" for r in REGIME_ORDER
        ))

        # Verify all 4 regimes
        missing = [r for r in REGIME_ORDER if r not in regime_df["regime"].values]
        if missing:
            st.warning(f"Regimes with no data: {missing}")
        else:
            st.success("All 4 regimes represented ✓")

        plot_metrics_reg = [
            ("area_frac", "Area Fraction",      "fraction"),
            ("Ibar",      "Mean Intensity",     "°C"),
            ("Dbar",      "Mean Duration",      "days"),
            ("Cbar",      "Cumul. Intensity",   "°C·days"),
        ]

        # Box plots and the median table both restrict to event days
        # (area_frac > regional-event threshold). Including non-event days
        # would dilute every distribution with zeros and make the box plots
        # and medians all read as zero — not useful.
        event_df = regime_df[regime_df["area_frac"] > AREA_THRESH]

        st.caption(
            f"Box plots and medians below are computed over **event days only** "
            f"(area_frac > {AREA_THRESH:.0%}). Non-event days are excluded so the "
            "distributions reflect heatwave severity in each regime, not the "
            "proportion of zero-activity days."
        )

        fig_reg = make_subplots(
            rows=1, cols=4,
            subplot_titles=[m[1] for m in plot_metrics_reg],
            horizontal_spacing=0.06,
        )

        for col_i, (col, title, unit) in enumerate(plot_metrics_reg, start=1):
            for reg_i, regime in enumerate(REGIME_ORDER, start=1):
                sub = event_df.loc[event_df["regime"] == regime, col].values
                if len(sub) == 0:
                    continue
                fig_reg.add_trace(go.Box(
                    y=sub,
                    name=regime,
                    marker_color=REGIME_COLOR[regime],
                    line_color=REGIME_COLOR[regime],
                    fillcolor=REGIME_COLOR[regime].replace(")", ",0.4)").replace("rgb", "rgba")
                              if REGIME_COLOR[regime].startswith("rgb") else REGIME_COLOR[regime],
                    opacity=0.7,
                    showlegend=(col_i == 1),
                    boxmean=True,
                    hovertemplate=f"{regime}<br>{title}: %{{y:.4f}}<extra></extra>",
                ), row=1, col=col_i)
            fig_reg.update_yaxes(title_text=unit, row=1, col=col_i,
                                 title_font={"size": 10})
            fig_reg.update_xaxes(showticklabels=False, row=1, col=col_i)

        fig_reg.update_layout(
            height=480,
            template="plotly_white",
            legend={"title": "Regime", "x": 1.01, "y": 0.9},
            margin={"l": 55, "r": 150, "t": 60, "b": 30},
            title=f"MHW Metrics by Climate Regime — {region.upper()}  ({y_start}–{y_end})",
            boxmode="group",
        )
        st.plotly_chart(fig_reg, use_container_width=True)

        # Regime median table — medians over event days only, so they reflect
        # event severity rather than being diluted to zero by quiet days.
        st.subheader("Median values by regime (event days only)")
        medians = []
        for r in REGIME_ORDER:
            all_days   = regime_df[regime_df["regime"] == r]
            event_only = all_days[all_days["area_frac"] > AREA_THRESH]
            if len(all_days) == 0:
                continue
            medians.append({
                "Regime": r,
                "Total days":  len(all_days),
                "Event days":  len(event_only),
                "Event rate":  f"{len(event_only) / len(all_days):.1%}",
                "Area Frac. (median)":         (
                    round(event_only["area_frac"].median(), 4) if len(event_only) else None
                ),
                "Intensity median (°C)":       (
                    round(event_only["Ibar"].median(), 3) if len(event_only) else None
                ),
                "Duration median (days)":      (
                    round(event_only["Dbar"].median(), 2) if len(event_only) else None
                ),
                "Cumul. Int. median (°C·days)": (
                    round(event_only["Cbar"].median(), 3) if len(event_only) else None
                ),
            })
        if medians:
            st.dataframe(pd.DataFrame(medians), use_container_width=True, hide_index=True)
            st.caption(
                "*Event days* = days when regional area fraction exceeded "
                f"{AREA_THRESH:.0%}. Medians of area fraction, intensity, "
                "duration, and cumulative intensity are computed across those "
                "event days only. *Event rate* tells you how often the region "
                "was in a regional-scale MHW given the climate regime."
            )

        # Phase timeline
        st.markdown("---")
        st.subheader("AO / PDO Phase Timeline")
        ao_yr = (regime_df.groupby("year")
                 .agg(mean_ao=("ao", "mean"), mean_pdo=("pdo", "mean"))
                 .reset_index())

        fig_ph = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               subplot_titles=["Annual mean AO", "Annual mean PDO"],
                               vertical_spacing=0.1)
        ao_colors = ["steelblue" if v >= 0 else "tomato" for v in ao_yr["mean_ao"]]
        pdo_colors = ["darkorange" if v >= 0 else "royalblue" for v in ao_yr["mean_pdo"]]

        fig_ph.add_trace(go.Bar(x=ao_yr["year"], y=ao_yr["mean_ao"],
                                marker_color=ao_colors, width=0.7,
                                hovertemplate="Year %{x}: AO=%{y:.3f}<extra></extra>"),
                         row=1, col=1)
        fig_ph.add_trace(go.Bar(x=ao_yr["year"], y=ao_yr["mean_pdo"],
                                marker_color=pdo_colors, width=0.7,
                                hovertemplate="Year %{x}: PDO=%{y:.3f}<extra></extra>"),
                         row=2, col=1)
        for r in [1, 2]:
            fig_ph.add_hline(y=0, line_dash="dot", line_color="gray",
                             line_width=1, row=r, col=1)
        fig_ph.update_layout(height=340, template="plotly_white", showlegend=False,
                              margin={"l": 55, "r": 20, "t": 50, "b": 30})
        fig_ph.update_xaxes(tickmode="linear", dtick=2, row=2, col=1)
        st.plotly_chart(fig_ph, use_container_width=True)
