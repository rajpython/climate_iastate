"""Page 4 — Cold Pool: Observed & Validation (Eastern Bering Sea).

Two panels:
  * **A — Observed cold-pool index** (AFSC bottom-trawl survey): area below the chosen
    threshold + mean bottom temperature. The threshold dropdown drives this panel.
  * **C — Survey-replicated validation**: each selected model sampled at the survey's own
    haul locations and dates, vs observed bottom temperature (the literature-standard,
    apples-to-apples comparison). Bottom-temperature based, so the threshold doesn't apply.

Model *behaviour* and model-vs-model comparison live on the companion page,
`5_Cold_Pool_Models.py`. Fetch data with `mhw-fetch-coldpool`.
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
    load_observed,
    load_survey_replicate,
    threshold_short,
)


def main() -> None:
    st.set_page_config(page_title="Cold Pool — Observed & Validation", layout="wide", page_icon="🧊")
    st.title("🧊 Cold Pool — Observed & Validation (Eastern Bering Sea)")
    st.caption(
        "The observed cold-pool index from the **NOAA AFSC summer bottom-trawl survey**, and "
        "how well the regional models reproduce it when compared the fair way. Model behaviour "
        "and model-vs-model comparison are on the **Cold Pool — Model Comparison** page."
    )

    df = load_observed()
    if df is None:
        st.error("Cold-pool parquet not found. Run: `mhw-fetch-coldpool`")
        return

    # ---- Sidebar ----
    st.sidebar.header("Controls")
    thr_label = st.sidebar.selectbox("Observed cold-pool threshold", list(THRESHOLDS), index=0)
    thr_col = THRESHOLDS[thr_label]
    thr_short = threshold_short(thr_label)
    yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
    yr_range = st.sidebar.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
    show_bt = st.sidebar.checkbox("Overlay mean bottom temperature", value=True)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Validation")
    model_choices = st.sidebar.multiselect(
        "Validate model(s) against the survey", list(MODEL_SOURCES),
        help="Each model is sampled at the survey hauls and compared to observed bottom temp.",
    )

    d = df[(df["year"] >= yr_range[0]) & (df["year"] <= yr_range[1])].copy()

    # ---- Panel A: Observed cold-pool index ----
    st.markdown("### Observed cold-pool index — AFSC bottom-trawl survey")
    st.caption(
        "The validated ground truth: area of the EBS survey footprint with bottom "
        "temperature at or below the selected threshold, plus mean bottom temperature. "
        "Annual, lagged."
    )

    latest = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else None
    long_mean = df[thr_col].mean()
    c1, c2, c3 = st.columns(3)
    delta = None if prev is None else f"{latest[thr_col] - prev[thr_col]:+,.0f} km² vs {int(prev['year'])}"
    c1.metric(f"{int(latest['year'])} cold-pool area ({thr_short})",
              f"{latest[thr_col]:,.0f} km²", delta=delta, delta_color="inverse")
    pct_of_mean = 100.0 * latest[thr_col] / long_mean if long_mean else float("nan")
    c2.metric("vs 1982–present mean", f"{pct_of_mean:.0f}%",
              help=f"Long-term mean ≈ {long_mean:,.0f} km²")
    if pd.notna(latest.get("mean_bottom_temp")):
        c3.metric(f"{int(latest['year'])} mean bottom temp", f"{latest['mean_bottom_temp']:.2f} °C")

    n_rows = 2 if show_bt else 1
    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=([f"Cold-pool area  {thr_short}"]
                        + (["Mean bottom (gear) temperature"] if show_bt else [])),
    )
    fig.add_trace(go.Bar(x=d["year"], y=d[thr_col], marker_color="steelblue",
                         name="Cold-pool area",
                         hovertemplate="%{x}: %{y:,.0f} km²<extra></extra>"), row=1, col=1)
    fig.add_hline(y=long_mean, line_dash="dash", line_color="gray", line_width=1,
                  annotation_text="1982–present mean", annotation_font_size=9, row=1, col=1)
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

    # ---- Panel C: Survey-replicated validation ----
    if model_choices:
        sr_loaded = {name: load_survey_replicate(name) for name in model_choices}
        if any(a is not None for a, _ in sr_loaded.values()):
            st.markdown("### Survey-replicated validation — model co-located with survey stations")
            st.caption(
                "Each model's bottom temperature is sampled **at the survey's own haul "
                "locations and dates**, then compared to the observed gear temperature — the "
                "method of Kearney (2021) and Seelanki et al. (2025). Co-locating in space and "
                "time removes the footprint/timing mismatch, so the bias below is the *true* "
                "model bias, directly comparable to the published literature. "
                "(Bottom-temperature based — the threshold control does not apply here.)"
            )
            srfig = make_subplots(rows=1, cols=1)
            obs_plotted = False
            sr_rows = []
            for name, (annual, skill) in sr_loaded.items():
                if annual is None:
                    st.warning(f"{name} survey replicate not built. Run: `mhw-build-survey-replicate`")
                    continue
                a = annual[(annual["year"] >= yr_range[0]) & (annual["year"] <= yr_range[1])]
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
    else:
        st.info("Pick one or both models in the sidebar to see the survey-replicated validation.")

    # ---- Provenance ----
    last_update = str(df["last_update"].iloc[-1])[:10] if "last_update" in df else "—"
    st.markdown(
        f"""
        **Sources & coverage**
        - **Observed (validation target):** NOAA AFSC `afsc-gap-products/coldpool`
          (Zenodo [10.5281/zenodo.16915337](https://doi.org/10.5281/zenodo.16915337)) ·
          survey years **{yr_min}–{yr_max}** (no 2020 — survey cancelled) · last updated {last_update}.
        - **Bering10K ROMS** (NOAA PMEL / UW ACLIM hindcast) · **CEFI MOM6 NEP** (NOAA GFDL/PSL).

        All **lagged** (recent-historical), not near-real-time. See the **Model Comparison**
        page for full-shelf model behaviour and model-vs-model comparison.
        """
    )


main()
