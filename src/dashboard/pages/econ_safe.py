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
    PURPLE,
    RED,
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
    by_total,
    category_colors,
    fmp_label,
    load_safe_report,
    stacked_bar,
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
    return st.sidebar.selectbox(
        "FMP area", opts, format_func=fmp_label, key=key,
        help=("FMP = Fishery Management Plan. BSAI (Bering Sea & Aleutian Islands) and GOA "
              "(Gulf of Alaska) are the two North Pacific groundfish management areas defined "
              "under NPFMC's Fishery Management Plans."))


def _econ_callout() -> None:
    callout(
        "Commercial groundfish economics from NOAA/AFSC's <b>Economic SAFE</b> (via AKFIN), at "
        "<b>FMP</b> (Fishery Management Plan) area resolution — <b>BSAI</b> (Bering Sea & Aleutian "
        "Islands) and <b>GOA</b> (Gulf of Alaska). These are management areas, <b>not</b> the "
        "survey ecosystem regions: BSAI bundles the Bering Sea and Aleutians and cannot be split. "
        "Values are <b>nominal</b> (not inflation-adjusted).",
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

    ir = sub[(sub["year"] >= yr[0]) & (sub["year"] <= yr[1]) & (sub["species_group"] != "All Groundfish")]
    catch_by_sp = ir.groupby("species_group")["retained_catch_mt"].sum().sort_values(ascending=False)
    all_sp = catch_by_sp.index.tolist()
    default_sp = (ir.groupby("species_group")["exvessel_value"].sum()
                  .sort_values(ascending=False).head(5).index.tolist())

    def _sp_label(sp: str) -> str:
        return f"{sp} — {_fmt_t(float(catch_by_sp.get(sp, 0.0)))}"

    picked = st.sidebar.multiselect("Species group (by catch)", all_sp, default=default_sp,
                                    format_func=_sp_label, key="cv_species")
    st.sidebar.caption(f"Each figure is total retained catch over {yr[0]}–{yr[1]} "
                       f"({sector.lower()}); the list re-ranks as you move the slider.")

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
    cmap = category_colors(by_total(sub[sub["species_group"] != "All Groundfish"],
                                    "species_group", "exvessel_value"))

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
            stacked_bar(sel, "species_group", "retained_catch_mt", "Retained catch (metric tons)",
                        ",.0f", colors=cmap)
        else:
            _sparse_table(sel, "species_group", "retained_catch_mt", "Retained catch (t)")

    with st.container(border=True):
        section_title("Ex-vessel value", note="current (nominal) US$, selected species")
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "species_group", "exvessel_value", "Ex-vessel value (US$)", "$,.0f",
                        colors=cmap)
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
    cmap = category_colors(by_total(sub[sub["species"] != "All Groundfish"],
                                    "species", "wholesale_value"))

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
            stacked_bar(sel, "species", "product_weight_mt", "Product weight (metric tons)",
                        ",.0f", colors=cmap)
        else:
            _sparse_table(sel, "species", "product_weight_mt", "Product weight (t)")

    with st.container(border=True):
        section_title("Wholesale value", note="current (nominal) US$, selected species")
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "species", "wholesale_value", "Wholesale value (US$)", "$,.0f",
                        colors=cmap)
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
            stacked_bar(d, "fleet_port", "wsval_m", "First-wholesale value (US$ millions)", "$,.1f")
        else:
            _sparse_table(d, "fleet_port", "wsval_m", "Value ($M)")


# ---------------------------------------------------------------------------
# Month-axis chart (seasonality)
# ---------------------------------------------------------------------------
_MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_chart(df: pd.DataFrame, cat_col: str, val_col: str, y_title: str) -> None:
    """One line per category across the calendar year (mean over the selected years)."""
    fig = go.Figure()
    for i, (cat, g) in enumerate(df.groupby(cat_col)):
        s = g.groupby("month_number")[val_col].mean().reindex(range(1, 13))
        fig.add_trace(go.Scatter(
            x=_MONTH_ABBR, y=s.values, mode="lines+markers", name=str(cat),
            line=dict(color=ECON_PALETTE[i % len(ECON_PALETTE)], width=2), marker=dict(size=5),
            connectgaps=False, hovertemplate="%{x}: %{y:,.0f}<extra>" + str(cat) + "</extra>"))
    fig.update_layout(
        template="plotly_white", height=360, margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title=y_title, xaxis_title="Month", font=dict(size=13),
        legend=dict(orientation="h", y=1.16, font=dict(size=11)))
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Fishing Effort & Labor (GFSAFE015 / 016 / 017 / 018)
# ---------------------------------------------------------------------------

def render_effort_labor() -> None:
    inject_css()
    ves = load_safe_report("gfsafe015")
    if ves is None or ves.empty:
        st.title("🚢 Groundfish Fishing Effort & Labor")
        st.info("Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    st.sidebar.header("Controls")
    area = _fmp_selector(ves, "ef_area")
    sub = ves[ves["area_code"] == area]
    sector = _pick_prefer(sub, "harvest_sector", "Harvest sector", "ef_sector", "All Sectors")
    y0, y1 = int(sub["year"].min()), int(sub["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="ef_years")

    page_header("🚢", "Groundfish Fishing Effort & Labor", fmp_label(area),
                f"{fmp_label(area)} · {sector}",
                caption=("Fishing activity and employment in the groundfish fisheries — vessels, "
                         "effort, and crew (NOAA Economic SAFE, GFSAFE015–018)."))
    _econ_callout()

    # A) Vessels by target fishery (015)
    va = sub[(sub["harvest_sector"] == sector) & (sub["year"] >= yr[0]) & (sub["year"] <= yr[1])
             & (sub["target"] != "All Target Species")]
    with st.container(border=True):
        section_title("Vessels by target fishery", note=f"{sector.lower()} (GFSAFE015)")
        allv = sub[(sub["harvest_sector"] == sector) & (sub["target"] == "All Target Species")]
        latest = int(allv["year"].max()) if not allv.empty else int(sub["year"].max())
        tot = int(allv.loc[allv["year"] == latest, "vessels"].sum()) if not allv.empty else 0
        kpi_grid([
            kpi_card(f"Vessels ({latest})", f"{tot:,}", BLUE, sub="all target species"),
            kpi_card("Targets · years", f"{va['target'].nunique()} · {va['year'].nunique()}", SLATE,
                     sub=f"{yr[0]}–{yr[1]}"),
        ], cols=2)
        if not va.empty and va["year"].nunique() >= _MIN_FOR_CHART:
            _series_chart(va, "target", "vessels", "Vessels", ",.0f")
        else:
            _sparse_table(va, "target", "vessels", "Vessels")

    # B) Seasonality — vessels by month (016)
    mv = load_safe_report("gfsafe016")
    if mv is not None and not mv.empty:
        m = mv[(mv["area_code"] == area) & (mv["month"] != "All Months")
               & (mv["gear"] != "All Gear") & (mv["year"] >= yr[0]) & (mv["year"] <= yr[1])]
        if "harvest_sector" in m.columns and (m["harvest_sector"] == sector).any():
            m = m[m["harvest_sector"] == sector]
        if not m.empty:
            with st.container(border=True):
                section_title("Seasonality of activity", note="mean vessels per month by gear (GFSAFE016)")
                _month_chart(m, "gear", "vessels", "Vessels (monthly mean)")

    # C) Fishing effort — vessel-weeks (017)
    vw = load_safe_report("gfsafe017")
    if vw is not None and not vw.empty:
        w = vw[(vw["area_code"] == area) & (vw["gear"] == "All Gear")
               & (vw["groundfish_target_species"] != "All Target Species")
               & (vw["year"] >= yr[0]) & (vw["year"] <= yr[1])]
        if not w.empty:
            with st.container(border=True):
                section_title("Fishing effort (vessel-weeks)",
                              note="all gear, summed across sectors, by target (GFSAFE017)")
                if w["year"].nunique() >= _MIN_FOR_CHART:
                    stacked_bar(w, "groundfish_target_species", "vessel_weeks", "Vessel-weeks", ",.0f")
                else:
                    _sparse_table(w, "groundfish_target_species", "vessel_weeks", "Vessel-weeks")

    # D) Crew labor — crew-weeks (018)
    cw = load_safe_report("gfsafe018")
    if cw is not None and not cw.empty:
        c = cw[(cw["area_code"] == area) & (cw["month"] == "All Months")
               & (cw["year"] >= yr[0]) & (cw["year"] <= yr[1])]
        if not c.empty and (c["cv_crewweeks"].notna().any() or c["atseaproc_crewweeks"].notna().any()):
            long = pd.concat([
                pd.DataFrame({"year": c["year"], "series": "Catcher vessels", "crewweeks": c["cv_crewweeks"]}),
                pd.DataFrame({"year": c["year"], "series": "At-sea processors", "crewweeks": c["atseaproc_crewweeks"]}),
            ], ignore_index=True).dropna(subset=["crewweeks"])
            with st.container(border=True):
                section_title("Crew labor (crew-weeks)", note="annual, by sector (GFSAFE018, 2009–)")
                if long["year"].nunique() >= _MIN_FOR_CHART:
                    stacked_bar(long, "series", "crewweeks", "Crew weeks", ",.0f")
                else:
                    _sparse_table(long, "series", "crewweeks", "Crew weeks")

    footer("Source: NOAA/AFSC Groundfish Economic SAFE via AKFIN (GFSAFE015–018); FMP-area, annual.",
           guide_url="/econ_safe_guide")


# ---------------------------------------------------------------------------
# Page: Fleet & Ownership (GFSAFE011 / 019 / 010)
# ---------------------------------------------------------------------------

def render_fleet_ownership() -> None:
    inject_css()
    val = load_safe_report("gfsafe011")
    if val is None or val.empty:
        st.title("⚓ Groundfish Fleet & Ownership")
        st.info("Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    st.sidebar.header("Controls")
    area = _fmp_selector(val, "fo_area")
    sub = val[val["area_code"] == area]
    y0, y1 = int(sub["year"].min()), int(sub["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="fo_years")

    page_header("⚓", "Groundfish Fleet & Ownership", fmp_label(area),
                fmp_label(area),
                caption=("Who fishes for groundfish — value by fleet, fleet characteristics, and "
                         "how ex-vessel value splits between Alaska and out-of-state (Economic SAFE)."))
    _econ_callout()

    # A) Ex-vessel value by fleet (011)
    d = sub[(sub["year"] >= yr[0]) & (sub["year"] <= yr[1])]
    top = _top_by(d, "fleet", "exves_val_m", 8)
    dd = d[d["fleet"].isin(top)]
    latest = int(d["year"].max())
    lr = d[d["year"] == latest]
    with st.container(border=True):
        section_title("Ex-vessel value by fleet", note="US$ millions, top fleets (GFSAFE011, 2009–)")
        kpi_grid([
            kpi_card(f"Fleet value ({latest})", _fmt_usd(float(lr["exves_val_m"].sum()) * 1e6), AMBER,
                     sub="all fleets, nominal"),
            kpi_card(f"Vessels ({latest})", f"{int(lr['vessels'].sum()):,}", BLUE, sub="all fleets"),
            kpi_card("Fleets · years", f"{d['fleet'].nunique()} · {d['year'].nunique()}", SLATE,
                     sub=f"{yr[0]}–{yr[1]}"),
        ], cols=3)
        if dd["year"].nunique() >= _MIN_FOR_CHART:
            stacked_bar(dd, "fleet", "exves_val_m", "Ex-vessel value (US$ millions)", "$,.1f")
        else:
            _sparse_table(dd, "fleet", "exves_val_m", "Value ($M)")

    # B) Fleet characteristics (019)
    fc = load_safe_report("gfsafe019")
    if fc is not None and not fc.empty:
        f = fc[(fc["area_code"] == area) & (fc["fleet"] != "No Fleet / Other")]
        if not f.empty:
            fy = int(f["year"].max())
            t = f[f["year"] == fy].copy()
            tbl = pd.DataFrame({
                "Fleet": t["fleet"],
                "Vessels": t["vessels"].astype("Int64"),
                "Mean length (ft)": t["length_avg"].round(0).astype("Int64"),
                "Mean net tonnage": t["nton_avg"].round(0).astype("Int64"),
            }).sort_values("Vessels", ascending=False).set_index("Fleet")
            with st.container(border=True):
                section_title("Fleet characteristics", note=f"vessel size by fleet, {fy} (GFSAFE019)")
                st.markdown(styled_table(tbl, precision=0), unsafe_allow_html=True)

    # C) Ex-vessel value by residency (010)
    res = load_safe_report("gfsafe010")
    if res is not None and not res.empty:
        r = res[(res["area_code"] == area) & (res["species_group"] != "All Groundfish")
                & (res["year"] >= yr[0]) & (res["year"] <= yr[1])].copy()
        r = r[r["alaska_exvesval_share"].notna()]
        if not r.empty:
            r["ak_pct"] = r["alaska_exvesval_share"] * 100.0
            with st.container(border=True):
                section_title("Ex-vessel value kept by Alaska residents",
                              note="% of ex-vessel value to Alaska-resident harvesters (GFSAFE010)")
                callout("Share of each species group's ex-vessel value paid to <b>Alaska-resident</b> "
                        "vessels (the remainder goes to out-of-state harvesters).", icon="🏠", tint=SLATE)
                if r["year"].nunique() >= _MIN_FOR_CHART:
                    _series_chart(r, "species_group", "ak_pct", "Alaska-resident value share (%)", ".0f", agg="mean")
                else:
                    _sparse_table(r, "species_group", "ak_pct", "AK share (%)")

    footer("Source: NOAA/AFSC Groundfish Economic SAFE via AKFIN (GFSAFE010/011/019); FMP-area, annual.",
           guide_url="/econ_safe_guide")


# ---------------------------------------------------------------------------
# Page: Crab Economics (BSAI Crab Economic SAFE — CRSAFEEXEC01)
# ---------------------------------------------------------------------------

def _titlecase(name: str) -> str:
    """Nicely title-case an all-caps fishery name (keeps 'and' lowercase)."""
    t = str(name).title()
    return t.replace(" And ", " and ").replace("St.", "St.")


def _snow_crab_spotlight(d: pd.DataFrame) -> None:
    """The signature panel: the Bering Sea snow-crab collapse and its cold-pool link."""
    sc = d[d["fishery_name"] == "BERING SEA SNOW CRAB"].dropna(subset=["hpy_soldmt"]).sort_values("year")
    if sc.empty:
        return
    last = sc.iloc[-1]
    # Use the RECENT pre-collapse peak (last ~8 years), not the all-time 1998 high — the climate
    # story is the 2021→2022 crash, and framing it against a 1990s baseline would overstate it.
    recent = sc[sc["year"] >= int(last["year"]) - 8]
    peak = recent.loc[recent["hpy_soldmt"].idxmax()]
    drop = (1 - last["hpy_soldmt"] / peak["hpy_soldmt"]) * 100 if peak["hpy_soldmt"] else 0
    with st.container(border=True):
        section_title("Spotlight — snow crab & the cold pool",
                      note="a climate–fisheries collapse in ex-vessel terms")
        kpi_grid([
            kpi_card(f"Recent peak ({int(peak['year'])})", _fmt_t(float(peak["hpy_soldmt"])), GREEN,
                     sub=_fmt_usd(float(peak["hpy_exv_nom"])) + " ex-vessel"),
            kpi_card(f"Final season ({int(last['year'])})", _fmt_t(float(last["hpy_soldmt"])), RED,
                     sub=_fmt_usd(float(last["hpy_exv_nom"])) + " ex-vessel"),
            kpi_card(f"Decline ({int(peak['year'])}→{int(last['year'])})", f"−{drop:.0f}%", RED,
                     sub="harvested weight"),
        ], cols=3)
        callout(
            "Bering Sea <b>snow crab</b> harvest fell from "
            f"<b>{float(peak['hpy_soldmt']):,.0f} t</b> in {int(peak['year'])} to "
            f"<b>{float(last['hpy_soldmt']):,.0f} t</b> in {int(last['year'])}, and the fishery was "
            "then <b>closed</b> for the 2022/23 and 2023/24 seasons after the stock collapsed. The "
            "crash followed the record-warm Bering Sea of 2018–2019 and the loss of the cold pool "
            "that snow crab depend on — see the <a target='_self' href='/bering_bottom_observed'>"
            "Bering Cold Pool &amp; Bottom Temperature</a> and "
            "<a target='_self' href='/bering_catch'>Catch × Bottom State</a> pages.",
            icon="❄️", tint=PURPLE)


def render_crab() -> None:
    inject_css()
    d = load_safe_report("crsafeexec01")
    if d is None or d.empty:
        st.title("🦀 BSAI Crab Economics")
        st.info("Crab Economic SAFE data not built yet. Run `mhw-ingest-econ-safe`.")
        return

    d = d.copy()
    d["stock"] = d["fishery_name"].map(_titlecase)
    st.sidebar.header("Controls")
    y0, y1 = int(d["year"].min()), int(d["year"].max())
    yr = st.sidebar.slider("Year range", y0, y1, (y0, y1), key="crab_years")
    all_stocks = sorted(d["stock"].unique())
    default = [s for s in all_stocks if any(k in s for k in
              ("Snow", "Bristol Bay Red King", "Bering Sea Tanner", "Golden King"))]
    picked = st.sidebar.multiselect("Crab fishery", all_stocks, default=default or all_stocks,
                                    key="crab_stocks")

    page_header("🦀", "BSAI Crab Economics", "Bering Sea & Aleutian Islands",
                "Bering Sea & Aleutian Islands crab",
                caption=("Commercial crab harvest, ex-vessel value, and price by fishery/stock — "
                         "NOAA BSAI Crab Economic SAFE (CRSAFEEXEC01)."))
    callout(
        "BSAI <b>crab</b> economics (fishery-dependent), by crab stock — snow, Bristol Bay red king, "
        "Bering Sea Tanner, and the king-crab fisheries. Distinct from the survey; values are "
        "<b>nominal</b> (not inflation-adjusted). This is where the cold pool meets the dock — "
        "see the snow-crab spotlight below.",
        icon="🦀", tint=BLUE)

    _snow_crab_spotlight(d)

    if not picked:
        st.info("Select one or more crab fisheries in the sidebar.")
        return
    sel = d[(d["year"] >= yr[0]) & (d["year"] <= yr[1]) & (d["stock"].isin(picked))]
    if sel.empty:
        st.warning("No crab data for the selected fisheries / years.")
        return

    latest = int(sel.dropna(subset=["hpy_soldmt"])["year"].max())
    lr = sel[sel["year"] == latest]
    n_years = sel["year"].nunique()
    cmap = category_colors(by_total(d, "stock", "hpy_soldmt"))

    with st.container(border=True):
        section_title("Harvest & ex-vessel value", note="by crab fishery (CRSAFEEXEC01)")
        kpi_grid([
            kpi_card(f"Harvest ({latest})", _fmt_t(float(lr["hpy_soldmt"].sum())), GREEN,
                     sub="selected fisheries"),
            kpi_card(f"Ex-vessel value ({latest})", _fmt_usd(float(lr["hpy_exv_nom"].sum())), AMBER,
                     sub="nominal $"),
            kpi_card(f"Mean price ({latest})", f"${lr['hpy_exvpr_nom'].mean():.2f}/lb" if not lr.empty else "—",
                     BLUE, sub="ex-vessel"),
            kpi_card("Fisheries · years", f"{sel['stock'].nunique()} · {n_years}", SLATE,
                     sub=f"{int(sel['year'].min())}–{latest}"),
        ], cols=4)
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "stock", "hpy_soldmt", "Harvest (metric tons)", ",.0f", colors=cmap)
        else:
            _sparse_table(sel, "stock", "hpy_soldmt", "Harvest (t)")

    with st.container(border=True):
        section_title("Ex-vessel value", note="current (nominal) US$, by crab fishery")
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "stock", "hpy_exv_nom", "Ex-vessel value (US$)", "$,.0f", colors=cmap)
        else:
            _sparse_table(sel, "stock", "hpy_exv_nom", "Ex-vessel value ($)")

    with st.container(border=True):
        section_title("Ex-vessel price", note="US$ per pound, by crab fishery")
        if n_years >= _MIN_FOR_CHART:
            _series_chart(sel, "stock", "hpy_exvpr_nom", "Ex-vessel price (US$/lb)", "$.2f", agg="mean")
        else:
            _sparse_table(sel, "stock", "hpy_exvpr_nom", "Price ($/lb)")

    footer("Source: NOAA/AFSC BSAI Crab Economic SAFE via AKFIN (CRSAFEEXEC01); by crab fishery, "
           "annual, nominal ex-vessel value.", guide_url="/econ_safe_guide")
