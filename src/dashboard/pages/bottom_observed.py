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

import numpy as np
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
    load_model,
    load_observed,
    load_survey_replicate,
    load_survey_replicate_hauls,
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
        _obs_vs_model_scatter(region, model_choices)
    else:
        st.info("Pick one or both models in the sidebar to see the survey-replicated validation.")

    last_update = str(df["last_update"].iloc[-1])[:10] if "last_update" in df else "—"
    footer(
        "Sources — observed cold-pool <b>area index</b> (≤ 2/1/0/−1 °C): NOAA AFSC "
        "<code>afsc-gap-products/coldpool</code> (Zenodo 10.5281/zenodo.16915337), spatially "
        "interpolated from the survey. Per-haul <b>validation</b> temperatures: NOAA FOSS AFSC "
        "bottom-trawl survey. Models: Bering10K ROMS (NOAA PMEL / UW ACLIM) · CEFI MOM6 NEP "
        f"(NOAA GFDL / PSL). Survey years {yr_min}–{yr_max}; index last updated {last_update}. "
        "All lagged (recent-historical), not near-real-time."
    )


# Per-subarea lines for the packaged GOA/AI index (column slug -> label, colour). Solid,
# high-contrast colours so the subareas read clearly against the bold region-wide line.
_SUBAREA_LINES = [
    ("mean_bottom_temp_western", "Western", "#1f77b4"),   # blue
    ("mean_bottom_temp_eastern", "Eastern", "#d62728"),   # red
    ("mean_bottom_temp_central", "Central", "#2ca02c"),   # green
]
_SUBAREA_COLORS = {"Western": "#1f77b4", "Eastern": "#d62728"}
# Longitude boundary splitting a region's hauls into the packaged product's subareas. GOA's
# western/eastern Gulf split follows the AFSC convention at ~147°W.
_SUBAREA_LON_SPLIT = {"goa": -147.0}


def _assign_subarea(h: pd.DataFrame, region: str) -> pd.DataFrame:
    """Label each haul Western/Eastern by longitude (region-specific split); single 'All' group
    where no split is defined."""
    h = h.copy()
    split = _SUBAREA_LON_SPLIT.get(region)
    if split is None:
        h["subarea"] = "All"
    else:
        h["subarea"] = np.where(h["longitude"] >= split, "Eastern", "Western")
    return h


def _packaged_index_card(region: str, df: pd.DataFrame) -> None:
    """Headline observed card from the packaged AFSC bottom-temperature index (GOA/AI)."""
    df = df.sort_values("year").reset_index(drop=True)
    latest = df.iloc[-1]
    yr = int(latest["year"])
    series = df["mean_bottom_temp"]
    span = f"{int(df['year'].min())}–{int(df['year'].max())}"
    long_mean = float(series.mean())
    pct = percentile_rank(latest["mean_bottom_temp"], series)
    rank_warm = ordinal_rank(latest["mean_bottom_temp"], series, smallest=False)
    base = df.loc[(df["year"] >= BASELINE_START) & (df["year"] <= BASELINE_END), "mean_bottom_temp"]
    anom = anomaly(latest["mean_bottom_temp"], base) if not base.empty else float("nan")

    label = region_label(region)
    with st.container(border=True):
        section_title("Observed bottom temperature — AFSC bottom-trawl survey")
        st.caption(
            f"The official AFSC summer bottom-trawl survey mean bottom (gear) temperature for the "
            f"**{label}** — region-wide and by subarea, by survey year. This is a triennial/biennial "
            "survey (lagged), so points are survey years, not every calendar year."
        )
        anom_sub = (f"<span style='color:{RED}'>{'▲' if anom >= 0 else '▼'} {anom:+.2f} °C vs "
                    f"{BASELINE_START}–{BASELINE_END}</span>") if pd.notna(anom) else "&nbsp;"
        kpi_grid([
            kpi_card(f"{yr} mean bottom temp", f"{latest['mean_bottom_temp']:.2f} °C", RED, sub=anom_sub),
            kpi_card("Percentile rank", f"{pct:.0f}th pct", BLUE,
                     sub=f"{ordinal(rank_warm)} warmest of {len(series)}", label_note=f"({span})"),
        ], cols=2, template="1fr 1fr 0.9fr")

        warmth = ("notably warm" if pct >= 80 else "notably cool" if pct < 20 else "near-typical")
        temp_clause = ("" if not pd.notna(anom)
                       else f" — {anom:+.2f} °C vs the {BASELINE_START}–{BASELINE_END} norm")
        callout(
            f"<b>{warmth.capitalize()}</b> — {yr}'s mean bottom temperature sits in the "
            f"<b>{pct:.0f}th percentile</b> of the {span} survey record "
            f"({ordinal(rank_warm)} warmest of {len(series)}){temp_clause}.",
            icon="🌡️", tint=BLUE)

        fig = go.Figure()
        # Subareas first (solid, high-contrast); connectgaps=False so a year a subarea was not
        # surveyed (e.g. eastern Gulf in 2001) shows as a break rather than a misleading line.
        for col, nm, color in _SUBAREA_LINES:
            if col in df:
                fig.add_trace(go.Scatter(x=df["year"], y=df[col], mode="lines+markers", name=nm,
                                         line={"color": color, "width": 2}, marker={"size": 6},
                                         connectgaps=False,
                                         hovertemplate=f"%{{x}} {nm}: %{{y:.2f}} °C<extra></extra>"))
        # Region-wide on top, bold and dark so it dominates.
        fig.add_trace(go.Scatter(x=df["year"], y=df["mean_bottom_temp"], mode="lines+markers",
                                 name="Region-wide", line={"color": "#111111", "width": 3.5},
                                 marker={"size": 7},
                                 hovertemplate="%{x} region-wide: %{y:.2f} °C<extra></extra>"))
        fig.add_hline(y=long_mean, line_dash="dash", line_color="gray", line_width=1,
                      annotation_text=f"{span} mean", annotation_font_size=9)
        fig.update_yaxes(title_text="Mean bottom temp (°C)")
        fig.update_layout(height=380, template="plotly_white",
                          margin={"l": 60, "r": 20, "t": 50, "b": 40},
                          legend={"orientation": "h", "y": 1.06, "yanchor": "bottom",
                                  "x": 0, "xanchor": "left"})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Region-wide is the **unweighted mean of the subareas surveyed that year** (the "
                   "packaged product carries no stratum areas, so subareas are weighted equally); "
                   "in a year a subarea was not surveyed the region-wide value reflects only the "
                   "surveyed subarea(s). Ranked against the available survey years. Descriptive of "
                   "past observed state — not a forecast.")


def _modelled_shelf_card(region: str) -> None:
    """Continuous modelled shelf bottom-temperature series over the ≤ 200 m shelf.

    For GOA/AI (B2) it fills the gaps between sparse survey years and overlays the survey dots;
    for the model-only Arctic (B3) it is the *only* product (no observed series to overlay)."""
    reg = get_region(region)
    id_to_label = {v: k for k, v in MODEL_SOURCES.items()}
    loaded = []
    for sid in reg.valid_sources:
        df = load_model(sid, region)
        if df is not None and not df.empty and "mean_bottom_temp" in df.columns:
            loaded.append((id_to_label.get(sid, sid),
                           df.dropna(subset=["mean_bottom_temp"]).sort_values("year")))
    if not loaded:
        return
    obs = load_observed(region)
    has_obs = obs is not None and "mean_bottom_temp" in obs.columns

    with st.container(border=True):
        section_title("Modelled shelf bottom temperature — continuous (full hindcast)")
        if has_obs:
            st.caption(
                "The model's area-weighted mean bottom temperature over the **≤ 200 m shelf**, every "
                "year — continuous, filling the gaps between the sparse survey years above. This is the "
                "model's own shelf domain (a different footprint than the survey index); the fair "
                "model-vs-survey skill comparison is the validation panel below."
            )
        else:
            st.caption(
                "The model's area-weighted mean bottom temperature over the **≤ 200 m shelf**, every "
                "year. With **no in-region survey**, this is the only available product — read it as "
                "modelled conditions, not measurements."
            )
        name0, d0 = loaded[0]
        latest = d0.iloc[-1]
        yr = int(latest["year"])
        span = f"{int(d0['year'].min())}–{int(d0['year'].max())}"
        base = d0.loc[(d0["year"] >= BASELINE_START) & (d0["year"] <= BASELINE_END), "mean_bottom_temp"]
        anom = anomaly(latest["mean_bottom_temp"], base) if not base.empty else float("nan")
        anom_sub = (f"<span style='color:{RED}'>{'▲' if anom >= 0 else '▼'} {anom:+.2f} °C vs "
                    f"{BASELINE_START}–{BASELINE_END}</span>") if pd.notna(anom) else "&nbsp;"
        kpi_grid([
            kpi_card(f"{yr} modelled shelf BT", f"{latest['mean_bottom_temp']:.2f} °C", RED,
                     sub=anom_sub, label_note=f"({name0})"),
            kpi_card("Hindcast span", span, BLUE, sub="continuous, every year"),
        ], cols=2, template="1fr 1fr 0.9fr")

        fig = go.Figure()
        for name, d in loaded:
            fig.add_trace(go.Scatter(x=d["year"], y=d["mean_bottom_temp"], mode="lines+markers",
                          name=name, line={"color": MODEL_COLORS.get(name, "darkorange"), "width": 2.5},
                          marker={"size": 5}, hovertemplate="%{x} modelled: %{y:.2f} °C<extra></extra>"))
        if has_obs:   # overlay the survey dots so the gap-filling is visible
            fig.add_trace(go.Scatter(x=obs["year"], y=obs["mean_bottom_temp"], mode="markers",
                          name="Observed (survey)", marker={"color": "black", "size": 8,
                          "symbol": "circle-open", "line": {"width": 1.5}},
                          hovertemplate="%{x} observed: %{y:.2f} °C<extra></extra>"))
        fig.add_hline(y=float(d0["mean_bottom_temp"].mean()), line_dash="dash", line_color="gray",
                      line_width=1, annotation_text=f"{span} modelled mean", annotation_font_size=9)
        fig.update_yaxes(title_text="Shelf mean bottom temp (°C)")
        fig.update_layout(height=360, template="plotly_white", margin={"l": 60, "r": 20, "t": 50, "b": 40},
                          legend={"orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0, "xanchor": "left"})
        st.plotly_chart(fig, use_container_width=True)
        if has_obs:
            st.caption("Continuous modelled line (≤ 200 m shelf, standalone-bathymetry mask) with the "
                       "survey observations (open circles) overlaid — close in level here but different "
                       "domains. MOM6 NEP is less-validated outside the Bering. Descriptive — not a forecast.")
        else:
            st.caption("Modelled over the ≤ 200 m shelf (standalone-bathymetry/ETOPO mask). MOM6 NEP "
                       "is model-only / unvalidated in this region. Descriptive — not a forecast.")


def _survey_derived_card(region: str) -> None:
    """Fallback observed card for a bottom-temp region with no packaged index (slope): the
    observed survey bottom temperature derived from the survey-replicate output."""
    obs = None
    for sid in MODEL_SOURCES.values():
        annual, _ = load_survey_replicate(sid, region)
        if annual is not None and "obs_mean_bottom_temp" in annual:
            obs = annual.dropna(subset=["obs_mean_bottom_temp"]).sort_values("year")
            break

    with st.container(border=True):
        section_title("Observed bottom temperature — AFSC survey hauls")
        st.caption("Observed bottom-temperature *conditions* for this deep-water region: the "
                   "survey bottom (gear) temperature, by survey year.")
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


def _bottom_temp_observed(region: str, model_choices: list[str]) -> None:
    """Bottom-temperature-region view (slope, GOA, AI; no cold pool): observed survey bottom
    temperature (packaged AFSC index where available, else survey-derived) + model validation."""
    packaged = load_observed(region)
    if packaged is not None and "mean_bottom_temp" in packaged.columns:
        _packaged_index_card(region, packaged)
        _modelled_shelf_card(region)
        src_line = (f"Sources — observed bottom-temperature index ({region.upper()}, by subarea, "
                    "biennial): NOAA AFSC <code>afsc-gap-products/coldpool</code> "
                    "(Zenodo 10.5281/zenodo.16915337). Per-haul validation temperatures: NOAA FOSS "
                    "AFSC bottom-trawl survey. Model: CEFI MOM6 NEP (NOAA GFDL / PSL; less-validated "
                    "outside the Bering). All lagged, not near-real-time.")
    else:
        _survey_derived_card(region)
        src_line = ("Sources — per-haul survey bottom temperatures: NOAA FOSS AFSC bottom-trawl survey "
                    "(BSS slope survey, 2002–2016, discontinued). Models: Bering10K ROMS "
                    "(NOAA PMEL / UW ACLIM) · CEFI MOM6 NEP (NOAA GFDL / PSL). All lagged, not "
                    "near-real-time.")

    if model_choices:
        if _survey_replicate_panel(region, model_choices):
            _obs_vs_model_scatter(region, model_choices)
            if packaged is not None:
                _bias_interpretation(region, model_choices)
        else:
            st.warning(f"Survey replicate not built for {region}. Run: "
                       f"`mhw-build-survey-replicate --source mom6_nep --region {region}`.")
    else:
        st.info("Pick at least one model in the sidebar to compare against the survey.")
    footer(src_line)


def _bias_interpretation(region: str, model_choices: list[str]) -> None:
    """Interpret the survey-replicated skill for a packaged bottom-temp region (GOA/AI), using
    the per-haul split: the bias is spatially structured (not a uniform offset), so name where it
    is concentrated and note that it largely cancels in anomalies (interannual/management use)."""
    name = model_choices[0]
    h = load_survey_replicate_hauls(MODEL_SOURCES[name], region)
    if h is None or h.empty:
        return
    h = _assign_subarea(h.dropna(subset=["obs_bottom_temp", "model_bottom_temp", "longitude"]), region)
    overall = float((h["model_bottom_temp"] - h["obs_bottom_temp"]).mean())
    r = float(h["model_bottom_temp"].corr(h["obs_bottom_temp"]))
    direction = "cold" if overall < 0 else "warm"
    sub_bias = {sub: float((g["model_bottom_temp"] - g["obs_bottom_temp"]).mean())
                for sub, g in h.groupby("subarea")}
    spatial = ""
    if {"Western", "Eastern"} <= set(sub_bias):
        w, e = sub_bias["Western"], sub_bias["Eastern"]
        spatial = (f" The offset is <b>not uniform</b>: ~<b>{abs(w):.1f} °C {'cold' if w < 0 else 'warm'} "
                   f"in the western Gulf</b> but only {abs(e):.2f} °C in the eastern Gulf "
                   "(near-unbiased) — so the pooled number is dominated by the data-rich west.")
    # Be honest about correlation: a low r means the haul-to-haul pattern is poorly captured even
    # if the mean level (bias) is reasonable — important for the steep, tidally-mixed Aleutians.
    if r >= 0.6:
        skill_clause = (f"while still tracking the year-to-year pattern (r = {r:.2f}; the points "
                        "hug the 1:1 line). It largely cancels in anomalies, so interannual and "
                        "management use is more robust than absolute values.")
    else:
        skill_clause = (f"but the haul-to-haul correlation is <b>weak (r = {r:.2f})</b> — the model "
                        "captures the broad temperature level better than individual-haul variation "
                        "here, so treat point-level model values cautiously.")
    callout(
        f"<b>Why the bias?</b> {name} runs a {direction} bias of <b>{abs(overall):.2f} °C</b> overall "
        f"{skill_clause}{spatial} This is consistent with MOM6's coarse (~10 km) grid and smoothed "
        "bathymetry over a narrow, steep shelf, and its less-established validation outside the Bering.",
        icon="🔎", tint=BLUE)


def _model_scatter_panel(name: str, sel: pd.DataFrame, has_split: bool, height: int,
                         coverage: tuple[int, int]) -> None:
    """One model's observed-vs-model scatter + skill table (rendered inside its own column).

    ``coverage`` is the model's (first, last) survey-replicated year, used to explain an empty
    panel: a model can be absent for a year the *survey* ran simply because the *model* hindcast
    does not reach that year (e.g. the Bering10K hindcast currently ends in 2024)."""
    st.markdown(f"**{name}** · {len(sel):,} hauls")
    if sel.empty:
        st.info(f"No **{name}** values for this selection — its hindcast covers "
                f"**{coverage[0]}–{coverage[1]}**, so there is no modelled field to sample at "
                "these survey hauls (the survey itself ran; the model simply does not reach this year).")
        return
    lo = float(min(sel["obs_bottom_temp"].min(), sel["model_bottom_temp"].min())) - 0.3
    hi = float(max(sel["obs_bottom_temp"].max(), sel["model_bottom_temp"].max())) + 0.3
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="1:1 (perfect)",
                             line={"color": "#444", "width": 1, "dash": "dash"}, hoverinfo="skip"))
    rows = []
    for sub in ("Western", "Eastern", "All"):
        s = sel[sel["subarea"] == sub]
        if s.empty:
            continue
        legend_nm = f"{sub} (n={len(s):,})" if has_split else f"hauls (n={len(s):,})"
        fig.add_trace(go.Scatter(
            x=s["obs_bottom_temp"], y=s["model_bottom_temp"], mode="markers", name=legend_nm,
            marker={"color": _SUBAREA_COLORS.get(sub, "#1f77b4"), "size": 5, "opacity": 0.4,
                    "line": {"width": 0}},
            hovertemplate="observed %{x:.2f} °C<br>model %{y:.2f} °C<extra></extra>"))
        d = s["model_bottom_temp"] - s["obs_bottom_temp"]
        rows.append({"Group": sub if has_split else "All hauls", "Hauls": len(s),
                     "Bias (°C)": round(float(d.mean()), 2),
                     "RMSE (°C)": round(float(np.sqrt((d ** 2).mean())), 2),
                     "r": round(float(s["model_bottom_temp"].corr(s["obs_bottom_temp"])), 2)})
    fig.update_xaxes(title_text="Observed (°C)", range=[lo, hi])
    fig.update_yaxes(title_text="Model (°C)", range=[lo, hi], scaleanchor="x", scaleratio=1)
    fig.update_layout(height=height, template="plotly_white",
                      margin={"l": 55, "r": 15, "t": 34, "b": 44},
                      legend={"orientation": "h", "y": 1.02, "yanchor": "bottom",
                              "x": 0, "xanchor": "left", "font": {"size": 11}})
    st.plotly_chart(fig, use_container_width=True)
    if has_split and len(rows) > 1:   # pooled row only meaningful when subareas are split
        d = sel["model_bottom_temp"] - sel["obs_bottom_temp"]
        rows.append({"Group": "All (pooled)", "Hauls": len(sel),
                     "Bias (°C)": round(float(d.mean()), 2),
                     "RMSE (°C)": round(float(np.sqrt((d ** 2).mean())), 2),
                     "r": round(float(sel["model_bottom_temp"].corr(sel["obs_bottom_temp"])), 2)})
    st.dataframe(pd.DataFrame(rows).set_index("Group"), use_container_width=True)


def _obs_vs_model_scatter(region: str, model_choices: list[str]) -> None:
    """Haul-level observed-vs-model scatter(s), with a single-year or cumulative (start → year)
    selector. Each point is one survey haul (observed gear temp on x, the model sampled at that
    haul on y) so over- vs under-prediction is visible directly. With two models (the Bering
    regions) the panels sit side by side; where a region has subareas (GOA/AI) a Combined /
    Western / Eastern selector colours and filters them."""
    loaded = []
    for name in model_choices:
        h = load_survey_replicate_hauls(MODEL_SOURCES[name], region)
        if h is not None and not h.empty:
            h = _assign_subarea(
                h.dropna(subset=["obs_bottom_temp", "model_bottom_temp", "longitude"]), region)
            loaded.append((name, h))
    if not loaded:
        return
    has_split = region in _SUBAREA_LON_SPLIT
    years = sorted({int(y) for _, h in loaded for y in h["year"].unique()})
    if not years:
        return

    with st.container(border=True):
        section_title("Observed vs model, haul-by-haul")
        split_note = " Western and eastern hauls are coloured separately." if has_split else ""
        models_note = " One panel per model." if len(loaded) > 1 else ""
        st.caption(
            "Each point is a single survey haul: **observed** gear temperature (x) vs the **model** "
            "bottom temperature read at that haul's location and date (y). The dashed **1:1 line** is "
            "a perfect match — points **below** it mean the model ran colder than observed, **above** "
            f"warmer.{split_note}{models_note}"
        )
        coverage = {name: (int(h["year"].min()), int(h["year"].max())) for name, h in loaded}
        if len({c[1] for c in coverage.values()}) > 1:   # models end in different years
            spans = " · ".join(f"{n} {lo}–{hi}" for n, (lo, hi) in coverage.items())
            st.caption(f"⚠️ Model coverage differs: {spans}. A model has no points in years its "
                       "hindcast does not reach (the Bering10K hindcast currently ends in 2024; "
                       "MOM6 NEP runs to 2025), so a single recent year may show only one model.")
        if has_split:
            c0, c1, c2 = st.columns([1, 1, 1.4])
            sub_choice = c0.radio("Subarea", ["Combined", "Western", "Eastern"],
                                  key=f"scat_sub_{region}")
        else:
            sub_choice = "Combined"
            c1, c2 = st.columns([1, 1.4])
        mode = c1.radio("Years", ["Cumulative (start → year)", "Single year"],
                        key=f"scat_mode_{region}", horizontal=False)
        if mode == "Single year":
            yr = c2.selectbox("Year", years, index=len(years) - 1, key=f"scat_yr_{region}")
            ylo = yhi = yr
            label = str(yr)
        else:
            end = c2.select_slider("Include survey years up to", years, value=years[-1],
                                   key=f"scat_end_{region}")
            ylo, yhi = years[0], end
            label = f"{years[0]}–{end}"
        if sub_choice != "Combined":
            label = f"{sub_choice} · {label}"
        st.markdown(f"**{label}**")

        height = 520 if len(loaded) == 1 else 430
        panels = st.columns(len(loaded)) if len(loaded) > 1 else [None]
        for (name, h), col in zip(loaded, panels):
            sel = h[(h["year"] >= ylo) & (h["year"] <= yhi)]
            if sub_choice != "Combined":
                sel = sel[sel["subarea"] == sub_choice]
            if col is None:
                _model_scatter_panel(name, sel, has_split, height, coverage[name])
            else:
                with col:
                    _model_scatter_panel(name, sel, has_split, height, coverage[name])
        st.caption("Bias = model − observed, per haul (not area-weighted)."
                   + (" The pooled row is the haul-weighted mean over the selection." if has_split else ""))


def _modelled_only(region: str) -> None:
    """Model-only region view (Arctic: Chukchi/Beaufort) — no survey, so the continuous modelled
    shelf series is the only product, shown with a prominent unvalidated-here banner."""
    st.warning(
        "**Model-only region.** The Chukchi and Beaufort have no AFSC bottom-trawl survey, so there "
        "is no observed index, catch, or in-region validation here. The series below is the CEFI "
        "MOM6 NEP hindcast over the ≤ 200 m shelf — modelled conditions, not measurements, and "
        "unvalidated in this region."
    )
    _modelled_shelf_card(region)
    footer("Source: CEFI MOM6 NEP (NOAA GFDL / PSL) — modelled bottom temperature over the ≤ 200 m "
           "shelf (standalone-bathymetry/ETOPO mask). No in-region survey → model-only, unvalidated "
           "here. Lagged, not near-real-time.")


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

    # Model-only regions (Arctic: no survey, no observed) — distinct lean render.
    if reg.observed is None and not reg.has_survey_hauls:
        page_header("🧊", "Bottom Temperature", region_label(region),
                    f"{region_label(region)} ({region.upper()})",
                    caption="Modelled bottom-temperature conditions — model-only (no in-region survey).")
        _modelled_only(region)
        return

    # Only offer the models valid for this region (e.g. GOA is MOM6-only — Bering10K is out of
    # the Gulf domain). Bottom-temp regions default the survey-replication validation on.
    valid_labels = [lbl for lbl, sid in MODEL_SOURCES.items() if sid in reg.valid_sources]
    model_choices = st.sidebar.multiselect(
        "Validate model(s) against the survey", valid_labels,
        default=([] if is_cold_pool else valid_labels),
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
