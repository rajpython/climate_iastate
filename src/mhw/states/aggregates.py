"""Regional aggregation — Section 7 area-weighted daily metrics.

Reads grid-level MHW state arrays and applies cos(lat) weights + region masks
to produce scalar daily time series per region:

    area_frac   fraction of region cells in active MHW state   [0, 1]
    Ibar        area-weighted mean intensity (conditional on A=1)   [°C]
    Dbar        area-weighted mean duration  (conditional on A=1)   [days]
    Cbar        area-weighted mean cumulative intensity  [°C·days]
    Obar        area-weighted mean onset rate  [°C/day]

Conditional means are zero when area_frac=0 (no active cells).

Two properties worth stating because they have been misdescribed before:

* **The area_frac denominator is the STATIC mask.** `Sum(w)` is computed once from
  `weights * mask`, so a cell that never carries valid SST contributes 0 to the
  numerator and its full cos(lat) to the denominator on every day; ice-masked cells
  behave the same way on the days they are masked. Nothing "drops out" for want of
  valid SST. (Wording of record, lofra-mini 2026-09-30, who found it from the data:
  the sealed area_frac reproduces only under this reading.)
* **Obar is signed and unclamped** (SDL-030), faithful to Oliver's marineHeatWaves /
  heatwaveR. In the 20260722 vintage the negatives are **4 daily + 1 monthly** —
  chukchi daily 2, beaufort daily 2, beaufort monthly 1; no other zone, most negative
  -0.0248. Do not state that as "five values": it is a total across two series.
  Anything that log-transforms Obar, takes a rate magnitude, or filters >= 0 will
  mis-handle them.

Equations from mhw_README.md Section 7:
    area_frac  = Σ(w·A) / Σ(w)            (sum over region mask cells)
    Xbar       = Σ(w·X·A) / Σ(w·A)        (conditional mean, zero when Σ(w·A)=0)

CLI:
    mhw-aggregate --region goa --start 2023-01-01 --end 2023-12-31 [--plot] [--backend plotly|cartopy]
"""
from __future__ import annotations

import argparse
import json
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.climatology.build_mu_theta import PROJECT_ROOT, _load_config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DERIVED   = PROJECT_ROOT / "data" / "derived"
STATES_DIR     = DATA_DERIVED / "states_grid"
MASKS_PATH     = DATA_DERIVED / "masks" / "region_masks.zarr"
WEIGHTS_PATH   = DATA_DERIVED / "weights" / "weights.zarr"
AGGREGATES_DIR = DATA_DERIVED / "aggregates_region"
PLOTS_DIR      = PROJECT_ROOT / "outputs" / "plots"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _find_states_zarr(region_id: str, start_date: date, end_date: date) -> Path:
    """Return path to states zarr; raise FileNotFoundError if missing."""
    fname = f"states_{region_id}_{start_date}_{end_date}.zarr"
    p = STATES_DIR / fname
    if not p.exists():
        raise FileNotFoundError(
            f"States zarr not found: {p}\n"
            f"Run: mhw-run-states --region {region_id} --start {start_date} --end {end_date}"
        )
    return p


def _load_states(region_id: str, start_date: date, end_date: date) -> xr.Dataset:
    """Load grid-level state arrays from Zarr."""
    path = _find_states_zarr(region_id, start_date, end_date)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds = xr.open_zarr(str(path), consolidated=False)
    return ds


def _load_mask_weights(
    region_id: str,
    state_lats: np.ndarray,
    state_lons: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Load region mask and cos(lat) weights subsetted to the state grid.

    Returns
    -------
    mask    : (n_lat, n_lon) uint8   — 1 inside region, 0 outside
    weights : (n_lat, n_lon) float32 — cos(lat) area weights
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m_ds = xr.open_zarr(str(MASKS_PATH), consolidated=False)
        w_ds = xr.open_zarr(str(WEIGHTS_PATH), consolidated=False)

    mask_sub = (
        m_ds[region_id]
        .sel(lat=state_lats, lon=state_lons, method="nearest")
        .values.astype(np.uint8)
    )
    weights_sub = (
        w_ds["weights"]
        .sel(lat=state_lats, lon=state_lons, method="nearest")
        .values.astype(np.float32)
    )
    m_ds.close()
    w_ds.close()
    return mask_sub, weights_sub


# ---------------------------------------------------------------------------
# Core aggregation (Section 7 equations)
# ---------------------------------------------------------------------------
VALUE_COLUMNS = ("area_frac", "Ibar", "Dbar", "Cbar", "Obar")


def load_filled_days() -> dict[str, str]:
    """Map ``YYYY-MM-DD`` -> source string, from ``config/filled_days.json``.

    A day listed there had no OISST input in the producer's own fetch and was
    supplied from elsewhere. Missing file or unreadable JSON returns {} — the
    registry is provenance, not a gate, so its absence must not stop a build.
    """
    path = PROJECT_ROOT / "config" / "filled_days.json"
    try:
        doc = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {d: v.get("source", "filled") for d, v in doc.get("days", {}).items()}


def aggregate_region(
    ds: xr.Dataset,
    mask: np.ndarray,
    weights: np.ndarray,
    *,
    filled_days: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Compute daily region-level metrics from grid-level state arrays.

    Parameters
    ----------
    ds      : xr.Dataset with variables A, I, D, C, O; dims (time, lat, lon)
    mask    : (n_lat, n_lon) uint8
    weights : (n_lat, n_lon) float32

    Returns
    -------
    DataFrame with columns: date, area_frac, Ibar, Dbar, Cbar, Obar, plus the QC
    columns n_days_input, n_cells_valid, n_mask_cells, valid_frac when the state
    store carries them (see below).

    QC columns (added 2026-09-30; names per the LOFRA delivery spec, admin `…-18`)
    -----------------------------------------------------------------------------
    A metric alone cannot say how much real data stands behind it. Eight calendar
    days were absent from the OISST inputs and the engine scored each as a day on
    which no cell exceeded, which is indistinguishable in the output from a genuine
    quiet day -- and a row-count completeness audit cannot see it, because the rows
    are all present. These columns make it visible in the product itself:

      n_days_input   1 if the input supplied a time step for this calendar day, else 0
      n_cells_valid  mask cells with a usable observation (not ice-masked, finite
                     SST and theta90) on this day
      n_mask_cells   the zone's mask cell count (constant; the denominator)
      valid_frac     cos(lat)-weighted share of the zone with a usable observation (SST present,
                     not ice-masked AND theta90 defined -- the same valid_cells() rule the engine uses)
      n_cells_event_unscorable  mask cells inside an event (A=1) but unscorable that day; they keep
                     event continuity and are EXCLUDED from area_frac and the conditional means

    The names are not cosmetic: the sealing gate recognises count columns by the
    prefixes ``n_days`` / ``n_obs`` / ``n_valid``. The valid-cell count must NOT
    start ``n_valid`` -- Beaufort has thousands of days with zero ice-free cells,
    which the gate would read as "a value from zero inputs" and hard-fail.

    No-input rule: on a row with ``n_days_input == 0`` every value column
    (area_frac, Ibar, Dbar, Cbar, Obar) is NaN, not zero -- absence of data is not
    a measurement of zero. See :func:`to_monthly` for the monthly counterpart.

    State stores written before this change carry neither ``V`` nor ``input_present``;
    for those the QC columns are emitted as NaN rather than guessed, so an old vintage
    is never silently reported as complete.
    """
    # Load all variables to memory (GOA: 32×160×365 = ~7 MB per variable)
    A_event = ds["A"].values.astype(np.float32)   # (T, lat, lon) -- event membership (Hobday)
    # DETECTED area (vintage #6, admin ...-20261001-17 item v): a cell counts toward the area and the
    # conditional means on day t only if it is in a qualifying event AND scorable that day (V: SST
    # present, not ice-masked, theta90 defined). An unscorable day inside a <=2-day gap keeps event
    # continuity (A, D, C stay as the engine wrote them) but is never detected area -- otherwise a
    # day with no usable observation reads as a measured heatwave (the defect class of the 2026-09-30
    # missing-day episode). Stores without V (pre-QC vintages) keep the old reading.
    if "V" in ds.data_vars:
        A = A_event * ds["V"].values.astype(np.float32)
    else:
        A = A_event
    I = ds["I"].values.astype(np.float32)
    C = ds["C"].values.astype(np.float32)
    O = ds["O"].values.astype(np.float32)

    # D may be timedelta64[ns] due to CF-decoding of "units: days" attribute
    D_raw = ds["D"].values
    if np.issubdtype(D_raw.dtype, np.timedelta64):
        # Convert nanoseconds → days
        D = (D_raw.astype("timedelta64[ns]").astype(np.int64) / 86_400_000_000_000).astype(np.float32)
    else:
        D = D_raw.astype(np.float32)

    times = pd.DatetimeIndex(ds["time"].values).date.tolist()

    # Region-masked weights: w_g = cos(lat) * mask_g  — shape (n_lat, n_lon)
    # Use float64 for sums to preserve accuracy across many grid cells
    wm = (weights * mask).astype(np.float64)
    sum_wm = float(np.sum(wm))   # total region weight (constant)

    # Broadcast to (1, lat, lon) for vectorized time-axis operations
    wm3 = wm[np.newaxis, :, :]

    # --- Section 7.1: area fraction ---
    # area_frac[t] = Σ_g(w_g * A_g[t]) / Σ_g(w_g)
    sum_wA = np.sum(wm3 * A, axis=(1, 2))        # (T,)
    area_frac = (sum_wA / sum_wm).astype(np.float32)

    # --- Section 7.2: conditional means ---
    # Xbar[t] = Σ_g(w_g * X_g[t] * A_g[t]) / Σ_g(w_g * A_g[t])
    # Replace zero-denominator with NaN, then set NaN → 0
    safe_denom = np.where(sum_wA > 0, sum_wA, np.nan)

    def _cond_mean(X: np.ndarray) -> np.ndarray:
        return (np.nansum(wm3 * X * A, axis=(1, 2)) / safe_denom).astype(np.float32)

    Ibar = np.nan_to_num(_cond_mean(I), nan=0.0)
    Dbar = np.nan_to_num(_cond_mean(D), nan=0.0)
    Cbar = np.nan_to_num(_cond_mean(C), nan=0.0)
    Obar = np.nan_to_num(_cond_mean(O), nan=0.0)

    out = pd.DataFrame({
        "date":      times,
        "area_frac": area_frac,
        "Ibar":      Ibar,
        "Dbar":      Dbar,
        "Cbar":      Cbar,
        "Obar":      Obar,
    })

    # --- QC columns ---------------------------------------------------------
    n_mask = int(mask.sum())
    if "V" in ds.data_vars:
        V = ds["V"].values.astype(bool)
        m3 = mask.astype(bool)[np.newaxis, :, :]
        # in an event but unscorable that day: kept for continuity, excluded from detected area
        out["n_cells_event_unscorable"] = ((A_event > 0) & ~V & m3).sum(axis=(1, 2)).astype(np.int32)
        out["n_cells_valid"] = (V & m3).sum(axis=(1, 2)).astype(np.int32)
        out["valid_frac"] = (
            np.sum(wm3 * (V & m3), axis=(1, 2)) / sum_wm
        ).astype(np.float32)
    else:
        out["n_cells_valid"] = np.nan
        out["valid_frac"] = np.nan
        out["n_cells_event_unscorable"] = np.nan
    # The state store keeps its own variable name (input_present); the product
    # column follows the delivery spec.
    if "input_present" in ds.data_vars:
        out["n_days_input"] = ds["input_present"].values.astype(np.int8)
        no_input = out["n_days_input"].to_numpy() == 0
        out.loc[no_input, list(VALUE_COLUMNS)] = np.nan
    else:
        out["n_days_input"] = np.nan
    out["n_mask_cells"] = np.int32(n_mask)
    fd = filled_days or {}
    out["filled"] = [fd.get(str(d), "") for d in out["date"]]
    return out


def to_monthly(daily: pd.DataFrame) -> pd.DataFrame:
    """Calendar-month means of the daily product, with honest completeness counts.

    Returns one row per month (``date`` = first of month) with the value columns
    averaged over **input days only** (rows with ``n_days_input == 0`` are NaN in
    the daily product and drop out of the mean), plus:

      n_days         daily rows aggregated into the month
      n_days_input   of those, days whose input was read (NaN if unknown)
      days_in_month  the CALENDAR length of the month -- never the row count

    ``days_in_month`` is what lets a reader see that a trailing partial month is
    partial: the 2026-09-30 candidate closed on ``2026-07-01`` with
    ``n_days_in_month = 1`` -- one day of 31 declaring itself complete. It carries
    no ``n_`` prefix, so the sealing gate ignores it. A month whose every day lacks
    input has NaN values, never zeros.
    """
    df = daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    if "n_days_input" not in df:
        df["n_days_input"] = np.nan
    month = df["date"].dt.to_period("M")
    g = df.groupby(month, sort=True)
    out = g[list(VALUE_COLUMNS)].mean()          # pandas mean skips NaN rows
    out["n_days"] = g.size()
    out["n_days_input"] = g["n_days_input"].sum(min_count=1)
    out.index = out.index.to_timestamp()
    out = out.rename_axis("date").reset_index()
    out["days_in_month"] = out["date"].dt.days_in_month.astype(np.int64)
    if out["n_days_input"].notna().all():
        out["n_days_input"] = out["n_days_input"].astype(np.int64)
    return out[["date", *VALUE_COLUMNS, "n_days", "n_days_input", "days_in_month"]]


# ---------------------------------------------------------------------------
# Save/load parquet
# ---------------------------------------------------------------------------
def save_aggregates(df: pd.DataFrame, region_id: str) -> Path:
    """Write aggregate DataFrame to parquet, merging with any existing data.

    Existing rows whose dates overlap with df are replaced.
    Output: data/derived/aggregates_region/region_daily_{region_id}.parquet
    """
    AGGREGATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AGGREGATES_DIR / f"region_daily_{region_id}.parquet"

    if out_path.exists():
        existing = pd.read_parquet(out_path)
        existing = existing[~existing["date"].isin(df["date"])]
        combined = pd.concat([existing, df], ignore_index=True).sort_values("date").reset_index(drop=True)
    else:
        combined = df.sort_values("date").reset_index(drop=True)

    combined.to_parquet(out_path, index=False)
    return out_path


# ---------------------------------------------------------------------------
# Plotly time series (5 panels, opens in browser)
# ---------------------------------------------------------------------------
def plot_aggregates_plotly(df: pd.DataFrame, region_id: str) -> None:
    """Five-panel interactive Plotly time series for all aggregated metrics."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = [
        ("area_frac", "Area Fraction",                  "fraction [0,1]", "steelblue"),
        ("Ibar",      "Mean Intensity (Ī)",             "°C",             "orangered"),
        ("Dbar",      "Mean Duration (D̄)",              "days",           "purple"),
        ("Cbar",      "Mean Cumulative Intensity (C̄)", "°C·days",        "seagreen"),
        ("Obar",      "Mean Onset Rate (Ō)",            "°C/day",         "darkorange"),
    ]

    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        subplot_titles=[m[1] for m in metrics],
        vertical_spacing=0.06,
    )

    dates = pd.to_datetime(df["date"])

    for row, (col, title, ylabel, color) in enumerate(metrics, start=1):
        fig.add_trace(
            go.Scatter(
                x=dates, y=df[col],
                mode="lines",
                name=title,
                line={"color": color, "width": 1.5},
                hovertemplate=f"%{{x|%Y-%m-%d}}: %{{y:.3f}} {ylabel}<extra></extra>",
            ),
            row=row, col=1,
        )
        fig.update_yaxes(title_text=ylabel, row=row, col=1)

    fig.update_layout(
        title=f"MHW Regional Aggregates — {region_id.upper()}",
        height=1200,
        showlegend=False,
        template="plotly_white",
    )

    html_path = PLOTS_DIR / f"aggregates_{region_id}.html"
    png_path  = PLOTS_DIR / f"aggregates_{region_id}.png"
    fig.write_html(str(html_path))
    fig.write_image(str(png_path))
    print(f"  Plot (HTML) → {html_path}")
    fig.show()


# ---------------------------------------------------------------------------
# Matplotlib time series (5 panels, shading for MHW-active periods)
# ---------------------------------------------------------------------------
def plot_aggregates_cartopy(df: pd.DataFrame, region_id: str) -> None:
    """Five-panel matplotlib time series with event-period shading."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = [
        ("area_frac", "Area Fraction",                  "fraction [0,1]", "steelblue"),
        ("Ibar",      "Mean Intensity (Ī)",             "°C",             "orangered"),
        ("Dbar",      "Mean Duration (D̄)",              "days",           "purple"),
        ("Cbar",      "Mean Cumulative Intensity (C̄)", "°C·days",        "seagreen"),
        ("Obar",      "Mean Onset Rate (Ō)",            "°C/day",         "darkorange"),
    ]

    dates = pd.to_datetime(df["date"])
    active = df["area_frac"].values > 0.05   # event-active flag for shading

    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True,
                             constrained_layout=True)
    fig.suptitle(f"MHW Regional Aggregates — {region_id.upper()}", fontsize=13)

    for ax, (col, title, ylabel, color) in zip(axes, metrics):
        ax.plot(dates, df[col], color=color, linewidth=1.2)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, fontsize=10, pad=3)
        ax.grid(True, alpha=0.3)

        # Shade event-active periods in non-area_frac panels
        if col != "area_frac":
            # Find contiguous active spans and axvspan them
            in_span = False
            for i, (d, flag) in enumerate(zip(dates, active)):
                if flag and not in_span:
                    span_start = d
                    in_span = True
                elif not flag and in_span:
                    ax.axvspan(span_start, d, color="salmon", alpha=0.15, linewidth=0)
                    in_span = False
            if in_span:
                ax.axvspan(span_start, dates.iloc[-1], color="salmon", alpha=0.15, linewidth=0)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())

    png_path = PLOTS_DIR / f"aggregates_{region_id}_mpl.png"
    fig.savefig(str(png_path), dpi=150, bbox_inches="tight")
    print(f"  Plot (PNG) → {png_path}")
    plt.show()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Aggregate grid-level MHW states to region-level daily metrics."
    )
    p.add_argument("--region",  default="goa",                     help="Region ID (default: goa)")
    p.add_argument("--start",   required=True,                     help="Start date YYYY-MM-DD")
    p.add_argument("--end",     required=True,                     help="End date YYYY-MM-DD")
    p.add_argument("--plot",    action="store_true",               help="Generate time series plot")
    p.add_argument("--backend", choices=["plotly", "cartopy"],
                   default="plotly",                               help="Plot backend (default: plotly)")
    args = p.parse_args()

    start_date = date.fromisoformat(args.start)
    end_date   = date.fromisoformat(args.end)

    print(f"Loading states: {args.region}  {args.start} → {args.end} …")
    ds = _load_states(args.region, start_date, end_date)
    state_lats = ds["lat"].values
    state_lons = ds["lon"].values

    print("Loading mask + weights …")
    mask, weights = _load_mask_weights(args.region, state_lats, state_lons)
    n_mask = int(mask.sum())
    print(f"  {n_mask} cells in region '{args.region}'")

    print("Aggregating …")
    df = aggregate_region(ds, mask, weights)
    ds.close()

    # Summary stats
    peak = df.loc[df["area_frac"].idxmax()]
    print(f"  Peak day:   {peak['date']}  area_frac={peak['area_frac']:.4f}  Ibar={peak['Ibar']:.2f} °C")
    print(f"  area_frac range: [{df['area_frac'].min():.4f}, {df['area_frac'].max():.4f}]")
    print(f"  Ibar range:      [{df['Ibar'].min():.3f}, {df['Ibar'].max():.3f}] °C")
    print(f"  Dbar range:      [{df['Dbar'].min():.1f}, {df['Dbar'].max():.1f}] days")

    out_path = save_aggregates(df, args.region)
    print(f"  Saved {len(df)} rows → {out_path}")

    if args.plot:
        if args.backend == "plotly":
            plot_aggregates_plotly(df, args.region)
        else:
            plot_aggregates_cartopy(df, args.region)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
