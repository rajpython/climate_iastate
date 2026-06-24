"""Cold Pool & Bottom Temperature (Bering Sea: EBS, NBS, Slope) — observed survey indicators.

One region dropdown spans the Bering bottom-state areas; the panels adapt to the region's
product kind:
  * **Cold-pool regions** (EBS, NBS) — the observed **cold-pool index** (AFSC bottom-trawl
    survey area below the chosen threshold + mean bottom temperature) + survey-replicated
    model validation.
  * **Bottom-temperature regions** (Bering slope) — no cold pool: observed bottom temperature
    vs the models, co-located at the survey hauls.

Build data with `mhw-fetch-coldpool` / `mhw-build-survey-replicate`.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from dashboard.components.bottom_ui import (
    BLUE,
    GREEN,
    RED,
    callout,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
    section_title,
)
from dashboard.components.coldpool_data import (
    MODEL_COLORS,
    MODEL_SOURCES,
    THRESHOLDS,
    list_bottom_state_regions,
    load_observed,
    load_survey_replicate,
    ordinal,
    region_label,
    threshold_short,
)
from mhw.bottom.indicators import (
    BASELINE_END,
    BASELINE_START,
    analog_years,
    anomaly,
    ordinal_rank,
    percentile_rank,
    risk_category,
)
from mhw.bottom.regions import get_region


def _survey_replicate_panel(region: str, model_choices: list[str], yr_range=None) -> bool:
    """Survey-replicated validation card (model co-located at survey hauls). False if unbuilt."""
    sr_loaded = {name: load_survey_replicate(MODEL_SOURCES[name], region) for name in model_choices}
    if not any(a is not None for a, _ in sr_loaded.values()):
        return False
    with st.container(border=True):
        section_title("Survey-replicated validation — model co-located with survey stations")
        st.caption(
            "Each model's bottom temperature is sampled **at the survey's own haul locations and "
            "dates**, then compared to observed gear temperature (Kearney 2021; Seelanki et al. "
            "2025). Co-locating removes the footprint/timing mismatch, so the bias is the *true* "
            "model bias, directly comparable to the published literature."
        )
        srfig = go.Figure()
        obs_plotted = False
        sr_rows = []
        for name, (annual, skill) in sr_loaded.items():
            if annual is None:
                continue
            a = annual if yr_range is None else annual[(annual["year"] >= yr_range[0])
                                                       & (annual["year"] <= yr_range[1])]
            if not obs_plotted:
                srfig.add_trace(go.Scatter(x=a["year"], y=a["obs_mean_bottom_temp"],
                                mode="lines+markers", name="Observed (survey)",
                                line={"color": "black", "width": 2}))
                obs_plotted = True
            srfig.add_trace(go.Scatter(x=a["year"], y=a["model_mean_bottom_temp"], mode="lines+markers",
                            name=name, line={"color": MODEL_COLORS.get(name, "gray"), "width": 2,
                                             "dash": "dash"}))
            if skill:
                sr_rows.append({"Model": name, "Bias (°C)": round(skill["bias"], 2),
                                "RMSE (°C)": round(skill["rmse"], 2),
                                "r (haul-level)": round(skill["r"], 2), "Hauls": skill["n"]})
        srfig.add_hline(y=2.0, line_dash="dot", line_color="gray", line_width=1)
        srfig.update_yaxes(title_text="Mean bottom temp at hauls (°C)")
        srfig.update_layout(height=400, template="plotly_white",
                            margin={"l": 70, "r": 20, "t": 50, "b": 40},
                            legend={"orientation": "h", "y": 1.06, "yanchor": "bottom",
                                    "x": 0, "xanchor": "left"})
        st.plotly_chart(srfig, use_container_width=True)
        if sr_rows:
            st.markdown("**Validation skill (model sampled at survey hauls):**")
            st.dataframe(pd.DataFrame(sr_rows).set_index("Model"), use_container_width=True)
            st.caption("Bias = model − observed bottom temperature, co-located at hauls — the "
                       "defensible, literature-comparable numbers.")
    return True


def _cold_pool_observed(region: str, model_choices: list[str]) -> None:
    """Cold-pool-region view: observed cold-pool index card + survey-replicated validation."""
    df = load_observed(region)
    if df is None:
        st.error(f"Cold-pool parquet not found for {region}. Run: `mhw-fetch-coldpool --region {region}`")
        return

    thr_label = st.sidebar.selectbox("Observed cold-pool threshold", list(THRESHOLDS), index=0)
    thr_col = THRESHOLDS[thr_label]
    thr_short = threshold_short(thr_label)
    yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
    yr_range = st.sidebar.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
    show_bt = st.sidebar.checkbox("Overlay mean bottom temperature", value=True)
    d = df[(df["year"] >= yr_range[0]) & (df["year"] <= yr_range[1])].copy()

    latest = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else None
    yr = int(latest["year"])
    area_pop = df[thr_col]
    long_mean = area_pop.mean()
    full_span = f"{int(df['year'].min())}–{int(df['year'].max())}"
    pct = percentile_rank(latest[thr_col], area_pop)
    rank_small = ordinal_rank(latest[thr_col], area_pop, smallest=True)
    category = risk_category(pct, concern_when_low=True)
    bt_anom = float("nan")
    if pd.notna(latest.get("mean_bottom_temp")):
        base_bt = df.loc[(df["year"] >= BASELINE_START) & (df["year"] <= BASELINE_END), "mean_bottom_temp"]
        bt_anom = anomaly(latest["mean_bottom_temp"], base_bt)

    with st.container(border=True):
        section_title("Observed cold-pool index — AFSC bottom-trawl survey")
        st.caption(
            f"The validated ground truth: area of the {region.upper()} survey footprint with bottom "
            "temperature at or below the selected threshold, plus mean bottom temperature. Annual, lagged."
        )
        area_sub = "&nbsp;"
        if prev is not None:
            d_area = latest[thr_col] - prev[thr_col]
            area_sub = (f"<span style='color:{GREEN}'>{'▼' if d_area < 0 else '▲'} {d_area:+,.0f} "
                        f"km² vs {int(prev['year'])}</span>")
        bt_val, bt_sub = "—", "&nbsp;"
        if pd.notna(latest.get("mean_bottom_temp")):
            bt_val = f"{latest['mean_bottom_temp']:.2f} °C"
            if pd.notna(bt_anom):
                bt_sub = (f"<span style='color:{RED}'>{'▲' if bt_anom >= 0 else '▼'} {bt_anom:+.2f} "
                          f"°C vs {BASELINE_START}–{BASELINE_END}</span>")
        kpi_grid([
            kpi_card(f"{yr} cold-pool area", f"{latest[thr_col]:,.0f} km²", GREEN,
                     sub=area_sub, label_note=f"({thr_short})"),
            kpi_card("Percentile rank", f"{pct:.0f}th pct", BLUE,
                     sub=f"{ordinal(rank_small)} smallest", label_note=f"({full_span})"),
            kpi_card(f"{yr} mean bottom temp", bt_val, RED, sub=bt_sub),
        ], cols=3)

        habitat = ("an <b>expanded</b> cold-water thermal refuge" if pct >= 80
                   else "a <b>reduced</b> cold-water thermal refuge" if pct < 20
                   else "near-typical cold-water thermal habitat")
        temp_clause = ("" if not pd.notna(bt_anom)
                       else f" Mean bottom temperature is {bt_anom:+.2f} °C vs the "
                            f"{BASELINE_START}–{BASELINE_END} norm.")
        callout(
            f"<b>{category}</b> — {yr}'s cold pool sits in the <b>{pct:.0f}th percentile</b> of the "
            f"{full_span} survey record ({ordinal(rank_small)} smallest), indicating {habitat}.{temp_clause}",
            icon="🌡️", tint=BLUE)
        analog_cols = [df[thr_col].values]
        if "mean_bottom_temp" in df:
            analog_cols.append(df["mean_bottom_temp"].values)
        analogs = analog_years(yr, df["year"].values, *analog_cols, k=3)
        if analogs:
            st.caption("Historical analogs (most similar [area, bottom temp]): "
                       + ", ".join(str(a) for a in analogs) + ".")
        st.caption(
            "Percentile and analogs are ranked against the full observed survey record; categories "
            "(top 20% Favorable · bottom 20% Elevated · bottom 10% High concern) are stated "
            "conventions for the cold-water specialist view. Descriptive of past state — not a forecast."
        )

        n_rows = 2 if show_bt else 1
        fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                            subplot_titles=([f"Cold-pool area  {thr_short}"]
                                            + (["Mean bottom (gear) temperature"] if show_bt else [])))
        fig.add_trace(go.Bar(x=d["year"], y=d[thr_col], marker_color="steelblue", name="Cold-pool area",
                             hovertemplate="%{x}: %{y:,.0f} km²<extra></extra>"), row=1, col=1)
        fig.add_hline(y=long_mean, line_dash="dash", line_color="gray", line_width=1,
                      annotation_text=f"{full_span} mean", annotation_font_size=9, row=1, col=1)
        fig.update_yaxes(title_text="km²", row=1, col=1)
        if show_bt and "mean_bottom_temp" in d:
            fig.add_trace(go.Scatter(x=d["year"], y=d["mean_bottom_temp"], mode="lines+markers",
                                     line={"color": "firebrick", "width": 2}, name="Mean bottom temp",
                                     hovertemplate="%{x}: %{y:.2f} °C<extra></extra>"), row=2, col=1)
            fig.add_hline(y=2.0, line_dash="dot", line_color="steelblue", line_width=1,
                          annotation_text="2 °C", annotation_font_size=9, row=2, col=1)
            fig.update_yaxes(title_text="°C", row=2, col=1)
        fig.update_layout(height=300 * n_rows, template="plotly_white", showlegend=False,
                          bargap=0.15, margin={"l": 60, "r": 20, "t": 50, "b": 40})
        st.plotly_chart(fig, use_container_width=True)

        if region == "ebs":
            callout(
                "<b>Where is the cold pool?</b> Its <b>southern extent</b> — how far south the ≤ 2 °C "
                "cold pool reaches, and whether it has retreated north — has its own page.",
                icon="🧭", tint=GREEN)
            st.page_link("pages/cold_pool_position.py", label="Open Cold-Pool Position →", icon="🧭")

    if model_choices:
        _survey_replicate_panel(region, model_choices, yr_range)
    else:
        st.info("Pick one or both models in the sidebar to see the survey-replicated validation.")

    last_update = str(df["last_update"].iloc[-1])[:10] if "last_update" in df else "—"
    footer(
        f"Data sources: NOAA AFSC <code>afsc-gap-products/coldpool</code> "
        f"(Zenodo 10.5281/zenodo.16915337) · survey years {yr_min}–{yr_max} · last updated {last_update}. "
        f"All lagged (recent-historical), not near-real-time."
    )


def _bottom_temp_observed(region: str, model_choices: list[str]) -> None:
    """Bottom-temperature-region view (slope; no cold pool): observed survey bottom temp."""
    obs = None
    for sid in MODEL_SOURCES.values():
        annual, _ = load_survey_replicate(sid, region)
        if annual is not None and "obs_mean_bottom_temp" in annual:
            obs = annual.dropna(subset=["obs_mean_bottom_temp"]).sort_values("year")
            break

    with st.container(border=True):
        section_title("Observed bottom temperature — AFSC survey hauls")
        st.caption("A deep / non-cold-pool shelf — **no ≤ 2 °C cold pool**. The product is "
                   "bottom-temperature *conditions*: the observed survey bottom temperature, by year.")
        if obs is None or obs.empty:
            st.warning(f"Observed bottom temperature not built for {region}. Run: "
                       f"`mhw-build-survey-replicate --source bering10k --region {region}`.")
        else:
            latest = obs.iloc[-1]
            yr = int(latest["year"])
            series = obs["obs_mean_bottom_temp"]
            span = f"{int(obs['year'].min())}–{int(obs['year'].max())}"
            pct = percentile_rank(latest["obs_mean_bottom_temp"], series)
            rank_warm = ordinal_rank(latest["obs_mean_bottom_temp"], series, smallest=False)
            base = obs.loc[(obs["year"] >= BASELINE_START) & (obs["year"] <= BASELINE_END),
                           "obs_mean_bottom_temp"]
            anom = anomaly(latest["obs_mean_bottom_temp"], base) if not base.empty else float("nan")
            anom_sub = (f"<span style='color:{RED}'>{'▲' if anom >= 0 else '▼'} {anom:+.2f} °C vs "
                        f"{BASELINE_START}–{BASELINE_END}</span>") if pd.notna(anom) else "&nbsp;"
            kpi_grid([
                kpi_card(f"{yr} mean bottom temp", f"{latest['obs_mean_bottom_temp']:.2f} °C", RED,
                         sub=anom_sub),
                kpi_card("Percentile rank", f"{pct:.0f}th pct", BLUE,
                         sub=f"{ordinal(rank_warm)} warmest of {len(series)}", label_note=f"({span})"),
            ], cols=2, template="1fr 1fr 0.9fr")
            st.caption("Ranked against the available survey years (sporadic for a discontinued slope "
                       "survey). Descriptive of past observed state — not a forecast.")

    if model_choices:
        if not _survey_replicate_panel(region, model_choices):
            st.warning(f"Survey replicate not built for {region}. Run: "
                       f"`mhw-build-survey-replicate --source bering10k --region {region}` (and mom6_nep).")
    else:
        st.info("Pick at least one model in the sidebar to compare against the survey.")
    footer("Data sources: AFSC bottom-trawl survey hauls via the FOSS REST API (BSS survey, "
           "2002–2016, discontinued); Bering10K ROMS · CEFI MOM6 NEP. All lagged, not near-real-time.")


def render(group: str = "bering") -> None:
    """Render the Cold Pool & Bottom Temperature page (page config/fonts owned by the nav shell)."""
    inject_css()
    st.sidebar.header("Controls")
    regions = list_bottom_state_regions(group)
    if not regions:
        st.title("Cold Pool & Bottom Temperature")
        st.error("No bottom-state region built. Run: `mhw-fetch-coldpool --region ebs`")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="bs_obs_region")
    reg = get_region(region)
    is_cold_pool = reg.product_kind == "cold_pool"

    model_choices = st.sidebar.multiselect(
        "Validate model(s) against the survey", list(MODEL_SOURCES),
        default=([] if is_cold_pool else list(MODEL_SOURCES)),
        help="Each model is sampled at the survey hauls and compared to observed bottom temp.",
    )

    if is_cold_pool:
        page_header("🧊", "Cold Pool & Bottom Temperature", region_label(region),
                    f"{region_label(region)} ({region.upper()})",
                    caption=("The observed cold-pool index from the NOAA AFSC summer bottom-trawl "
                             "survey, and how well the regional models reproduce it when compared "
                             "the fair way."))
        _cold_pool_observed(region, model_choices)
    else:
        page_header("🌡️", "Bottom Temperature", region_label(region),
                    f"{region_label(region)} ({region.upper()})",
                    caption="Observed bottom-temperature conditions from the AFSC survey (no cold pool).")
        _bottom_temp_observed(region, model_choices)
