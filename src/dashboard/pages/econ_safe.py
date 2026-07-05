"""Commercial groundfish economics — AKFIN Groundfish Economic SAFE (FMP-area resolution).

Fishery-dependent economics for the Alaska groundfish fisheries at **FMP-area** resolution
(Bering Sea & Aleutian Islands, Gulf of Alaska, All Alaska) — the management units economists use,
which do NOT split into the board's Bering/Aleutians ecosystem regions (AI is bundled into BSAI).

Phase A pages:
  * ``render_catch_value`` — retained catch (t) + ex-vessel value ($) by species (GFSAFE002).
  * ``render_prices``      — ex-vessel price ($/lb) by species/gear/sector (GFSAFE009).

Build data with ``mhw-ingest-econ-safe``.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.bottom_ui import (
    AMBER,
    BLUE,
    GREEN,
    SLATE,
    callout,
    footer,
    inject_css,
    kpi_card,
    kpi_grid,
    page_header,
    section_title,
    styled_table,
)
from dashboard.components.econ_data import (
    ECON_PALETTE,
    available_areas,
    fmp_label,
    load_safe_report,
)

_MIN_FOR_CHART = 3
_LBS_PER_TONNE = 2204.6226218


# ---------------------------------------------------------------------------
# Formatting + shared chart
# ---------------------------------------------------------------------------

def _fmt_usd(v: float) -> str:
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:.2f}B"
    if a >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


def _fmt_t(v: float) -> str:
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    if a >= 1e6:
        return f"{v / 1e6:.2f}M t"
    if a >= 1e3:
        return f"{v / 1e3:.0f}k t"
    return f"{v:,.0f} t"


def _series_chart(df: pd.DataFrame, cat_col: str, val_col: str, y_title: str,
                  hover_fmt: str, agg: str = "sum") -> None:
    """One line per category over the year axis (gaps broken; duplicate years aggregated)."""
    fig = go.Figure()
    years = list(range(int(df["year"].min()), int(df["year"].max()) + 1))
    for i, (cat, g) in enumerate(df.groupby(cat_col)):
        s = g.groupby("year")[val_col].agg(agg).reindex(years)
        fig.add_trace(go.Scatter(
            x=years, y=s.values, mode="lines+markers", name=str(cat),
            line=dict(color=ECON_PALETTE[i % len(ECON_PALETTE)], width=2), marker=dict(size=5),
            connectgaps=False,
            hovertemplate="%{x}: %{y:" + hover_fmt + "}<extra>" + str(cat) + "</extra>"))
    fig.update_layout(
        template="plotly_white", height=400, margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title=y_title, xaxis_title="Year", font=dict(size=13),
        legend=dict(orientation="h", y=1.14, font=dict(size=11)))
    fig.update_xaxes(dtick=5, tickformat="d")
    st.plotly_chart(fig, use_container_width=True)


def _fmp_selector(df: pd.DataFrame, key: str) -> str | None:
    opts = available_areas(df)
    if not opts:
        return None
    return st.sidebar.selectbox("FMP area", opts, format_func=fmp_label, key=key)


def _econ_callout() -> None:
    callout(
        "Commercial groundfish economics from NOAA/AFSC's <b>Economic SAFE</b> (via AKFIN), at "
        "<b>FMP-area</b> resolution — <b>BSAI</b> (Bering Sea & Aleutian Islands) and <b>GOA</b> "
        "(Gulf of Alaska). These are management areas, <b>not</b> the survey ecosystem regions: "
        "BSAI bundles the Bering Sea and Aleutians and cannot be split. Values are "
        "<b>nominal</b> (not inflation-adjusted).",
        icon="⚓", tint=BLUE)


# ---------------------------------------------------------------------------
# Page: Catch & Ex-Vessel Value (GFSAFE002)
# ---------------------------------------------------------------------------

def render_catch_value() -> None:
    inject_css()
    df = load_safe_report("gfsafe002")
    if df is None or df.empty:
        st.title("💵 Groundfish Catch & Ex-Vessel Value")
        st.info("Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    st.sidebar.header("Controls")
    area = _fmp_selector(df, "cv_area")
    sub = df[df["area_code"] == area]
    sectors = ["All Sectors"] + [s for s in sorted(sub["harvest_sector"].unique()) if s != "All Sectors"]
    sector = st.sidebar.selectbox("Harvest sector", sectors, key="cv_sector")
    sub = sub[sub["harvest_sector"] == sector]

    y0, y1 = int(sub["year"].min()), int(sub["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="cv_years")

    all_sp = [s for s in sorted(sub["species_group"].unique()) if s != "All Groundfish"]
    default_sp = (sub[sub["species_group"] != "All Groundfish"]
                  .groupby("species_group")["exvessel_value"].sum()
                  .sort_values(ascending=False).head(5).index.tolist())
    picked = st.sidebar.multiselect("Species group", all_sp, default=default_sp, key="cv_species")

    page_header("💵", "Groundfish Catch & Ex-Vessel Value", fmp_label(area),
                f"{fmp_label(area)} · {sector}",
                caption=("Retained commercial groundfish catch and ex-vessel value by species — "
                         "NOAA Economic SAFE (GFSAFE002)."))
    _econ_callout()

    if not picked:
        st.info("Select one or more species groups in the sidebar.")
        return
    sel = sub[(sub["year"] >= yr[0]) & (sub["year"] <= yr[1]) & (sub["species_group"].isin(picked))]
    if sel.empty:
        st.warning("No data for the selected species / years.")
        return

    latest = int(sel["year"].max())
    lr = sel[sel["year"] == latest]
    tot_t, tot_v = float(lr["retained_catch_mt"].sum()), float(lr["exvessel_value"].sum())
    price = tot_v / (tot_t * _LBS_PER_TONNE) if tot_t else float("nan")
    n_years = sel["year"].nunique()

    with st.container(border=True):
        section_title("Retained catch & ex-vessel value", note=f"{sector.lower()}, selected species")
        kpi_grid([
            kpi_card(f"Retained catch ({latest})", _fmt_t(tot_t), GREEN, sub="selected species"),
            kpi_card(f"Ex-vessel value ({latest})", _fmt_usd(tot_v), AMBER, sub="nominal $"),
            kpi_card(f"Implied price ({latest})", f"${price:.2f}/lb" if tot_t else "—", BLUE,
                     sub="value ÷ catch"),
            kpi_card("Species · years", f"{sel['species_group'].nunique()} · {n_years}", SLATE,
                     sub=f"{int(sel['year'].min())}–{latest}"),
        ], cols=4)
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "species_group", "retained_catch_mt", "Retained catch (metric tons)", ",.0f")
        else:
            _sparse_table(sel, "species_group", "retained_catch_mt", "Retained catch (t)")

    with st.container(border=True):
        section_title("Ex-vessel value", note="current (nominal) US$, selected species")
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "species_group", "exvessel_value", "Ex-vessel value (US$)", "$,.0f")
        else:
            _sparse_table(sel, "species_group", "exvessel_value", "Ex-vessel value ($)")

    footer("Source: NOAA/AFSC Groundfish Economic SAFE via AKFIN (GFSAFE002); FMP-area, annual, "
           "nominal ex-vessel value.", guide_url="/econ_safe_guide")


def _sparse_table(df: pd.DataFrame, cat_col: str, val_col: str, title: str) -> None:
    wide = df.pivot_table(index=cat_col, columns="year", values=val_col, aggfunc="sum")
    wide.columns = [str(int(c)) for c in wide.columns]
    st.caption(f"Too few years for a time series — {title.lower()} shown as a table.")
    st.markdown(styled_table(wide, precision=0), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Ex-Vessel Prices (GFSAFE009)
# ---------------------------------------------------------------------------

def render_prices() -> None:
    inject_css()
    df = load_safe_report("gfsafe009")
    if df is None or df.empty:
        st.title("🏷️ Groundfish Ex-Vessel Prices")
        st.info("Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    st.sidebar.header("Controls")
    area = _fmp_selector(df, "pr_area")
    sub = df[df["area_code"] == area]

    def _pick(col, label, key, prefer="All Sectors"):
        opts = sorted(sub[col].unique())
        opts = [o for o in opts if o == prefer] + [o for o in opts if o != prefer]
        return st.sidebar.selectbox(label, opts, key=key)

    gear = _pick("gear", "Gear", "pr_gear", prefer="All Gear")
    psector = _pick("processing_sector", "Processing sector", "pr_psector", prefer="All Sectors")
    sub = sub[(sub["gear"] == gear) & (sub["processing_sector"] == psector)]

    y0, y1 = int(sub["year"].min()), int(sub["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="pr_years")
    all_sp = [s for s in sorted(sub["species"].unique()) if s != "All Groundfish"]
    default_sp = all_sp[:5]
    picked = st.sidebar.multiselect("Species", all_sp, default=default_sp, key="pr_species")

    page_header("🏷️", "Groundfish Ex-Vessel Prices", fmp_label(area),
                f"{fmp_label(area)} · {gear} · {psector}",
                caption="Ex-vessel price paid to harvesters ($/lb) by species — Economic SAFE (GFSAFE009).")
    _econ_callout()

    if not picked:
        st.info("Select one or more species in the sidebar.")
        return
    sel = sub[(sub["year"] >= yr[0]) & (sub["year"] <= yr[1]) & (sub["species"].isin(picked))]
    if sel.empty or sel["exves_price_lb"].dropna().empty:
        st.warning("No price data for the selected species / years / filters.")
        return

    latest = int(sel.dropna(subset=["exves_price_lb"])["year"].max())
    lr = sel[sel["year"] == latest]
    n_years = sel["year"].nunique()
    with st.container(border=True):
        section_title("Ex-vessel price", note="US$ per pound, selected species")
        kpi_grid([
            kpi_card(f"Mean price ({latest})", f"${lr['exves_price_lb'].mean():.2f}/lb", BLUE,
                     sub="across selected species"),
            kpi_card(f"Range ({latest})",
                     f"${lr['exves_price_lb'].min():.2f}–{lr['exves_price_lb'].max():.2f}", SLATE,
                     sub="/lb"),
            kpi_card("Species · years", f"{sel['species'].nunique()} · {n_years}", SLATE,
                     sub=f"{int(sel['year'].min())}–{latest}"),
        ], cols=3)
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "species", "exves_price_lb", "Ex-vessel price (US$/lb)", "$.2f", agg="mean")
        else:
            _sparse_table(sel, "species", "exves_price_lb", "Price ($/lb)")

    footer("Source: NOAA/AFSC Groundfish Economic SAFE via AKFIN (GFSAFE009); FMP-area, annual, "
           "nominal ex-vessel price.", guide_url="/econ_safe_guide")


# ---------------------------------------------------------------------------
# Page: Wholesale production & value (GFSAFE012 / 013 / 014)
# ---------------------------------------------------------------------------

def _pick_prefer(sub: pd.DataFrame, col: str, label: str, key: str, prefer: str):
    opts = sorted(sub[col].dropna().unique())
    opts = [o for o in opts if o == prefer] + [o for o in opts if o != prefer]
    return st.sidebar.selectbox(label, opts, key=key)


def _top_by(df: pd.DataFrame, cat_col: str, val_col: str, n: int, exclude=()) -> list[str]:
    g = df[~df[cat_col].isin(exclude)].groupby(cat_col)[val_col].sum().sort_values(ascending=False)
    return g.head(n).index.tolist()


def render_wholesale() -> None:
    inject_css()
    prod = load_safe_report("gfsafe012")
    if prod is None or prod.empty:
        st.title("🏭 Groundfish Wholesale Production & Value")
        st.info("Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    st.sidebar.header("Controls")
    area = _fmp_selector(prod, "ws_area")
    sub = prod[prod["area_code"] == area]
    psector = _pick_prefer(sub, "processing_sector", "Processing sector", "ws_psector", "All Sectors")
    product = _pick_prefer(sub, "product", "Product form", "ws_product", "All Products")
    sub = sub[(sub["processing_sector"] == psector) & (sub["product"] == product)]

    y0, y1 = int(sub["year"].min()), int(sub["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="ws_years")
    all_sp = [s for s in sorted(sub["species"].unique()) if s != "All Groundfish"]
    default_sp = _top_by(sub, "species", "wholesale_value", 5, exclude=("All Groundfish",))
    picked = st.sidebar.multiselect("Species", all_sp, default=default_sp, key="ws_species")

    page_header("🏭", "Groundfish Wholesale Production & Value", fmp_label(area),
                f"{fmp_label(area)} · {psector} · {product}",
                caption=("First-wholesale (processed) production, value, and price of Alaska "
                         "groundfish — NOAA Economic SAFE (GFSAFE012/013/014)."))
    _econ_callout()

    if not picked:
        st.info("Select one or more species in the sidebar.")
        return
    sel = sub[(sub["year"] >= yr[0]) & (sub["year"] <= yr[1]) & (sub["species"].isin(picked))]
    if sel.empty:
        st.warning("No wholesale data for the selected species / years / filters.")
        return

    latest = int(sel["year"].max())
    lr = sel[sel["year"] == latest]
    tot_t, tot_v = float(lr["product_weight_mt"].sum()), float(lr["wholesale_value"].sum())
    price = tot_v / (tot_t * _LBS_PER_TONNE) if tot_t else float("nan")
    n_years = sel["year"].nunique()

    with st.container(border=True):
        section_title("Wholesale production & value", note=f"{product.lower()}, selected species")
        kpi_grid([
            kpi_card(f"Product weight ({latest})", _fmt_t(tot_t), GREEN, sub="processed weight"),
            kpi_card(f"Wholesale value ({latest})", _fmt_usd(tot_v), AMBER, sub="nominal $"),
            kpi_card(f"Wholesale price ({latest})", f"${price:.2f}/lb" if tot_t else "—", BLUE,
                     sub="value ÷ weight"),
            kpi_card("Species · years", f"{sel['species'].nunique()} · {n_years}", SLATE,
                     sub=f"{int(sel['year'].min())}–{latest}"),
        ], cols=4)
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "species", "product_weight_mt", "Product weight (metric tons)", ",.0f")
        else:
            _sparse_table(sel, "species", "product_weight_mt", "Product weight (t)")

    with st.container(border=True):
        section_title("Wholesale value", note="current (nominal) US$, selected species")
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "species", "wholesale_value", "Wholesale value (US$)", "$,.0f")
        else:
            _sparse_table(sel, "species", "wholesale_value", "Wholesale value ($)")

    _wholesale_unit_value_panel(area, yr)
    _wholesale_processor_panel(area, yr)

    footer("Source: NOAA/AFSC Groundfish Economic SAFE via AKFIN (GFSAFE012/013/014); FMP-area, "
           "annual, nominal first-wholesale value.", guide_url="/econ_safe_guide")


def _wholesale_unit_value_panel(area: str, yr: tuple[int, int]) -> None:
    df = load_safe_report("gfsafe013")
    if df is None or df.empty:
        return
    # 013's processing sectors are area-specific (no universal "All Sectors" row for BSAI), so
    # average the unit value across whatever sectors are present per species group × year.
    d = df[(df["area_code"] == area) & (df["year"] >= yr[0]) & (df["year"] <= yr[1])]
    d = d[d["species_group"] != "All Groundfish"]
    if d.empty or d["wslprice_perroundmt"].dropna().empty:
        return
    with st.container(border=True):
        section_title("Wholesale unit value", note="US$ per round metric ton, sector-mean (GFSAFE013)")
        if d["year"].nunique() >= _MIN_FOR_CHART:
            _series_chart(d, "species_group", "wslprice_perroundmt",
                          "Wholesale unit value (US$/round t)", "$,.0f", agg="mean")
        else:
            _sparse_table(d, "species_group", "wslprice_perroundmt", "Unit value ($/round t)")


def _wholesale_processor_panel(area: str, yr: tuple[int, int]) -> None:
    df = load_safe_report("gfsafe014")
    if df is None or df.empty:
        return
    d = df[(df["area_code"] == area) & (df["year"] >= yr[0]) & (df["year"] <= yr[1])]
    if d.empty or d["wsval_m"].dropna().empty:
        return
    top = _top_by(d, "fleet_port", "wsval_m", 8)
    d = d[d["fleet_port"].isin(top)]
    with st.container(border=True):
        section_title("First-wholesale value by processor group",
                      note="US$ millions, top processor groups (GFSAFE014, 2012–)")
        if d["year"].nunique() >= _MIN_FOR_CHART:
            _series_chart(d, "fleet_port", "wsval_m", "First-wholesale value (US$ millions)", "$,.1f")
        else:
            _sparse_table(d, "fleet_port", "wsval_m", "Value ($M)")
