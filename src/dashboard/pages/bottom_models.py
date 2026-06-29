"""Model Comparison (Bering Sea: EBS, NBS, Slope).

One region dropdown; the panels adapt to the region's product kind:
  * **Cold-pool regions** (EBS, NBS) — each model's cold pool over its ≤200 m shelf domain vs
    the observed survey (pattern), and the two models on identical footing (inter-model
    uncertainty). The threshold dropdown drives the area.
  * **Bottom-temperature regions** (Bering slope) — each model's mean bottom temperature over
    its full region domain across the whole period, with the sporadic survey means overlaid.

The model's *true* skill against the survey lives on the Cold Pool & Bottom Temperature page.
Build data with `mhw-build-coldpool-model` (and `--monthly` for the model-vs-model panel).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    GREEN,
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
    MODEL_SOURCES,
    THRESHOLDS,
    list_bottom_state_regions,
    load_kriged_area,
    load_model,
    load_observed,
    load_survey_replicate,
    region_label,
    threshold_short,
    zscore as _z,
)
from mhw.bottom.regions import get_region


def _kriged_area_panel(region: str, model_choices: list[str], base: pd.DataFrame,
                       thr_col: str, thr_short: str) -> None:
    """Apples-to-apples ABSOLUTE cold-pool area (B0).

    Each model's survey-replicated temps kriged through AFSC's exact pipeline (same 5 km grid,
    survey-area mask, ≤-threshold count) → an area directly comparable to the observed index in
    absolute km². Unlike the full-shelf view below, this differs from observed *only* in the
    temperatures, so we can show real km² (no z-scoring) and a true bias/RMSE.
    """
    kriged = {name: load_kriged_area(MODEL_SOURCES[name], region) for name in model_choices}
    kriged = {name: k for name, k in kriged.items() if k is not None}
    if not kriged:
        return  # not built for this region — silently fall back to the views below
    with st.container(border=True):
        section_title("Cold-pool area — apples-to-apples (kriged the way the survey is)")
        when_note("Each model sampled at <b>every survey haul</b> (nearest cell + time step), then "
                  "kriged onto AFSC's <b>5 km survey grid</b> and summed below the threshold — the "
                  "identical recipe used for the observed index.")
        st.caption(
            f"The defensible absolute-area comparison at the **{thr_short}** threshold: because the "
            "model temperatures go through the *same* kriging, grid, mask, and cell count as the "
            "survey, the two areas differ **only in the temperatures** — so we can compare real "
            "km² (not just the standardized pattern shown below), and the gap is a genuine bias."
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=base["year"], y=base[thr_col], mode="lines+markers",
                      name="Observed (survey, kriged)", line={"color": "black", "width": 2}))
        rows = []
        for name, k in kriged.items():
            color = MODEL_COLORS.get(name, "gray")
            k = k[(k["year"] >= base["year"].min()) & (k["year"] <= base["year"].max())]
            fig.add_trace(go.Scatter(x=k["year"], y=k[thr_col], mode="lines+markers",
                          name=f"{name} (kriged)", line={"color": color, "width": 2, "dash": "dash"}))
            cc = base[["year", thr_col]].merge(k[["year", thr_col]], on="year",
                                               suffixes=("_obs", "_mod")).dropna()
            if len(cc) >= 3:
                d = cc[f"{thr_col}_mod"] - cc[f"{thr_col}_obs"]
                rows.append({
                    "Model": name,
                    "Bias (km²)": f"{d.mean():+,.0f}",
                    "RMSE (km²)": f"{np.sqrt((d ** 2).mean()):,.0f}",
                    "r": round(float(np.corrcoef(cc[f"{thr_col}_obs"], cc[f"{thr_col}_mod"])[0, 1]), 2),
                    "Years": len(cc),
                })
        fig.update_yaxes(title_text=f"Cold-pool area {thr_short} (km²)", rangemode="tozero")
        fig.update_layout(height=420, template="plotly_white",
                          margin={"l": 80, "r": 20, "t": 30, "b": 40},
                          legend={"orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0, "xanchor": "left"})
        st.plotly_chart(fig, use_container_width=True)
        if rows:
            st.markdown("**Agreement with the survey, absolute area** "
                        "(bias = model − observed; a true difference, not a footprint artifact):")
            st.markdown(styled_table(pd.DataFrame(rows).set_index("Model")), unsafe_allow_html=True)
        if region == "nbs":
            callout("The NBS survey ran in only a handful of years (sporadic since 2010), so these "
                    "are <b>6–7 points</b> — read the <b>bias</b> (small for both models), not the "
                    "year-to-year correlation, which is noisy on so few years.", icon="⚠️", tint=AMBER)
        callout("This kriged area reproduces AFSC's published index when fed the observed haul "
                "temperatures (mean error ≈0.6 %, r≈1.0), so the modelled curve here is the model's "
                "cold pool measured on the survey's own terms.", icon="✓", tint=GREEN)


def _cold_pool_models(region: str, model_choices: list[str]) -> None:
    """Cold-pool-region view: apples-to-apples kriged area (B0) + full-shelf model vs observed (B1)
    + model-vs-model (B2)."""
    df = load_observed(region)
    if df is None:
        st.error(f"Cold-pool parquet not found for {region}. Run: `mhw-fetch-coldpool --region {region}`")
        return
    thr_label = st.sidebar.selectbox("Model cold-pool threshold", list(THRESHOLDS), index=0)
    thr_col = THRESHOLDS[thr_label]
    thr_short = threshold_short(thr_label)
    yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
    yr_lo, yr_hi = st.sidebar.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
    if thr_col != "area_lte2_km2":
        st.sidebar.caption("⚠️ At very cold thresholds (≤ 0 / −1 °C) many years have near-"
                           "zero area, so the standardized pattern and correlations get noisy.")

    loaded = {name: load_model(MODEL_SOURCES[name], region) for name in model_choices}
    for name, m in loaded.items():
        if m is None:
            st.warning(f"{name} modelled cold pool not built yet. Run: `mhw-build-coldpool-model`")
    loaded = {name: m for name, m in loaded.items() if m is not None}
    base = df[(df["year"] >= yr_lo) & (df["year"] <= yr_hi)]

    # ---- Panel B0: apples-to-apples kriged area (absolute km², the headline comparison) ----
    _kriged_area_panel(region, model_choices, base, thr_col, thr_short)

    # ---- Panel B1: full-shelf model view vs observed ----
    if loaded:
        with st.container(border=True):
            section_title(f"Full-shelf model view — {' & '.join(loaded)}")
            when_note("Model = each year's <b>early-July (~4 Jul)</b> survey-season snapshot over the "
                      "≤200 m shelf; observed = AFSC <b>summer survey</b>. One value per year.")
            st.caption(
                f"Each model's cold pool over its full ≤200 m shelf domain (its *own* view), shown "
                f"against the observed survey at the **{thr_short}** threshold. The model domain is "
                "larger than the survey footprint, so absolute area runs larger than the observed "
                "index — area is therefore **standardized** (pattern), bottom temperature in absolute "
                "°C. *For the absolute, apples-to-apples area, see the kriged panel above; for the "
                "model's true bias against the survey, see Cold Pool & Bottom Temperature.*"
            )
            cfig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12)
            cfig.add_trace(go.Scatter(x=base["year"], y=_z(base[thr_col]), mode="lines+markers",
                           name="Observed", line={"color": "black", "width": 2}), row=1, col=1)
            cfig.add_trace(go.Scatter(x=base["year"], y=base["mean_bottom_temp"], mode="lines+markers",
                           name="Observed", showlegend=False, line={"color": "black", "width": 2}), row=2, col=1)
            rows = []
            for name, mdf in loaded.items():
                color = MODEL_COLORS.get(name, "gray")
                m = mdf[(mdf["year"] >= yr_lo) & (mdf["year"] <= yr_hi)]
                cfig.add_trace(go.Scatter(x=m["year"], y=_z(m[thr_col]), mode="lines+markers",
                               name=name, line={"color": color, "width": 2, "dash": "dash"}), row=1, col=1)
                cfig.add_trace(go.Scatter(x=m["year"], y=m["mean_bottom_temp"], mode="lines+markers",
                               name=name, showlegend=False, line={"color": color, "width": 2, "dash": "dash"}), row=2, col=1)
                cc = base.merge(m, on="year", suffixes=("_obs", "_mod")).dropna(
                    subset=[f"{thr_col}_obs", f"{thr_col}_mod", "mean_bottom_temp_obs", "mean_bottom_temp_mod"])
                if len(cc) >= 3:
                    rows.append({
                        "Model": name,
                        f"r (area {thr_short})": round(float(np.corrcoef(cc[f"{thr_col}_obs"], cc[f"{thr_col}_mod"])[0, 1]), 2),
                        "r (bottom temp)": round(float(np.corrcoef(cc["mean_bottom_temp_obs"], cc["mean_bottom_temp_mod"])[0, 1]), 2),
                        "Years": len(cc),
                    })
            cfig.update_yaxes(title_text=f"Cold-pool area {thr_short} (z-score)", row=1, col=1)
            cfig.add_hline(y=2.0, line_dash="dot", line_color="gray", line_width=1, row=2, col=1)
            cfig.update_yaxes(title_text="Mean bottom temp (°C)", row=2, col=1)
            cfig.update_layout(height=600, template="plotly_white",
                               margin={"l": 70, "r": 20, "t": 64, "b": 40},
                               legend={"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "xanchor": "left"})
            st.plotly_chart(cfig, use_container_width=True)
            if rows:
                st.markdown("**Pattern agreement with the survey** (*r* = correlation):")
                st.markdown(styled_table(pd.DataFrame(rows).set_index("Model")),
                            unsafe_allow_html=True)

    # ---- Panel B2: model vs model, identical footing (≤200 m shelf, monthly) ----
    if len(model_choices) >= 2:
        monthly = {name: load_model(MODEL_SOURCES[name], region, monthly=True) for name in model_choices}
        monthly = {name: m for name, m in monthly.items() if m is not None}
        if len(monthly) >= 2:
            with st.container(border=True):
                section_title("Model vs model — identical footing (≤200 m shelf, monthly)")
                when_note("Both models on each year's <b>July monthly field</b>, ≤200 m shelf — "
                          "identical time basis, no observations.")
                st.caption(
                    f"The two models on **exactly** the same basis — same ≤200 m shelf domain, same "
                    f"July monthly-mean cadence, no observations — at the **{thr_short}** threshold. "
                    "This isolates genuine model-to-model differences: where they agree we can be "
                    "confident; where they diverge is the inter-model uncertainty."
                )
                bfig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12)
                series = {}
                for name, mdf in monthly.items():
                    color = MODEL_COLORS.get(name, "gray")
                    m = mdf[(mdf["year"] >= yr_lo) & (mdf["year"] <= yr_hi)]
                    series[name] = m.set_index("year")
                    bfig.add_trace(go.Scatter(x=m["year"], y=_z(m[thr_col]), mode="lines+markers",
                                   name=name, line={"color": color, "width": 2}), row=1, col=1)
                    bfig.add_trace(go.Scatter(x=m["year"], y=m["mean_bottom_temp"], mode="lines+markers",
                                   name=name, showlegend=False, line={"color": color, "width": 2}), row=2, col=1)
                bfig.update_yaxes(title_text=f"Cold-pool area {thr_short} (z-score)", row=1, col=1)
                bfig.update_yaxes(title_text="Mean bottom temp (°C)", row=2, col=1)
                bfig.update_layout(height=600, template="plotly_white",
                                   margin={"l": 70, "r": 20, "t": 64, "b": 40},
                                   legend={"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "xanchor": "left"})
                st.plotly_chart(bfig, use_container_width=True)
                names = list(series)
                if len(names) == 2:
                    a, b = series[names[0]], series[names[1]]
                    common = a.index.intersection(b.index)
                    if len(common) >= 3:
                        da, db = a.loc[common, "mean_bottom_temp"], b.loc[common, "mean_bottom_temp"]
                        r_area = float(np.corrcoef(a.loc[common, thr_col], b.loc[common, thr_col])[0, 1])
                        r_bt = float(np.corrcoef(da, db)[0, 1])
                        mean_diff = float((db - da).mean())
                        kpi_grid([
                            kpi_card(f"Inter-model r — area {thr_short}", f"{r_area:.2f}", BLUE),
                            kpi_card("Inter-model r — bottom temp", f"{r_bt:.2f}", BLUE),
                            kpi_card(f"Mean Δ ({names[1]} − {names[0]})", f"{mean_diff:+.2f} °C", AMBER),
                        ], cols=3)
                        st.caption("Both models on identical ≤200 m shelf + July-monthly footing.")
    elif len(model_choices) == 1:
        st.info("Select both models to see the model-vs-model comparison.")


def _bottom_temp_models(region: str, model_choices: list[str]) -> None:
    """Bottom-temperature-region view: full model-domain mean-BT record + survey points."""
    full = {name: load_model(MODEL_SOURCES[name], region) for name in model_choices}
    full = {n: m for n, m in full.items() if m is not None}
    with st.container(border=True):
        section_title("Model bottom-temperature record — full region domain")
        when_note("Each year's modelled bottom for <b>early July (~4 Jul)</b>, the survey season, "
                  "over the ≤200 m shelf — a summer snapshot, not an annual mean.")
        if not full:
            st.warning(f"Model series not built for {region}. Run: "
                       f"`mhw-build-coldpool-model --source bering10k --region {region}` (and mom6_nep).")
            return
        st.caption(
            "Each model's mean bottom temperature over its full region domain (the depth-banded "
            "slope footprint), across the whole model period — a long, continuous record where the "
            "survey is sporadic. Survey-year observed means are overlaid as points for context. The "
            "model domain is **not strata-matched** to the survey, so absolute values can differ from "
            "the co-located comparison on Cold Pool & Bottom Temperature."
        )
        f2 = go.Figure()
        for name in model_choices:
            annual, _ = load_survey_replicate(MODEL_SOURCES[name], region)
            if annual is not None:
                f2.add_trace(go.Scatter(x=annual["year"], y=annual["obs_mean_bottom_temp"],
                              mode="markers", name="Observed (survey)",
                              marker={"color": "black", "size": 8, "symbol": "x"}))
                break
        for name, m in full.items():
            f2.add_trace(go.Scatter(x=m["year"], y=m["mean_bottom_temp"], mode="lines",
                          name=f"{name} (model domain)",
                          line={"color": MODEL_COLORS.get(name, "gray"), "width": 2}))
        f2.update_yaxes(title_text="Mean bottom temp (°C)")
        f2.update_layout(height=460, template="plotly_white",
                         margin={"l": 70, "r": 20, "t": 30, "b": 40},
                         legend={"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "xanchor": "left"})
        st.plotly_chart(f2, use_container_width=True)


def render(group: str = "bering") -> None:
    """Render the Model Comparison page (page config/fonts owned by the navigation shell)."""
    inject_css()
    st.sidebar.header("Controls")
    regions = list_bottom_state_regions(group)
    if not regions:
        st.title("Model Comparison")
        st.error("No bottom-state region built. Run: `mhw-fetch-coldpool --region ebs`")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="bs_mod_region")
    reg = get_region(region)
    is_cold_pool = reg.product_kind == "cold_pool"

    page_header("🌡️", "Model Comparison", region_label(region),
                f"{region_label(region)} ({region.upper()})",
                caption=("How the regional ocean models (Bering10K ROMS, CEFI MOM6 NEP) behave over "
                         "this region, and how they compare to each other. For each model's true "
                         "skill against the survey, see Cold Pool & Bottom Temperature."))

    model_choices = st.sidebar.multiselect(
        "Models to show", list(MODEL_SOURCES), default=list(MODEL_SOURCES),
        help="Pick one or both regional models.",
    )
    if not model_choices:
        st.info("Pick one or both models in the sidebar.")
        return

    if is_cold_pool:
        _cold_pool_models(region, model_choices)
    else:
        _bottom_temp_models(region, model_choices)

    footer("Models: Bering10K ROMS (NOAA PMEL / UW ACLIM) · CEFI MOM6 NEP (NOAA GFDL / PSL), "
           "compared to the observed cold-pool index (NOAA AFSC <code>afsc-gap-products/coldpool</code>, "
           "Zenodo 10.5281/zenodo.16915337). All lagged (recent-historical), not near-real-time.")
