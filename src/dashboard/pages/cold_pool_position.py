"""Cold-Pool Position · Eastern Bering Sea — a first-class page for the *position* of the cold
pool (distinct from area, bottom temperature, and model validation).

It answers "where does the ≤ 2 °C cold pool reach, relative to history?" via the derived
**southern extent** indicator (5th-percentile latitude of cold locations — observed survey hauls,
with models for comparison). Page config / fonts are owned by the navigation shell; this script
renders the page body (EBS only). See the design in the approved plan note.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.coldpool_data import (
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
    ordinal_rank,
    percentile_rank,
    position_category,
)
from mhw.bottom.regions import EBS

REGION = "ebs"
GREEN, BLUE, AMBER = "#2e7d32", "#1565c0", "#b35900"
# Time-series display names (hindcast wording per the page design).
_TS_NAMES = {"Bering10K ROMS": "Bering10K (hindcast)", "CEFI MOM6 NEP": "MOM6-NEP (hindcast)"}

_CSS = """<style>
.cpp-sec { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;
    color:#1565c0; margin-bottom:0.5rem; }
.cpp-sec small { font-weight:400; color:#5f6b7a; text-transform:none; letter-spacing:0; }
.cpp-chip { border:1px solid rgba(130,130,130,0.35); border-radius:0.5rem; padding:0.35rem 0.75rem;
    font-size:0.92rem; color:#2b3a4a; background:rgba(130,130,130,0.06); white-space:nowrap; }
.cpp-grid { display:grid; grid-template-columns: 1fr 1fr 0.82fr; gap:0.55rem; margin-bottom:0.8rem; }
.cpp-kpi { border:1px solid rgba(130,130,130,0.25); border-radius:0.5rem; padding:0.65rem 0.8rem; }
.cpp-kpi-label { font-size:0.8rem; font-weight:600; color:#2b3a4a; }
.cpp-kpi-label small { font-weight:400; color:#5f6b7a; }
.cpp-kpi-val { font-size:1.65rem; font-weight:800; line-height:1.15; margin:0.1rem 0; }
.cpp-kpi-sub { font-size:0.74rem; color:#5f6b7a; }
.cpp-green { color:#2e7d32; } .cpp-blue { color:#1565c0; }
.cpp-diff { grid-column:3; grid-row:1 / span 2; display:flex; flex-direction:column;
    justify-content:center; align-items:center; text-align:center;
    background:rgba(130,130,130,0.05); }
.cpp-diff-top { font-size:0.78rem; color:#5f6b7a; }
.cpp-diff-arrow { font-size:1.5rem; line-height:1.1; }
.cpp-diff-val { font-size:1.5rem; font-weight:800; }
.cpp-callout { display:flex; gap:0.85rem; align-items:center; border:1px solid rgba(46,125,50,0.35);
    background:rgba(46,125,50,0.05); border-radius:0.6rem; padding:0.8rem 1rem; margin-bottom:0.4rem; }
.cpp-callout-icon { font-size:1.7rem; color:#2e7d32; }
.cpp-callout-txt { font-size:0.95rem; color:#2b3a4a; }
.cpp-analog { border:1px solid rgba(130,130,130,0.25); border-top:4px solid var(--ac);
    border-radius:0.5rem; padding:0.7rem 0.95rem; }
.cpp-analog-year { font-size:1.6rem; font-weight:800; color:var(--ac); }
.cpp-analog-dist { font-size:0.82rem; font-weight:600; color:var(--ac); }
.cpp-analog-row { font-size:0.78rem; color:#3a4a5a; margin-top:0.2rem; }
.cpp-about { border:1px solid rgba(130,130,130,0.25); border-radius:0.5rem; padding:0.7rem 0.95rem;
    background:rgba(130,130,130,0.04); font-size:0.84rem; color:#3a4a5a; }
.cpp-guidebtn { display:inline-block; border:1px solid rgba(130,130,130,0.4); border-radius:0.5rem;
    padding:0.5rem 1rem; color:#1565c0; text-decoration:none; font-weight:600; }
.cpp-footer { font-size:0.8rem; color:#7a8694; }
</style>"""
st.markdown(_CSS, unsafe_allow_html=True)


# --- Header ------------------------------------------------------------------------------
h_title, h_chip = st.columns([3, 1])
with h_title:
    st.title("🧊 Cold-Pool Position")
with h_chip:
    st.markdown("<div style='text-align:right; padding-top:1.1rem;'>"
                "<span class='cpp-chip'>Region: Eastern Bering Sea (EBS)</span></div>",
                unsafe_allow_html=True)
st.markdown("#### Cold-Pool Southern Extent — *where* the cold pool reaches")
st.markdown(
    "This page tracks how far south the ≤ 2 °C cold pool reaches each year, complementing the "
    "cold-pool **area** and **mean bottom temperature** indicators."
)

# --- Data --------------------------------------------------------------------------------
obs = load_observed_southern_extent(REGION)
area_df = load_observed(REGION)
models = {name: load_model(MODEL_SOURCES[name], REGION) for name in MODEL_SOURCES}
models = {n: m.dropna(subset=["southern_extent_lat"]).sort_values("year")
          for n, m in models.items()
          if m is not None and "southern_extent_lat" in m
          and m["southern_extent_lat"].notna().any()}

if obs is None and not models:
    st.info("The southern-extent indicator isn't built yet. Run `mhw-fetch-coldpool --region ebs` "
            "(observed) and `mhw-build-coldpool-model --region ebs` (models).")
    st.stop()

head_is_obs = obs is not None
df = obs if head_is_obs else next(iter(models.values()))
series = df["southern_extent_lat"]
yr = int(df.iloc[-1]["year"])
val = float(df.iloc[-1]["southern_extent_lat"])
span = f"{int(df['year'].min())}–{int(df['year'].max())}"
start_year = int(df["year"].min())
base = df.loc[(df["year"] >= BASELINE_START) & (df["year"] <= BASELINE_END), "southern_extent_lat"]
base_mean = float(base.mean()) if not base.empty else float("nan")
diff = val - base_mean if pd.notna(base_mean) else float("nan")
pct = percentile_rank(val, series)
category = position_category(pct)
if pct >= 50:
    rank, rank_word = ordinal_rank(val, series, smallest=False), "farthest north"
else:
    rank, rank_word = ordinal_rank(val, series, smallest=True), "farthest south"
north = pd.notna(diff) and diff >= 0
diff_word = "farther north" if north else "farther south"
diff_color = GREEN if north else AMBER
diff_arrow = "↑" if north else "↓"

# Analog years: joint similarity in z-scored [southern extent, cold-pool area]; capture distances.
analog_rows: list[tuple[int, float, float, float | None]] = []
if area_df is not None and "area_lte2_km2" in area_df.columns:
    m = (df.merge(area_df[["year", "area_lte2_km2"]], on="year", how="inner")
         .dropna(subset=["southern_extent_lat", "area_lte2_km2"]))
    if len(m) >= 4:
        e, a, yy = (m["southern_extent_lat"].to_numpy(), m["area_lte2_km2"].to_numpy(),
                    m["year"].to_numpy())
        ze = (e - e.mean()) / (e.std() or 1.0)
        za = (a - a.mean()) / (a.std() or 1.0)
        ti = np.where(yy == yr)[0]
        if len(ti):
            t = ti[0]
            d = np.sqrt((ze - ze[t]) ** 2 + (za - za[t]) ** 2)
            order = [i for i in np.argsort(d) if yy[i] != yr][:3]
            analog_rows = [(int(yy[i]), float(d[i]), float(e[i]), float(a[i])) for i in order]


# --- Top section: Key indicators | Map ---------------------------------------------------
left, right = st.columns([1, 1])

with left:
    with st.container(border=True):
        st.markdown("<div class='cpp-sec'>Key indicators <small>(Observed)</small></div>",
                    unsafe_allow_html=True)
        mean_txt = f"{base_mean:.2f}° N" if pd.notna(base_mean) else "—"
        diff_html = (
            "<div class='cpp-kpi cpp-diff'>"
            "<div class='cpp-diff-top'>Difference from<br>1991–2020 mean</div>"
            f"<div class='cpp-diff-arrow' style='color:{diff_color}'>{diff_arrow}</div>"
            f"<div class='cpp-diff-val' style='color:{diff_color}'>{diff:+.2f}°</div>"
            f"<div class='cpp-kpi-sub'>{diff_word}</div></div>"
        ) if pd.notna(diff) else "<div class='cpp-kpi cpp-diff'><div class='cpp-diff-top'>—</div></div>"
        st.markdown(
            f"<div class='cpp-grid'>"
            f"<div class='cpp-kpi'><div class='cpp-kpi-label'>Current southern extent "
            f"<small>({yr})</small></div><div class='cpp-kpi-val cpp-green'>{val:.2f}° N</div>"
            f"<div class='cpp-kpi-sub'>Latest observed year</div></div>"
            f"<div class='cpp-kpi'><div class='cpp-kpi-label'>Historical mean position "
            f"<small>({BASELINE_START}–{BASELINE_END})</small></div>"
            f"<div class='cpp-kpi-val'>{mean_txt}</div><div class='cpp-kpi-sub'>&nbsp;</div></div>"
            f"{diff_html}"
            f"<div class='cpp-kpi'><div class='cpp-kpi-label'>Percentile "
            f"<small>(since {start_year})</small></div><div class='cpp-kpi-val cpp-blue'>"
            f"{pct:.0f}th</div><div class='cpp-kpi-sub'>{category.lower()}</div></div>"
            f"<div class='cpp-kpi'><div class='cpp-kpi-label'>Historical rank</div>"
            f"<div class='cpp-kpi-val cpp-blue'>{ordinal(rank)}</div>"
            f"<div class='cpp-kpi-sub'>{rank_word} since {start_year}</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        src = "observed cold pool" if head_is_obs else "modelled cold pool"
        st.markdown(
            "<div class='cpp-callout'><div class='cpp-callout-icon'>↑</div>"
            f"<div class='cpp-callout-txt'><b>{category}</b> — in {yr} the {src} reached about "
            f"<b>{val:.2f}° N</b>, <b style='color:{diff_color}'>{abs(diff):.2f}° {diff_word}</b> "
            f"than typical, the <b>{ordinal(rank)} {rank_word}</b> since {start_year}.</div></div>",
            unsafe_allow_html=True,
        )
        if analog_rows:
            st.caption("Most similar years (by position and cold-pool area): "
                       + ", ".join(str(y) for y, *_ in analog_rows) + ".")

with right:
    with st.container(border=True):
        st.markdown("<div class='cpp-sec'>Where the cold pool reaches</div>",
                    unsafe_allow_html=True)
        lon_w, lon_e = EBS.lon_min + 0.5, EBS.lon_max - 0.5
        mfig = go.Figure()
        fp = load_survey_footprint(REGION)
        if fp is not None:
            lon_r, lat_r = fp
            mfig.add_trace(go.Scattergeo(lon=lon_r, lat=lat_r, mode="lines",
                           line={"color": "rgba(90,90,90,0.7)", "width": 1.3},
                           name="EBS shelf (0–200 m)", hoverinfo="skip"))
        if pd.notna(base_mean):
            mfig.add_trace(go.Scattergeo(lon=[lon_w, lon_e], lat=[base_mean, base_mean],
                           mode="lines", line={"color": BLUE, "width": 2.5},
                           name=f"Historical mean southern extent ({BASELINE_START}–{BASELINE_END})"))
            mfig.add_trace(go.Scattergeo(lon=[lon_e - 1.0], lat=[base_mean - 0.45], mode="text",
                           text=[f"<b>{base_mean:.2f}°N</b>"], textposition="middle center",
                           textfont={"color": BLUE, "size": 13}, showlegend=False, hoverinfo="skip"))
        mfig.add_trace(go.Scattergeo(lon=[lon_w, lon_e], lat=[val, val], mode="lines",
                       line={"color": GREEN, "width": 3.5}, name=f"Current southern extent ({yr})"))
        mfig.add_trace(go.Scattergeo(lon=[lon_e - 1.0], lat=[val + 0.45], mode="text",
                       text=[f"<b>{val:.2f}°N</b>"], textposition="middle center",
                       textfont={"color": GREEN, "size": 13}, showlegend=False, hoverinfo="skip"))
        # Degree tick labels (geo subplots don't render graticule labels) — small text in the
        # ocean margins, aligned with the 1° lat / 5° lon gridlines.
        lat_ticks = [54, 55, 56, 57, 58, 59, 60]
        lon_ticks = [-175, -170, -165, -160]
        mfig.add_trace(go.Scattergeo(lon=[-177.6] * len(lat_ticks), lat=lat_ticks, mode="text",
                       text=[f"<b>{t}°N</b>" for t in lat_ticks],
                       textfont={"size": 11, "color": "#1f2a36"},
                       showlegend=False, hoverinfo="skip"))
        mfig.add_trace(go.Scattergeo(lon=lon_ticks, lat=[53.5] * len(lon_ticks), mode="text",
                       text=[f"<b>{abs(t)}°W</b>" for t in lon_ticks],
                       textfont={"size": 11, "color": "#1f2a36"},
                       showlegend=False, hoverinfo="skip"))
        mfig.update_geos(
            resolution=50, projection_type="mercator",
            lataxis={"range": [53.0, 61.0], "showgrid": True, "gridcolor": "rgba(150,150,150,0.3)", "dtick": 1},
            lonaxis={"range": [-178.7, -156.5], "showgrid": True, "gridcolor": "rgba(150,150,150,0.3)", "dtick": 5},
            showland=True, landcolor="#e9e2d3", showocean=True, oceancolor="#cfe3f2",
            showcoastlines=True, coastlinecolor="#9aa7b5", coastlinewidth=0.8,
            showlakes=False, showrivers=False)
        mfig.update_layout(height=430, margin={"l": 0, "r": 0, "t": 6, "b": 0},
                           legend={"orientation": "h", "y": -0.02, "yanchor": "top", "x": 0,
                                   "xanchor": "left", "font": {"size": 11}})
        st.plotly_chart(mfig, use_container_width=True)
        st.caption(
            "The lines are a **derived position indicator** (the southern reach of the ≤ 2 °C cold "
            "pool), **not** a literal 2 °C isotherm. The outline is the AFSC survey footprint. "
            "Higher (farther north) = a northward-contracted cold pool."
        )


# --- Time series -------------------------------------------------------------------------
ts_h, ts_t = st.columns([3, 1])
with ts_h:
    st.markdown("<div class='cpp-sec'>Southern extent through time</div>", unsafe_allow_html=True)
with ts_t:
    show = st.segmented_control("Show", ["All", "Observed", "Models"], default="All",
                                key="sext_show", label_visibility="collapsed") or "All"

fig = go.Figure()
if pd.notna(base_mean) and not base.empty:
    p10, p90 = float(np.percentile(base, 10)), float(np.percentile(base, 90))
    x0 = int(min([df["year"].min()] + [m["year"].min() for m in models.values()] or [start_year]))
    x1 = int(max([df["year"].max()] + [m["year"].max() for m in models.values()] or [yr]))
    fig.add_trace(go.Scatter(x=[x0, x1, x1, x0], y=[p10, p10, p90, p90], fill="toself",
                  fillcolor="rgba(130,130,130,0.15)", line={"width": 0}, hoverinfo="skip",
                  name="1991–2020 range (10th–90th pct)"))
    fig.add_hline(y=base_mean, line_color="rgba(90,90,90,0.7)", line_width=1.2,
                  annotation_text="1991–2020 mean", annotation_font_size=9)
if show in ("All", "Models"):
    for name, m in models.items():
        color = "#1f77b4" if "Bering" in name else "#e8820c"
        fig.add_trace(go.Scatter(x=m["year"], y=m["southern_extent_lat"], mode="lines",
                      name=_TS_NAMES[name], line={"color": color, "width": 1.8, "dash": "dash"}))
if obs is not None and show in ("All", "Observed"):
    fig.add_trace(go.Scatter(x=obs["year"], y=obs["southern_extent_lat"], mode="lines+markers",
                  name="Observed (AFSC surveys)",
                  line={"color": "black", "width": 2}, marker={"size": 5, "color": "black"}))
fig.update_yaxes(title_text="Southern extent (°N) — Higher = farther north", range=[55, 61])
fig.update_xaxes(title_text="Year")
fig.update_layout(height=380, template="plotly_white",
                  margin={"l": 70, "r": 20, "t": 10, "b": 40},
                  legend={"orientation": "h", "y": -0.18, "yanchor": "top", "x": 0, "xanchor": "left"})
st.plotly_chart(fig, use_container_width=True)


# --- Analog years ------------------------------------------------------------------------
st.markdown("<div class='cpp-sec'>Most similar historical years "
            "<small>(by southern extent &amp; cold-pool area)</small></div>", unsafe_allow_html=True)
st.caption("Years with similar cold-pool position and size (z-scored Euclidean distance).")
ac1, ac2, ac3, ac4 = st.columns([1, 1, 1, 0.95])
_accent = [GREEN, BLUE, AMBER]
for col, accent, row in zip((ac1, ac2, ac3), _accent, analog_rows):
    ay, adist, aext, aarea = row
    area_txt = f"{aarea:,.0f} km²" if aarea is not None and pd.notna(aarea) else "n/a"
    with col:
        st.markdown(
            f"<div class='cpp-analog' style='--ac:{accent}'>"
            f"<div class='cpp-analog-year'>{ay}</div>"
            f"<div class='cpp-analog-dist'>Distance: {adist:.2f}</div>"
            f"<div class='cpp-analog-row'>Extent: {aext:.2f}° N&nbsp;&nbsp;|&nbsp;&nbsp;Area: {area_txt}</div>"
            "</div>", unsafe_allow_html=True)
with ac4:
    st.markdown(
        "<div class='cpp-about'><b>About analogs</b><br>Analog years match both southern extent "
        "and cold-pool area (z-scored). If area is unavailable, analogs are based on extent only."
        "</div>", unsafe_allow_html=True)


# --- Methods + footer --------------------------------------------------------------------
st.divider()
m_txt, m_btn = st.columns([3, 1])
with m_txt:
    st.markdown("<div class='cpp-sec'>Methods <small>(brief)</small></div>", unsafe_allow_html=True)
    st.markdown(
        "Southern extent is a derived indicator defined as the 5th-percentile latitude of ≤ 2 °C "
        "cold-pool locations on the eastern Bering Sea shelf. Observed values are based on AFSC "
        "summer survey hauls (read from NOAA FOSS); model values on gridded shelf cells (Bering10K "
        "and MOM6-NEP). It is **not** an official ESR metric."
    )
with m_btn:
    st.markdown("<div style='padding-top:1.6rem;'><a class='cpp-guidebtn' target='_self' "
                "href='/bering_bottom_state_guide'>Learn more in the guide →</a></div>",
                unsafe_allow_html=True)

st.divider()
f1, f2 = st.columns([2, 1])
f1.markdown("<div class='cpp-footer'>Data sources: observed extent from AFSC bottom-trawl survey "
            "hauls via NOAA FOSS; model extent from Bering10K ROMS (NOAA PMEL / UW ACLIM) and "
            "CEFI MOM6-NEP (NOAA GFDL / PSL).</div>", unsafe_allow_html=True)
f2.markdown(f"<div class='cpp-footer' style='text-align:right'>Derived position indicator · "
            f"latest survey {yr}</div>", unsafe_allow_html=True)
