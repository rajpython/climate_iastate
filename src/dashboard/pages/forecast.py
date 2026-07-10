"""Marine Heatwaves → Forecast view.

The third view of the Marine Heatwaves hub (after Operational and Historical), rendered via the
hub's segmented control. It displays LOFRA's **frozen** damped-persistence forecast module (v1,
pinned in ``config/forecast.yml``, vendored at ``vendor/forecast-module-v1/``) run forward over
our own monthly ``area_frac``. Forecasting is a *consumed* research-cell product: the board pins
the paper-validated coefficients and shows them with honest labels — it does not fit anything.

Honest-labeling requirements carried on every tile (from the module README):
  * Damped persistence, leads 1–3 months only; skill fades by ~2–3 months.
  * NBS gets a persistence forecast but carries the Arctic ice-contamination caveat.
  * Chukchi/Beaufort are climatology-only (ice-contaminated SST — a data limit, no occurrence).
  * SEBS onset watch is an EXPERIMENTAL two-state discriminator — never a probability, never
    "beats persistence"; deferred here until the broad-basin field is rebuilt locally.
  * Show the coefficient vintage (2026-04) and the module version on the panel.

Reads the pinned artifacts directly (``mhw.forecast.deploy.read_forecast_artifact``) so the view
does not depend on the API being up. Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
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
from mhw.forecast.deploy import (
    hindcast_series,
    load_forecast_config,
    read_area_frac_monthly,
    read_forecast_artifact,
)

# Standard-normal half-width multipliers for the two nested predictive bands (two-sided).
_Z50 = 0.6744897501960817   # 50% interval  → ppf(0.75)
_Z90 = 1.6448536269514722   # 90% interval  → ppf(0.95)
_HIST_MONTHS = 24          # default months of actuals/hindcast shown before the forecast origin
_LOOKBACK = {"1 yr": 12, "2 yr": 24, "3 yr": 36, "All": 10_000}   # history-window selector

# Full zone names + the geography-first render order (mirrors the board's section layout).
_ZONE_NAMES = {
    "sebs": "Southeastern Bering", "nbs": "Northern Bering",
    "wgoa": "Western Gulf of Alaska", "egoa": "Eastern Gulf of Alaska",
    "ai_west": "Western Aleutians", "ai_central": "Central Aleutians",
    "ai_east": "Eastern Aleutians", "chukchi": "Chukchi", "beaufort": "Beaufort",
}
_GROUPS = [
    ("Bering Sea", ["sebs", "nbs"]),
    ("Gulf of Alaska", ["wgoa", "egoa"]),
    ("Aleutian Islands", ["ai_west", "ai_central", "ai_east"]),
    ("Arctic", ["chukchi", "beaufort"]),
]
_ROLE_LABEL = {"persistence": "Damped persistence", "climatology": "Climatology only"}


def _pct(x) -> str:
    return "—" if x is None else f"{float(x) * 100:.1f}%"


def _lead_card(row) -> str:
    """One KPI card for a single forecast lead (point + honest band + L1 occurrence)."""
    months = int(row["lead_months"])
    conf = str(row["confidence"])
    band = f"band {float(row['band_lo']) * 100:.0f}–{float(row['band_hi']) * 100:.0f}%"
    sub = band
    l1 = row.get("l1_prob")
    if l1 is not None and not (isinstance(l1, float) and l1 != l1):  # not NaN
        sub = f"{band} · P(>q90) {float(l1) * 100:.0f}%"
    return kpi_card(
        label=f"{months}-month", value=_pct(row["point"]), value_color=RED,
        sub=sub, label_note=f"({conf})",
        tip="Point forecast of the monthly heatwave area fraction. The band is a 90% predictive "
            "interval from the AR(1) forecast-error variance (display-clipped to 0–100%). "
            "P(>q90) is the chance the area exceeds the zone's 90th-percentile threshold.",
    )


def _zone_card(zone: str, cfg: dict) -> None:
    meta_role = cfg["zones"][zone]
    role = meta_role["role"]
    name = _ZONE_NAMES.get(zone, zone)
    note = _ROLE_LABEL.get(role, role)
    if meta_role.get("ice_caveat") and role == "persistence":
        note += " · Arctic ice caveat"
    with st.container(border=True):
        section_title(f"{name}", note=note)
        try:
            df, _ = read_forecast_artifact(zone)
        except FileNotFoundError:
            callout(f"No forecast artifact yet for <b>{name}</b>. Run "
                    f"<code>mhw-run-forecast</code> to produce it.", icon="⚙️", tint=SLATE)
            return
        kpi_grid([_lead_card(r) for _, r in df.iterrows()], cols=len(df))
        if role == "climatology":
            callout(
                f"<b>{name}:</b> the satellite SST record here is ice-contaminated, so damped "
                "persistence falls below climatology by two months — magnitude/area is shown as "
                "<b>climatology only</b> (a data limitation, not a skill result). No occurrence "
                "probability is issued.", icon="🧊", tint=SLATE)
        elif meta_role.get("ice_caveat"):
            callout(
                f"<b>{name}:</b> carries genuine one-month persistence skill and gets a forecast, "
                "but the satellite SST is ice-contaminated — read the outlook with the ice caveat "
                "and note there is no broad-field/LIM reading for this zone.", icon="🧊", tint=AMBER)


def _clip01_arr(a: np.ndarray) -> np.ndarray:
    return np.clip(a, 0.0, 1.0)


def _outlook_figure(zone: str, cfg: dict, hist_months: int = _HIST_MONTHS, hc=None):
    """Build the fan chart: *hist_months* of actual area_frac + one-month-ahead hindcast + the
    1/2/3-month forecast, all with nested 50% / 90% predictive bands and dates on the x-axis.
    *hc* is the precomputed hindcast frame (recomputed if None). Returns (figure, meta) or None.
    """
    try:
        fdf, meta = read_forecast_artifact(zone)
    except FileNotFoundError:
        return None
    if hc is None:
        hc = hindcast_series(zone, hist_months, cfg)
    hist = read_area_frac_monthly(zone).tail(hist_months).copy()
    hist["date"] = pd.to_datetime(hist["date"])
    origin_date = hist["date"].iloc[-1]
    origin_val = float(hist["area_frac"].iloc[-1])

    fdf = fdf.sort_values("lead_months")
    t = pd.to_datetime(fdf["target_date"])
    pt = fdf["point"].to_numpy(float)
    sd = np.sqrt(fdf["ar1_var"].to_numpy(float))

    # Forecast bands start at the origin (zero width) so the fan opens from the last actual.
    x = pd.DatetimeIndex([origin_date, *t])
    mid = _clip01_arr(np.concatenate([[origin_val], pt]))

    def band(xs, hi, lo, rgba, name, show_legend):
        # 'tonexty' fills each lower edge up to the immediately preceding upper edge.
        return [
            go.Scatter(x=xs, y=hi * 100, mode="lines", line=dict(width=0),
                       hoverinfo="skip", showlegend=False),
            go.Scatter(x=xs, y=lo * 100, mode="lines", line=dict(width=0), fill="tonexty",
                       fillcolor=rgba, name=name, showlegend=show_legend, hoverinfo="skip"),
        ]

    fig = go.Figure()

    # --- Hindcast: one-month-ahead frozen model rolled across the shown history (amber) ---
    if not hc.empty:
        hx = pd.to_datetime(hc["date"])
        hpt, hsd = hc["point"].to_numpy(float), np.sqrt(hc["ar1_var"].to_numpy(float))
        for z, op in ((_Z90, 0.10), (_Z50, 0.22)):
            for tr in band(hx, _clip01_arr(hpt + z * hsd), _clip01_arr(hpt - z * hsd),
                           f"rgba(179,89,0,{op})", "", False):
                fig.add_trace(tr)
        fig.add_trace(go.Scatter(
            x=hx, y=_clip01_arr(hpt) * 100, mode="lines+markers", name="Hindcast (1-mo)",
            line=dict(color=AMBER, width=2, dash="dash"), marker=dict(size=5, color=AMBER),
            hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra>hindcast</extra>"))

    # --- Forecast: 1–3 month fan from the July origin (blue) ---
    for z, rgba, nm in ((_Z90, "rgba(21,101,192,0.12)", "90% interval"),
                        (_Z50, "rgba(21,101,192,0.30)", "50% interval")):
        for tr in band(x, _clip01_arr(np.concatenate([[origin_val], pt + z * sd])),
                       _clip01_arr(np.concatenate([[origin_val], pt - z * sd])), rgba, nm, True):
            fig.add_trace(tr)
    fig.add_trace(go.Scatter(
        x=x, y=mid * 100, mode="lines+markers", name="Forecast (point)",
        line=dict(color=BLUE, width=2.5, dash="dot"), marker=dict(size=7, color=BLUE),
        hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra>point</extra>"))

    # --- Actual history (dark, on top) ---
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["area_frac"] * 100, mode="lines+markers", name="Actual",
        line=dict(color=SLATE, width=2.5), marker=dict(size=6, color=SLATE),
        hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra>actual</extra>"))
    fig.add_vline(x=origin_date, line=dict(color="#9aa5b1", width=1, dash="dash"))
    fig.add_annotation(x=origin_date, y=1.0, yref="paper", yanchor="bottom",
                       text="forecast start", showarrow=False, font=dict(size=11, color="#7a8694"))
    # Mark the coefficient fit vintage when it falls inside the shown window — hindcast months
    # on/before it are in-sample (honest boundary for a long lookback).
    vdate = pd.Timestamp(meta.get("coefficient_vintage")) if meta.get("coefficient_vintage") else None
    if vdate is not None and hist["date"].iloc[0] < vdate < origin_date:
        fig.add_vline(x=vdate, line=dict(color="#c9a26b", width=1, dash="dot"))
        fig.add_annotation(x=vdate, y=1.0, yref="paper", yanchor="bottom",
                           text="coeff. vintage", showarrow=False,
                           font=dict(size=10, color="#b35900"))
    # Thin the x tick density for long lookbacks so month labels don't collide.
    n_pts = len(hist) + len(t)
    dtick = ("M24" if n_pts > 180 else "M12" if n_pts > 90 else "M6" if n_pts > 30
             else "M3" if n_pts > 15 else "M1")
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified", plot_bgcolor="white",
        yaxis=dict(title="Heatwave area of zone (%)", rangemode="tozero",
                   gridcolor="#eef1f5", zeroline=False),
        xaxis=dict(gridcolor="#eef1f5", dtick=dtick, tickformat="%b\n%Y"))
    return fig, meta


def _skill_stats(hc) -> dict:
    """One-month-ahead skill over the hindcast window: RMSE, bias (mean pred−obs), correlation."""
    err = (hc["point"] - hc["actual"]).to_numpy(float)
    a, p = hc["actual"].to_numpy(float), hc["point"].to_numpy(float)
    corr = float(np.corrcoef(a, p)[0, 1]) if len(hc) > 2 and a.std() > 0 and p.std() > 0 else float("nan")
    return {"rmse": float(np.sqrt((err ** 2).mean())), "bias": float(err.mean()),
            "corr": corr, "n": int(len(hc))}


def _skill_scatter(hc):
    """Predicted-vs-observed scatter (one dot per month) at the same target date, with the 1:1 line.
    A pure lag shows here as scatter below the line at the extremes — not as a time shift."""
    a, p = hc["actual"].to_numpy(float) * 100, hc["point"].to_numpy(float) * 100
    hi = max(1.0, float(np.nanmax([a.max(), p.max()]))) * 1.05
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, hi], y=[0, hi], mode="lines", name="1:1 (perfect)",
                             line=dict(color="#9aa5b1", width=1, dash="dash"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=a, y=p, mode="markers", name="months",
        marker=dict(size=7, color="rgba(179,89,0,0.55)", line=dict(width=0.5, color=AMBER)),
        customdata=pd.to_datetime(hc["date"]).dt.strftime("%b %Y"),
        hovertemplate="%{customdata}<br>observed %{x:.1f}%<br>predicted %{y:.1f}%<extra></extra>"))
    fig.update_layout(
        height=360, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, plot_bgcolor="white",
        xaxis=dict(title="Observed area (%)", range=[0, hi], gridcolor="#eef1f5", zeroline=False),
        yaxis=dict(title="Predicted area, 1-mo ahead (%)", range=[0, hi], gridcolor="#eef1f5",
                   zeroline=False, scaleanchor="x", scaleratio=1))
    return fig


def _zone_outlook(cfg: dict) -> None:
    """Zone-selectable fan chart below the tiles (recent actuals + fanned 1–3 month forecast)."""
    with st.container(border=True):
        section_title("Zone Outlook", note="actuals + one-month hindcast + fanned 1–3 month forecast")
        zones = [z for _, zs in _GROUPS for z in zs if z in cfg["zones"]]
        c1, c2 = st.columns([2, 3])
        with c1:
            zone = st.selectbox("Zone", zones, index=0, key="fc_outlook_zone",
                                format_func=lambda z: _ZONE_NAMES.get(z, z))
        with c2:
            span = st.segmented_control("History shown", list(_LOOKBACK), default="2 yr",
                                        key="fc_outlook_span") or "2 yr"
        hc = hindcast_series(zone, _LOOKBACK[span], cfg)   # computed once, shared by chart + scatter
        built = _outlook_figure(zone, cfg, _LOOKBACK[span], hc=hc)
        if built is None:
            callout("No forecast artifact yet for this zone. Run <code>mhw-run-forecast</code>.",
                    icon="⚙️", tint=SLATE)
            return
        fig, meta = built
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        role = cfg["zones"][zone]["role"]
        model = "damped persistence" if role == "persistence" else "climatology"
        callout(
            f"<b>How to read:</b> the grey line is the observed monthly heatwave area. The amber "
            "dashed line is the <b>hindcast</b> — the same frozen model run <b>one month ahead</b> "
            "at each past month, with amber 50%/90% bands — so you can see how it tracked reality "
            f"(where amber and grey diverge is the error). The dotted blue line is the <b>{model}</b> "
            "point forecast for the next three months, with blue <b>50%</b> (likely) and <b>90%</b> "
            "(plausible) bands that widen with lead time as skill fades. Lower edges floor at 0% "
            f"(area can't be negative). Coefficient vintage {meta.get('coefficient_vintage')}; "
            "hindcast months on/before that vintage are in-sample, so read it as illustrative of "
            "tracking, not a clean skill score.", icon="📈", tint=SLATE)

        # --- Predicted-vs-observed skill (same window; the shift-free diagnostic) ---
        if len(hc) > 2:
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
            section_title("Forecast Skill", note="predicted vs observed, one month ahead")
            s = _skill_stats(hc)
            kpi_grid([
                kpi_card("RMSE", f"{s['rmse'] * 100:.1f}%", RED, sub="one-month-ahead error",
                         label_note="(lower better)"),
                kpi_card("Bias", f"{s['bias'] * 100:+.1f}%", SLATE, sub="mean predicted − observed",
                         label_note="(0 = unbiased)"),
                kpi_card("Correlation", "—" if s["corr"] != s["corr"] else f"{s['corr']:.2f}", BLUE,
                         sub="predicted vs observed", label_note="(1 = perfect)"),
                kpi_card("Months", f"{s['n']}", SLATE, sub=f"in the {span} window"),
            ], cols=4)
            st.plotly_chart(_skill_scatter(hc), use_container_width=True,
                            config={"displayModeBar": False})
            callout(
                "Each dot is one month: <b>observed</b> area (x) against the <b>one-month-ahead "
                "forecast</b> (y) for that same month. Dots on the dashed <b>1:1</b> line are "
                "perfect; points below it are under-forecasts, above are over-forecasts. This is "
                "the shift-free view of the same numbers as the time chart — the apparent one-month "
                "<i>lag</i> there is not a level bias (see <b>Bias ≈ 0</b>) but limited skill, which "
                "shows here as scatter around the line, widest at the extremes.", icon="🎯", tint=SLATE)


def render() -> None:
    inject_css()
    cfg = load_forecast_config()
    version = cfg.get("module_version") or "unpinned"
    vintage = cfg.get("fit_vintage") or "—"

    page_header(
        "🔮", "Marine Heatwave Forecast", subtitle="Short-term outlook · Alaska ESR zones",
        region_label_text="Alaska ESR zones",
        caption="Damped-persistence outlook of the monthly marine-heatwave area fraction for the "
                "nine Alaska ESR (Ecosystem Status Report) zones, leads 1–3 months.")

    callout(
        "This is a <b>consumed research-cell product</b>: the board pins the paper-validated "
        f"forecast module ({version}, frozen coefficients, vintage {vintage}) and displays it — "
        "it does not fit a forecast. <b>Damped persistence is the forecast</b> across the "
        "productive zones; nothing tested resolvably beats it at these leads, and <b>skill fades "
        "by ~2–3 months</b>. Honesty ladder: 1-month <i>headline</i>, 2-month <i>banded</i>, "
        "3-month <i>low-confidence watch</i>.", icon="🧭")

    callout(
        "<b>Reading the tiles:</b> each percentage is the forecast <b>share of the zone under an "
        "active marine heatwave</b> that month (0% = none, 100% = the whole zone). The <i>band</i> "
        "beneath it is a <b>90% predictive interval</b> — the plausible range around the point — "
        "and it widens with lead time. <b>P(&gt;q90)</b> on the 1-month tile is the chance the area "
        "exceeds the zone's historical 90th-percentile month. See the <b>Zone Outlook</b> chart "
        "below for the actuals-plus-forecast view with 50% and 90% bands.", icon="ℹ️", tint=BLUE)

    for group_name, zones in _GROUPS:
        section_title(group_name)
        for zone in zones:
            if zone in cfg["zones"]:
                _zone_card(zone, cfg)

    _zone_outlook(cfg)

    # SEBS onset watch — experimental, deferred until the broad-basin field is rebuilt locally.
    with st.container(border=True):
        section_title("SEBS Onset Watch", note="experimental")
        callout(
            "An <b>experimental</b> two-state early-warning discriminator (elevated / normal) for "
            "Southeastern Bering heatwave <i>onset</i> — a discrimination indicator, <b>not</b> a "
            "calibrated probability and <b>not</b> framed as beating persistence. It is deferred "
            "until the broad-basin OISST field is rebuilt locally, so no state is issued yet.",
            icon="🧪", tint=AMBER)

    footer(
        f"Source: LOFRA frozen forecast module {version} (damped persistence / climatology), "
        f"coefficient vintage {vintage}; run forward over our monthly area_frac. Leads 1–3 months.",
        guide_url="/marine_heatwave_guide")
