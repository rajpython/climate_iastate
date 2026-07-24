"""Page 1 — Operational Dashboard.

Four panels in tabs, sharing a single region selector from the sidebar:
  🗺️  Live MHW Map
  📈  Event Metrics (time series)
  🌐  Predictability Context (AO / PDO)
  🚦  Risk Gauge

Run standalone:
    streamlit run src/dashboard/pages/1_Operational.py
"""
from __future__ import annotations

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
    REGION_NAMES as _REGION_NAMES,
    _active_spans,
    list_regions,
    load_aggregates,
    mhw_plot,
    region_menu_label,
)
from dashboard.components.driver_links import (
    build_drivers_frame,
    targets_for_region,
)
from dashboard.components.predictability_panel import (
    _add_event_shading,
    _zero_line,
    best_lag_table,
    deseasonalize,
    lagged_cross_correlation,
    load_ao,
    load_npi,
    load_pdo,
)
from dashboard.components.risk_gauge import (
    RISK_WEIGHTS,
    _make_gauge,
    _make_pct_bars,
    _make_sparkline,
    load_risk_table,
)
from dashboard.pages.forecast import render_forecast_panel, zones_for_region
from mhw.forecast.deploy import load_forecast_config
from mhw.states.risk import compute_risk_table, save_risk_table

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    PURPLE,
    RED,
    SLATE,
    callout,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
    section_title,
)

RISK_DIR = Path(__file__).parents[3] / "data" / "derived" / "risk"
# Region names (_REGION_NAMES) + grouped dropdown labels (region_menu_label) come from
# ts_event_metrics — ESR ecosystem regions (ebs=combined, sebs/nbs; goa=combined, wgoa/egoa; Arctic).

# Human-friendly date formatting
_DATE_FMT = "%b %d, %Y"          # e.g. "Feb 24, 2024"
_PLOTLY_DATE = "%b %d, %Y"       # Plotly d3 format
_PLOTLY_MONTH = "%b %Y"          # Plotly d3 format (month only)


def _fmt(d) -> str:
    """Human-friendly date string, e.g. 'Feb 24, 2024'."""
    return pd.Timestamp(d).strftime(_DATE_FMT)

# Page config, fonts and sidebar styling are owned by the navigation shell
# (Alaska_Dashboard.py) — this script just renders the page body.


# The cross-zone driver × metric matrix and its shared monthly driver/target builders moved to
# ``dashboard.components.driver_links`` (rendered on the standalone "Climate Driver Links" page).
# The per-region table below reuses ``build_drivers_frame`` / ``targets_for_region`` from there.


def _driver_cross_correlation(region, agg_df, ao_df, pdo_df, npi_anom) -> None:
    """Region-scoped lagged cross-correlation of the climate drivers vs the MHW metrics.

    Correlates each driver (AO monthly-mean, PDO, deseasonalized NPI) **leading** the region's
    monthly area fraction, mean intensity and onset count by 0–6 months over the full overlapping
    record, then tabulates the best driver-leads lag per pair. Descriptive context, not a forecast.
    """
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    section_title(f"Driver Cross-Correlation — {_REGION_NAMES.get(region, region.upper())}",
                  note="driver leads this zone's MHW by 0–6 months · Pearson r on monthly series")
    if agg_df is None or agg_df.empty:
        callout("No monthly MHW series for this region yet — run <code>mhw-aggregate</code>.",
                icon="🔗", tint=SLATE)
        return

    drivers = build_drivers_frame(ao_df, pdo_df, npi_anom)
    targets = targets_for_region(agg_df)

    grid = lagged_cross_correlation(drivers, targets, max_lag=6)
    best = best_lag_table(grid)
    if best.empty:
        callout("Not enough overlapping months to estimate driver correlations.",
                icon="🔗", tint=SLATE)
        return

    disp = best[["driver", "target", "lag", "r", "n"]].copy()
    disp["r"] = disp["r"].map(lambda v: f"{v:+.2f}")
    disp = disp.rename(columns={"driver": "Driver", "target": "MHW metric",
                                "lag": "Best lead (mo)", "r": "r", "n": "n months"})
    st.dataframe(disp, hide_index=True, use_container_width=True)

    top = best.iloc[0]
    sign = "positively" if top["r"] >= 0 else "negatively"
    lead = "the same month" if int(top["lag"]) == 0 else f"{int(top['lag'])} month(s) ahead"
    callout(
        f"Strongest link: <b>{top['driver']}</b> {sign} co-varies with <b>{top['target']}</b> at a "
        f"lead of <b>{lead}</b> (r = {top['r']:+.2f}, n = {int(top['n'])}). NPI is deseasonalized; "
        "AO/PDO are native anomalies. This is a plain association, <b>not</b> causation and "
        "<b>not</b> a fitted forecast.", icon="🔗", tint=BLUE)

    with st.expander("Full lag grid — r at each 0–6 month lead"):
        pivot = (grid.assign(pair=grid["driver"] + " → " + grid["target"])
                 .pivot(index="pair", columns="lag", values="r")
                 .map(lambda v: "" if pd.isna(v) else f"{v:+.2f}"))
        pivot.columns = [f"lead {c}" for c in pivot.columns]
        st.dataframe(pivot, use_container_width=True)


def render() -> None:
    """Operational MHW view — rendered inside the Marine Heatwaves hub."""
    inject_css()
    # ---------------------------------------------------------------------------
    # Shared sidebar — region selector
    # ---------------------------------------------------------------------------
    st.sidebar.header("Controls")

    regions = list_regions()
    if not regions:
        page_header("🌊", "Operational MHW", "Live & recent marine-heatwave state", "—")
        st.error("No aggregates parquet found. Run the backfill first.")
        st.stop()

    region = st.sidebar.selectbox("Region", regions, format_func=region_menu_label, key="op_region")
    page_header("🌊", "Operational MHW", "Live & recent marine-heatwave state",
                f"{_REGION_NAMES.get(region, region.upper())} ({region.upper()})",
                caption=("Today's and recent marine-heatwave state for the selected region — "
                         "the live map, event metrics, AO/PDO context, and a composite risk score."))

    # ---------------------------------------------------------------------------
    # Load data (all cached — fast after first run)
    # ---------------------------------------------------------------------------
    available = find_available_states()
    agg_df    = load_aggregates(region)
    ao_df     = load_ao()
    pdo_df    = load_pdo()
    npi_df    = load_npi()

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
    tab_map, tab_ts, tab_pred, tab_risk, tab_fc = st.tabs([
        "🗺️ Live MHW Map",
        "📈 Event Metrics",
        "🌐 Climate Drivers",
        "🚦 Risk Gauge",
        "🔮 Forecast",
    ])

    # ============================================================
    # TAB 1 — Live MHW Map
    # ============================================================
    with tab_map, st.container(border=True):
        if not available:
            st.warning("No state zarr files found. Run `mhw-run-states` first.")
        else:
            reg_files = [r for r in available if r["region"] == region]
            if not reg_files:
                reg_files = available   # fallback: show whatever is available
            # Most-recent zarr first so the selectbox defaults to the latest period.
            # Combined with the date slider's default-to-last-day below, the map
            # opens on today's data and the user scrolls backwards from there.
            reg_files = sorted(reg_files, key=lambda r: r["end"], reverse=True)

            labels = [f"{r['region'].upper()}  {_fmt(r['start'])} → {_fmt(r['end'])}" for r in reg_files]
            choice = st.selectbox("Period", range(len(labels)),
                                  format_func=lambda i: labels[i],
                                  key=f"map_period_{region}")
            info   = reg_files[choice]
            data   = load_states(info["path"])
            dates  = data["dates"]

            avail_metrics = {k: v for k, v in MAP_METRICS.items() if k in data}
            c1, c2 = st.columns([1, 3])
            with c1:
                metric_key = st.selectbox("Metric", list(avail_metrics.keys()),
                                          format_func=lambda k: avail_metrics[k][0],
                                          index=1, key="map_metric")
                # A single-date zarr can't drive a slider (min==max is a
                # Streamlit error); pin to the only day in that case.
                if len(dates) > 1:
                    date_idx = st.slider("Date", 0, len(dates) - 1, len(dates) - 1,
                                         key="map_date")
                else:
                    date_idx = 0
                st.caption(f"**{_fmt(dates[date_idx])}**")

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
            # Dateline-aware centre: a region straddling 180° (the Aleutians' two-strip grid)
            # has lons in both far-east and far-west, so a plain mean lands mid-ocean — centre
            # on the dateline instead. The choropleth cells themselves draw at their true lon.
            _lons = data["lons"]
            _center_lon = 180.0 if (_lons.max() - _lons.min() > 180) else float(_lons.mean())
            fig.update_layout(
                title=f"{label} — {info['region'].upper()} — {_fmt(dates[date_idx])}",
                map=dict(
                    style="open-street-map",
                    center={"lat": float(data["lats"].mean()), "lon": _center_lon},
                    zoom=3.5,
                ),
                height=500,
                margin={"l": 0, "r": 0, "t": 50, "b": 0},
            )
            with c2:
                st.plotly_chart(fig, use_container_width=True, key="map_chart")

            valid = np.isfinite(values)
            _cards = [
                kpi_card("Min", f"{np.nanmin(values):{fmt}}", SLATE),
                kpi_card("Max", f"{np.nanmax(values):{fmt}}", SLATE),
                kpi_card("Mean (valid)",
                         f"{np.nanmean(values[valid]):{fmt}}" if valid.any() else "—", SLATE),
            ]
            if metric_key == "A":
                n_act = int((values > 0).sum())
                _cards.append(kpi_card("Active cells",
                              f"{n_act} / {values.size} ({100 * n_act / values.size:.1f}%)", BLUE))
            kpi_grid(_cards, cols=len(_cards))

    # ============================================================
    # TAB 2 — Event Metrics Time Series
    # ============================================================
    with tab_ts, st.container(border=True):
        if agg_df is None or agg_df.empty:
            st.warning(f"No aggregates for region '{region}'. Run `mhw-aggregate`.")
        else:
            n_total = len(agg_df)
            window_opts = {"30 days": 30, "60 days": 60, "90 days": 90,
                           "180 days": 180, "1 year": 365, "Full record": n_total}
            window_label = st.selectbox("Window", list(window_opts.keys()),
                                        index=4, key="ts_window")
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
                    hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}} {ylabel}<extra></extra>",
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
            mhw_plot(fig, use_container_width=True, key="ts_chart")

            # Summary
            ev_days = int((df_win["area_frac"] > AREA_THRESH).sum())
            peak    = df_win.loc[df_win["area_frac"].idxmax()]
            kpi_grid([
                kpi_card("Event Days", f"{ev_days}", BLUE),
                kpi_card("Peak Area Fraction", f"{peak['area_frac']:.4f}", BLUE),
                kpi_card("Peak date", _fmt(peak["date"]), SLATE),
            ], cols=3)

    # ============================================================
    # TAB 3 — Climate Drivers (AO / PDO / Aleutian Low + cross-correlation)
    # ============================================================
    with tab_pred, st.container(border=True):
        if ao_df is None:
            st.error("AO data not found.")
        else:
            window_pred = st.selectbox("Window", ["90 days", "180 days", "1 year", "All"],
                                       index=2, key="pred_window")
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

            # NPI (Aleutian Low proxy) is raw SLP with a strong seasonal cycle → deseasonalize to a
            # monthly anomaly before plotting/correlating. It updates slower than AO/PDO, so it only
            # appears in the chart for windows that reach its record (shown when the window overlaps).
            npi_anom = (deseasonalize(npi_df, "npi") if npi_df is not None and not npi_df.empty
                        else None)
            npi_win = (npi_anom[(npi_anom["date"] >= t_start) & (npi_anom["date"] <= t_end)]
                       if npi_anom is not None else None)
            show_pdo = pdo_win is not None and not pdo_win.empty
            show_npi = npi_win is not None and not npi_win.empty
            show_mhw = agg_win is not None and not agg_win.empty

            row_titles = ["AO (daily)"]
            if show_pdo:
                row_titles.append("PDO (monthly)")
            if show_npi:
                row_titles.append("NPI anomaly (monthly) — low = strong Aleutian Low")
            if show_mhw:
                row_titles += ["Area Fraction", "Mean Intensity (°C)"]
            n_rows = len(row_titles)
            fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True,
                                subplot_titles=row_titles, vertical_spacing=0.07)

            r = 1
            ao_colors = np.where(ao_win["ao"].values >= 0, "steelblue", "tomato")
            fig.add_trace(go.Bar(x=ao_win["date"], y=ao_win["ao"],
                                 marker_color=ao_colors.tolist(), name="AO",
                                 hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}}<extra></extra>"),
                          row=r, col=1)
            _zero_line(fig, r)
            fig.update_yaxes(title_text="AO", row=r, col=1, title_font={"size": 9})
            r += 1

            if show_pdo:
                pdo_colors = np.where(pdo_win["pdo"].values >= 0, "darkorange", "royalblue")
                fig.add_trace(go.Bar(x=pdo_win["date"], y=pdo_win["pdo"],
                                     marker_color=pdo_colors.tolist(), name="PDO",
                                     hovertemplate=f"%{{x|{_PLOTLY_MONTH}}}: %{{y:.3f}}<extra></extra>"),
                              row=r, col=1)
                _zero_line(fig, r)
                fig.update_yaxes(title_text="PDO", row=r, col=1, title_font={"size": 9})
                r += 1

            if show_npi:
                # Purple = negative anomaly (deep low → strong Aleutian Low); teal = positive.
                npi_colors = np.where(npi_win["npi"].values >= 0, "#4c9a8f", "#8e6fb3")
                fig.add_trace(go.Bar(x=npi_win["date"], y=npi_win["npi"],
                                     marker_color=npi_colors.tolist(), name="NPI",
                                     hovertemplate=f"%{{x|{_PLOTLY_MONTH}}}: %{{y:.2f}} hPa<extra></extra>"),
                              row=r, col=1)
                _zero_line(fig, r)
                fig.update_yaxes(title_text="hPa", row=r, col=1, title_font={"size": 9})
                r += 1

            if show_mhw:
                active_flag = agg_win["area_frac"].values > AREA_THRESH
                fig.add_trace(go.Scatter(
                    x=agg_win["date"], y=agg_win["area_frac"], mode="lines",
                    line={"color": "tomato", "width": 1.8},
                    fill="tozeroy", fillcolor="rgba(255,99,71,0.15)",
                    hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.4f}}<extra></extra>"),
                    row=r, col=1)
                fig.add_hline(y=AREA_THRESH, line_dash="dash", line_color="darkred",
                              line_width=1, row=r, col=1)
                fig.update_yaxes(title_text="fraction", row=r, col=1, title_font={"size": 9})
                r += 1

                fig.add_trace(go.Scatter(
                    x=agg_win["date"], y=agg_win["Ibar"], mode="lines",
                    line={"color": "orangered", "width": 1.8},
                    hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}} °C<extra></extra>"),
                    row=r, col=1)
                fig.update_yaxes(title_text="°C", row=r, col=1, title_font={"size": 9})

                _add_event_shading(fig, agg_win["date"], active_flag, n_rows)

            fig.update_layout(
                title=f"Climate Drivers — {_REGION_NAMES.get(region, region.upper())}",
                height=210 * n_rows, showlegend=False, template="plotly_white",
                bargap=0.05, margin={"l": 60, "r": 20, "t": 60, "b": 40},
            )
            # Force shared x-axis to the requested window (Plotly auto-expands
            # when subplots mix daily and monthly data with different end dates)
            fig.update_xaxes(range=[str(t_start), str(t_end)])
            mhw_plot(fig, use_container_width=True, key="pred_chart")

            _cards = [
                kpi_card("Latest AO", f"{float(ao_df['ao'].iloc[-1]):.3f}", SLATE),
                kpi_card("Mean AO (window)", f"{float(ao_win['ao'].mean()):.3f}", SLATE),
            ]
            if pdo_df is not None and not pdo_df.empty:
                _cards.append(kpi_card("Latest PDO", f"{float(pdo_df['pdo'].iloc[-1]):.3f}", SLATE))
            if npi_anom is not None and not npi_anom.empty:
                _npi_last = npi_anom.iloc[-1]
                _cards.append(kpi_card(
                    "Latest NPI anomaly", f"{float(_npi_last['npi']):+.2f}", SLATE,
                    sub=f"hPa · to {_fmt(_npi_last['date'])}", label_note="(low = strong Low)"))
            if agg_win is not None and not agg_win.empty:
                _cards.append(kpi_card("MHW event days",
                              f"{int((agg_win['area_frac'] > AREA_THRESH).sum())}", BLUE))
            kpi_grid(_cards, cols=len(_cards))

            _driver_cross_correlation(region, agg_df, ao_df, pdo_df, npi_anom)

            # The all-zones comparison lives on its own page; link to it rather than repeating the
            # same cross-zone matrix on every region view.
            callout(
                "Want the big picture? See <a href='/driver_correlations' "
                "style='text-decoration:underline'><b>Climate Driver Links</b></a> for the strongest "
                "PDO / AO / NPI correlations across every ESR zone.", icon="🗺️", tint=SLATE)

    # ============================================================
    # TAB 4 — Risk Gauge
    # ============================================================
    with tab_risk, st.container(border=True):
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
                st.warning(f"No risk data for {_fmt(sel_date)}.")
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
                            kpi_grid([
                                kpi_card("Area Fraction", f"{agg_row['area_frac']:.4f}", BLUE),
                                kpi_card("Mean Intensity (°C)", f"{agg_row['Ibar']:.2f}", RED),
                                kpi_card("Mean Duration (days)", f"{agg_row['Dbar']:.1f}", PURPLE),
                                kpi_card("Cumul. Intensity (°C·days)", f"{agg_row['Cbar']:.2f}", AMBER),
                            ], cols=2)

                with p_col:
                    st.plotly_chart(_make_pct_bars(row_r), use_container_width=True, key="risk_pct_bars")
                    st.markdown(
                        "**Risk levels:** "
                        ":green[🟢 Normal (0–33)]  "
                        ":orange[🟠 Elevated (33–66)]  "
                        ":red[🔴 High Risk (66–100)]"
                    )
                    st.caption(
                        f"Weights: Area Fraction {RISK_WEIGHTS['area_frac']:.0%}, "
                        f"Mean Intensity {RISK_WEIGHTS['Ibar']:.0%}, "
                        f"Mean Duration {RISK_WEIGHTS['Dbar']:.0%}, "
                        f"Cumul. Intensity {RISK_WEIGHTS['Cbar']:.0%}. "
                        "Reference: full 1982–present backfill distribution."
                    )

                st.markdown("---")
                if agg_df is not None:
                    st.plotly_chart(_make_sparkline(risk_df, agg_df, n_days=30),
                                    use_container_width=True, key="risk_sparkline")

    # ============================================================
    # TAB 5 — Forecast (LOFRA frozen module, scoped to this region's ESR zones)
    # ============================================================
    with tab_fc:
        try:
            fc_cfg = load_forecast_config()
        except Exception as exc:  # missing config/vendor — degrade, don't crash the page
            st.info(f"Forecast module not available: {exc}")
        else:
            render_forecast_panel(zones_for_region(region, fc_cfg), fc_cfg)

    footer("Data sources: NOAA OISST v2.1 (SST + sea ice) · CPC Arctic Oscillation · PSL Pacific "
           "Decadal Oscillation. Daily; OISST typically lags real time by 1–2 days.")
