"""Ocean Conditions — observed-first shelf water properties beyond bottom temperature.

Surfaces AFSC-survey observed indicators, each co-presented with the model where the survey
anchors it. Variables (sidebar):
  * **Bottom salinity** — gear salinity (EBS/NBS, ~2008–) or survey-CTD salinity (GOA/AI) vs MOM6 `sob`.
  * **Bottom dissolved oxygen** — survey-CTD sea-floor O₂ (SBE 43, EBS/NBS, ~2021–) vs MOM6 `btm_o2`.
  * **Bottom pH** — survey-CTD sea-floor pH (~2021–; provisional, sensor drift) vs MOM6 (from `btm_htotal`).

**Sparse-data rule:** with fewer than three observed survey years, a time-series line would imply
a trend we did not observe — so the observed series and the model comparison are shown as
**tables** (no connecting line, no continuous model curve).

Build:
  observed → `mhw-fetch-coldpool` (salinity, EBS/NBS) / `mhw-fetch-survey-ctd` (salinity GOA/AI; O₂/pH)
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
    styled_table,
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
    ocean_health_observed_product,
    region_label,
)

# Below this many observed survey years, use a table instead of a time-series chart.
_MIN_FOR_CHART = 3


def _when_text(variable: str, product: str | None) -> str:
    """Temporal-context line, aware of which observed product supplied the series."""
    if product == "coldpool":
        return ("Survey-mean of the trawl gear salinity sensor over each summer's stations — one "
                "value per survey year. Salinity sensors begin ~2008 (EBS) / 2010 (NBS).")
    if variable == "salinity":   # survey-CTD salinity (GOA/AI)
        return ("Mean over each summer's survey-CTD casts (SBE 19plus V2), sea-floor salinity per "
                "station. GOA/AI have no packaged salinity index, so this comes from the CTD "
                "product (~2021–, biennial surveys) and is short.")
    return ("Mean over each summer's survey-CTD casts (SBE 19plus V2 + SBE 43), sea-floor value "
            "per station. The O₂ and pH sensors were added to the surveys ~2021, so the record "
            "starts then and is still short.")


_SOURCES_LINE = {
    "salinity": ("NOAA AFSC bottom-trawl survey (observed bottom salinity, PSS-78 — cold-pool "
                 "index for EBS/NBS, survey-CTD for GOA/AI) · CEFI MOM6-COBALT-NEP10k v1.0 "
                 "(modelled <code>sob</code>)."),
    "oxygen": ("NOAA AFSC survey-CTD (SBE 43 dissolved oxygen, ml/l; gapctd / NCEI) · "
               "CEFI MOM6-COBALT-NEP10k v1.0 (modelled <code>btm_o2</code>, converted to ml/l)."),
    "ph": ("NOAA AFSC survey-CTD (sea-floor pH, total scale; gapctd / NCEI — provisional) · "
           "CEFI MOM6-COBALT-NEP10k v1.0 (modelled pH from <code>btm_htotal</code>)."),
}


def _meta(variable: str) -> dict:
    from mhw.bottom.oceanhealth import VARIABLES
    return VARIABLES[variable]


def _units(variable: str) -> str:
    return _meta(variable)["units"]


def _fmt(v: float, variable: str) -> str:
    u = _units(variable)
    return f"{v:.2f} {u}".strip() if u else f"{v:.2f}"


def _axis_title(variable: str) -> str:
    m = _meta(variable)
    return f"{m['label']} ({m['units']})" if m["units"] else m["label"]


def _with_year_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex to the full year span so missing survey years become NaN — the line breaks at real
    gaps (with ``connectgaps=False``) rather than bridging them."""
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


# ---------------------------------------------------------------------------
# Observed panel
# ---------------------------------------------------------------------------

def _observed_panel(variable: str, region: str, obs: pd.DataFrame) -> None:
    m = _meta(variable)
    units = m["units"]
    with st.container(border=True):
        section_title("Observed shelf conditions",
                      note="AFSC summer bottom-trawl survey (survey-mean, lagged)")
        when_note(_when_text(variable, ocean_health_observed_product(variable, region)))
        if m.get("provisional"):
            callout("Bottom <b>pH</b> from the trawl-mounted ISFET sensor carries a known "
                    "drift/quality caveat (AFSC flags it); values are plausibility-filtered and "
                    "shown as <b>provisional</b> context, not a calibrated index.",
                    icon="⚠️", tint=AMBER)
        lo, hi = float(obs["value"].min()), float(obs["value"].max())
        rng = (f"{lo:.2f}" if lo == hi else f"{lo:.2f} – {hi:.2f}") + (f" {units}" if units else "")
        latest = obs.iloc[-1]
        kpi_grid([
            kpi_card(f"Latest ({int(latest['year'])})", _fmt(latest["value"], variable), BLUE),
            kpi_card("Mean (record)", _fmt(obs["value"].mean(), variable), BLUE),
            kpi_card("Range", rng, SLATE),
            kpi_card("Survey years", f"{len(obs)}", SLATE,
                     sub=f"{int(obs['year'].min())}–{int(obs['year'].max())}"),
        ], cols=4)

        if len(obs) >= _MIN_FOR_CHART:
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
            fig.update_xaxes(dtick=1, tickformat="d")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Too few survey years for a time series — shown as a table.")
            disp = pd.DataFrame({"Year": [str(int(y)) for y in obs["year"]]})
            disp[_axis_title(variable)] = [round(float(v), 2) for v in obs["value"]]
            if "n" in obs.columns:
                disp["Stations"] = [int(x) if pd.notna(x) else 0 for x in obs["n"]]
            st.markdown(styled_table(disp.set_index("Year")), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Model comparison panel
# ---------------------------------------------------------------------------

def _model_intro(variable: str, obs: pd.DataFrame, first_model: str) -> None:
    span = f"~{int(obs['year'].min())}–{int(obs['year'].max())}"
    if len(obs) < _MIN_FOR_CHART:
        tail = (f"The observed record is only {len(obs)} survey year(s) ({span}), so read this as "
                f"a level/bias check, not a skill assessment.")
    else:
        tail = (f"Compared over the {len(obs)} survey years with observations ({span}); with a "
                f"small interannual range, the mean level/bias is more telling than year-to-year "
                f"tracking.")
    st.caption(
        f"Modelled shelf-mean {_meta(variable)['label'].lower()} is the area-weighted mean over "
        f"the same depth-masked shelf footprint used for the cold-pool / bottom-temperature "
        f"products. First mention: {MODEL_FULL_NAMES.get(first_model, first_model)}. {tail}")


def _model_panel(variable: str, region: str, obs: pd.DataFrame) -> None:
    units = _units(variable)
    models = {name: load_ocean_health_model(variable, sid, region)
              for name, sid in MODEL_SOURCES.items()}
    models = {name: df for name, df in models.items() if df is not None}
    if not models:
        return
    with st.container(border=True):
        section_title("Observed vs. model", note="model co-presented where the survey anchors it")
        _model_intro(variable, obs, next(iter(models)))

        if len(obs) >= _MIN_FOR_CHART:
            _model_chart(variable, obs, models, units)
        else:
            _model_table(variable, obs, models, units)


def _model_chart(variable: str, obs: pd.DataFrame, models: dict, units: str) -> None:
    fig = go.Figure()
    og = _with_year_gaps(obs)
    fig.add_trace(go.Scatter(
        x=og["year"], y=og["value"], mode="lines+markers", name="Observed (survey)",
        line=dict(color="black", width=2), marker=dict(size=7), connectgaps=False,
        hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    skill_cards = []
    for name, mod in models.items():
        fig.add_trace(go.Scatter(
            x=mod["year"], y=mod["value"], mode="lines", name=name,
            line=dict(color=MODEL_COLORS.get(name, "darkorange"), width=2),
            hovertemplate="%{x}: %{y:.2f} (" + name + ")<extra></extra>"))
        sk = _skill(obs, mod)
        if sk is not None:
            usuf = f" {units}" if units else ""
            sub = f"RMSE {sk['rmse']:.2f}" + (f" · r {sk['r']:.2f}" if sk["n"] >= 3 else "")
            skill_cards.append(kpi_card(f"{name} bias", f"{sk['bias']:+.2f}{usuf}", BLUE, sub=sub,
                                        label_note=f"n={sk['n']} ({sk['y0']}–{sk['y1']})"))
    fig.update_layout(
        template="plotly_white", height=380, margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title=_axis_title(variable), xaxis_title="Year",
        font=dict(size=13), legend=dict(orientation="h", y=1.12))
    fig.update_xaxes(dtick=1, tickformat="d")
    st.plotly_chart(fig, use_container_width=True)
    if skill_cards:
        kpi_grid(skill_cards, cols=len(skill_cards))


def _model_table(variable: str, obs: pd.DataFrame, models: dict, units: str) -> None:
    """Sparse case: a per-year observed-vs-model table (no continuous model line drawn against
    one or two observations)."""
    rows = []
    for _, r in obs.iterrows():
        y = int(r["year"])
        row = {"Year": str(y), "Observed": round(float(r["value"]), 2)}
        for name, mod in models.items():
            mv = mod.loc[mod["year"] == y, "value"]
            val = round(float(mv.iloc[0]), 2) if len(mv) else np.nan
            row[name] = val
            row[f"Δ vs {name}"] = round(val - float(r["value"]), 2) if not np.isnan(val) else np.nan
        rows.append(row)
    st.markdown(styled_table(pd.DataFrame(rows).set_index("Year")), unsafe_allow_html=True)
    usuf = f" {units}" if units else ""
    callout(
        f"MOM6-COBALT-NEP is a continuous physical simulation (a value every month, everywhere), "
        f"compared here <b>only at the survey years</b> — one or two observations cannot validate "
        f"a time series, only check the level. Δ is model − observed{(' in ' + units) if units else ''}.",
        tint=SLATE)
    sk = _skill(obs, next(iter(models.values())))
    if sk is not None:
        kpi_grid([kpi_card(f"{next(iter(models))} mean bias", f"{sk['bias']:+.2f}{usuf}", BLUE,
                           label_note=f"n={sk['n']} ({sk['y0']}–{sk['y1']})")], cols=1)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render(group: str = "bering") -> None:
    """Render the Ocean Conditions page (page config / fonts owned by the nav shell)."""
    inject_css()
    st.sidebar.header("Controls")
    var_label = st.sidebar.selectbox("Variable", list(OCEAN_HEALTH_VARS), index=0, key="oh_variable")
    variable = OCEAN_HEALTH_VARS[var_label]

    regions = list_ocean_health_regions(variable, group)
    if not regions:
        st.title("Ocean Conditions")
        st.info(
            f"No observed **{var_label.lower()}** series is available in this region group yet. "
            "These indicators are survey-derived; build them with "
            "`mhw-fetch-coldpool` (salinity, EBS/NBS) or `mhw-fetch-survey-ctd` (salinity GOA/AI; "
            "O₂ / pH, EBS/NBS).")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=region_label, key="oh_region")

    page_header("💧", "Ocean Conditions", region_label(region),
                f"{region_label(region)} ({region.upper()})",
                caption=(f"Observed-first shelf conditions beyond temperature — {var_label.lower()} "
                         "from the AFSC survey, with the model co-presented for comparison."))

    obs = load_ocean_health_observed(variable, region)
    if obs is None or obs.empty:
        st.warning(f"Observed {var_label.lower()} not available for {region_label(region)}.")
        return

    _observed_panel(variable, region, obs)
    _model_panel(variable, region, obs)

    footer(f"Sources: {_SOURCES_LINE[variable]} Annual, summer-survey, lagged — not near-real-time.")
