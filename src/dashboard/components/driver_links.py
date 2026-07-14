"""Cross-zone climate-driver links — the shared 3×3 driver × metric matrix and its plain-English
walk-through, plus the monthly driver/target builders reused by the region-scoped panel.

The matrix answers "which ESR zone does each index (PDO / AO / NPI) line up with most strongly, for
heatwave area / intensity / onset, and at what lead?" — a single cross-zone view. It lives on its
own page (``pages/driver_correlations.py``) and is linked from the per-region Climate Drivers tab,
so the same all-zones summary is not repeated on every region.

Everything here is **descriptive association** (lagged Pearson correlation), never causation and
never a forecast — the wording is deliberately associational.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from dashboard.components.bottom_ui import (
    BLUE,
    SLATE,
    callout,
    footer,
    inject_css,
    page_header,
    section_title,
)
from dashboard.components.predictability_panel import (
    best_lag_table,
    deseasonalize,
    lagged_cross_correlation,
    load_ao,
    load_npi,
    load_pdo,
    monthly_onset_counts,
    to_monthly_mean,
)
from dashboard.components.ts_event_metrics import (
    REGION_NAMES,
    list_regions,
    load_aggregates,
)

# Monthly MHW targets each driver is scored against. "Onset events" (monthly count of new heatwaves
# beginning) is included because event *initiation* may line up differently from heatwave
# area/intensity. Order here sets the display order.
TARGET_METRICS = ["Area fraction", "Mean intensity", "Onset events"]
_DRIVERS_ORDER = ["PDO", "AO", "NPI"]

# Stable plain-English gloss on what a *high* value of each index goes along with. Deliberately
# associational wording (no "drives"/"warms"/"causes") — these are correlations, not mechanisms.
_DRIVER_GLOSS = {
    "PDO": "The Pacific Decadal Oscillation's warm (positive) phase goes together with warmer water "
           "in the eastern Gulf of Alaska and cooler water in the central and western North Pacific.",
    "AO":  "The Arctic Oscillation's high (positive) phase goes together with cold polar air staying "
           "in the Arctic and milder mid-latitudes.",
    "NPI": "The North Pacific Index measures pressure over the Aleutian Low — a **low** NPI marks a "
           "**stronger** Aleutian Low, a pattern that goes together with warm, moist southerly flow "
           "over the Gulf of Alaska.",
}

# Natural singular phrases for the metrics in prose (the matrix headers keep the formal names).
_METRIC_PHRASE = {
    "Area fraction": "heatwave area", "Mean intensity": "heatwave intensity",
    "Onset events": "the onset rate",
}


def build_drivers_frame(ao_df, pdo_df, npi_anom) -> pd.DataFrame:
    """Monthly climate-driver frame (AO daily → month mean; PDO/NPI already monthly, NPI as
    deseasonalized anomaly). Columns: date + one per available driver (AO, PDO, NPI)."""
    drivers = to_monthly_mean(ao_df, "ao").rename(columns={"ao": "AO"})
    if pdo_df is not None and not pdo_df.empty:
        drivers = drivers.merge(pdo_df[["date", "pdo"]].rename(columns={"pdo": "PDO"}),
                                on="date", how="outer")
    if npi_anom is not None and not npi_anom.empty:
        drivers = drivers.merge(npi_anom.rename(columns={"npi": "NPI"}), on="date", how="outer")
    return drivers.sort_values("date").reset_index(drop=True)


def targets_for_region(agg_df) -> pd.DataFrame:
    """Monthly MHW targets for one region: area fraction, mean intensity, and onset-event count."""
    return (to_monthly_mean(agg_df, "area_frac").rename(columns={"area_frac": "Area fraction"})
            .merge(to_monthly_mean(agg_df, "Ibar").rename(columns={"Ibar": "Mean intensity"}),
                   on="date", how="outer")
            .merge(monthly_onset_counts(agg_df), on="date", how="outer"))


@st.cache_data(show_spinner="Comparing drivers across zones …", ttl=3600)
def cross_zone_best_lead(metric: str) -> pd.DataFrame:
    """For every region, the strongest driver-leads correlation with ``metric`` (one row per zone).

    Loads each region's aggregates and the shared basin-scale drivers, scores each driver leading
    ``metric`` by 0–6 months, and keeps the best-|r| lead per (zone, driver). Returns a tidy frame
    ``[zone, region, driver, r, lag, n]``. Cached — it sweeps all regions. Descriptive, not a fit.
    """
    ao_df, pdo_df, npi_df = load_ao(), load_pdo(), load_npi()
    if ao_df is None:
        return pd.DataFrame(columns=["zone", "region", "driver", "r", "lag", "n"])
    npi_anom = deseasonalize(npi_df, "npi") if npi_df is not None and not npi_df.empty else None
    drivers = build_drivers_frame(ao_df, pdo_df, npi_anom)

    rows: list[dict] = []
    for reg in list_regions():
        agg = load_aggregates(reg)
        if agg is None or agg.empty:
            continue
        tgt = targets_for_region(agg)
        if metric not in tgt.columns:
            continue
        best = best_lag_table(lagged_cross_correlation(drivers, tgt[["date", metric]], max_lag=6))
        zone = REGION_NAMES.get(reg, reg.upper())
        for _, b in best.iterrows():
            rows.append({"zone": zone, "region": reg, "driver": b["driver"],
                         "r": float(b["r"]), "lag": int(b["lag"]), "n": int(b["n"])})
    return pd.DataFrame(rows)


def _lead_cell_css(v: float) -> str:
    """Background CSS for a matrix cell by signed r: blue = positive, amber = negative, alpha ∝ |r|."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "background-color:#f5f6f8;color:#9aa5b1"
    a = 0.10 + 0.55 * min(abs(v) / 0.6, 1.0)
    rgb = "21,101,192" if v >= 0 else "179,89,0"
    return f"background-color:rgba({rgb},{a:.2f})"


def _plain_link_clause(drv: str, metric: str, r: float, zone: str, lag: int) -> str:
    """One plain-English clause for a driver × metric cell, correct for each index's sign convention
    (NPI is inverted: a low index = strong Aleutian Low = warmer). Wording is purely associational —
    it describes co-movement, never that one quantity causes the other."""
    m = _METRIC_PHRASE.get(metric, metric.lower())
    if drv == "NPI":
        cond = "a stronger Aleutian Low"
        direction = "higher" if r < 0 else "lower"      # low NPI (neg anomaly) ↔ warmer
    else:
        cond = "a warm-phase PDO" if drv == "PDO" else "a high AO"
        direction = "higher" if r >= 0 else "lower"
    tail = (f"in the same months as {cond}" if lag == 0
            else f"when {cond} was present about {lag} month{'s' if lag != 1 else ''} earlier")
    return (f"{m} in the **{zone}** tends to be **{direction}** {tail} "
            f"(r {r:+.2f})")


def matrix_section() -> None:
    """Compact 3×3 driver × metric matrix (strongest |r| across zones + which zone + lead) followed
    by a plain-English, association-only walk-through of every cell."""
    section_title("Strongest Driver Links — All Zones",
                  note="highest |Pearson r| across zones, and which ESR zone, per driver × metric")

    # (driver, metric) → (r, zone, lead months) with the largest |r| over every zone.
    best: dict[tuple[str, str], tuple[float, str, int]] = {}
    for metric in TARGET_METRICS:
        tidy = cross_zone_best_lead(metric)
        if tidy.empty:
            continue
        for drv in _DRIVERS_ORDER:
            sub = tidy[tidy["driver"] == drv]
            if sub.empty:
                continue
            row = sub.loc[sub["r"].abs().idxmax()]
            best[(drv, metric)] = (float(row["r"]), str(row["zone"]), int(row["lag"]))
    if not best:
        callout("Not enough overlapping months yet to compare drivers across zones.",
                icon="🗺️", tint=SLATE)
        return

    th = "padding:7px 10px;text-align:center;font-size:0.78rem;color:#5b6b7b;font-weight:600"
    header = "".join(f"<th style='{th}'>{m}</th>" for m in TARGET_METRICS)
    body = []
    for drv in _DRIVERS_ORDER:
        tds = []
        for metric in TARGET_METRICS:
            cell = best.get((drv, metric))
            if cell is None:
                tds.append("<td style='padding:7px 10px;background:#f5f6f8;color:#9aa5b1'>—</td>")
                continue
            r, zone, lag = cell
            lead = "same month" if lag == 0 else f"leads {lag} mo"
            tds.append(
                f"<td style='padding:7px 10px;text-align:center;{_lead_cell_css(r)}'>"
                f"<div style='font-weight:700;font-size:0.98rem;color:#243444'>{r:+.2f}</div>"
                f"<div style='font-size:0.72rem;color:#3a4a5b'>{zone}</div>"
                f"<div style='font-size:0.68rem;color:#5b6b7b'>{lead}</div></td>")
        body.append(f"<tr><th style='{th};text-align:left'>{drv}</th>{''.join(tds)}</tr>")
    st.markdown(
        "<table style='border-collapse:collapse;width:100%;margin:0.2rem 0 0.6rem'>"
        f"<thead><tr><th></th>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>",
        unsafe_allow_html=True)

    callout(
        "Each cell is the <b>single strongest correlation</b> (r) between that driver and metric "
        "found across all ESR zones, the <b>zone</b> where it occurs, and the <b>lead</b> (how many "
        "months the driver leads the metric). <span style='color:#1565c0'>Blue</span> = they move together; "
        "<span style='color:#b35900'>amber</span> = opposite; darker = stronger. NPI is "
        "deseasonalized (low NPI = strong Aleutian Low). Plain association (correlation), "
        "<b>not</b> causation and <b>not</b> a forecast.",
        icon="🗺️", tint=BLUE)

    # Plain-English walk-through of each cell, in normal body text (no card styling), generated
    # from the live values so it always matches the matrix above.
    lines = [
        "**What these links mean.** These are plain statistical **associations** (Pearson "
        "correlations) over the monthly record — a tendency for two things to move together, **not** "
        "evidence that one causes the other, and not a forecast. They are useful for knowing "
        "*where* each index is worth watching. All links below are weak-to-moderate.",
    ]
    for drv in _DRIVERS_ORDER:
        clauses = [_plain_link_clause(drv, metric, *best[(drv, metric)])
                   for metric in TARGET_METRICS if (drv, metric) in best]
        if not clauses:
            continue
        sentence = "; ".join(clauses)
        lines.append(f"**{drv}.** {_DRIVER_GLOSS[drv]} Here, {sentence}.")
    # Flag the weakest index (computed live, not hard-coded) as barely-there context.
    maxabs = {drv: max(abs(best[(drv, m)][0]) for m in TARGET_METRICS if (drv, m) in best)
              for drv in _DRIVERS_ORDER if any((drv, m) in best for m in TARGET_METRICS)}
    if maxabs:
        weakest = min(maxabs, key=maxabs.get)
        lines.append(
            f"The **{weakest}** links are the weakest of the three (all |r| ≤ {maxabs[weakest]:.2f}), "
            "so treat them as barely-there tendencies rather than a usable signal on their own.")
    st.markdown("\n\n".join(lines))


def render() -> None:
    """Standalone page: the cross-zone driver-links matrix + walk-through, with its own chrome."""
    inject_css()
    page_header(
        "🗺️", "Climate Driver Links", subtitle="Strongest driver associations across Alaska ESR zones",
        region_label_text="All zones",
        caption="Where each large-scale index (PDO · AO · NPI / Aleutian Low) lines up most strongly "
                "with marine-heatwave area, intensity and onset — across every ESR zone, at leads of "
                "0–6 months. Plain association, not causation and not a forecast.")
    with st.container(border=True):
        matrix_section()
    footer(
        "Source: NOAA OISST-derived monthly MHW aggregates × AO / PDO / NPI indices; lagged Pearson "
        "correlation (driver leads by 0–6 months) over the full overlapping record.",
        guide_url="/marine_heatwave_guide")
