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

# A distinct title icon per species (crabs vs the various fish).
SPECIES_ICONS = {
    "Snow crab": "🦀",
    "Red king crab": "🦀",     # rendered as a crowned crab in _title_icon_html
    "Pacific cod": "🐟",
    "Walleye pollock": "🐠",
    "Arrowtooth flounder": "🐡",
}


def _title_icon_html(label: str) -> str:
    """Inline icon for the page title. Red king crab gets a crown perched on top of a
    larger crab (no single 'crowned crab' glyph exists, so we layer two emoji with CSS)."""
    if label == "Red king crab":
        return (
            '<span style="position:relative; display:inline-block; line-height:1; '
            'font-size:1.2em; vertical-align:-0.08em;">🦀'
            '<span style="position:absolute; top:-0.14em; left:50%; '
            'transform:translateX(-50%); font-size:0.52em;">👑</span></span>'
        )
    return SPECIES_ICONS.get(label, "🎣")


@st.cache_data(show_spinner="Loading catch …", ttl=3600)
def load_catch(code: int) -> pd.DataFrame | None:
    p = RAW_DIR / f"catch_bottom_state_{code}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def _breakdown_table(dy: pd.DataFrame) -> pd.DataFrame:
    """Cold-pool vs warmer haul breakdown for one region/year: hauls, share, density, biomass."""
    total = dy["cpue_kgkm2"].sum()

    def row(sub: pd.DataFrame) -> dict:
        n = len(sub)
        return {
            "Hauls": n,
            "Share of hauls": f"{100 * n / len(dy):.0f}%" if len(dy) else "—",
            "Mean CPUE (kg/km²)": f"{sub['cpue_kgkm2'].mean():,.0f}" if n else "—",
            "Biomass share": f"{100 * sub['cpue_kgkm2'].sum() / total:.0f}%" if total else "—",
        }

    cold = dy[dy["bottom_temperature_c"] <= COLD_POOL_C]
    warm = dy[dy["bottom_temperature_c"] > COLD_POOL_C]
    return pd.DataFrame.from_dict(
        {"Cold pool (≤ 2 °C)": row(cold), "Warmer (> 2 °C)": row(warm), "All hauls": row(dy)},
        orient="index",
    )


def _styled_breakdown_html(dy: pd.DataFrame) -> str:
    """The breakdown table as a styled HTML table — dark borders, bold headers, tinted rows
    (cold = blue, warm = red, matching the map)."""
    df = _breakdown_table(dy)
    row_bg = {"Cold pool (≤ 2 °C)": "#e8f1fb", "Warmer (> 2 °C)": "#fdecea", "All hauls": "#f3f4f6"}
    sty = (
        df.style
        .apply(lambda r: [f"background-color:{row_bg.get(r.name, '')}"] * len(r), axis=1)
        .set_table_styles([
            {"selector": "", "props": [("border-collapse", "collapse"), ("border", "2px solid #2c3e50")]},
            {"selector": "th", "props": [("border", "1px solid #2c3e50"), ("padding", "8px 18px"),
                                         ("background-color", "#dfe6ee"), ("font-weight", "700"),
                                         ("font-size", "0.95rem"), ("text-align", "center"),
                                         ("color", "#1f2a36")]},
            {"selector": "td", "props": [("border", "1px solid #7b8a9a"), ("padding", "8px 18px"),
                                         ("text-align", "right"), ("font-size", "0.95rem")]},
            {"selector": "th.row_heading", "props": [("text-align", "left")]},
        ])
    )
    return sty.to_html()


def main() -> None:
    st.set_page_config(page_title="Catch × Bottom State", layout="wide", page_icon="🎣")

    st.sidebar.header("Controls")
    sp_label = st.sidebar.selectbox("Species", list(SPECIES_LABELS), index=0)
    code = SPECIES_LABELS[sp_label]

    df = load_catch(code)
    if df is None:
        st.markdown(f"## {_title_icon_html(sp_label)} {sp_label}", unsafe_allow_html=True)
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

    # ---- Top header: region · year · species, shown once above the first table ----
    st.markdown(f"## {_title_icon_html(sp_label)} {sp_label} · {region_label(region)} · {year}",
                unsafe_allow_html=True)

    # ---- Section 1: tabular summary (thermal partition for cold-pool regions) ----
    st.markdown(f"### {'Catch partitioned by thermal regime' if is_cold_pool else 'Catch summary'}")
    caught = int((dy["cpue_kgkm2"] > 0).sum())
    st.caption(f"{len(dy):,} survey hauls · {caught:,} caught {sp_label.lower()}.")
    if is_cold_pool:
        st.markdown(_styled_breakdown_html(dy), unsafe_allow_html=True)
        cold = dy[dy["bottom_temperature_c"] <= COLD_POOL_C]
        warm = dy[dy["bottom_temperature_c"] > COLD_POOL_C]
        cw = warm["cpue_kgkm2"].mean()
        if len(cold) and len(warm) and cw > 0:
            ratio = cold["cpue_kgkm2"].mean() / cw
            in_share = 100 * cold["cpue_kgkm2"].sum() / dy["cpue_kgkm2"].sum()
            haul_share = 100 * len(cold) / len(dy)
            st.caption(
                f"{sp_label} were **{ratio:.1f}× denser** in the cold pool — concentrating "
                f"**{in_share:.0f}%** of the biomass into **{haul_share:.0f}%** of the hauls."
            )
    else:
        st.caption(f"Mean CPUE **{dy['cpue_kgkm2'].mean():,.0f} kg/km²** "
                   f"(deep slope — no ≤ 2 °C cold pool to split on).")

    # ---- Section 2: density–temperature relationship ----
    st.markdown("### Catch density as a function of bottom temperature")
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

    # ---- Panel 2: map — bottom temperature (colour) × CPUE (marker size) ----
    # Same tile-basemap style as the live MHW Operational map (go.Scattermap on
    # open-street-map). Colour shows the thermal field (blue cold → red warm, diverging
    # around the 2 °C cold-pool line); marker size shows catch density.
    st.markdown("### Spatial co-distribution of catch and bottom temperature")
    cpue = dy["cpue_kgkm2"].to_numpy()
    cmax = float(max(cpue.max(), 1.0))
    size = 4 + 26 * np.sqrt(np.clip(cpue, 0, None) / cmax)   # sqrt scaling; zero-catch ≈ 4 px
    mfig = go.Figure(go.Scattermap(
        lat=dy["latitude"], lon=dy["longitude"], mode="markers",
        marker={"size": size, "color": dy["bottom_temperature_c"], "colorscale": "RdBu_r",
                "cmid": COLD_POOL_C, "opacity": 0.82,
                "colorbar": {"title": "Bottom<br>temp °C", "thickness": 15}},
        customdata=np.column_stack([dy["bottom_temperature_c"], cpue]),
        hovertemplate="%{lat:.2f}, %{lon:.2f}<br>bottom %{customdata[0]:.1f} °C<br>"
                      "CPUE %{customdata[1]:,.0f} kg/km²<extra></extra>"))
    mfig.update_layout(
        map={"style": "open-street-map",
             "center": {"lat": float(dy["latitude"].mean()), "lon": float(dy["longitude"].mean())},
             "zoom": 4.0},
        height=560, margin={"l": 0, "r": 0, "t": 10, "b": 0})
    st.plotly_chart(mfig, use_container_width=True)

    note = (" Snow crab is a cold-water specialist — in the eastern Bering it concentrates in the "
            "cold pool, so the biggest dots sit on the blue (cold) water." if code == 68580 and is_cold_pool else "")
    st.caption(
        "Each dot is a survey tow: **colour = bottom temperature** (blue cold → red warm, split at "
        "the 2 °C cold-pool line), **size = CPUE** (catch density, kg/km²; tiny dots are tows that "
        "caught little or none)." + note +
        " Source: NOAA **FOSS** AFSC bottom-trawl survey (`haul` ⟕ `catch` on `hauljoin`). "
        "Association is not mechanism — present as exploratory."
    )


main()
