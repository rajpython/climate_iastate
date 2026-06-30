"""Model Comparison (Bering Sea: EBS, NBS, Slope).

One region dropdown; the panels adapt to the region's product kind:
  * **Cold-pool regions** (SEBS, NBS) — two panels, both in absolute km²: each model's cold-pool
    area kriged exactly like the survey (apples-to-apples, with bias/RMSE), and the two models on
    identical footing (inter-model uncertainty). The threshold dropdown drives the area.
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
    MODEL_FULL_NAMES,
    MODEL_SOURCES,
    THRESHOLDS,
    list_bottom_state_regions,
    load_kriged_area,
    load_model,
    load_observed,
    load_survey_replicate,
    region_label,
    threshold_short,
)
from mhw.bottom.regions import get_region

# Model-validation panels live with the observed page module but render here now (Option 1: the
# Bottom Temperature page is observed-only; all model comparison lives on this page).
from dashboard.pages.bottom_observed import (  # noqa: E402
    _bias_interpretation,
    _obs_vs_model_scatter,
    _survey_replicate_panel,
)


def _snapshot_table(region: str, model_choices: list[str], base: pd.DataFrame | None = None,
                    thr_col: str | None = None, thr_short: str | None = None) -> None:
    """Compact per-year snapshot — columns = Observed + each selected model, rows = mean bottom
    temperature (and cold-pool area for cold-pool regions). The year is chosen above the table; the
    models in the sidebar. Cold-pool values come from the identical kriging (observed = AFSC index);
    bottom-temp values from the survey-replicated co-location. Bering10K applies in the Bering only;
    the Gulf/Aleutians are MOM6 only (the sidebar already filters to the region's valid models)."""
    is_cp = thr_col is not None
    models: dict[str, pd.DataFrame] = {}
    obs_bt = obs_area = None
    if is_cp:
        obs_bt = base.set_index("year")["mean_bottom_temp"] if "mean_bottom_temp" in base.columns else None
        obs_area = base.set_index("year")[thr_col]
        for name in model_choices:
            k = load_kriged_area(MODEL_SOURCES[name], region)
            if k is not None and "mean_bottom_temp" in k.columns:
                models[name] = k.set_index("year")
        years = sorted(int(y) for y in obs_area.dropna().index)
    else:
        years_set: set[int] = set()
        for name in model_choices:
            ann, _ = load_survey_replicate(MODEL_SOURCES[name], region)
            if ann is not None and "model_mean_bottom_temp" in ann.columns:
                models[name] = ann.set_index("year")
                if obs_bt is None:
                    obs_bt = ann.set_index("year")["obs_mean_bottom_temp"]
                years_set |= {int(y) for y in ann["year"]}
        years = sorted(years_set)
    if not models or not years:
        return

    with st.container(border=True):
        section_title("Snapshot — observed vs models, by year")
        when_note("A single survey year, side by side — pick the year below; pick the model(s) in the "
                  "sidebar. Bering10K applies in the Bering only; the Gulf/Aleutians are MOM6 only.")
        year = st.selectbox("Year", years, index=len(years) - 1, key=f"snap_year_{region}")

        def at(s, col=None):
            try:
                v = s.loc[year] if col is None else s.loc[year, col]
                return float(v) if pd.notna(v) else None
            except (KeyError, TypeError, ValueError):
                return None

        def ft(v):
            return f"{v:.2f}" if v is not None else "—"

        def fa(v):
            return f"{v:,.0f}" if v is not None else "—"

        cols = ["Observed"] + list(models)
        bt_row = {"Observed": ft(at(obs_bt) if obs_bt is not None else None)}
        mcol = "mean_bottom_temp" if is_cp else "model_mean_bottom_temp"
        for name, m in models.items():
            bt_row[name] = ft(at(m, mcol))
        data = {"Mean bottom temperature (°C)": bt_row}
        if is_cp:
            area_row = {"Observed": fa(at(obs_area))}
            for name, m in models.items():
                area_row[name] = fa(at(m, thr_col))
            data[f"Cold-pool area {thr_short} (km²)"] = area_row
        st.markdown(styled_table(pd.DataFrame(data).T[cols]), unsafe_allow_html=True)
        st.caption("Same apples-to-apples basis as the panels below (kriged for cold-pool regions; "
                   "survey-co-located for bottom-temperature regions). “—” = not surveyed/built that year.")


def _kriged_temp_panel(region: str, model_choices: list[str], base: pd.DataFrame) -> None:
    """Apples-to-apples mean bottom TEMPERATURE — companion to the kriged area, from the same kriging.

    Each model's survey-replicated temps are kriged onto AFSC's 5 km grid and averaged over the
    survey-area mask; the observed reference is AFSC's published mean (which is that same kriged-mean,
    verified to ≈0.003 °C). So model and survey go through the identical pipeline — the gap is a true
    bias in °C, not a domain artifact.
    """
    kriged = {name: load_kriged_area(MODEL_SOURCES[name], region) for name in model_choices}
    kriged = {n: k for n, k in kriged.items()
              if k is not None and "mean_bottom_temp" in k.columns}
    if not kriged or "mean_bottom_temp" not in base:
        return
    with st.container(border=True):
        section_title("Mean bottom temperature — apples-to-apples (kriged the way the survey is)")
        when_note("Each model sampled at <b>every survey haul</b>, kriged onto AFSC's <b>5 km survey "
                  "grid</b>, then averaged over the survey area — the same recipe (and the same kriging) "
                  "behind the cold-pool area below and behind the observed mean bottom temperature.")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=base["year"], y=base["mean_bottom_temp"], mode="lines+markers",
                      name="Observed (survey, kriged)", line={"color": "black", "width": 2}))
        rows = []
        for name, k in kriged.items():
            color = MODEL_COLORS.get(name, "gray")
            k = k[(k["year"] >= base["year"].min()) & (k["year"] <= base["year"].max())]
            fig.add_trace(go.Scatter(x=k["year"], y=k["mean_bottom_temp"], mode="lines+markers",
                          name=f"{name} (kriged)", line={"color": color, "width": 2, "dash": "dash"}))
            cc = base[["year", "mean_bottom_temp"]].merge(
                k[["year", "mean_bottom_temp"]], on="year", suffixes=("_obs", "_mod")).dropna()
            if len(cc) >= 3:
                d = cc["mean_bottom_temp_mod"] - cc["mean_bottom_temp_obs"]
                rows.append({
                    "Model": name,
                    "Bias (°C)": f"{d.mean():+.2f}",
                    "RMSE (°C)": f"{np.sqrt((d ** 2).mean()):.2f}",
                    "r": round(float(np.corrcoef(cc["mean_bottom_temp_obs"], cc["mean_bottom_temp_mod"])[0, 1]), 2),
                    "Years": len(cc),
                })
        fig.add_hline(y=2.0, line_dash="dot", line_color="gray", line_width=1,
                      annotation_text="2 °C", annotation_font_size=9)
        fig.update_yaxes(title_text="Mean bottom temp (°C)")
        fig.update_layout(height=420, template="plotly_white",
                          margin={"l": 80, "r": 20, "t": 30, "b": 40},
                          legend={"orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0, "xanchor": "left"})
        st.plotly_chart(fig, use_container_width=True)
        if rows:
            st.markdown("**Agreement with the survey, mean bottom temperature** "
                        "(bias = model − observed, °C):")
            st.markdown(styled_table(pd.DataFrame(rows).set_index("Model")), unsafe_allow_html=True)


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
            callout(
                "<b>How to read this:</b> &nbsp;<b>Bias</b> is the average signed gap "
                "(model − observed) in km² — <b>+</b> means the model's cold pool runs <i>larger</i> "
                "than the survey's, <b>−</b> means smaller; it's the systematic offset. &nbsp;"
                "<b>RMSE</b> is the typical size of the year-to-year error in km² (always ≥ |bias|): "
                "it folds in both the bias <i>and</i> the scatter, so a small bias with a large RMSE "
                "means the model is right <i>on average</i> but off in individual years. &nbsp;"
                "<b>r</b> is the year-to-year pattern correlation — whether the model rises and falls "
                "<i>in step</i> with the survey (1 = perfect tracking), independent of any offset.",
                icon="📖", tint=BLUE)
        if region == "nbs":
            callout("The NBS survey ran in only a handful of years (sporadic since 2010), so these "
                    "are <b>6–7 points</b> — read the <b>bias</b> (small for both models), not the "
                    "year-to-year correlation, which is noisy on so few years.", icon="⚠️", tint=AMBER)
        callout("This kriged area reproduces AFSC's published index when fed the observed haul "
                "temperatures (mean error ≈0.6 %, r≈1.0), so the modelled curve here is the model's "
                "cold pool measured on the survey's own terms.", icon="✓", tint=GREEN)


def _cold_pool_models(region: str, model_choices: list[str]) -> None:
    """Cold-pool-region view: three panels — apples-to-apples kriged mean bottom *temperature* and
    kriged cold-pool *area* vs the survey (both absolute, from one kriging, with bias/RMSE), then
    model-vs-model on identical footing (absolute) with the survey overlaid for reference."""
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

    base = df[(df["year"] >= yr_lo) & (df["year"] <= yr_hi)]

    # ---- Snapshot table (observed vs models, one chosen year) ----
    _snapshot_table(region, model_choices, base, thr_col, thr_short)
    # ---- Panel 1: apples-to-apples kriged mean bottom TEMPERATURE ----
    _kriged_temp_panel(region, model_choices, base)
    # ---- Panel 2: apples-to-apples kriged cold-pool AREA (same kriging) ----
    # (The model's full-shelf view is deliberately NOT shown: the model domain is larger than the
    # survey footprint, so its absolute area/temperature would be a footprint artifact. These two
    # kriged panels are the honest absolute comparisons.)
    _kriged_area_panel(region, model_choices, base, thr_col, thr_short)

    # ---- Panel 3: model vs model, identical footing (≤200 m shelf, monthly) ----
    if len(model_choices) >= 2:
        monthly = {name: load_model(MODEL_SOURCES[name], region, monthly=True) for name in model_choices}
        monthly = {name: m for name, m in monthly.items() if m is not None}
        if len(monthly) >= 2:
            with st.container(border=True):
                section_title("Model vs model — identical footing (≤200 m shelf, monthly)")
                when_note("Both models on each year's <b>July monthly field</b>, ≤200 m shelf — "
                          "identical time basis. The survey is overlaid only as a light reference.")
                st.caption(
                    f"The two models on **exactly** the same basis — same ≤200 m shelf domain, same "
                    f"July monthly-mean cadence — at the **{thr_short}** threshold. This isolates "
                    "genuine model-to-model differences: where they agree we can be confident; where "
                    "they diverge is the inter-model uncertainty. The **observed survey** is drawn as "
                    "a light dashed line for context only — it sits on the smaller survey footprint, "
                    "not the model shelf, so don't read the model–observed gap here (that's the kriged "
                    "panels above)."
                )
                bfig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12)
                bfig.add_trace(go.Scatter(x=base["year"], y=base[thr_col], mode="lines",
                               name="Observed (survey footprint)", opacity=0.5,
                               line={"color": "gray", "width": 1.5, "dash": "dot"}), row=1, col=1)
                bfig.add_trace(go.Scatter(x=base["year"], y=base["mean_bottom_temp"], mode="lines",
                               name="Observed", showlegend=False, opacity=0.5,
                               line={"color": "gray", "width": 1.5, "dash": "dot"}), row=2, col=1)
                series = {}
                for name, mdf in monthly.items():
                    color = MODEL_COLORS.get(name, "gray")
                    m = mdf[(mdf["year"] >= yr_lo) & (mdf["year"] <= yr_hi)]
                    series[name] = m.set_index("year")
                    bfig.add_trace(go.Scatter(x=m["year"], y=m[thr_col], mode="lines+markers",
                                   name=name, line={"color": color, "width": 2}), row=1, col=1)
                    bfig.add_trace(go.Scatter(x=m["year"], y=m["mean_bottom_temp"], mode="lines+markers",
                                   name=name, showlegend=False, line={"color": color, "width": 2}), row=2, col=1)
                bfig.update_yaxes(title_text=f"Cold-pool area {thr_short} (km²)", rangemode="tozero", row=1, col=1)
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
    """Bottom-temperature-region view: per-year snapshot + full model-domain mean-BT record +
    survey-replicated validation."""
    _snapshot_table(region, model_choices)   # observed vs model mean bottom temp, one chosen year
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

    # Survey-replicated validation (model co-located at the survey hauls) — the model's true skill,
    # moved here from the observed page so all model comparison lives on this page.
    if _survey_replicate_panel(region, model_choices):
        _obs_vs_model_scatter(region, model_choices)
        if load_observed(region) is not None:
            _bias_interpretation(region, model_choices)
    else:
        st.warning(f"Survey replicate not built for {region}. Run: "
                   f"`mhw-build-survey-replicate --source mom6_nep --region {region}`.")


def _model_coverage(region: str, labels: list[str], is_cold_pool: bool) -> str:
    """A 'Bering10K ROMS (1982–2024) · MOM6 NEP10k (1993–2025)' string, read from the *same* data
    the snapshot/panels use — so the stated periods match the table's blank ('—') years and nobody
    is surprised that, e.g., 1982 has no MOM6."""
    parts = []
    for lbl in labels:
        src = MODEL_SOURCES[lbl]
        if is_cold_pool:
            d = load_kriged_area(src, region)
            yr = d["year"] if d is not None and "year" in d.columns else None
        else:
            ann, _ = load_survey_replicate(src, region)
            yr = ann["year"] if ann is not None and "year" in ann.columns else None
        if yr is not None and len(yr):
            parts.append(f"{lbl} ({int(yr.min())}–{int(yr.max())})")
    return " · ".join(parts)


def render(group: str = "bering") -> None:
    """Render the Model Comparison page (page config/fonts owned by the navigation shell)."""
    inject_css()
    st.sidebar.header("Controls")
    regions = list_bottom_state_regions(group)
    if not regions:
        st.title("Model Comparison")
        st.error("No bottom-state region built. Run: `mhw-fetch-coldpool --region sebs`")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="bs_mod_region")
    reg = get_region(region)
    is_cold_pool = reg.product_kind == "cold_pool"
    valid_labels = [lbl for lbl, sid in MODEL_SOURCES.items() if sid in reg.valid_sources]

    coverage = _model_coverage(region, valid_labels, is_cold_pool)
    full_names = " and ".join(MODEL_FULL_NAMES.get(lbl, lbl) for lbl in valid_labels)
    cap = (f"How the regional ocean model{'s' if len(valid_labels) > 1 else ''} — {full_names} — "
           "behave over this region")
    if len(valid_labels) > 1:
        cap += " and how they compare to each other"
    if coverage:
        cap += f". Coverage: {coverage}"
    cap += (". Models extend only over their own hindcast period, so a year outside it shows “—” in "
            "the snapshot. For each model's true skill against the survey, see Cold Pool & Bottom "
            "Temperature.")
    page_header("🌡️", "Model Comparison", region_label(region),
                f"{region_label(region)} ({region.upper()})", caption=cap)

    model_choices = st.sidebar.multiselect(
        "Models to show", valid_labels, default=valid_labels,
        help="Pick the regional model(s) valid for this region.",
    )
    if not model_choices:
        st.info("Pick at least one model in the sidebar.")
        return

    if is_cold_pool:
        _cold_pool_models(region, model_choices)
    else:
        _bottom_temp_models(region, model_choices)

    footer("Models: <b>Bering10K ROMS</b> (NOAA PMEL / UW — ACLIM hindcast "
           "<code>B10K-K20_Level2_CORECFS</code>) · <b>CEFI MOM6-COBALT-NEP10k v1.0</b> (NOAA GFDL; "
           "Drenkard et&nbsp;al., GMD 18:5245, 2025) — compared to the observed cold-pool index (NOAA AFSC "
           "<code>afsc-gap-products/coldpool</code>, Zenodo 10.5281/zenodo.16915337). All lagged "
           "(recent-historical), not near-real-time.")
