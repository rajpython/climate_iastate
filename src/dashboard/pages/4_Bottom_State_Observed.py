"""Page 4 — Bottom State: Observed & Validation (Bering Sea: EBS, NBS, Slope).

One region dropdown spans the Bering bottom-state areas; the panels adapt to the region's
product kind:

  * **Cold-pool regions** (EBS, NBS) — the observed **cold-pool index** (AFSC bottom-trawl
    survey area below the chosen threshold + mean bottom temperature), plus survey-replicated
    model validation. "Cold pool" is used only here, where it is well defined.
  * **Bottom-temperature regions** (Bering slope) — no cold pool (deep water): just the
    observed bottom temperature vs the models, co-located at the survey hauls.

Model behaviour and model-vs-model comparison live on `5_Cold_Pool_Models.py`. Build data with
`mhw-fetch-coldpool` / `mhw-build-survey-replicate`.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from dashboard.components.coldpool_data import (
    MODEL_COLORS,
    MODEL_SOURCES,
    THRESHOLDS,
    list_bottom_state_regions,
    load_observed,
    load_survey_replicate,
    region_label,
    threshold_short,
)
from dashboard.components.style import apply_explanatory_font
from mhw.bottom.regions import get_region


def _survey_replicate_panel(region: str, model_choices: list[str], yr_range=None) -> bool:
    """Survey-replicated bottom-temperature panel — works for any region. Returns False if
    nothing is built yet."""
    sr_loaded = {name: load_survey_replicate(MODEL_SOURCES[name], region) for name in model_choices}
    if not any(a is not None for a, _ in sr_loaded.values()):
        return False
    st.markdown("### Survey-replicated validation — model co-located with survey stations")
    st.caption(
        "Each model's bottom temperature is sampled **at the survey's own haul locations and "
        "dates**, then compared to the observed gear temperature — the method of Kearney (2021) "
        "and Seelanki et al. (2025). Co-locating in space and time removes the footprint/timing "
        "mismatch, so the bias below is the *true* model bias, directly comparable to the "
        "published literature."
    )
    srfig = make_subplots(rows=1, cols=1)
    obs_plotted = False
    sr_rows = []
    for name, (annual, skill) in sr_loaded.items():
        if annual is None:
            st.warning(f"{name} survey replicate not built. Run: "
                       f"`mhw-build-survey-replicate --source {MODEL_SOURCES[name]} --region {region}`")
            continue
        a = annual
        if yr_range is not None:
            a = a[(a["year"] >= yr_range[0]) & (a["year"] <= yr_range[1])]
        if not obs_plotted:
            srfig.add_trace(go.Scatter(x=a["year"], y=a["obs_mean_bottom_temp"],
                            mode="lines+markers", name="Observed (survey)",
                            line={"color": "black", "width": 2}))
            obs_plotted = True
        srfig.add_trace(go.Scatter(x=a["year"], y=a["model_mean_bottom_temp"],
                        mode="lines+markers", name=name,
                        line={"color": MODEL_COLORS.get(name, "gray"), "width": 2, "dash": "dash"}))
        if skill:
            sr_rows.append({"Model": name, "Bias (°C)": round(skill["bias"], 2),
                            "RMSE (°C)": round(skill["rmse"], 2),
                            "r (haul-level)": round(skill["r"], 2), "Hauls": skill["n"]})
    srfig.add_hline(y=2.0, line_dash="dot", line_color="gray", line_width=1)
    srfig.update_yaxes(title_text="Mean bottom temp at hauls (°C)")
    srfig.update_layout(height=420, template="plotly_white",
                        margin={"l": 70, "r": 20, "t": 60, "b": 40},
                        legend={"orientation": "h", "y": 1.06, "yanchor": "bottom",
                                "x": 0, "xanchor": "left"})
    st.plotly_chart(srfig, use_container_width=True)
    if sr_rows:
        st.markdown("**Validation skill (model sampled at survey hauls):**")
        st.dataframe(pd.DataFrame(sr_rows).set_index("Model"), use_container_width=True)
        st.caption("Bias = model − observed bottom temperature, co-located at hauls. "
                   "The defensible, literature-comparable numbers.")
    return True


def _cold_pool_observed(region: str, model_choices: list[str]) -> None:
    """The cold-pool-region view: observed area index (Panel A) + survey-replicate (Panel C)."""
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

    # ---- Panel A: observed cold-pool index ----
    st.markdown("### Observed cold-pool index — AFSC bottom-trawl survey")
    st.caption(
        f"The validated ground truth: area of the {region.upper()} survey footprint with bottom "
        "temperature at or below the selected threshold, plus mean bottom temperature. Annual, lagged."
    )
    latest = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else None
    long_mean = df[thr_col].mean()
    span = f"{yr_min}–{yr_max}"
    c1, c2, c3 = st.columns(3)
    delta = None if prev is None else f"{latest[thr_col] - prev[thr_col]:+,.0f} km² vs {int(prev['year'])}"
    c1.metric(f"{int(latest['year'])} cold-pool area ({thr_short})",
              f"{latest[thr_col]:,.0f} km²", delta=delta, delta_color="inverse")
    pct_of_mean = 100.0 * latest[thr_col] / long_mean if long_mean else float("nan")
    c2.metric(f"vs {span} mean", f"{pct_of_mean:.0f}%", help=f"Long-term mean ≈ {long_mean:,.0f} km²")
    if pd.notna(latest.get("mean_bottom_temp")):
        c3.metric(f"{int(latest['year'])} mean bottom temp", f"{latest['mean_bottom_temp']:.2f} °C")

    n_rows = 2 if show_bt else 1
    fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=([f"Cold-pool area  {thr_short}"]
                                        + (["Mean bottom (gear) temperature"] if show_bt else [])))
    fig.add_trace(go.Bar(x=d["year"], y=d[thr_col], marker_color="steelblue", name="Cold-pool area",
                         hovertemplate="%{x}: %{y:,.0f} km²<extra></extra>"), row=1, col=1)
    fig.add_hline(y=long_mean, line_dash="dash", line_color="gray", line_width=1,
                  annotation_text=f"{span} mean", annotation_font_size=9, row=1, col=1)
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

    # ---- Panel C: survey-replicated validation ----
    if model_choices:
        _survey_replicate_panel(region, model_choices, yr_range)
    else:
        st.info("Pick one or both models in the sidebar to see the survey-replicated validation.")

    last_update = str(df["last_update"].iloc[-1])[:10] if "last_update" in df else "—"
    st.markdown(
        f"""
        **Sources & coverage**
        - **Observed (validation target):** NOAA AFSC `afsc-gap-products/coldpool`
          (Zenodo [10.5281/zenodo.16915337](https://doi.org/10.5281/zenodo.16915337)) ·
          survey years **{yr_min}–{yr_max}** · last updated {last_update}.
        - **Bering10K ROMS** (NOAA PMEL / UW ACLIM) · **CEFI MOM6 NEP** (NOAA GFDL/PSL).

        All **lagged** (recent-historical), not near-real-time. See **Bottom State — Model
        Comparison** for full-shelf model behaviour and model-vs-model comparison.
        """
    )


def _bottom_temp_observed(region: str, model_choices: list[str]) -> None:
    """The bottom-temperature-region view (no cold pool): survey-replicated bottom temp only."""
    st.caption(
        "A deep / non-cold-pool shelf — **no ≤2 °C cold pool**. The product is "
        "bottom-temperature *conditions*: the observed survey bottom temperature vs the regional "
        "models, co-located at the survey hauls."
    )
    if not model_choices:
        st.info("Pick at least one model in the sidebar.")
        return
    if not _survey_replicate_panel(region, model_choices):
        st.warning(f"Survey replicate not built for {region}. Run: "
                   f"`mhw-build-survey-replicate --source bering10k --region {region}` (and mom6_nep).")
    st.markdown(
        """
        **Sources & coverage**
        - **Observed:** AFSC bottom-trawl survey hauls via the **FOSS** REST API (bottom
          temperature per tow). For the Bering slope: the **BSS** survey, **2002–2016,
          discontinued** thereafter — sporadic, lagged.
        - **Bering10K ROMS** (NOAA PMEL / UW ACLIM) · **CEFI MOM6 NEP** (NOAA GFDL/PSL), bottom
          temperature over the region's depth band. All **lagged**, not near-real-time.
        """
    )


def main() -> None:
    st.set_page_config(page_title="Bottom State — Observed & Validation", layout="wide", page_icon="🧊")
    apply_explanatory_font()

    st.sidebar.header("Controls")
    regions = list_bottom_state_regions()
    if not regions:
        st.title("Bottom State — Observed & Validation")
        st.error("No bottom-state region built. Run: `mhw-fetch-coldpool --region ebs`")
        return
    region = st.sidebar.selectbox("Region", regions, format_func=str.upper, key="bs_obs_region")
    reg = get_region(region)
    is_cold_pool = reg.product_kind == "cold_pool"

    icon = "🧊" if is_cold_pool else "🌡️"
    st.title(f"{icon} Bottom State — Observed & Validation · {region_label(region)}")
    if is_cold_pool:
        st.caption(
            "The observed **cold-pool index** from the NOAA AFSC summer bottom-trawl survey, and "
            "how well the regional models reproduce it when compared the fair way."
        )

    model_choices = st.sidebar.multiselect(
        "Validate model(s) against the survey", list(MODEL_SOURCES),
        default=([] if is_cold_pool else list(MODEL_SOURCES)),
        help="Each model is sampled at the survey hauls and compared to observed bottom temp.",
    )

    if is_cold_pool:
        _cold_pool_observed(region, model_choices)
    else:
        _bottom_temp_observed(region, model_choices)


main()
