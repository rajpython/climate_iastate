"""Page 4 — Bottom Conditions: EBS Cold Pool (AFSC observed).

The eastern Bering Sea **cold pool** (shelf bottom water ≤ 2 °C, formed under winter
sea ice and persisting through summer) is a first-order control on groundfish and
crab distribution — and is invisible to SST. This page surfaces the *observed*
cold-pool index from the AFSC summer bottom-trawl survey: the validated, directly
downloadable ground-truth against which modelled bottom temperature (Bering10K ROMS,
CEFI MOM6 NEP) will later be compared.

Data is **annual and lagged** (one summer survey per year; not near-real-time) — the
page is labelled accordingly.

Fetch with: ``mhw-fetch-coldpool``

Run:
    streamlit run src/dashboard/MHW_Dashboard.py   (then pick this page)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
_PARQUET = RAW_DIR / "coldpool_index_observed.parquet"

# Threshold column choices (label -> parquet column).
_THRESHOLDS = {
    "≤ 2 °C  (headline index)": "area_lte2_km2",
    "≤ 1 °C": "area_lte1_km2",
    "≤ 0 °C": "area_lte0_km2",
    "≤ −1 °C": "area_lteminus1_km2",
}


@st.cache_data(show_spinner="Loading cold-pool index …", ttl=3600)
def load_coldpool() -> pd.DataFrame | None:
    if not _PARQUET.exists():
        return None
    return pd.read_parquet(_PARQUET).sort_values("year").reset_index(drop=True)


def main() -> None:
    st.set_page_config(page_title="Cold Pool (EBS)", layout="wide", page_icon="🧊")
    st.title("🧊 Bottom Conditions — Eastern Bering Sea Cold Pool")
    st.caption(
        "Observed cold-pool index from the **NOAA AFSC summer bottom-trawl survey** "
        "(area of the EBS shelf with bottom temperature below a threshold). "
        "Annual, **lagged** — not near-real-time."
    )

    df = load_coldpool()
    if df is None:
        st.error("Cold-pool parquet not found. Run: `mhw-fetch-coldpool`")
        return

    # ---- Sidebar controls ----
    st.sidebar.header("Controls")
    thr_label = st.sidebar.selectbox("Cold-pool threshold", list(_THRESHOLDS), index=0)
    thr_col = _THRESHOLDS[thr_label]
    yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
    yr_range = st.sidebar.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
    show_bt = st.sidebar.checkbox("Overlay mean bottom temperature", value=True)

    d = df[(df["year"] >= yr_range[0]) & (df["year"] <= yr_range[1])].copy()

    # ---- Headline metrics ----
    latest = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else None
    long_mean = df[thr_col].mean()

    c1, c2, c3 = st.columns(3)
    delta = None if prev is None else f"{latest[thr_col] - prev[thr_col]:+,.0f} km² vs {int(prev['year'])}"
    c1.metric(
        f"{int(latest['year'])} cold-pool area ({thr_label.split('  ')[0]})",
        f"{latest[thr_col]:,.0f} km²",
        delta=delta,
        delta_color="inverse",  # shrinking cold pool = warming = adverse
    )
    pct_of_mean = 100.0 * latest[thr_col] / long_mean if long_mean else float("nan")
    c2.metric("vs 1982–present mean", f"{pct_of_mean:.0f}%",
              help=f"Long-term mean ≈ {long_mean:,.0f} km²")
    if pd.notna(latest.get("mean_bottom_temp")):
        c3.metric(f"{int(latest['year'])} mean bottom temp", f"{latest['mean_bottom_temp']:.2f} °C")

    # ---- Figure: area bars (+ optional bottom-temp line) ----
    n_rows = 2 if show_bt else 1
    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=(
            [f"Cold-pool area  {thr_label.split('  ')[0]}"]
            + (["Mean bottom (gear) temperature"] if show_bt else [])
        ),
    )

    fig.add_trace(
        go.Bar(
            x=d["year"], y=d[thr_col], marker_color="steelblue",
            name="Cold-pool area",
            hovertemplate="%{x}: %{y:,.0f} km²<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_hline(y=long_mean, line_dash="dash", line_color="gray", line_width=1,
                  annotation_text="1982–present mean", annotation_font_size=9, row=1, col=1)
    fig.update_yaxes(title_text="km²", row=1, col=1)

    if show_bt and "mean_bottom_temp" in d:
        fig.add_trace(
            go.Scatter(
                x=d["year"], y=d["mean_bottom_temp"], mode="lines+markers",
                line={"color": "firebrick", "width": 2}, name="Mean bottom temp",
                hovertemplate="%{x}: %{y:.2f} °C<extra></extra>",
            ),
            row=2, col=1,
        )
        fig.add_hline(y=2.0, line_dash="dot", line_color="steelblue", line_width=1,
                      annotation_text="2 °C", annotation_font_size=9, row=2, col=1)
        fig.update_yaxes(title_text="°C", row=2, col=1)

    fig.update_layout(
        height=300 * n_rows, template="plotly_white", showlegend=False,
        bargap=0.15, margin={"l": 60, "r": 20, "t": 50, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Provenance ----
    last_update = str(df["last_update"].iloc[-1])[:10] if "last_update" in df else "—"
    st.markdown(
        f"""
        **Source:** NOAA AFSC `afsc-gap-products/coldpool` (Zenodo
        [10.5281/zenodo.16915337](https://doi.org/10.5281/zenodo.16915337)) ·
        survey years {yr_min}–{yr_max} (no 2020 — survey cancelled) · last updated {last_update}.
        **Status:** *observed, lagged* (annual summer survey). This is the **validation
        target**; modelled bottom-temperature cold pool (Bering10K ROMS · CEFI MOM6 NEP)
        will be shown alongside it once ingested.
        """
    )


main()
