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
from mhw import record
from mhw.states.risk import LEVEL_INCOMPLETE

from dashboard.components.mhw_record_ui import (  # noqa: E402
    ICE_FILL,
    UNKNOWN_FILL,
    add_area_with_coverage,
    as_of_text,
    coverage_footnote,
    coverage_legend_html,
    map_legend_html,
)
from dashboard.components.mhw_revision_note import render_mhw_revision_note  # noqa: E402
from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    PURPLE,
    RED,
    SLATE,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
)

RISK_DIR = record.risk_dir()   # coverage-aware risk recomputed from the D1 record
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

def render() -> None:
    """Operational MHW view — rendered inside the Marine Heatwaves hub."""
    inject_css()
    # ---------------------------------------------------------------------------
    # Shared sidebar — region selector
    # ---------------------------------------------------------------------------
    st.sidebar.header("Controls")

    regions = list_regions()
    if not regions:
        page_header("🌊", "Operational MHW", f"Latest marine-heatwave state, {as_of_text()}", "—")
        st.error("No aggregates parquet found. Run the backfill first.")
        st.stop()

    region = st.sidebar.selectbox("Region", regions, format_func=region_menu_label, key="op_region")
    page_header("🌊", "Operational MHW", f"Latest marine-heatwave state, {as_of_text()}",
                f"{_REGION_NAMES.get(region, region.upper())} ({region.upper()})",
                caption=("The most recent certified marine-heatwave state for the selected region — "
                         "the map, event metrics, AO/PDO context, and a composite risk score."))
    render_mhw_revision_note(region)

    # ---------------------------------------------------------------------------
    # Load data (all cached — fast after first run)
    # ---------------------------------------------------------------------------
    available = find_available_states()
    agg_df    = load_aggregates(region)
    ao_df     = load_ao()
    pdo_df    = load_pdo()

    # Risk percentiles are precomputed from the record at staging (never written from the page).
    risk_df = load_risk_table(region)

    # ---------------------------------------------------------------------------
    # Tabs
    # ---------------------------------------------------------------------------
    tab_map, tab_ts, tab_pred, tab_risk = st.tabs([
        "🗺️ MHW Map",
        "📈 Event Metrics",
        "🌐 Predictability",
        "🚦 Risk Gauge",
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
                date_idx = st.slider("Date", 0, len(dates) - 1, len(dates) - 1,
                                     key="map_date")
                st.caption(f"**{_fmt(dates[date_idx])}**")

            label, colorscale, vmin, vmax, fmt = avail_metrics[metric_key]
            if "V" in data and data.get("R") is not None:
                values, cls = record.map_cells(metric_key, data[metric_key][date_idx], data["A"][date_idx],
                                               data["V"][date_idx], data["R"], data["reason"][date_idx])
            else:   # pre-D1 store (no coverage layers): draw as before
                values = data[metric_key][date_idx].astype(float)
                cls = np.full(values.shape, record.CELL_SCORED, dtype=np.int8)

            lons_2d, lats_2d = np.meshgrid(data["lons"], data["lats"])
            lat_flat  = lats_2d.flatten()
            lon_flat  = lons_2d.flatten()
            val_flat  = values.flatten().astype(float)
            cls_flat  = cls.flatten()
            # Only show where the metric is detected (A·V·R) — everything else is a coverage layer
            val_flat[~(val_flat > 0)] = np.nan
            ids = [str(i) for i in range(len(val_flat))]

            geojson = make_grid_geojson(info["path"])

            fig = go.Figure()
            for k, fillc, name in ((record.CELL_ICE, ICE_FILL, "Observed ice"),
                                   (record.CELL_UNKNOWN, UNKNOWN_FILL, "Not assessed (unknown)")):
                sel = np.flatnonzero(cls_flat == k)
                if sel.size:
                    fig.add_trace(go.Choroplethmap(
                        geojson=geojson, locations=[ids[i] for i in sel], z=np.ones(sel.size),
                        colorscale=[[0, fillc], [1, fillc]], showscale=False,
                        marker_opacity=1.0, marker_line_width=0, name=name,
                        customdata=np.column_stack([lat_flat[sel], lon_flat[sel]]),
                        hovertemplate=(f"Lat: %{{customdata[0]:.3f}}<br>Lon: %{{customdata[1]:.3f}}<br>"
                                       f"{name}<extra></extra>"),
                    ))
            fig.add_trace(go.Choroplethmap(
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
                showlegend=False,
            )
            with c2:
                st.plotly_chart(fig, use_container_width=True, key="map_chart")
                st.markdown(map_legend_html(), unsafe_allow_html=True)
                st.caption("Coloured cells are retained, assessable and in a heatwave on this day. "
                           "Excluded cells (142 across the zones) are never coloured.")

            n_ret = int((cls != record.CELL_HIDDEN).sum())
            n_unk = int((cls == record.CELL_UNKNOWN).sum())
            n_ice = int((cls == record.CELL_ICE).sum())
            shown = values[np.isfinite(values)]
            _cards = [
                kpi_card("Max", f"{shown.max():{fmt}}" if shown.size else "—", SLATE),
                kpi_card("Mean (detected)", f"{shown.mean():{fmt}}" if shown.size else "—", SLATE),
                kpi_card("Observed-ice cells", f"{n_ice} / {n_ret}", BLUE),
                kpi_card("Not-assessed cells", f"{n_unk} / {n_ret}", AMBER),
            ]
            if metric_key == "A":
                n_act = int(np.isfinite(values).sum())
                _cards.insert(0, kpi_card("Detected cells",
                              f"{n_act} / {n_ret} ({100 * n_act / max(n_ret, 1):.1f}%)", RED))
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

            # Event days are judged on eligible days only (a rejected day is never 0 or 1).
            active_flag = ((df_win["area_frac"] > AREA_THRESH) & df_win["eligible"]).to_numpy()
            spans = _active_spans(df_win["date"], active_flag)

            fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                                subplot_titles=[m[1] for m in METRIC_DEFS],
                                vertical_spacing=0.06)

            for row, (col, title, ylabel, color) in enumerate(METRIC_DEFS, start=1):
                if col == "area_frac":
                    add_area_with_coverage(fig, df_win, row=row, col=1, color=color, fill=None)
                else:
                    fig.add_trace(go.Scatter(
                        x=df_win["date"], y=df_win[col].where(~df_win["gap"]), mode="lines",
                        connectgaps=False, line={"color": color, "width": 1.8},
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
            st.markdown(coverage_legend_html(), unsafe_allow_html=True)
            st.caption(coverage_footnote(region))

            # Summary (eligible days only)
            elig = df_win[df_win["eligible"]]
            ev_days = int((elig["area_frac"] > AREA_THRESH).sum())
            n_rej = int((~df_win["eligible"]).sum())
            _cards = [kpi_card("Event Days", f"{ev_days}", BLUE,
                               sub=f"{n_rej} incomplete-coverage day(s) not counted" if n_rej else "")]
            if not elig.empty:
                peak = elig.loc[elig["area_frac"].idxmax()]
                _cards += [kpi_card("Peak Area Fraction", f"{peak['area_frac']:.4f}", BLUE),
                           kpi_card("Peak date", _fmt(peak["date"]), SLATE)]
            kpi_grid(_cards, cols=len(_cards))

    # ============================================================
    # TAB 3 — Predictability Context
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

            row_titles = ["AO (daily)", "PDO (monthly)", "Area Fraction", "Mean Intensity (°C)"]
            n_rows = len(row_titles)
            fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True,
                                subplot_titles=row_titles, vertical_spacing=0.07)

            ao_colors = np.where(ao_win["ao"].values >= 0, "steelblue", "tomato")
            fig.add_trace(go.Bar(x=ao_win["date"], y=ao_win["ao"],
                                 marker_color=ao_colors.tolist(), name="AO",
                                 hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}}<extra></extra>"),
                          row=1, col=1)
            _zero_line(fig, 1)
            fig.update_yaxes(title_text="AO", row=1, col=1, title_font={"size": 9})

            if pdo_win is not None and not pdo_win.empty:
                pdo_colors = np.where(pdo_win["pdo"].values >= 0, "darkorange", "royalblue")
                fig.add_trace(go.Bar(x=pdo_win["date"], y=pdo_win["pdo"],
                                     marker_color=pdo_colors.tolist(), name="PDO",
                                     hovertemplate=f"%{{x|{_PLOTLY_MONTH}}}: %{{y:.3f}}<extra></extra>"),
                              row=2, col=1)
                _zero_line(fig, 2)
                fig.update_yaxes(title_text="PDO", row=2, col=1, title_font={"size": 9})

            if agg_win is not None and not agg_win.empty:
                active_flag = ((agg_win["area_frac"] > AREA_THRESH) & agg_win["eligible"]).to_numpy()
                add_area_with_coverage(fig, agg_win, row=3, col=1, color="tomato",
                                       fill="rgba(255,99,71,0.15)")
                fig.add_hline(y=AREA_THRESH, line_dash="dash", line_color="darkred",
                              line_width=1, row=3, col=1)
                fig.update_yaxes(title_text="fraction", row=3, col=1, title_font={"size": 9})

                fig.add_trace(go.Scatter(
                    x=agg_win["date"], y=agg_win["Ibar"].where(~agg_win["gap"]), mode="lines",
                    connectgaps=False,
                    line={"color": "orangered", "width": 1.8},
                    hovertemplate=f"%{{x|{_PLOTLY_DATE}}}: %{{y:.3f}} °C<extra></extra>"),
                    row=4, col=1)
                fig.update_yaxes(title_text="°C", row=4, col=1, title_font={"size": 9})

                _add_event_shading(fig, agg_win["date"], active_flag, n_rows)

            fig.update_layout(
                title=f"Predictability Context — {region.upper()}",
                height=220 * n_rows, showlegend=False, template="plotly_white",
                bargap=0.05, margin={"l": 60, "r": 20, "t": 60, "b": 40},
            )
            # Force shared x-axis to the requested window (Plotly auto-expands
            # when subplots mix daily and monthly data with different end dates)
            fig.update_xaxes(range=[str(t_start), str(t_end)])
            mhw_plot(fig, use_container_width=True, key="pred_chart")
            st.markdown(coverage_legend_html(), unsafe_allow_html=True)

            _cards = [
                kpi_card("Latest AO", f"{float(ao_df['ao'].iloc[-1]):.3f}", SLATE),
                kpi_card("Mean AO (window)", f"{float(ao_win['ao'].mean()):.3f}", SLATE),
            ]
            if pdo_df is not None and not pdo_df.empty:
                _cards.append(kpi_card("Latest PDO", f"{float(pdo_df['pdo'].iloc[-1]):.3f}", SLATE))
            if agg_win is not None and not agg_win.empty:
                _cards.append(kpi_card("MHW event days",
                              f"{int(((agg_win['area_frac'] > AREA_THRESH) & agg_win['eligible']).sum())}",
                              BLUE))
            kpi_grid(_cards, cols=len(_cards))

    # ============================================================
    # TAB 4 — Risk Gauge
    # ============================================================
    with tab_risk, st.container(border=True):
        if risk_df is None:
            st.error("Risk table not found. Run `mhw-compute-risk`.")
        else:
            min_d = risk_df["date"].dt.date.min()
            max_d = risk_df["date"].dt.date.max()
            sel_date = st.date_input(f"Reference date (record certified to {record.CERTIFIED_THROUGH_TEXT})",
                                     value=max_d,
                                     min_value=min_d, max_value=max_d,
                                     key="risk_date")

            row_r = risk_df[risk_df["date"].dt.date == sel_date]
            if row_r.empty:
                st.warning(f"No risk data for {_fmt(sel_date)}.")
            else:
                row_r = row_r.iloc[0]
                score  = float(row_r["composite_risk"])
                level  = str(row_r["risk_level"])
            if not row_r.empty and level == LEVEL_INCOMPLETE:
                st.warning(f"{_fmt(sel_date)}: incomplete coverage — more than 25 % of the zone could not "
                           "be assessed, so no risk score is given for this day.")
            elif not row_r.empty:
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
                        "Reference: every eligible day (unknown share ≤ 25 %) of the record, "
                        f"1982 – {record.CERTIFIED_THROUGH_TEXT}."
                    )

                st.markdown("---")
                if agg_df is not None:
                    st.plotly_chart(_make_sparkline(risk_df, agg_df, n_days=30),
                                    use_container_width=True, key="risk_sparkline")

    footer("Data sources: NOAA OISST v2.1 (SST + sea ice), heatwave record vintage #7 (D1), certified "
           f"1982 – {record.CERTIFIED_THROUGH_TEXT} · CPC Arctic Oscillation · PSL Pacific Decadal "
           "Oscillation.", guide_url="/marine_heatwave_guide")
