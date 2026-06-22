"""Page 6 — Catch × Bottom State (Bering Sea survey catch).

The cheapest, most defensible bridge between the **physical** board (bottom temperature, the
cold pool) and the **biological** board (catch): they come from the *same hauls*. Every AFSC
bottom-trawl tow records both its bottom temperature and, per species, the catch (CPUE) at that
spot — joined on one key. **Snow crab is the headline** (a cold-water specialist): in the eastern
Bering it concentrates in the cold pool.

Observed-only · survey footprint (EBS / NBS / Slope) · annual · lagged · **exploratory, not
causal** (depth, substrate, prey co-vary with temperature). Build data with `mhw-fetch-catch
--species <code> --regions EBS NBS BSS`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.coldpool_data import list_bottom_state_regions, region_label
from mhw.bottom.regions import get_region
from mhw.fetch.foss_catch import cold_pool_summary

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
COLD_POOL_C = 2.0

# Dashboard region id -> FOSS survey code (the catch frame's `region` column).
REGION_TO_SRVY = {"ebs": "EBS", "nbs": "NBS", "slope": "BSS"}

# Pretty label -> FOSS species_code (headline first).
SPECIES_LABELS = {
    "Snow crab": 68580,
    "Red king crab": 69322,
    "Pacific cod": 21720,
    "Walleye pollock": 21740,
    "Arrowtooth flounder": 10110,
}


@st.cache_data(show_spinner="Loading catch …", ttl=3600)
def load_catch(code: int) -> pd.DataFrame | None:
    p = RAW_DIR / f"catch_bottom_state_{code}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def main() -> None:
    st.set_page_config(page_title="Catch × Bottom State", layout="wide", page_icon="🦀")

    st.sidebar.header("Controls")
    sp_label = st.sidebar.selectbox("Species", list(SPECIES_LABELS), index=0)
    code = SPECIES_LABELS[sp_label]

    st.title(f"🦀 Catch × Bottom State — {sp_label}")
    st.caption(
        "Survey catch (CPUE) paired with the **bottom temperature at the same haul**. "
        "Observed-only, survey footprint, annual, lagged — **exploratory, not causal**."
    )

    df = load_catch(code)
    if df is None:
        st.error(f"Catch not built for **{sp_label}**. Run: "
                 f"`mhw-fetch-catch --species {code} --regions EBS NBS BSS`")
        return

    bering = [r for r in list_bottom_state_regions() if r in REGION_TO_SRVY]
    if not bering:
        st.error("No Bering bottom-state regions built.")
        return
    region = st.sidebar.selectbox("Region", bering, format_func=str.upper, key="catch_region")
    srvy = REGION_TO_SRVY[region]
    is_cold_pool = get_region(region).product_kind == "cold_pool"

    d = df[(df["region"] == srvy) & df["bottom_temperature_c"].notna()].copy()
    if d.empty:
        st.warning(f"No {sp_label} catch records for {region.upper()}.")
        return
    years = sorted(int(y) for y in d["year"].unique())
    year = st.sidebar.select_slider("Year", years, value=years[-1])
    dy = d[d["year"] == year]

    # ---- Summary metrics ----
    summ = cold_pool_summary(d).query("year == @year")
    s = summ.iloc[0] if not summ.empty else None
    caught = int((dy["cpue_kgkm2"] > 0).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{region.upper()} {year} hauls", f"{len(dy):,}", help=f"{caught} with {sp_label.lower()}")
    if s is not None:
        c2.metric("Corr(bottom temp, CPUE)", f"{s['corr_bt_cpue']:+.2f}",
                  help="Negative ⇒ more catch where it is colder")
        if is_cold_pool:
            c3.metric("Biomass in cold pool (≤2 °C)", f"{100 * s['frac_biomass_in_band']:.0f}%",
                      help=f"{100 * s['frac_hauls_in_band']:.0f}% of hauls were ≤2 °C")
            ratio = (s["mean_cpue_in_band"] / s["mean_cpue_out_band"]) if s["mean_cpue_out_band"] else float("nan")
            c4.metric("Mean CPUE: cold ÷ warm", f"{ratio:.1f}×" if np.isfinite(ratio) else "—",
                      help=f"{s['mean_cpue_in_band']:,.0f} vs {s['mean_cpue_out_band']:,.0f} kg/km²")

    # ---- Panel 1: CPUE vs bottom temperature ----
    st.markdown(f"### Catch vs bottom temperature — {region_label(region)}, {year}")
    fig = go.Figure()
    if is_cold_pool:
        x0 = float(np.floor(d["bottom_temperature_c"].min()) - 0.5)
        fig.add_vrect(x0=x0, x1=COLD_POOL_C, fillcolor="steelblue", opacity=0.12, line_width=0,
                      annotation_text="cold pool ≤2 °C", annotation_position="top left",
                      annotation_font_size=11)
    fig.add_trace(go.Scatter(
        x=dy["bottom_temperature_c"], y=dy["cpue_kgkm2"], mode="markers",
        marker={"size": 7, "color": dy["cpue_kgkm2"], "colorscale": "Viridis",
                "showscale": False, "line": {"width": 0.5, "color": "white"}},
        hovertemplate="bottom temp %{x:.1f} °C<br>CPUE %{y:,.0f} kg/km²<extra></extra>"))
    fig.update_xaxes(title_text="Bottom temperature (°C)")
    fig.update_yaxes(title_text="CPUE (kg/km²)")
    fig.update_layout(height=440, template="plotly_white",
                      margin={"l": 70, "r": 20, "t": 20, "b": 50})
    st.plotly_chart(fig, use_container_width=True)

    # ---- Panel 2: CPUE map (cold-pool hauls highlighted) ----
    st.markdown(f"### Where it was caught — CPUE map, {region_label(region)} {year}")
    mfig = go.Figure()
    if is_cold_pool:
        cp = dy[dy["bottom_temperature_c"] <= COLD_POOL_C]
        mfig.add_trace(go.Scattergeo(
            lon=cp["longitude"], lat=cp["latitude"], mode="markers",
            marker={"size": 5, "color": "rgba(70,130,180,0.45)", "symbol": "circle"},
            name="cold-pool haul (≤2 °C)", hoverinfo="skip"))
    present = dy[dy["cpue_kgkm2"] > 0]
    mfig.add_trace(go.Scattergeo(
        lon=present["longitude"], lat=present["latitude"], mode="markers",
        marker={"size": 4 + 14 * (present["cpue_kgkm2"] / max(present["cpue_kgkm2"].max(), 1)) ** 0.5,
                "color": present["cpue_kgkm2"], "colorscale": "YlOrRd",
                "colorbar": {"title": "CPUE<br>kg/km²"}, "line": {"width": 0.3, "color": "gray"}},
        name=sp_label,
        hovertemplate="%{lat:.2f}, %{lon:.2f}<br>CPUE %{marker.color:,.0f} kg/km²<extra></extra>"))
    mfig.update_geos(lataxis_range=[53, 67], lonaxis_range=[-182, -155],
                     showland=True, landcolor="rgb(243,243,243)",
                     showocean=True, oceancolor="rgb(230,240,245)",
                     resolution=50, showcountries=True, countrycolor="white")
    mfig.update_layout(height=520, margin={"l": 0, "r": 0, "t": 10, "b": 0},
                       legend={"orientation": "h", "y": 0, "x": 0})
    st.plotly_chart(mfig, use_container_width=True)

    note = (" Snow crab is a cold-water specialist — in the eastern Bering it concentrates in the "
            "cold pool." if code == 68580 and is_cold_pool else "")
    st.caption(
        "CPUE = survey catch-per-unit-effort (kg/km²) at each tow; marker size/colour = CPUE. "
        + ("Blue dots mark hauls inside the ≤2 °C cold pool." if is_cold_pool else
           "This is a deep, non-cold-pool shelf — no ≤2 °C band shown.")
        + note +
        " Source: NOAA **FOSS** AFSC bottom-trawl survey (`haul` ⟕ `catch` on `hauljoin`). "
        "Association is not mechanism — present as exploratory."
    )


main()
