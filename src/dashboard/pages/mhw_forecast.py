"""Alaska-wide Climate → Marine Heatwave Forecast (NOAA PSL).

A replication of NOAA PSL's *experimental* Marine Heatwave forecast (Jacox et
al. 2022): the probability, per ocean cell and lead time, that the monthly SST
anomaly exceeds the local 90th-percentile threshold, from the NMME ensemble.
This page **displays the published product** for the nine Alaska ESR zones — it
does not fit or recompute the forecast (that is the LOFRA research cell's work,
shown separately under Marine Heatwaves → Forecast).

Everything the page reads is a small derived artifact built by
``mhw-build-psl-mhw`` from the raw PSL NetCDF files; the loaders in
``components.psl_mhw_data`` cache them so widget changes only slice arrays.
Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

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
from dashboard.components.psl_mhw_data import (
    config,
    load_obs_status,
    load_prob_cube,
    load_sedi,
    load_zone_coverage,
    load_zone_meta,
    load_zone_series,
    lon_to_180,
    make_grid_geojson,
    zone_outline,
)

_ZONE_NAMES = {
    "sebs": "Southeastern Bering", "nbs": "Northern Bering",
    "wgoa": "Western Gulf of Alaska", "egoa": "Eastern Gulf of Alaska",
    "ai_west": "Western Aleutians", "ai_central": "Central Aleutians",
    "ai_east": "Eastern Aleutians", "chukchi": "Chukchi", "beaufort": "Beaufort",
}
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_CLIM_PCT = 10.0   # a well-calibrated forecast averages the 10% climatological base rate


def _fmt_zone(z: str) -> str:
    return _ZONE_NAMES.get(z, z)


def _center_lon(lons180: np.ndarray) -> float:
    """Dateline-aware map centre: use 180 when the window spans the antimeridian."""
    return 180.0 if (lons180.max() - lons180.min()) > 180.0 else float(lons180.mean())


# ---------------------------------------------------------------------------
# Panel 1 — probability map
# ---------------------------------------------------------------------------

def _cell_map(z2d: np.ndarray, lats: np.ndarray, lons0360: np.ndarray, *,
              colorscale: str, zmin: float, zmax: float, cbar_title: str, value_fmt: str,
              value_label: str, outline: dict | None = None,
              coverage: np.ndarray | None = None, height: int = 520) -> go.Figure:
    """One 1° choropleth over the Alaska grid, optionally masked + framed to a zone.

    ``z2d`` is (lat, lon) in display units. When ``coverage`` is given, cells
    outside the zone polygon are set transparent; when ``outline`` is given the
    zone boundary is drawn and the map recenters/zooms to it. Each cell carries
    its (lat, lon) as customdata so a click can be resolved back to a grid cell.
    """
    lons180 = lon_to_180(lons0360)
    geojson = make_grid_geojson(tuple(lats.tolist()), tuple(lons0360.tolist()))
    lon2d, lat2d = np.meshgrid(lons180, lats)

    zc = z2d.astype(float).copy()
    if coverage is not None and coverage.shape == zc.shape:
        zc[coverage <= 0] = np.nan                             # mask to the selected zone
    val = zc.flatten()
    ids = [str(i) for i in range(val.size)]

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, locations=ids, z=val,
        colorscale=colorscale, zmin=zmin, zmax=zmax,
        marker_opacity=0.72, marker_line_width=0,
        colorbar=dict(title=cbar_title, thickness=15),
        customdata=np.column_stack([lat2d.flatten(), lon2d.flatten()]),
        hovertemplate="Lat %{customdata[0]:.1f}, Lon %{customdata[1]:.1f}<br>"
                      + value_label + ": %{z:" + value_fmt + "}<extra></extra>",
    ))
    if outline is not None:
        fig.add_trace(go.Scattermap(
            lon=outline["lon"], lat=outline["lat"], mode="lines",
            line=dict(color="#0d3b66", width=2.5),
            hoverinfo="skip", showlegend=False))
        center, zoom = outline["center"], outline["zoom"]
    else:
        center, zoom = {"lat": float(lats.mean()), "lon": _center_lon(lons180)}, 2.4

    fig.update_layout(
        map=dict(style="open-street-map", center=center, zoom=zoom),
        height=height, margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


def _probability_map(cube: dict, init_idx: int, lead: float,
                     outline: dict | None = None,
                     coverage: np.ndarray | None = None) -> go.Figure:
    lead_idx = int(np.argmin(np.abs(cube["leads"] - lead)))
    z = cube["prob"][init_idx, lead_idx] * 100.0               # (lat, lon) %, NaN = land
    return _cell_map(z, cube["lats"], cube["lons"],
                     colorscale="Reds", zmin=0, zmax=100, cbar_title="MHW prob (%)",
                     value_fmt=".0f", value_label="Probability",
                     outline=outline, coverage=coverage)


# ---------------------------------------------------------------------------
# Panel 2 — zone probability vs lead
# ---------------------------------------------------------------------------

def _prob_lead_figure(traces: list, highlight_lead: float | None, title: str,
                      height: int = 380) -> go.Figure:
    """One overlaid probability-by-lead panel, NOAA PSL styling.

    ``traces`` is a list of (label, x, y, dashed, color). Both flavours share one
    axis — trend-retained solid, detrended dashed — on a fixed 0–100% scale with
    a red dashed "10% threshold" line, a PSL-style centred title, and the
    selected lead marked with a gold dot (PSL's "current lead month", tied here
    to the lead slider that also drives the map).
    """
    fig = go.Figure()
    fig.add_hline(y=_CLIM_PCT, line=dict(color=RED, width=1.6, dash="dash"))
    fig.add_annotation(x=1, xref="x domain", y=_CLIM_PCT, yref="y",
                       xanchor="right", yanchor="bottom", text="10% threshold",
                       showarrow=False, font=dict(size=13, color=RED))
    first = True
    for label, x, y, dashed, color in traces:
        if x is None or len(x) == 0:
            continue
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=label,
            line=dict(color=color, width=2.5, dash="dash" if dashed else "solid"),
            marker=dict(size=6, color=color),
            hovertemplate="+%{x} mo: %{y:.0f}%<extra>" + label + "</extra>"))
        if highlight_lead is not None:
            xi = int(np.argmin(np.abs(x - highlight_lead)))
            fig.add_trace(go.Scatter(
                x=[x[xi]], y=[y[xi]], mode="markers", name="current lead month",
                legendgroup="sel", showlegend=first,
                marker=dict(size=13, color=AMBER, line=dict(width=1.5, color="white")),
                hovertemplate="selected lead +%{x} mo: %{y:.0f}%<extra></extra>"))
            first = False
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=52, b=84),
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=16, color="#3b4654")),
        legend=dict(orientation="h", yanchor="top", y=-0.24, x=0.5, xanchor="center",
                    font=dict(size=14)),
        plot_bgcolor="white", hovermode="x unified",
        yaxis=dict(title=dict(text="MHW probability (%)", font=dict(color=RED, size=14)),
                   range=[0, 100], gridcolor="#eef1f5", zeroline=False,
                   tickfont=dict(color=RED),
                   showline=True, linecolor="#c9d2db", linewidth=1, ticks="outside",
                   tickcolor="#c9d2db", ticklen=4),
        xaxis=dict(title=dict(text="Lead time (months)", standoff=8), gridcolor="#eef1f5",
                   showline=True, linecolor="#c9d2db", linewidth=1, ticks="outside",
                   tickcolor="#c9d2db", ticklen=4))
    return fig


def _zone_series_figure(zone: str, init_time, series_by_flavor: dict,
                        highlight_lead: float | None, title: str) -> go.Figure:
    traces = []
    for flavor, label, dashed, color in [("trend", "Trend-retained", False, BLUE),
                                         ("detrend", "Detrended", True, PURPLE)]:
        df = series_by_flavor.get(flavor)
        if df is None:
            continue
        sub = df[(df["zone"] == zone) & (df["init_time"] == init_time)].sort_values("lead_months")
        if sub.empty:
            continue
        traces.append((label, sub["lead_months"].to_numpy(),
                       sub["prob"].to_numpy() * 100.0, dashed, color))
    return _prob_lead_figure(traces, highlight_lead, title)


def _cell_series_figure(cubes: dict, init_idx: int, lat_i: int, lon_j: int,
                        highlight_lead: float, title: str) -> go.Figure:
    """Probability-by-lead for one clicked grid cell (trend solid + detrended dashed)."""
    traces = []
    for flavor, label, dashed, color in [("trend", "Trend-retained", False, BLUE),
                                         ("detrend", "Detrended", True, PURPLE)]:
        cube = cubes.get(flavor)
        if cube is None:
            continue
        traces.append((label, cube["leads"],
                       cube["prob"][init_idx, :, lat_i, lon_j].astype(float) * 100.0,
                       dashed, color))
    return _prob_lead_figure(traces, highlight_lead, title, height=360)


def _clicked_cell(event, cube: dict) -> tuple[int, int, float, float] | None:
    """Resolve a map click to (lat_i, lon_j, lat, lon180), or None.

    Prefers the choropleth cell centroid ``ct`` ([lon, lat]); falls back to the
    per-cell customdata, which Streamlit serializes as a {'0': lat, '1': lon}
    dict. Only the choropleth trace (curve 0) carries either, so the zone-outline
    trace is ignored. The result snaps to the nearest cube cell.
    """
    try:
        points = event["selection"]["points"]
    except (KeyError, TypeError):
        return None
    for pt in points:
        if pt.get("curve_number", 0) != 0:
            continue
        ct = pt.get("ct")
        if ct and len(ct) == 2:
            lon180, lat = float(ct[0]), float(ct[1])
        else:
            cd = pt.get("customdata")
            if isinstance(cd, dict):
                cd = [cd.get("0"), cd.get("1")]
            if not cd or cd[0] is None:
                continue
            lat, lon180 = float(cd[0]), float(cd[1])
        lon360 = lon180 % 360.0
        lat_i = int(np.argmin(np.abs(cube["lats"] - lat)))
        lon_j = int(np.argmin(np.abs(cube["lons"] - lon360)))
        return lat_i, lon_j, float(cube["lats"][lat_i]), lon180
    return None


# ---------------------------------------------------------------------------
# Panel 3 — SEDI skill map
# ---------------------------------------------------------------------------

def _skill_map(sedi: dict, flavor: str, lead: float,
               outline: dict | None = None,
               coverage: np.ndarray | None = None) -> go.Figure:
    lead_idx = int(np.argmin(np.abs(sedi["leads"] - lead)))
    z = sedi[f"sedi_{flavor}"][lead_idx]                       # (lat, lon)
    return _cell_map(z, sedi["lats"], sedi["lons"],
                     colorscale="RdBu", zmin=-1, zmax=1, cbar_title="SEDI",
                     value_fmt=".2f", value_label="SEDI",
                     outline=outline, coverage=coverage, height=460)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render() -> None:
    inject_css()
    cfg = config()
    zones = cfg["zones"]

    trend_series = load_zone_series("trend")
    if trend_series.empty:
        page_header("🌊", "Alaska Marine Heatwave Forecast",
                    subtitle="NOAA PSL experimental MHW probability",
                    region_label_text="9 ESR zones")
        callout(
            "Forecast artifacts are not built yet. Run "
            "<code>mhw-fetch-psl-mhw</code> then <code>mhw-build-psl-mhw --flavor both</code> "
            "to generate them.", icon="⚙️", tint=SLATE)
        return

    # --- Controls (sidebar owns page controls per the house convention) ---
    st.sidebar.header("Forecast controls")
    years = sorted(trend_series["init_year"].unique())
    year = st.sidebar.selectbox("Initialization year", years, index=len(years) - 1,
                                key="psl_year")
    months = sorted(trend_series.loc[trend_series["init_year"] == year, "init_month"].unique())
    month = st.sidebar.selectbox("Initialization month", months, index=len(months) - 1,
                                 key="psl_month", format_func=lambda m: _MONTHS[m - 1])
    detrend = st.sidebar.toggle("Remove long-term trend (detrended)", key="psl_detrend")
    flavor = "detrend" if detrend else "trend"
    leads = sorted(trend_series["lead_months"].unique())
    lead = st.sidebar.select_slider("Lead time (months ahead)", options=leads, value=leads[0],
                                    key="psl_lead")
    zone = st.sidebar.selectbox("ESR zone", zones, key="psl_zone", format_func=_fmt_zone)
    zone_only = st.sidebar.toggle("Show only the selected zone", value=True, key="psl_zone_only",
                                  help="Mask the map to the cells inside the ESR zone; turn off to "
                                       "see the whole Alaska field for spatial context.")

    init_time = trend_series.loc[
        (trend_series["init_year"] == year) & (trend_series["init_month"] == month),
        "init_time"].iloc[0]

    page_header(
        "🌊", "Alaska Marine Heatwave Forecast",
        subtitle="NOAA PSL experimental MHW probability · Alaska ESR zones",
        region_label_text=_fmt_zone(zone),
        caption=f"Initialized {_MONTHS[month - 1]} {year} · "
                f"{'detrended' if detrend else 'trend-retained'} · +{lead:.1f} month lead")

    callout(
        "The <b>probability that each ocean cell is in a marine heatwave</b> — its monthly "
        "temperature above the local warmest-10% threshold — from NOAA PSL's experimental NMME "
        "forecast (Jacox et al. 2022). This page mirrors the published NOAA product for the nine "
        "Alaska ecosystem zones; it is separate from the board's own short-term forecast under "
        "<a href='/marine_heatwaves' style='text-decoration:underline'>Marine Heatwaves</a>.",
        icon="🌡️")

    cube = load_prob_cube(flavor)

    # --- Panel 1: probability map ---
    with st.container(border=True):
        scope = _fmt_zone(zone) if zone_only else "all Alaska ESR zones"
        section_title("Probability Map",
                      note=f"chance of MHW at +{lead:.1f} months, {_MONTHS[month - 1]} {year} start · "
                           f"{scope}")
        if cube is None or init_time not in cube["inits"]:
            callout("No probability cube for this selection.", icon="⚠️", tint=AMBER)
        else:
            init_idx = cube["inits"].index(init_time)
            coverage = load_zone_coverage(zone) if zone_only else None
            event = st.plotly_chart(
                _probability_map(cube, init_idx, lead, zone_outline(zone), coverage),
                use_container_width=True, on_select="rerun", selection_mode="points",
                key="psl_prob_map", config={"displayModeBar": False})
            if zone_only:
                body = ("Only the cells inside <b>" + _fmt_zone(zone) + "</b> are shown — the "
                        "same cells the zone probability below is averaged over. Red is a higher "
                        "chance the cell exceeds its 90th-percentile monthly temperature; near 10% "
                        "means no strong signal (the long-run base rate). Turn off "
                        "<i>Show only the selected zone</i> in the sidebar for the whole-Alaska map.")
            else:
                body = ("Red shows a higher chance the cell exceeds its 90th-percentile monthly "
                        "temperature; near 10% means no strong signal (the long-run base rate). "
                        "The dark outline marks <b>" + _fmt_zone(zone) + "</b>.")
            callout(body + " <b>Click any cell</b> to see its own probability-by-lead curve below.",
                    icon="🗺️", tint=SLATE)

            # Per-cell drill-down (PSL's page lets you click a grid cell; so do we).
            hit = _clicked_cell(event, cube)
            if hit is not None:
                lat_i, lon_j, clat, clon = hit
                cubes = {"trend": load_prob_cube("trend"), "detrend": load_prob_cube("detrend")}
                hemi = "E" if clon >= 0 else "W"
                cell_title = f"({abs(clon):.0f}{hemi},{clat:.0f}N) initialized {_MONTHS[month - 1]} {year}"
                section_title(f"Selected cell — {clat:.1f}°N, {abs(clon):.1f}°{hemi}",
                              note="probability by lead for this single 1° cell · "
                                   "trend solid, detrended dashed")
                st.plotly_chart(_cell_series_figure(cubes, init_idx, lat_i, lon_j, lead, cell_title),
                                use_container_width=True, config={"displayModeBar": False})
                callout(
                    "This is the forecast for the one 1° cell you clicked — the building block the "
                    "zone average below is made of. Click another cell to compare, or the same cell "
                    "again to keep it.", icon="📍", tint=SLATE)

    # --- Panel 2: zone probability vs lead ---
    with st.container(border=True):
        section_title(f"{_fmt_zone(zone)} — Probability by Lead",
                      note="trend-retained (solid) vs detrended (dashed), 0–100% scale, 10% threshold")
        series = {"trend": trend_series, "detrend": load_zone_series("detrend")}
        zone_title = f"{_fmt_zone(zone)} initialized {_MONTHS[month - 1]} {year}"
        st.plotly_chart(_zone_series_figure(zone, init_time, series, lead, zone_title),
                        use_container_width=True, config={"displayModeBar": False})

        meta = load_zone_meta()
        row = meta[meta["zone"] == zone]
        cards = []
        sub = trend_series[(trend_series["zone"] == zone)
                           & (trend_series["init_time"] == init_time)]
        near = sub[sub["lead_months"] == leads[0]]["prob"]
        if not near.empty:
            cards.append(kpi_card("Nearest-lead probability", f"{near.iloc[0] * 100:.0f}%", RED,
                                  sub=f"+{leads[0]:.1f} month, trend-retained"))
        if not row.empty:
            cards.append(kpi_card("Zone grid cells", f"{int(row['n_cells'].iloc[0])}", BLUE,
                                  sub="1° NMME cells with weight"))
            ice = float(row["ice_frac"].iloc[0])
            cards.append(kpi_card("Seasonal-ice fraction", f"{ice * 100:.0f}%",
                                  AMBER if ice > 0.5 else SLATE,
                                  sub="of the zone's weighted area", label_note="(caveat)"))
        if cards:
            kpi_grid(cards, cols=len(cards))
        obs = load_obs_status()
        if not obs.empty:
            callout(
                "Both forecasts on one axis: <b>trend-retained</b> (solid) and <b>detrended</b> "
                "(dashed). Detrending removes the long-term warming to isolate the month-to-month "
                "signal — useful for judging whether a high probability is genuinely unusual or "
                "just the new normal. The gold dot marks the lead you selected on the slider; the "
                "red dashed line is the 10% threshold (the long-run base rate).",
                icon="📈", tint=SLATE)

    # --- Panel 3: SEDI skill map ---
    with st.container(border=True):
        scope = _fmt_zone(zone) if zone_only else "all Alaska ESR zones"
        section_title("Forecast Skill — SEDI",
                      note=f"Symmetric Extremal Dependence Index at +{lead:.1f} months · {scope} · "
                           "1 = perfect, 0 = no better than chance")
        sedi = load_sedi()
        if sedi is None:
            callout(
                "The skill map is a heavy one-time build from the 1991–2020 hindcast and is "
                "computed locally, then shipped to the server. It is not available in this "
                "environment yet.", icon="🧪", tint=SLATE)
        else:
            sedi_cov = load_zone_coverage(zone) if zone_only else None
            st.plotly_chart(_skill_map(sedi, flavor, lead, zone_outline(zone), sedi_cov),
                            use_container_width=True, config={"displayModeBar": False})
            zi = sedi["zones"].index(zone) if zone in sedi["zones"] else None
            li = int(np.argmin(np.abs(sedi["leads"] - lead)))
            if zi is not None:
                zval = sedi[f"zone_sedi_{flavor}"][zi, li]
                kpi_grid([kpi_card(
                    f"{_fmt_zone(zone)} skill", "—" if np.isnan(zval) else f"{zval:.2f}", BLUE,
                    sub=f"SEDI at +{lead:.1f} months ahead")], cols=1)
            callout(
                "<b>SEDI (Symmetric Extremal Dependence Index)</b> compares past forecasts against "
                "what actually happened over 1991–2020. Values near 1 mean the forecast reliably "
                "flagged heatwaves at this lead; near 0 means no skill. It is pooled over all "
                "initialization months (skill is a property of the lead, not one calendar month), "
                "and is undefined — shown blank — for cells that never recorded a hit or a false "
                "alarm at this lead, which is why coverage thins at longer leads.",
                icon="🎯", tint=SLATE)

    footer(
        cfg["citation"] + " Forecast: NOAA PSL experimental Marine Heatwave Outlook "
        "(Jacox et al. 2022). Zonal means are area-weighted (cos-lat × cell coverage) over the "
        "AFSC ESR polygons.",
        guide_url="/marine_heatwave_guide")


if __name__ == "__main__":
    render()
