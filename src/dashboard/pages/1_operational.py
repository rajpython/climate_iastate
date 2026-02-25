"""Page 1 — Operational Dashboard.

Four panels in tabs, sharing a single region selector from the sidebar:
  🗺️  Live MHW Map
  📈  Event Metrics (time series)
  🌐  Predictability Context (AO / PDO)
  🚦  Risk Gauge

Run standalone:
    streamlit run src/dashboard/pages/1_operational.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Shared data loaders (imported for cache reuse across pages)
# ---------------------------------------------------------------------------
from dashboard.components.map_mhw import (
    METRICS as MAP_METRICS,
    find_available_states,
    load_land_mask,
    load_states,
    make_grid_geojson,
)
from dashboard.components.ts_event_metrics import (
    AREA_THRESH,
    METRIC_DEFS,
    _active_spans,
    list_regions,
    load_aggregates,
)
from dashboard.components.predictability_panel import (
    _add_event_shading,
    _zero_line,
    load_ao,
    load_pdo,
)
from dashboard.components.risk_gauge import (
    RISK_WEIGHTS,
    _make_gauge,
    _make_pct_bars,
    _make_sparkline,
    load_risk_table,
)
from mhw.states.risk import compute_risk_table, save_risk_table

RISK_DIR = Path(__file__).parents[3] / "data" / "derived" / "risk"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Operational Dashboard", layout="wide", page_icon="🌊")
st.title("🌊 Operational Dashboard")

# ---------------------------------------------------------------------------
# Shared sidebar — region selector
# ---------------------------------------------------------------------------
st.sidebar.header("Controls")

regions = list_regions()
if not regions:
    st.error("No aggregates parquet found. Run the backfill first.")
    st.stop()

region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="op_region")

# ---------------------------------------------------------------------------
# Load data (all cached — fast after first run)
# ---------------------------------------------------------------------------
available = find_available_states()
agg_df    = load_aggregates(region)
ao_df     = load_ao()
pdo_df    = load_pdo()

# Ensure risk table exists
_risk_path = RISK_DIR / f"risk_{region}.parquet"
if not _risk_path.exists() and agg_df is not None:
    _full = agg_df.copy()
    _full["date"] = pd.to_datetime(_full["date"]).dt.date
    _rt = compute_risk_table(_full)
    save_risk_table(_rt, region)

risk_df = load_risk_table(region)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_map, tab_ts, tab_pred, tab_risk = st.tabs([
    "🗺️ Live MHW Map",
    "📈 Event Metrics",
    "🌐 Predictability",
    "🚦 Risk Gauge",
])

# ============================================================
# TAB 1 — Live MHW Map
# ============================================================
with tab_map:
    if not available:
        st.warning("No state zarr files found. Run `mhw-run-states` first.")
    else:
        reg_files = [r for r in available if r["region"] == region]
        if not reg_files:
            reg_files = available   # fallback: show whatever is available

        labels = [f"{r['region'].upper()}  {r['start']} → {r['end']}" for r in reg_files]
        choice = st.selectbox("Period", range(len(labels)),
                              format_func=lambda i: labels[i], key="map_period")
        info   = reg_files[choice]
        data   = load_states(info["path"])
        dates  = data["dates"]

        avail_metrics = {k: v for k, v in MAP_METRICS.items() if k in data}
        c1, c2 = st.columns([1, 3])
        with c1:
            metric_key = st.selectbox("Metric", list(avail_metrics.keys()),
                                      format_func=lambda k: avail_metrics[k][0],
                                      index=1, key="map_metric")
            date_idx = st.slider("Date", 0, len(dates) - 1, len(dates) - 1,
                                 key="map_date")
            st.caption(f"**{dates[date_idx]}**")

        values = data[metric_key][date_idx]
        label, colorscale, vmin, vmax, fmt = avail_metrics[metric_key]

        lons_2d, lats_2d = np.meshgrid(data["lons"], data["lats"])
        lat_flat  = lats_2d.flatten()
        lon_flat  = lons_2d.flatten()
        val_flat  = values.flatten().astype(float)
        land_mask = load_land_mask(info["region"])
        if land_mask is not None:
            val_flat[land_mask.flatten()] = np.nan
        # Also hide ocean cells with no activity — only show where metric > 0
        val_flat[val_flat <= 0] = np.nan
        ids = [str(i) for i in range(len(val_flat))]

        geojson = make_grid_geojson(info["path"])

        fig = go.Figure(go.Choroplethmap(
            geojson=geojson,
            locations=ids,
            z=val_flat,
            colorscale=colorscale,
            zmin=vmin,
            zmax=vmax,
            marker_opacity=0.65,
            marker_line_width=0,
            colorbar=dict(title=label, thickness=14),
            customdata=np.column_stack([lat_flat, lon_flat]),
            hovertemplate=(
                f"Lat: %{{customdata[0]:.3f}}<br>Lon: %{{customdata[1]:.3f}}<br>"
                f"{label}: %{{z:{fmt}}}<extra></extra>"
            ),
        ))
        fig.update_layout(
            title=f"{label} — {info['region'].upper()} — {dates[date_idx]}",
            map=dict(
                style="open-street-map",
                center={"lat": float(data["lats"].mean()),
                        "lon": float(data["lons"].mean())},
                zoom=3.5,
            ),
            height=500,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
        )
        with c2:
            st.plotly_chart(fig, use_container_width=True, key="map_chart")

        sc1, sc2, sc3, sc4 = st.columns(4)
        valid = np.isfinite(values)
        sc1.metric("Min",         f"{np.nanmin(values):{fmt}}")
        sc2.metric("Max",         f"{np.nanmax(values):{fmt}}")
        sc3.metric("Mean (valid)",f"{np.nanmean(values[valid]):{fmt}}" if valid.any() else "—")
        if metric_key == "A":
            n_act = int((values > 0).sum())
            sc4.metric("Active cells", f"{n_act} / {values.size}  ({100*n_act/values.size:.1f}%)")

# ============================================================
# TAB 2 — Event Metrics Time Series
# ============================================================
with tab_ts:
    if agg_df is None or agg_df.empty:
        st.warning(f"No aggregates for region '{region}'. Run `mhw-aggregate`.")
    else:
        n_total = len(agg_df)
        window_opts = {"30 days": 30, "60 days": 60, "90 days": 90,
                       "180 days": 180, "Full record": n_total}
        window_label = st.selectbox("Window", list(window_opts.keys()),
                                    index=2, key="ts_window")
        window = window_opts[window_label]
        df_win = agg_df.tail(window).reset_index(drop=True)

        active_flag = df_win["area_frac"].values > AREA_THRESH
        spans = _active_spans(df_win["date"], active_flag)

        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            subplot_titles=[m[1] for m in METRIC_DEFS],
                            vertical_spacing=0.06)

        for row, (col, title, ylabel, color) in enumerate(METRIC_DEFS, start=1):
            fig.add_trace(go.Scatter(
                x=df_win["date"], y=df_win[col], mode="lines",
                line={"color": color, "width": 1.8},
                hovertemplate=f"%{{x|%Y-%m-%d}}: %{{y:.3f}} {ylabel}<extra></extra>",
                name=title,
            ), row=row, col=1)
            fig.update_yaxes(title_text=ylabel, row=row, col=1,
                             title_font={"size": 10})
            for s, e in spans:
                fig.add_vrect(x0=s, x1=e, fillcolor="salmon", opacity=0.15,
                              layer="below", line_width=0, row=row, col=1)
            if col == "area_frac":
                fig.add_hline(y=AREA_THRESH, line_dash="dash", line_color="red",
                              line_width=1, annotation_text="threshold",
                              annotation_font_size=9, row=row, col=1)

        fig.update_layout(
            title=f"MHW Event Metrics — {region.upper()}  (last {window} days)",
            height=210 * 5, showlegend=False, template="plotly_white",
            margin={"l": 60, "r": 20, "t": 60, "b": 40},
        )
        st.plotly_chart(fig, use_container_width=True, key="ts_chart")

        # Summary
        ev_days = int((df_win["area_frac"] > AREA_THRESH).sum())
        peak    = df_win.loc[df_win["area_frac"].idxmax()]
        c1, c2, c3 = st.columns(3)
        c1.metric("Event days (>0.05)", ev_days)
        c2.metric("Peak area_frac", f"{peak['area_frac']:.4f}")
        c3.metric("Peak date", str(peak["date"].date()))

# ============================================================
# TAB 3 — Predictability Context
# ============================================================
with tab_pred:
    if ao_df is None:
        st.error("AO data not found.")
    else:
        window_pred = st.selectbox("Window", ["90 days", "180 days", "1 year", "All"],
                                   index=1, key="pred_window")
        win_days = {"90 days": 90, "180 days": 180, "1 year": 365, "All": 99999}[window_pred]

        # Anchor time window on MHW data when available
        if agg_df is not None and not agg_df.empty:
            agg_win = agg_df.tail(min(win_days, len(agg_df))).reset_index(drop=True)
            t_start, t_end = agg_win["date"].iloc[0], agg_win["date"].iloc[-1]
        else:
            agg_win = None
            t_start = pd.Timestamp.now() - pd.Timedelta(days=win_days)
            t_end   = pd.Timestamp.now()

        ao_win  = ao_df[(ao_df["date"] >= t_start) & (ao_df["date"] <= t_end)]
        pdo_win = pdo_df[(pdo_df["date"] >= t_start) & (pdo_df["date"] <= t_end)] if pdo_df is not None else None

        if ao_win.empty:
            ao_win = ao_df.tail(min(win_days, len(ao_df))).reset_index(drop=True)
            st.info(f"AO data not available for MHW period. Showing most recent {win_days} AO days.")

        row_titles = ["AO (daily)", "PDO (monthly)", "Area Fraction", "Mean Intensity Ī (°C)"]
        n_rows = len(row_titles)
        fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True,
                            subplot_titles=row_titles, vertical_spacing=0.07)

        ao_colors = np.where(ao_win["ao"].values >= 0, "steelblue", "tomato")
        fig.add_trace(go.Bar(x=ao_win["date"], y=ao_win["ao"],
                             marker_color=ao_colors.tolist(), name="AO",
                             hovertemplate="%{x|%Y-%m-%d}: %{y:.3f}<extra></extra>"),
                      row=1, col=1)
        _zero_line(fig, 1)
        fig.update_yaxes(title_text="AO", row=1, col=1, title_font={"size": 9})

        if pdo_win is not None and not pdo_win.empty:
            pdo_colors = np.where(pdo_win["pdo"].values >= 0, "darkorange", "royalblue")
            fig.add_trace(go.Bar(x=pdo_win["date"], y=pdo_win["pdo"],
                                 marker_color=pdo_colors.tolist(), name="PDO",
                                 hovertemplate="%{x|%Y-%m}: %{y:.3f}<extra></extra>"),
                          row=2, col=1)
            _zero_line(fig, 2)
            fig.update_yaxes(title_text="PDO", row=2, col=1, title_font={"size": 9})

        if agg_win is not None and not agg_win.empty:
            active_flag = agg_win["area_frac"].values > AREA_THRESH
            fig.add_trace(go.Scatter(
                x=agg_win["date"], y=agg_win["area_frac"], mode="lines",
                line={"color": "tomato", "width": 1.8},
                fill="tozeroy", fillcolor="rgba(255,99,71,0.15)",
                hovertemplate="%{x|%Y-%m-%d}: %{y:.4f}<extra></extra>"),
                row=3, col=1)
            fig.add_hline(y=AREA_THRESH, line_dash="dash", line_color="darkred",
                          line_width=1, row=3, col=1)
            fig.update_yaxes(title_text="fraction", row=3, col=1, title_font={"size": 9})

            fig.add_trace(go.Scatter(
                x=agg_win["date"], y=agg_win["Ibar"], mode="lines",
                line={"color": "orangered", "width": 1.8},
                hovertemplate="%{x|%Y-%m-%d}: %{y:.3f} °C<extra></extra>"),
                row=4, col=1)
            fig.update_yaxes(title_text="°C", row=4, col=1, title_font={"size": 9})

            _add_event_shading(fig, agg_win["date"], active_flag, n_rows)

        fig.update_layout(
            title=f"Predictability Context — {region.upper()}",
            height=220 * n_rows, showlegend=False, template="plotly_white",
            bargap=0.05, margin={"l": 60, "r": 20, "t": 60, "b": 40},
        )
        st.plotly_chart(fig, use_container_width=True, key="pred_chart")

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Latest AO",       f"{float(ao_df['ao'].iloc[-1]):.3f}")
        pc2.metric("Mean AO (window)",f"{float(ao_win['ao'].mean()):.3f}")
        if pdo_df is not None and not pdo_df.empty:
            pc3.metric("Latest PDO", f"{float(pdo_df['pdo'].iloc[-1]):.3f}")
        if agg_win is not None and not agg_win.empty:
            pc4.metric("MHW event days", int((agg_win["area_frac"] > AREA_THRESH).sum()))

# ============================================================
# TAB 4 — Risk Gauge
# ============================================================
with tab_risk:
    if risk_df is None:
        st.error("Risk table not found. Run `mhw-compute-risk`.")
    else:
        if st.button("♻️ Recompute risk scores", key="risk_recompute"):
            load_risk_table.clear()
            st.rerun()

        min_d = risk_df["date"].dt.date.min()
        max_d = risk_df["date"].dt.date.max()
        sel_date = st.date_input("Reference date", value=max_d,
                                 min_value=min_d, max_value=max_d,
                                 key="risk_date")

        row_r = risk_df[risk_df["date"].dt.date == sel_date]
        if row_r.empty:
            st.warning(f"No risk data for {sel_date}.")
        else:
            row_r = row_r.iloc[0]
            score  = float(row_r["composite_risk"])
            level  = str(row_r["risk_level"])

            g_col, p_col = st.columns([1, 1.6])
            with g_col:
                st.plotly_chart(_make_gauge(score, level), use_container_width=True, key="risk_gauge")
                if agg_df is not None:
                    agg_row = agg_df[agg_df["date"].dt.date == sel_date]
                    if not agg_row.empty:
                        agg_row = agg_row.iloc[0]
                        mc1, mc2 = st.columns(2)
                        mc1.metric("area_frac", f"{agg_row['area_frac']:.4f}")
                        mc2.metric("Ī (°C)",    f"{agg_row['Ibar']:.2f}")
                        mc3, mc4 = st.columns(2)
                        mc3.metric("D̄ (days)",   f"{agg_row['Dbar']:.1f}")
                        mc4.metric("C̄ (°C·days)",f"{agg_row['Cbar']:.2f}")

            with p_col:
                st.plotly_chart(_make_pct_bars(row_r), use_container_width=True, key="risk_pct_bars")
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
                    f"Cbar {RISK_WEIGHTS['Cbar']:.0%}. "
                    "Reference: full 1982–2024 backfill distribution."
                )

            st.markdown("---")
            if agg_df is not None:
                st.plotly_chart(_make_sparkline(risk_df, agg_df, n_days=30),
                                use_container_width=True, key="risk_sparkline")
