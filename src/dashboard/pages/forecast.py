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
from mhw.forecast.scorings import (
    OCCURRENCE_CAPTION,
    occurrence_reliability,
    occurrence_skill,
)

# Standard-normal half-width multipliers for the two nested predictive bands (two-sided).
_Z50 = 0.6744897501960817   # 50% interval  → ppf(0.75)
_Z90 = 1.6448536269514722   # 90% interval  → ppf(0.95)
_HIST_MONTHS = 12          # default months of actuals/hindcast shown before the forecast origin
_LOOKBACK = {"3 mo": 3, "6 mo": 6, "1 yr": 12}                    # history-window selector

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
_ROLE_LABEL = {"persistence": "Short-term outlook", "climatology": "Typical-year estimate"}

# Map an Operational-tab region code → the forecast zone(s) it contains. Combined ESR regions
# expand to their forecast sub-zones (ebs = SEBS+NBS shelf; goa = W+E; ai = the three strata);
# single-zone regions map to themselves. Regions absent here (e.g. the slope) have no forecast.
REGION_TO_ZONES = {
    "ebs": ["sebs", "nbs"], "sebs": ["sebs"], "nbs": ["nbs"],
    "goa": ["wgoa", "egoa"], "wgoa": ["wgoa"], "egoa": ["egoa"],
    "ai": ["ai_west", "ai_central", "ai_east"],
    "ai_west": ["ai_west"], "ai_central": ["ai_central"], "ai_east": ["ai_east"],
    "chukchi": ["chukchi"], "beaufort": ["beaufort"],
}


def zones_for_region(region: str, cfg: dict) -> list[str]:
    """Forecast zones belonging to an Operational region, in board render order."""
    wanted = set(REGION_TO_ZONES.get(region, [region]))
    return [z for _, zs in _GROUPS for z in zs if z in wanted and z in cfg["zones"]]


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
        tip="Best-estimate forecast of the share of the zone under a marine heatwave that month. "
            "The band is the plausible range around it (a 90% interval), shown between 0% and 100%. "
            "P(>q90) is the chance the area is larger than in all but the warmest 10% of past months.",
    )


def _zone_card(zone: str, cfg: dict) -> None:
    meta_role = cfg["zones"][zone]
    role = meta_role["role"]
    name = _ZONE_NAMES.get(zone, zone)
    note = _ROLE_LABEL.get(role, role)
    if meta_role.get("ice_caveat") and role == "persistence":
        note += " · sea-ice caveat"
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
                f"<b>{name}:</b> sea ice disturbs the satellite temperature record here, so carrying "
                "recent conditions forward stops working beyond a month or two. We show a "
                "<b>typical-year estimate</b> instead — a data limitation, not a forecast result — "
                "and no heatwave-chance is issued.", icon="🧊", tint=SLATE)
        elif meta_role.get("ice_caveat"):
            callout(
                f"<b>{name}:</b> has genuine one-month forecast skill and gets an outlook, but sea "
                "ice affects the satellite temperatures — read it with that caveat in mind.",
                icon="🧊", tint=AMBER)


def _occurrence_zone_row(zone: str, cfg: dict) -> None:
    """One damped zone's occurrence read-out: live P(>q90) + its skill (BSS-vs-clim, AUC).

    Live probability is this month's forecast (``l1_prob`` in the artifact); the skill numbers are
    LOFRA's certified v2 validation of that same damped-persistence forecast — never re-derived.
    """
    name = _ZONE_NAMES.get(zone, zone)
    skill = occurrence_skill(zone, lead=1)
    try:
        fdf, _ = read_forecast_artifact(zone)
        l1 = fdf.loc[fdf["lead"] == "L1", "l1_prob"]
        prob = float(l1.iloc[0]) if len(l1) and not pd.isna(l1.iloc[0]) else None
    except FileNotFoundError:
        prob = None
    if skill is None and prob is None:
        return
    cards = [
        kpi_card(
            label=f"{name} · P(&gt;q90)", value=_pct(prob) if prob is not None else "—",
            value_color=BLUE, sub="next month",
            tip="This month's forecast chance that the heatwave area is larger than in all but the "
                "warmest 10% of past months — read off the same damped-persistence forecast as the "
                "magnitude tile."),
    ]
    if skill is not None:
        cards.append(kpi_card(
            label="Skill vs climatology", value=f"{skill['bss_clim']:.2f}", value_color=BLUE,
            sub="BSS · 1 month", label_note=f"(n={int(skill['n'])})",
            tip="Brier Skill Score against the seasonal average: 0 = no better than climatology, 1 = "
                "perfect. This measures skill over climatology — it is not a gain over persistence."))
        cards.append(kpi_card(
            label="Discrimination", value=f"{skill['auc']:.2f}", value_color=BLUE, sub="AUC · 1 month",
            tip="Area under the ROC curve: the chance the forecast ranks a true high-area month above "
                "a low-area one. 0.5 = no skill, 1.0 = perfect separation."))
    kpi_grid(cards, cols=len(cards))
    if cfg["zones"].get(zone, {}).get("ice_caveat"):
        callout(f"<b>{name}:</b> sea ice affects the satellite temperatures here — read the "
                "occurrence chance with that caveat.", icon="🧊", tint=AMBER)


def _reliability_figure(zone: str):
    """Reliability diagram for a zone's occurrence forecast: mean forecast prob vs observed
    frequency per bin, against the 1:1 perfect-reliability line. Marker size ∝ months in the bin.
    Returns a Plotly figure, or None when no reliability bins exist."""
    rb = occurrence_reliability(zone, lead=1)
    if rb.empty:
        return None
    x = rb["p_mean"].to_numpy(float) * 100
    y = rb["o_freq"].to_numpy(float) * 100
    n = rb["n"].to_numpy(float)
    hi = max(1.0, float(np.nanmax([x.max(), y.max()]))) * 1.08
    sizes = 8 + 22 * np.sqrt(n / max(n.max(), 1.0))   # ≥8px, area-encodes bin count
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, hi], y=[0, hi], mode="lines", name="perfect",
                             line=dict(color="#9aa5b1", width=1, dash="dash"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", name="observed",
        line=dict(color=BLUE, width=2),
        marker=dict(size=sizes, color="rgba(30,102,166,0.55)", line=dict(width=1, color=BLUE)),
        customdata=n,
        hovertemplate="forecast %{x:.0f}%<br>observed %{y:.0f}%<br>%{customdata:.0f} months<extra></extra>"))
    fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, plot_bgcolor="white",
        xaxis=dict(title="Forecast probability (%)", range=[0, hi], gridcolor="#eef1f5", zeroline=False),
        yaxis=dict(title="Observed frequency (%)", range=[0, hi], gridcolor="#eef1f5", zeroline=False,
                   scaleanchor="x", scaleratio=1))
    return fig


def _occurrence_section(zones: list[str], cfg: dict) -> None:
    """Occurrence-probability report card — the deployed damped-persistence forecast's P(>q90) and
    its skill, for the damped zones in view (climatology zones have no occurrence product)."""
    damped = [z for _, zs in _GROUPS for z in zs
              if z in set(zones) and cfg["zones"].get(z, {}).get("role") == "persistence"]
    if not damped:
        return
    with st.container(border=True):
        section_title("Occurrence Probability",
                      note="chance of an unusually large heatwave · one month ahead")
        callout(OCCURRENCE_CAPTION, icon="📈", tint=BLUE)
        for zone in damped:
            _occurrence_zone_row(zone, cfg)
        # Reliability curve for one zone at a time (keeps the card compact for multi-zone regions).
        zkey = "fc_occ_relia_" + "_".join(damped)
        zsel = st.selectbox("Reliability check — zone", damped, index=0, key=zkey,
                            format_func=lambda z: _ZONE_NAMES.get(z, z))
        fig = _reliability_figure(zsel)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False}, key=f"relia_{zsel}")
            st.caption("Points on the dashed line mean forecasts are well-calibrated — when it says "
                       "20%, it happens about 20% of the time. Bigger dots = more months in that bin.")


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
            x=hx, y=_clip01_arr(hpt) * 100, mode="lines+markers", name="Past forecasts (1-mo)",
            line=dict(color=AMBER, width=2, dash="dash"), marker=dict(size=5, color=AMBER),
            hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra>past forecast</extra>"))

    # --- Forecast: 1–3 month fan from the July origin (blue) ---
    for z, rgba, nm in ((_Z90, "rgba(21,101,192,0.12)", "90% interval"),
                        (_Z50, "rgba(21,101,192,0.30)", "50% interval")):
        for tr in band(x, _clip01_arr(np.concatenate([[origin_val], pt + z * sd])),
                       _clip01_arr(np.concatenate([[origin_val], pt - z * sd])), rgba, nm, True):
            fig.add_trace(tr)
    fig.add_trace(go.Scatter(
        x=x, y=mid * 100, mode="lines+markers", name="Forecast",
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
                           text="model built to here", showarrow=False,
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


def _zone_outlook(cfg: dict, zones: list[str]) -> None:
    """Zone-selectable fan chart below the tiles (recent actuals + fanned 1–3 month forecast).

    ``zones`` scopes the picker to the selected Operational region's forecast zone(s)."""
    with st.container(border=True):
        section_title("Zone Outlook", note="recent history, how past forecasts did, and the 1–3 month outlook")
        # Key the zone picker on the current zone set so switching Operational region does not
        # leave a stale (now out-of-options) selection in session state.
        zkey = "fc_outlook_zone_" + "_".join(zones)
        c1, c2 = st.columns([2, 3])
        with c1:
            zone = st.selectbox("Zone", zones, index=0, key=zkey,
                                format_func=lambda z: _ZONE_NAMES.get(z, z))
        with c2:
            span = st.segmented_control("History shown", list(_LOOKBACK), default="1 yr",
                                        key="fc_outlook_span") or "1 yr"
        hc = hindcast_series(zone, _LOOKBACK[span], cfg)   # computed once, shared by chart + scatter
        built = _outlook_figure(zone, cfg, _LOOKBACK[span], hc=hc)
        if built is None:
            callout("No forecast artifact yet for this zone. Run <code>mhw-run-forecast</code>.",
                    icon="⚙️", tint=SLATE)
            return
        fig, _ = built
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        callout(
            "<b>How to read:</b> the grey line is what actually happened — the monthly heatwave "
            "area. The amber dashed line shows how the forecast <b>would have done</b>: the same "
            "method run <b>one month ahead</b> at each past month, with amber 50%/90% ranges, so "
            "where amber and grey diverge is the miss. The dotted blue line is the <b>forecast</b> "
            "for the next three months, with blue <b>50%</b> (likely) and <b>90%</b> (plausible) "
            "ranges that widen further out as the forecast gets less certain. The lower edges stop "
            "at 0% (area can't be negative). Earlier months were used to build the method, so treat "
            "that part as an illustration of how it tracks, not a clean score.", icon="📈", tint=SLATE)

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


def render_forecast_panel(zones: list[str], cfg: dict | None = None) -> None:
    """Forecast body scoped to ``zones`` — the tiles, Zone Outlook, SEBS onset watch and footer.

    Rendered inside the Operational tab (filtered to the selected region's forecast zones), so it
    draws no page header of its own and assumes ``inject_css()`` was already called by the host.
    """
    cfg = cfg or load_forecast_config()

    if not zones:
        callout(
            "No outlook is issued for this region — the forecast covers the nine Alaska ESR zones "
            "(Bering shelf, Gulf of Alaska, Aleutians, Chukchi/Beaufort). Select one of those "
            "regions to see its outlook.", icon="🧭", tint=SLATE)
        return

    callout(
        "This short-term outlook comes from our <b>ongoing marine-heatwave forecasting research</b> "
        "(described in the <a href='/forecast_development' style='text-decoration:underline'>working "
        "paper</a>). It works by carrying recent conditions forward and easing them toward normal — a "
        "simple approach that, so far, nothing else has reliably beaten this far out. Read it as "
        "<b>most reliable one month ahead</b>, still useful at two months, and a <b>low-confidence "
        "watch by three months</b>.", icon="🧭")

    callout(
        "<b>Reading the tiles:</b> each percentage is the forecast <b>share of the zone under an "
        "active marine heatwave</b> that month (0% = none, 100% = the whole zone). The <i>band</i> "
        "beneath it is the <b>plausible range</b> around that number, and it widens the further out "
        "the forecast reaches. <b>P(&gt;q90)</b> on the 1-month tile is the chance the area is "
        "larger than in all but the warmest 10% of past months. See the <b>Zone Outlook</b> chart "
        "below for recent history alongside the outlook.", icon="ℹ️", tint=BLUE)

    zone_set = set(zones)
    for group_name, group_zones in _GROUPS:
        shown = [z for z in group_zones if z in zone_set and z in cfg["zones"]]
        if not shown:
            continue
        section_title(group_name)
        for zone in shown:
            _zone_card(zone, cfg)

    _occurrence_section(zones, cfg)

    _zone_outlook(cfg, zones)

    # SEBS onset watch — experimental, deferred until the broad-basin field is rebuilt locally.
    # Only relevant when the Southeastern Bering is in view.
    if "sebs" in zone_set:
        with st.container(border=True):
            section_title("SEBS Onset Watch", note="experimental")
            callout(
                "An <b>experimental</b> early-warning signal for the <i>start</i> of a Southeastern "
                "Bering heatwave — a simple elevated-vs-normal flag, <b>not</b> a calibrated "
                "probability. It is still in development, so no reading is issued yet.",
                icon="🧪", tint=AMBER)

    footer(
        "Source: our ongoing marine-heatwave forecasting research "
        "(<a href='/forecast_development' style='text-decoration:underline'>working paper</a>). "
        "Short-term outlook of the monthly heatwave area for each zone, 1–3 months ahead.",
        guide_url="/marine_heatwave_guide")


def render() -> None:
    """Standalone all-zones forecast view (page header + full panel).

    Retained for direct use / testing; the board now renders the forecast region-scoped inside the
    Operational tab via :func:`render_forecast_panel`.
    """
    inject_css()
    cfg = load_forecast_config()
    page_header(
        "🔮", "Marine Heatwave Forecast", subtitle="Short-term outlook · Alaska ESR zones",
        region_label_text="Alaska ESR zones",
        caption="Short-term outlook (1–3 months ahead) of the share of each Alaska ESR (Ecosystem "
                "Status Report) zone under a marine heatwave.")
    all_zones = [z for _, zs in _GROUPS for z in zs if z in cfg["zones"]]
    render_forecast_panel(all_zones, cfg)
