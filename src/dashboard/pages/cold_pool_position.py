"""Cold-Pool Position · Eastern Bering Sea — a first-class page for the *position* of the cold
pool (distinct from area, bottom temperature, and model validation).

It answers "where does the ≤ 2 °C cold pool reach, relative to history?" via the derived
**southern extent** indicator (5th-percentile latitude of cold locations — observed survey hauls,
with models for comparison). Page config / fonts are owned by the navigation shell; this script
renders the page body (EBS only — the cold pool's southern boundary is an EBS concept).
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.coldpool_data import (
    MODEL_COLORS,
    MODEL_SOURCES,
    load_model,
    load_observed,
    load_observed_southern_extent,
    load_survey_footprint,
    ordinal,
)
from mhw.bottom.indicators import (
    BASELINE_END,
    BASELINE_START,
    analog_years,
    anomaly,
    direction_phrase,
    ordinal_rank,
    percentile_rank,
    position_category,
)
from mhw.bottom.regions import EBS

REGION = "ebs"

st.title("🧊 Cold-Pool Position · Eastern Bering Sea")
st.markdown("#### Cold-Pool Southern Extent — *where* the cold pool reaches")
st.markdown(
    "This page tracks how far south the ≤ 2 °C cold pool reaches each year, complementing the "
    "cold-pool **area** and **mean bottom temperature** indicators on the Cold Pool & Bottom "
    "Temperature page."
)

obs = load_observed_southern_extent(REGION)
models = {name: load_model(MODEL_SOURCES[name], REGION) for name in MODEL_SOURCES}
models = {n: m.dropna(subset=["southern_extent_lat"]).sort_values("year")
          for n, m in models.items()
          if m is not None and "southern_extent_lat" in m
          and m["southern_extent_lat"].notna().any()}

if obs is None and not models:
    st.info("The southern-extent indicator isn't built yet. Run `mhw-fetch-coldpool --region ebs` "
            "(observed) and `mhw-build-coldpool-model --region ebs` (models).")
    st.stop()

# Headline = observed survey (ground truth) when available; otherwise fall back to a model.
if obs is not None:
    head_label, df = "observed cold pool", obs
else:
    head_label, (_, df) = "modelled cold pool", next(iter(models.items()))
series = df["southern_extent_lat"]
latest = df.iloc[-1]
yr = int(latest["year"])
val = float(latest["southern_extent_lat"])
span = f"{int(df['year'].min())}–{int(df['year'].max())}"
base = df.loc[(df["year"] >= BASELINE_START) & (df["year"] <= BASELINE_END), "southern_extent_lat"]
base_mean = float(base.mean()) if not base.empty else float("nan")
anom = anomaly(val, base) if not base.empty else float("nan")
pct = percentile_rank(val, series)
category = position_category(pct)
phrase = direction_phrase(anom)
start_year = int(df["year"].min())
if pct >= 50:
    rank, rank_word = ordinal_rank(val, series, smallest=False), "farthest north"
else:
    rank, rank_word = ordinal_rank(val, series, smallest=True), "farthest south"
rank_phrase = f"{ordinal(rank)} {rank_word} since {start_year}"

# --- KPI section --------------------------------------------------------------------------
r1c1, r1c2 = st.columns(2)
r1c1.metric(f"{yr} southern extent", f"{val:.1f} °N",
            delta=(phrase if pd.notna(anom) else None), delta_color="off")
r1c2.metric(f"Historical mean position ({BASELINE_START}–{BASELINE_END})",
            f"{base_mean:.1f} °N" if pd.notna(base_mean) else "—")
r2c1, r2c2 = st.columns(2)
r2c1.metric(f"Percentile ({span})", f"{pct:.0f}th")
r2c2.metric(f"Rank — {rank_word}", f"{ordinal(rank)} of {len(series)}", help=f"{rank_phrase}.")

eco = ("a northward-contracted cold pool, reducing southern cold-water habitat" if pct >= 70
       else "a southward-expanded cold pool" if pct <= 30
       else "a near-typical cold-pool position")
st.markdown(
    f"**{category}** — in {yr} the {head_label} reached about **{val:.1f} °N**, **{phrase}** "
    f"({ordinal(int(round(pct)))} percentile of the {span} record), indicating {eco}."
)

# Analog years: joint similarity in [southern extent, cold-pool area] (z-scored) so analogs match
# cold-pool position AND size. Falls back to extent-only if area is unavailable.
if obs is not None:
    area_src = load_observed(REGION)
    amerge = (df.merge(area_src[["year", "area_lte2_km2"]], on="year", how="inner")
              if area_src is not None and "area_lte2_km2" in area_src.columns else None)
else:
    amerge = df if "area_lte2_km2" in df.columns else None
if amerge is not None and amerge["area_lte2_km2"].notna().sum() >= 3:
    analogs = analog_years(yr, amerge["year"].values, amerge["southern_extent_lat"].values,
                           amerge["area_lte2_km2"].values, k=3)
    analog_caption = "Most similar years (by position and cold-pool area): "
else:
    analogs = analog_years(yr, df["year"].values, series.values, k=3)
    analog_caption = "Most similar years (by southern extent): "
if analogs:
    st.caption(analog_caption + ", ".join(str(a) for a in analogs) + ".")

# --- Map: survey-footprint outline + current vs historical-mean southern-extent lines ------
st.markdown("##### Position on the shelf")
lon_w, lon_e = EBS.lon_min + 0.5, EBS.lon_max - 0.5
mfig = go.Figure()
fp = load_survey_footprint(REGION)
if fp is not None:
    lon_r, lat_r = fp
    mfig.add_trace(go.Scattermap(lon=lon_r, lat=lat_r, mode="lines", fill="toself",
                   fillcolor="rgba(120,120,120,0.06)", line={"color": "rgba(90,90,90,0.5)", "width": 1},
                   name="Survey footprint", hoverinfo="skip"))
if pd.notna(base_mean):
    mfig.add_trace(go.Scattermap(lon=[lon_w, lon_e], lat=[base_mean, base_mean], mode="lines",
                   line={"color": "#555", "width": 2},
                   name=f"Historical mean southern extent ({BASELINE_START}–{BASELINE_END})"))
mfig.add_trace(go.Scattermap(lon=[lon_w, lon_e], lat=[val, val], mode="lines",
               line={"color": "firebrick", "width": 4}, name=f"Current southern extent ({yr})"))
mfig.update_layout(
    map={"style": "open-street-map", "center": {"lat": 58.3, "lon": -167.5}, "zoom": 3.7},
    height=480, margin={"l": 0, "r": 0, "t": 10, "b": 0}, font={"size": 14},
    legend={"orientation": "h", "y": 0.99, "yanchor": "top", "x": 0.01, "xanchor": "left",
            "bgcolor": "rgba(255,255,255,0.75)"})
st.plotly_chart(mfig, use_container_width=True)
st.caption(
    "The lines are a **derived position indicator** (the southern reach of the ≤ 2 °C cold pool), "
    "**not** a literal 2 °C isotherm. The shaded outline is the AFSC survey footprint. Higher "
    "(farther north) = a northward-contracted cold pool."
)

# --- Historical time series ---------------------------------------------------------------
st.markdown("##### Southern extent through time")
fig = go.Figure()
if obs is not None:
    fig.add_trace(go.Scatter(x=obs["year"], y=obs["southern_extent_lat"], mode="lines+markers",
                  name="Observed (survey)", line={"color": "black", "width": 2}))
for name, m in models.items():
    fig.add_trace(go.Scatter(x=m["year"], y=m["southern_extent_lat"], mode="lines+markers",
                  name=name, line={"color": MODEL_COLORS.get(name, "gray"), "width": 2, "dash": "dash"}))
if pd.notna(base_mean):
    fig.add_hline(y=base_mean, line_dash="dot", line_color="gray", line_width=1,
                  annotation_text=f"{BASELINE_START}–{BASELINE_END} mean", annotation_font_size=9)
fig.update_yaxes(title_text="Southern extent (°N) — higher = farther north")
fig.update_layout(height=380, template="plotly_white",
                  margin={"l": 70, "r": 20, "t": 30, "b": 40},
                  legend={"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "xanchor": "left"})
st.plotly_chart(fig, use_container_width=True)

# --- Methods note -------------------------------------------------------------------------
st.caption(
    "**Method.** Southern extent is a derived indicator defined as the 5th-percentile latitude of "
    "≤ 2 °C cold-pool locations on the eastern Bering Sea shelf — observed from survey hauls, "
    "models from gridded shelf cells (same definition, different sampling). It is **not** an "
    "official ESR metric; the definition is swappable. Descriptive of past state, not a forecast."
)
