"""Ocean Health — observed-first shelf conditions beyond bottom temperature (Bering).

Surfaces AFSC-survey observed indicators, each co-presented with the model where the survey
anchors it. Variables (sidebar):
  * **Bottom salinity** — survey gear salinity (EBS/NBS, ~2008–) vs MOM6 `sob`.
  * **Bottom dissolved oxygen** — survey-CTD sea-floor O₂ (SBE 43, EBS/NBS, ~2021–) vs MOM6 `btm_o2`.
  * **Bottom pH** — survey-CTD sea-floor pH (~2021–; provisional, sensor drift) vs MOM6 (from `btm_htotal`).

The layer is observed-led: a model series is shown only where an observed one anchors it. Build:
  observed → `mhw-fetch-coldpool` (salinity) / `mhw-fetch-survey-ctd` (O₂, pH)
  modelled → `mhw-build-ocean-health --variable {salinity,oxygen,ph} --source mom6_nep --region <id>`
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    SLATE,
    callout,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
    section_title,
    when_note,
)
from dashboard.components.coldpool_data import (
    MODEL_COLORS,
    MODEL_FULL_NAMES,
    MODEL_SOURCES,
    OCEAN_HEALTH_VARS,
    list_ocean_health_regions,
    load_ocean_health_model,
    load_ocean_health_observed,
    region_label,
)

# Per-observed-product "When" line (temporal context + method).
_WHEN = {
    "coldpool": ("Survey-mean of the trawl gear salinity sensor over each summer's stations — "
                 "one value per survey year. Salinity sensors begin ~2008 (EBS) / 2010 (NBS), so "
                 "early survey years are absent."),
    "survey_ctd": ("Mean over each summer's survey-CTD casts (SBE 19plus V2 + SBE 43), sea-floor "
                   "value per station. The O₂ and pH sensors were added to the surveys ~2021, so "
                   "the record starts then and is still short."),
}
_SOURCES_LINE = {
    "salinity": ("NOAA AFSC bottom-trawl survey (observed gear salinity, PSS-78) · "
                 "CEFI MOM6-COBALT-NEP10k v1.0 (modelled <code>sob</code>)."),
    "oxygen": ("NOAA AFSC survey-CTD (SBE 43 dissolved oxygen, ml/l; gapctd / NCEI) · "
               "CEFI MOM6-COBALT-NEP10k v1.0 (modelled <code>btm_o2</code>, converted to ml/l)."),
    "ph": ("NOAA AFSC survey-CTD (sea-floor pH, total scale; gapctd / NCEI — provisional) · "
           "CEFI MOM6-COBALT-NEP10k v1.0 (modelled pH from <code>btm_htotal</code>)."),
}


def _meta(variable: str) -> dict:
    from mhw.bottom.oceanhealth import VARIABLES
    return VARIABLES[variable]


def _fmt(v: float, variable: str) -> str:
    """Value with unit suffix; pH has no unit."""
    m = _meta(variable)
    u = m["units"]
    return f"{v:.2f} {u}".strip() if u else f"{v:.2f}"


def _axis_title(variable: str) -> str:
    m = _meta(variable)
    return f"{m['label']} ({m['units']})" if m["units"] else m["label"]


def _with_year_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex to the full year span so missing survey years become NaN — the line then
    *breaks* at real gaps (with ``connectgaps=False``) instead of bridging them."""
    full = range(int(df["year"].min()), int(df["year"].max()) + 1)
    return df.set_index("year").reindex(full).rename_axis("year").reset_index()


def _skill(obs: pd.DataFrame, mod: pd.DataFrame) -> dict | None:
    """Bias / RMSE / r on overlapping years (model − observed). None if <2 overlapping years."""
    m = obs.merge(mod, on="year", suffixes=("_obs", "_mod"))
    if len(m) < 2:
        return None
    d = m["value_mod"] - m["value_obs"]
    return {
        "n": int(len(m)), "y0": int(m["year"].min()), "y1": int(m["year"].max()),
        "bias": float(d.mean()), "rmse": float(np.sqrt((d ** 2).mean())),
        "r": float(np.corrcoef(m["value_obs"], m["value_mod"])[0, 1]),
    }


def _observed_panel(variable: str, obs: pd.DataFrame) -> None:
    m = _meta(variable)
    units = m["units"]
    with st.container(border=True):
        section_title("Observed shelf conditions",
                      note="AFSC summer bottom-trawl survey (survey-mean, lagged)")
        when_note(_WHEN[m["obs_product"]])
        if m.get("provisional"):
            callout("Bottom <b>pH</b> from the trawl-mounted ISFET sensor carries a known "
                    "drift/quality caveat (AFSC flags it); values are plausibility-filtered and "
                    "shown as <b>provisional</b> context, not a calibrated index.",
                    icon="⚠️", tint=AMBER)
        latest = obs.iloc[-1]
        cards = [
            kpi_card(f"Latest ({int(latest['year'])})", _fmt(latest["value"], variable), BLUE),
            kpi_card("Mean (record)", _fmt(obs["value"].mean(), variable), BLUE),
            kpi_card("Range",
                     f"{obs['value'].min():.2f} – {obs['value'].max():.2f}" + (f" {units}" if units else ""),
                     SLATE),
            kpi_card("Survey years", f"{len(obs)}", SLATE,
                     sub=f"{int(obs['year'].min())}–{int(obs['year'].max())}"),
        ]
        kpi_grid(cards, cols=4)

        og = _with_year_gaps(obs)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=og["year"], y=og["value"], mode="lines+markers", name="Observed (survey)",
            line=dict(color="black", width=2), marker=dict(size=7), connectgaps=False,
            hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
        fig.update_layout(
            template="plotly_white", height=380, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title=_axis_title(variable), xaxis_title="Survey year",
            font=dict(size=13), legend=dict(orientation="h", y=1.12))
        fig.update_xaxes(dtick=1, tickformat="d")   # integer survey years (avoid 2023.5 ticks)
        st.plotly_chart(fig, use_container_width=True)


def _model_panel(variable: str, region: str, obs: pd.DataFrame) -> None:
    m = _meta(variable)
    units = m["units"]
    models = {name: load_ocean_health_model(variable, sid, region)
              for name, sid in MODEL_SOURCES.items()}
    models = {name: df for name, df in models.items() if df is not None}
    if not models:
        return
    with st.container(border=True):
        section_title("Observed vs. model", note="model co-presented where the survey anchors it")
        first = next(iter(models))
        st.caption(
            f"Modelled shelf-mean {m['label'].lower()} is the area-weighted mean over the same "
            f"depth-masked shelf footprint used for the cold-pool / bottom-temperature products. "
            f"First mention: {MODEL_FULL_NAMES.get(first, first)}. The observed record is short "
            f"(~{int(obs['year'].min())}–{int(obs['year'].max())}), so read this as a level/bias "
            f"check, not a long-run skill assessment.")

        fig = go.Figure()
        og = _with_year_gaps(obs)
        fig.add_trace(go.Scatter(
            x=og["year"], y=og["value"], mode="lines+markers", name="Observed (survey)",
            line=dict(color="black", width=2), marker=dict(size=7), connectgaps=False,
            hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
        skill_cards = []
        for name, mod in models.items():
            color = MODEL_COLORS.get(name, "darkorange")
            fig.add_trace(go.Scatter(
                x=mod["year"], y=mod["value"], mode="lines", name=name,
                line=dict(color=color, width=2),
                hovertemplate="%{x}: %{y:.2f} (" + name + ")<extra></extra>"))
            sk = _skill(obs, mod)
            if sk is not None:
                usuf = f" {units}" if units else ""
                # r is meaningless with only 2 overlapping years — show it only from 3 up.
                sub = f"RMSE {sk['rmse']:.2f}" + (f" · r {sk['r']:.2f}" if sk["n"] >= 3 else "")
                skill_cards.append(kpi_card(
                    f"{name} bias", f"{sk['bias']:+.2f}{usuf}", BLUE, sub=sub,
                    label_note=f"n={sk['n']} ({sk['y0']}–{sk['y1']})"))
        fig.update_layout(
            template="plotly_white", height=380, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title=_axis_title(variable), xaxis_title="Year",
            font=dict(size=13), legend=dict(orientation="h", y=1.12))
        fig.update_xaxes(dtick=1, tickformat="d")
        st.plotly_chart(fig, use_container_width=True)
        if skill_cards:
            kpi_grid(skill_cards, cols=len(skill_cards))
            sk = _skill(obs, next(iter(models.values())))
            if sk is not None:
                usuf = f" {units}" if units else ""
                callout(
                    f"Over {sk['n']} overlapping survey years the model tracks the observed mean "
                    f"bottom {m['label'].lower()} to within <b>{sk['bias']:+.2f}{usuf}</b> "
                    f"(RMSE {sk['rmse']:.2f}). With so few years, treat this as a level check "
                    f"rather than interannual skill.", tint=BLUE)


def render(group: str = "bering") -> None:
    """Render the Ocean Health page (page config / fonts owned by the nav shell)."""
    inject_css()
    st.sidebar.header("Controls")
    var_label = st.sidebar.selectbox("Variable", list(OCEAN_HEALTH_VARS), index=0, key="oh_variable")
    variable = OCEAN_HEALTH_VARS[var_label]

    regions = list_ocean_health_regions(variable, group)
    if not regions:
        st.title("Ocean Health")
        st.info(
            f"No observed **{var_label.lower()}** series is available in this region group yet. "
            "These indicators are EBS/NBS-only; build them with "
            "`mhw-fetch-coldpool` (salinity) or `mhw-fetch-survey-ctd` (oxygen / pH).")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=region_label, key="oh_region")

    page_header("💧", "Ocean Health", region_label(region),
                f"{region_label(region)} ({region.upper()})",
                caption=(f"Observed-first shelf conditions beyond temperature — {var_label.lower()} "
                         "from the AFSC survey, with the model co-presented for comparison."))

    obs = load_ocean_health_observed(variable, region)
    if obs is None or obs.empty:
        st.warning(f"Observed {var_label.lower()} not available for {region_label(region)}.")
        return

    _observed_panel(variable, obs)
    _model_panel(variable, region, obs)

    footer(f"Sources: {_SOURCES_LINE[variable]} Annual, summer-survey, lagged — not near-real-time.")
