"""Commercial Landings — statewide Alaska commercial harvest (tons) + ex-vessel value ($).

The board's first **fishery-dependent** (commercial harvest) page, the economic counterpart to
the fishery-independent survey CPUE pages. Source is NOAA FOSS Commercial Landings — statewide
Alaska only (not sub-region), so it lives in its own top-level section rather than under a
geography group. Region-wise groundfish (NPFMC areas) is a later AKFIN track.

Reads ``data/raw/landings_foss_ak.parquet`` directly (build with ``mhw-fetch-landings-foss``).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
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
from dashboard.components.econ_data import by_total, category_colors, stacked_bar, year_slider
from mhw.econ.sources import FOSS_LANDINGS

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"

# Below this many years, draw a table rather than a misleading short bar series (shared board rule).
_MIN_FOR_CHART = 3


@st.cache_data(show_spinner=False, ttl=3600)
def load_landings() -> pd.DataFrame | None:
    """Load the statewide-AK commercial landings frame (None if not fetched yet)."""
    p = RAW_DIR / f"landings_{FOSS_LANDINGS.id}.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p).sort_values(["year", "species"]).reset_index(drop=True)


def _fmt_usd(v: float) -> str:
    """Compact $ label: $1.23B / $456M / $7.8M / $12,345."""
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:.2f}B"
    if a >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


def _fmt_t(v: float) -> str:
    """Compact metric-tons label: 1.23M t / 456k t / 7,800 t."""
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    if a >= 1e6:
        return f"{v / 1e6:.2f}M t"
    if a >= 1e3:
        return f"{v / 1e3:.0f}k t"
    return f"{v:,.0f} t"


def _species_label(species: str) -> str:
    """Tag NOAA aggregate/confidential rollup categories so they read as groups, not species."""
    return species[:-2].rstrip() + " (group)" if species.rstrip().endswith("**") else species


def _top_species_by_value(df: pd.DataFrame, n: int = 5) -> list[str]:
    """The *n* species with the greatest cumulative ex-vessel value (default selection)."""
    g = df.groupby("species")["value_usd"].sum().sort_values(ascending=False)
    return list(g.head(n).index)


# Landings and value are additive across species → stacked bars (composition + total at a glance);
# see dashboard.components.econ_data.stacked_bar.


def _species_table(df: pd.DataFrame, value_col: str, col_title: str) -> None:
    """Sparse fallback: a species × year table instead of a short, misleading line."""
    wide = df.pivot_table(index="species", columns="year", values=value_col, aggfunc="sum")
    wide.columns = [str(int(c)) for c in wide.columns]
    st.caption(f"Too few years for a time series — {col_title.lower()} shown as a table.")
    st.markdown(styled_table(wide, precision=0), unsafe_allow_html=True)


def render() -> None:
    """Render the statewide-Alaska Commercial Landings page (nav shell owns config/fonts)."""
    inject_css()

    df = load_landings()
    if df is None or df.empty:
        st.title("💰 Commercial Landings")
        st.info("Statewide-Alaska commercial landings are not built yet. Fetch them with "
                "`mhw-fetch-landings-foss` (writes `data/raw/landings_foss_ak.parquet`).")
        return

    y_min, y_max = int(df["year"].min()), int(df["year"].max())

    st.sidebar.header("Controls")
    yr = year_slider("Year range", y_min, y_max, "cl_years",
                     default=(max(y_min, y_max - 25), y_max))
    # Only offer species actually landed within the selected window — species landed only in
    # earlier decades would otherwise clutter the list and chart as empty lines.
    in_range = df[(df["year"] >= yr[0]) & (df["year"] <= yr[1])]
    all_species = sorted(df["species"].unique())
    # Order the picker by landings (largest first) and label each option with its scale, so the
    # dominant fisheries lead and a user can see at a glance that, e.g., "TUNA, ALBACORE — 18 t"
    # will be invisible next to pollock (~1.4M t). Alphabetical + no size cue was the frustration.
    land_by_sp = in_range.groupby("species")["landings_t"].sum().sort_values(ascending=False)
    available = land_by_sp.index.tolist()

    def _option_label(sp: str) -> str:
        return f"{_species_label(sp)} — {_fmt_t(float(land_by_sp.get(sp, 0.0)))}"

    picked = st.sidebar.multiselect(
        "Species (by landings)", available, default=_top_species_by_value(in_range, 5),
        format_func=_option_label, key="cl_species")
    st.sidebar.caption(f"Each species' figure is its **total landings over {yr[0]}–{yr[1]}** "
                       "(the selected years); the list re-ranks as you move the year-range slider.")

    page_header("💰", "Commercial Landings", "Statewide Alaska",
                "Alaska — statewide",
                caption=("Fishery-dependent commercial harvest — landings and ex-vessel value "
                         "reported to NOAA. Statewide Alaska only (not sub-region), current-dollar "
                         "(nominal) value."))
    callout(
        "This is <b>commercial harvest</b> (fishery-<i>dependent</i>) — what vessels landed and "
        "sold — and is <b>distinct from the survey</b>: survey CPUE on the Catch × Bottom State "
        "pages is a fishery-<i>independent</i> abundance index, not landings. Values are "
        "<b>statewide Alaska</b> (no Bering/GOA/AI split in this source) and <b>nominal</b> "
        "(not inflation-adjusted).",
        icon="🎣", tint=BLUE)

    if not picked:
        st.info("Select one or more species in the sidebar to see landings and ex-vessel value. "
                "(Charting all 98 landed species at once would be unreadable.)")
        return
    sel = df[(df["year"] >= yr[0]) & (df["year"] <= yr[1]) & (df["species"].isin(picked))]
    if sel.empty:
        st.warning("No landings for the selected species / years.")
        return

    latest = int(sel["year"].max())
    latest_rows = sel[sel["year"] == latest]
    n_years = sel["year"].nunique()
    # Stable colour per species, assigned by total ex-vessel VALUE (the basis of the default
    # selection), so the species a user actually sees get the distinct leading palette colours;
    # only the low-value tail — rarely shown — can wrap onto a repeat.
    cmap = category_colors(by_total(df, "species", "value_usd"))

    # --- Landings (metric tons) --------------------------------------------------------------
    with st.container(border=True):
        section_title("Commercial landings", note="metric tons, selected species")
        kpi_grid([
            kpi_card(f"Landings ({latest})", _fmt_t(latest_rows["landings_t"].sum()), GREEN,
                     sub="selected species"),
            kpi_card("Ex-vessel value", _fmt_usd(latest_rows["value_usd"].sum()), AMBER,
                     sub=f"{latest} · nominal $", label_note=f"({latest})"),
            kpi_card("Species shown", f"{sel['species'].nunique()}", BLUE,
                     sub=f"of {len(all_species)} landed"),
            kpi_card("Years", f"{n_years}", SLATE, sub=f"{int(sel['year'].min())}–{latest}"),
        ], cols=4)
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "species", "landings_t", "Landings (metric tons)", ",.0f", colors=cmap)
        else:
            _species_table(sel, "landings_t", "Landings (t)")

    # --- Ex-vessel value ($) + price ---------------------------------------------------------
    with st.container(border=True):
        section_title("Ex-vessel value", note="current (nominal) US$, selected species")
        if n_years >= _MIN_FOR_CHART:
            stacked_bar(sel, "species", "value_usd", "Ex-vessel value (US$)", "$,.0f", colors=cmap)
        else:
            _species_table(sel, "value_usd", "Ex-vessel value ($)")
        # Fleet-wide realised price (Σ value / Σ landings) over the selection — a simple $/t.
        tot_t, tot_v = sel["landings_t"].sum(), sel["value_usd"].sum()
        price = tot_v / tot_t if tot_t else float("nan")
        callout(
            f"Across the selection, ex-vessel value averaged <b>{_fmt_usd(price)}/t</b> "
            f"(Σ value ÷ Σ landings). Price varies widely by species — high-value shellfish and "
            f"salmon fetch far more per ton than groundfish like pollock.",
            icon="💵", tint=AMBER)

    footer(
        "Source: NOAA FOSS Commercial Landings (statewide Alaska; ex-vessel value; "
        f"latest finalised year {y_max}). Aggregated to protect confidential vessel/processor "
        "data (NOAA rule of three).",
        guide_url="/dashboard_guide")
