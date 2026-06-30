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

from dashboard.components.bottom_ui import (
    BLUE,
    callout,
    footer,
    inject_css,
    page_header,
    section_title,
    styled_table,
    when_note,
)
from dashboard.components.coldpool_data import list_bottom_state_regions, region_label
from mhw.bottom.regions import get_region

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
COLD_POOL_C = 2.0

# Sequential blue for bottom temperature: the colder, the deeper the blue (low temp = deep
# navy, high temp = pale blue). A smooth gradient — no hard split at the cold-pool line.
TEMP_COLORSCALE = [[0.0, "#08306b"], [0.45, "#3b7bbf"], [1.0, "#dceaf7"]]

# Dashboard region id -> FOSS survey code (the catch frame's `region` column).
REGION_TO_SRVY = {"sebs": "EBS", "nbs": "NBS", "slope": "BSS", "goa": "GOA", "ai": "AI"}

# ESR subareas selectable on the catch page (to match the SST subareas). Each is the parent
# survey's hauls clipped to the subarea's ESR polygon (point-in-polygon; the polygons live in
# config/regions.geojson, antimeridian-split for the Aleutians). No re-fetch — the hauls already
# carry lat/lon. Listed after their parent in the region dropdown.
CATCH_SUBAREAS = {"goa": ["wgoa", "egoa"], "ai": ["ai_west", "ai_central", "ai_east"]}
SUBAREA_PARENT = {s: p for p, subs in CATCH_SUBAREAS.items() for s in subs}
SUBAREA_LABELS = {
    "wgoa": "Western Gulf of Alaska", "egoa": "Eastern Gulf of Alaska",
    "ai_west": "Western Aleutians", "ai_central": "Central Aleutians", "ai_east": "Eastern Aleutians",
}
_REGIONS_GEOJSON = ROOT / "config" / "regions.geojson"


@st.cache_resource(show_spinner=False)
def _subarea_polygon(region: str):
    """Shapely polygon for a catch subarea, from config/regions.geojson (cached)."""
    import json
    from shapely.geometry import shape
    fc = json.loads(_REGIONS_GEOJSON.read_text())
    for f in fc["features"]:
        if f["properties"]["id"] == region:
            return shape(f["geometry"])
    return None


def _srvy_for(region: str) -> str:
    """FOSS survey code for a region or subarea (subareas inherit their parent survey)."""
    return REGION_TO_SRVY.get(region) or REGION_TO_SRVY[SUBAREA_PARENT[region]]


def _catch_region_label(region: str) -> str:
    """Grouped dropdown label: subareas indented under their parent ecosystem area."""
    if region in SUBAREA_LABELS:
        return f"   · {SUBAREA_LABELS[region]}"
    return region_label(region)


def _with_subareas(regions: list[str], group: str) -> list[str]:
    """Insert each ecosystem area's ESR subareas right after it in the region list."""
    out: list[str] = []
    for r in regions:
        out.append(r)
        out.extend(CATCH_SUBAREAS.get(r, []))
    return out


def _clip_to_subarea(d: pd.DataFrame, region: str) -> pd.DataFrame:
    """Keep only hauls whose (lon, lat) fall inside the subarea polygon (no-op for whole areas)."""
    if region not in SUBAREA_PARENT:
        return d
    poly = _subarea_polygon(region)
    if poly is None:
        return d
    import shapely
    inside = shapely.contains_xy(poly, d["longitude"].to_numpy(), d["latitude"].to_numpy())
    return d[inside]

# Per-group key species (pretty label -> FOSS species_code, headline first). The Bering leads
# with the cold-water crabs (the cold-pool story); the Gulf of Alaska — no cold pool — leads
# with its groundfish (Pacific cod, pollock, sablefish, arrowtooth, Pacific ocean perch).
SPECIES_BY_GROUP: dict[str, dict[str, int]] = {
    "bering": {
        "Snow crab": 68580,
        "Red king crab": 69322,
        "Pacific cod": 21720,
        "Walleye pollock": 21740,
        "Arrowtooth flounder": 10110,
    },
    "goa": {
        "Pacific cod": 21720,
        "Walleye pollock": 21740,
        "Sablefish": 20510,
        "Arrowtooth flounder": 10110,
        "Pacific ocean perch": 30060,
    },
    "ai": {
        "Atka mackerel": 21921,
        "Pacific ocean perch": 30060,
        "Pacific cod": 21720,
    },
}

# A distinct title icon per species (crabs vs the various fish; fish fall back to 🎣).
SPECIES_ICONS = {
    "Snow crab": "🦀",
    "Red king crab": "🦀",     # rendered as a crowned crab in _title_icon_html
    "Pacific cod": "🐟",
    "Walleye pollock": "🐠",
    "Arrowtooth flounder": "🐡",
    "Sablefish": "🐟",
    "Pacific ocean perch": "🐠",
    "Atka mackerel": "🐟",
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


def _fmt_cpue(v: float) -> str:
    """Format a mean CPUE. Integers for ≥1, but show significant figures when the value is
    positive yet would round to a misleading 0 (e.g. 0.38 kg/km² on the deep slope)."""
    if not np.isfinite(v):
        return "—"
    if v == 0:
        return "0"
    if round(v) == 0:
        return f"{v:.2g}"          # positive but rounds to 0 at integer precision
    return f"{v:,.0f}"


def _breakdown_table(dy: pd.DataFrame) -> pd.DataFrame:
    """Cold-pool vs warmer haul breakdown for one region/year: hauls, share, density, biomass."""
    total = dy["cpue_kgkm2"].sum()

    def row(sub: pd.DataFrame) -> dict:
        n = len(sub)
        return {
            "Hauls": n,
            "Share of hauls": f"{100 * n / len(dy):.0f}%" if len(dy) else "—",
            "Biomass share": f"{100 * sub['cpue_kgkm2'].sum() / total:.0f}%" if total else "—",
            "Mean CPUE (kg/km²)": _fmt_cpue(sub["cpue_kgkm2"].mean()) if n else "—",
        }

    cold = dy[dy["bottom_temperature_c"] <= COLD_POOL_C]
    warm = dy[dy["bottom_temperature_c"] > COLD_POOL_C]
    return pd.DataFrame.from_dict(
        {"Cold pool (≤ 2 °C)": row(cold), "Warmer (> 2 °C)": row(warm), "All hauls": row(dy)},
        orient="index",
    )


def _styled_breakdown_html(dy: pd.DataFrame) -> str:
    """Cold/warm/all breakdown table, rows tinted (cold = blue, warm = red) to match the map."""
    row_bg = {"Cold pool (≤ 2 °C)": "#e8f1fb", "Warmer (> 2 °C)": "#fdecea", "All hauls": "#f3f4f6"}
    return styled_table(_breakdown_table(dy), row_bg)


def _slope_summary_html(dy: pd.DataFrame) -> str:
    """One-row catch summary for non-cold-pool regions (slope), in the same table design."""
    df = pd.DataFrame.from_dict(
        {"All hauls": {"Hauls": f"{len(dy):,}",
                       "Caught": f"{int((dy['cpue_kgkm2'] > 0).sum()):,}",
                       "Mean CPUE (kg/km²)": _fmt_cpue(dy["cpue_kgkm2"].mean())}},
        orient="index",
    )
    return styled_table(df, {"All hauls": "#f3f4f6"})


def render(group: str = "bering") -> None:
    """Render the Catch × Bottom State page for one geographic group (page config/fonts are
    owned by the navigation shell)."""
    inject_css()
    st.sidebar.header("Controls")
    regions = [r for r in list_bottom_state_regions(group) if r in REGION_TO_SRVY]
    if not regions:
        st.error("No survey-catch regions built for this group.")
        return
    regions = _with_subareas(regions, group)   # GOA→W/E, AI→W/C/E (ESR subareas)
    region = st.sidebar.selectbox("Region", regions, format_func=_catch_region_label,
                                  key="catch_region")
    srvy = _srvy_for(region)
    # Subareas of GOA/AI are bottom-temperature (no cold pool); only true cold-pool regions split warm/cold.
    is_cold_pool = region in REGION_TO_SRVY and get_region(region).product_kind == "cold_pool"

    species = SPECIES_BY_GROUP.get(group, SPECIES_BY_GROUP["bering"])
    sp_label = st.sidebar.selectbox("Species", list(species), index=0)
    code = species[sp_label]
    _name = SUBAREA_LABELS.get(region, region_label(region))
    chip = f"{_name} ({region.upper()})"
    cap = ("Explore how key species' catch relates to bottom-temperature conditions — AFSC "
           "bottom-trawl survey (observed; exploratory, not causal).")

    df = load_catch(code)
    if df is None:
        page_header(_title_icon_html(sp_label), "Catch × Bottom State", sp_label, chip, caption=cap)
        st.error(f"Catch not built for **{sp_label}**. Run: "
                 f"`mhw-fetch-catch --species {code} --regions {srvy}`")
        return

    d = df[(df["region"] == srvy) & df["bottom_temperature_c"].notna()].copy()
    d = _clip_to_subarea(d, region)   # ESR subarea: keep only hauls inside the subarea polygon
    if d.empty:
        page_header(_title_icon_html(sp_label), "Catch × Bottom State", sp_label, chip, caption=cap)
        st.warning(f"No {sp_label} catch records for {_name}.")
        return
    years = sorted(int(y) for y in d["year"].unique())
    year = st.sidebar.select_slider("Year", years, value=years[-1])
    dy = d[d["year"] == year]

    page_header(_title_icon_html(sp_label), "Catch × Bottom State",
                f"{sp_label} · {_name} · {year}", chip, caption=cap)

    corr = dy["bottom_temperature_c"].corr(dy["cpue_kgkm2"])
    corr_txt = f"corr(CPUE, °C) = {corr:+.2f}" if pd.notna(corr) else None

    # ---- Section 1: tabular summary (thermal partition for cold-pool regions) ----
    with st.container(border=True):
        section_title("Catch partitioned by thermal regime"
                      + (" (≤ 2 °C threshold)" if is_cold_pool else "") if is_cold_pool
                      else "Catch summary")
        when_note("The selected year's <b>summer bottom-trawl survey</b> hauls — catch and bottom "
                  "temperature recorded on the <b>same tow</b> (so each pairing is exact).")
        st.caption("All catch values are **CPUE** — survey catch *density* (kg/km² swept), a "
                   "relative abundance index. It is **not** total stock biomass or commercial "
                   "landings: the population over the whole shelf is far larger and depends on the "
                   "stock's area and survey catchability.")
        if is_cold_pool:
            caught = int((dy["cpue_kgkm2"] > 0).sum())
            st.caption(f"{len(dy):,} survey hauls · {caught:,} caught {sp_label.lower()}.")
            st.markdown(_styled_breakdown_html(dy), unsafe_allow_html=True)
            cold = dy[dy["bottom_temperature_c"] <= COLD_POOL_C]
            warm = dy[dy["bottom_temperature_c"] > COLD_POOL_C]
            cw = warm["cpue_kgkm2"].mean()
            if len(cold) and len(warm) and cw > 0:
                ratio = cold["cpue_kgkm2"].mean() / cw
                in_share = 100 * cold["cpue_kgkm2"].sum() / dy["cpue_kgkm2"].sum()
                haul_share = 100 * len(cold) / len(dy)
                callout(
                    f"{sp_label} were <b>{ratio:.1f}× denser</b> in the cold pool — concentrating "
                    f"<b>{in_share:.0f}%</b> of the biomass into <b>{haul_share:.0f}%</b> of the hauls.",
                    icon="🦀", tint=BLUE)
        else:
            st.markdown(_slope_summary_html(dy), unsafe_allow_html=True)

    # ---- Section 2: density–temperature relationship ----
    with st.container(border=True):
        section_title("Catch density vs bottom temperature")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dy["bottom_temperature_c"], y=dy["cpue_kgkm2"], mode="markers",
            marker={"size": 8, "color": dy["bottom_temperature_c"], "colorscale": TEMP_COLORSCALE,
                    "showscale": False, "line": {"width": 0.5, "color": "rgba(90,90,90,0.4)"}},
            hovertemplate="bottom temp %{x:.1f} °C<br>CPUE %{y:,.0f} kg/km²<extra></extra>"))
        if is_cold_pool:   # mark the cold-pool boundary (no line for the slope, which has no cold pool)
            fig.add_vline(x=COLD_POOL_C, line_dash="dash", line_color="#444", line_width=1.5,
                          annotation_text="2 °C", annotation_position="top", annotation_font={"size": 13})
        fig.update_xaxes(title_text="Bottom temperature (°C)", title_font={"size": 18}, tickfont={"size": 14})
        fig.update_yaxes(title_text="CPUE (kg/km²)", title_font={"size": 18}, tickfont={"size": 14})
        if corr_txt:
            fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98, xanchor="right", yanchor="top",
                               text=corr_txt, showarrow=False, font={"size": 16, "color": "#1f2a36"},
                               bgcolor="rgba(255,255,255,0.8)", bordercolor="#9aa7b5", borderwidth=1, borderpad=5)
        fig.update_layout(height=440, template="plotly_white", font={"size": 15},
                          margin={"l": 80, "r": 20, "t": 20, "b": 60})
        st.plotly_chart(fig, use_container_width=True)

    # ---- Section 3: map — bottom temperature (colour) × CPUE (marker size) ----
    with st.container(border=True):
        section_title("Spatial co-distribution of catch & bottom temperature")
        cpue = dy["cpue_kgkm2"].to_numpy()
        cmax = float(max(cpue.max(), 1.0))
        size = 4 + 26 * np.sqrt(np.clip(cpue, 0, None) / cmax)   # sqrt scaling; zero-catch ≈ 4 px
        lats = dy["latitude"].to_numpy()
        lons = dy["longitude"].to_numpy()
        # Dateline-safe centring: a region straddling 180° (the Aleutians span ~+172°E to −170°W)
        # would otherwise average to a centre near 0° (off Europe). Plot such hauls on a 0–360°
        # axis so the chain stays contiguous and centres on its true mean; the hover still shows
        # the real −180..180 longitude (via customdata).
        straddle = float(lons.max() - lons.min()) > 180
        lon_plot = np.where(lons < 0, lons + 360, lons) if straddle else lons
        mfig = go.Figure(go.Scattermap(
            lat=lats, lon=lon_plot, mode="markers",
            marker={"size": size, "color": dy["bottom_temperature_c"], "colorscale": TEMP_COLORSCALE,
                    "opacity": 0.85,
                    "colorbar": {"title": {"text": "Bottom<br>temp °C", "font": {"size": 15}},
                                 "tickfont": {"size": 13}, "thickness": 16}},
            customdata=np.column_stack([dy["bottom_temperature_c"], cpue, lons]),
            hovertemplate="%{lat:.2f}, %{customdata[2]:.2f}<br>bottom %{customdata[0]:.1f} °C<br>"
                          "CPUE %{customdata[1]:,.0f} kg/km²<extra></extra>"))
        if corr_txt:
            mfig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, xanchor="left", yanchor="top",
                                text=corr_txt, showarrow=False, font={"size": 16, "color": "#1f2a36"},
                                bgcolor="rgba(255,255,255,0.85)", bordercolor="#9aa7b5", borderwidth=1, borderpad=5)
        mfig.update_layout(
            map={"style": "open-street-map",
                 "center": {"lat": float(lats.mean()), "lon": float(lon_plot.mean())},
                 "zoom": 3.4 if straddle else 4.0},
            height=560, margin={"l": 0, "r": 0, "t": 10, "b": 0}, font={"size": 15})
        st.plotly_chart(mfig, use_container_width=True)
        note = (" Snow crab is a cold-water specialist — in the eastern Bering it concentrates in the "
                "cold pool, so the biggest dots sit on the **deepest-blue (coldest)** water."
                if code == 68580 and is_cold_pool else "")
        st.caption(
            "Each dot is a survey tow: **colour = bottom temperature** (deeper blue = colder), "
            "**size = CPUE** (catch density, kg/km²; tiny dots are tows that caught little or none)."
            + note)

    footer("Source: NOAA FOSS AFSC bottom-trawl survey (haul ⟕ catch on hauljoin). "
           "Observed · survey footprint · annual · lagged — exploratory, not causal. "
           "<b>CPUE is a survey density index (kg/km² swept)</b> — a relative abundance measure, "
           "not total stock biomass or commercial landings.")
