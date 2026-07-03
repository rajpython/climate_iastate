"""Ocean Health — observed-first shelf conditions beyond bottom temperature (Bering).

Increment 1 surfaces **bottom salinity**: the AFSC bottom-trawl survey measures gear salinity
for EBS/NBS (the observed series), and the MOM6 NEP10k model is co-presented for comparison.
The layer is deliberately observed-led — a model series is shown only where an observed one
anchors it. Variables (and later regions) are chosen from the sidebar; the panels adapt.

Build data with:
  observed → `mhw-fetch-coldpool --region <id>`
  modelled → `mhw-build-ocean-health --variable salinity --source mom6_nep --region <id>`
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import (
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

_UNITS = {"salinity": "psu"}


def _with_year_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex to the full year span so missing survey years become NaN — the line then
    *breaks* at real gaps (with ``connectgaps=False``) instead of bridging them."""
    full = range(int(df["year"].min()), int(df["year"].max()) + 1)
    return df.set_index("year").reindex(full).rename_axis("year").reset_index()


def _skill(obs: pd.DataFrame, mod: pd.DataFrame) -> dict | None:
    """Bias / RMSE / r on overlapping years (model − observed). None if no overlap."""
    m = obs.merge(mod, on="year", suffixes=("_obs", "_mod"))
    if len(m) < 2:
        return None
    d = m["value_mod"] - m["value_obs"]
    return {
        "n": int(len(m)),
        "y0": int(m["year"].min()), "y1": int(m["year"].max()),
        "bias": float(d.mean()),
        "rmse": float(np.sqrt((d ** 2).mean())),
        "r": float(np.corrcoef(m["value_obs"], m["value_mod"])[0, 1]),
    }


def _observed_panel(variable: str, region: str, units: str, obs: pd.DataFrame) -> None:
    with st.container(border=True):
        section_title("Observed shelf conditions",
                      note="AFSC summer bottom-trawl survey (survey-mean, lagged)")
        when_note("Survey-mean of the trawl gear sensor over each summer's stations — one "
                  "value per survey year. Salinity sensors begin ~2008 (EBS) / 2010 (NBS), so "
                  "early survey years are absent.")
        latest = obs.iloc[-1]
        cards = [
            kpi_card(f"Latest ({int(latest['year'])})", f"{latest['value']:.2f} {units}",
                     BLUE, label_note=""),
            kpi_card("Mean (record)", f"{obs['value'].mean():.2f} {units}", BLUE),
            kpi_card("Range", f"{obs['value'].min():.2f} – {obs['value'].max():.2f}", SLATE),
            kpi_card("Survey years", f"{len(obs)}",
                     SLATE, sub=f"{int(obs['year'].min())}–{int(obs['year'].max())}"),
        ]
        kpi_grid(cards, cols=4)

        og = _with_year_gaps(obs)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=og["year"], y=og["value"], mode="lines+markers", name="Observed (survey)",
            line=dict(color="black", width=2), marker=dict(size=7),
            connectgaps=False,
            hovertemplate="%{x}: %{y:.2f} " + units + "<extra></extra>"))
        fig.update_layout(
            template="plotly_white", height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title=f"Bottom {variable} ({units})", xaxis_title="Survey year",
            font=dict(size=13), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)


def _model_panel(variable: str, region: str, units: str, obs: pd.DataFrame) -> None:
    models = {name: load_ocean_health_model(variable, sid, region)
              for name, sid in MODEL_SOURCES.items()}
    models = {name: df for name, df in models.items() if df is not None}
    if not models:
        return
    with st.container(border=True):
        section_title("Observed vs. model",
                      note="model co-presented where the survey anchors it")
        first = next(iter(models))
        st.caption(
            f"Modelled shelf-mean {variable} is the area-weighted mean over the same "
            f"depth-masked shelf footprint used for the cold-pool / bottom-temperature "
            f"products. First mention: {MODEL_FULL_NAMES.get(first, first)}. Salinity is a "
            f"low-variability field (record range ≈ "
            f"{obs['value'].max() - obs['value'].min():.2f} {units}), so the honest skill "
            f"lens is the mean **level** (bias), not tight year-to-year correlation.")

        fig = go.Figure()
        og = _with_year_gaps(obs)
        fig.add_trace(go.Scatter(
            x=og["year"], y=og["value"], mode="lines+markers", name="Observed (survey)",
            line=dict(color="black", width=2), marker=dict(size=7), connectgaps=False,
            hovertemplate="%{x}: %{y:.2f} " + units + "<extra></extra>"))
        skill_cards = []
        for name, mod in models.items():
            color = MODEL_COLORS.get(name, "darkorange")
            fig.add_trace(go.Scatter(
                x=mod["year"], y=mod["value"], mode="lines", name=name,
                line=dict(color=color, width=2, dash="solid"),
                hovertemplate="%{x}: %{y:.2f} " + units + f" ({name})<extra></extra>"))
            sk = _skill(obs, mod)
            if sk is not None:
                skill_cards.append(kpi_card(
                    f"{name} bias", f"{sk['bias']:+.2f} {units}", BLUE,
                    sub=f"RMSE {sk['rmse']:.2f} · r {sk['r']:.2f}",
                    label_note=f"n={sk['n']} ({sk['y0']}–{sk['y1']})"))
        fig.update_layout(
            template="plotly_white", height=380, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title=f"Bottom {variable} ({units})", xaxis_title="Year",
            font=dict(size=13), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)
        if skill_cards:
            kpi_grid(skill_cards, cols=len(skill_cards))
            sk = _skill(obs, next(iter(models.values())))
            if sk is not None:
                verdict = ("essentially unbiased" if abs(sk["bias"]) < 0.1
                           else ("slightly fresh" if sk["bias"] < 0 else "slightly salty"))
                callout(
                    f"Over {sk['n']} overlapping survey years the model tracks the observed "
                    f"mean bottom {variable} to within <b>{sk['bias']:+.2f} {units}</b> "
                    f"(RMSE {sk['rmse']:.2f}) — {verdict}. Interannual correlation is modest "
                    f"because the shelf-{variable} signal is small relative to survey noise.",
                    tint=BLUE)


def render(group: str = "bering") -> None:
    """Render the Ocean Health page (page config / fonts owned by the nav shell)."""
    inject_css()
    st.sidebar.header("Controls")
    var_label = st.sidebar.selectbox("Variable", list(OCEAN_HEALTH_VARS), index=0,
                                     key="oh_variable")
    variable = OCEAN_HEALTH_VARS[var_label]
    units = _UNITS.get(variable, "")

    regions = list_ocean_health_regions(variable, group)
    if not regions:
        st.title("Ocean Health")
        st.info(
            f"No observed **{var_label.lower()}** series is available in this region group yet. "
            "Bottom salinity is packaged only for the Eastern and Northern Bering shelf; run "
            "`mhw-fetch-coldpool --region sebs` to build it.")
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

    _observed_panel(variable, region, units, obs)
    _model_panel(variable, region, units, obs)

    footer(
        "Sources: NOAA AFSC bottom-trawl survey (observed gear salinity, PSS-78) · "
        "CEFI MOM6-COBALT-NEP10k v1.0 (modelled bottom salinity, <code>sob</code>). "
        "Annual, summer-survey, lagged — not near-real-time.")
