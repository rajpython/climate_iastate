"""Daily MHW state engine — Hobday-style exceedance detection with gap-bridging.

State variables (per grid cell per day):
    x      : threshold exceedance = max(0, SST − θ₉₀)        [°C, ≥0]
    A      : confirmed-active flag                             {0, 1}
    D      : duration = Dtilde when A=1, else 0               [days]
    I      : intensity                                         [°C]
    C      : cumulative intensity (resets on sub-threshold)    [°C·days]
    O      : onset rate                                        [°C/day]

Running state (not saved between days):
    G      : gap counter (consecutive sub-threshold days)
    Dtilde : exceedance counter with gap-bridging

All thresholds and parameters are read from config/climatology.yml.
Ice variable from OISST is in fraction [0, 1]; config `ice_threshold_percent` is
divided by 100 before comparison (same convention as Step 4).

Equations from mhw_README.md Section 6.

CLI:
    mhw-run-states --region goa --start 2023-01-01 --end 2023-12-31 [--plot] [--backend plotly|cartopy]
    mhw-backfill   --start 1982-01-01 --end 2023-12-31
"""
from __future__ import annotations

import argparse
import shutil
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from mhw.climatology.build_mu_theta import (
    PFEG_URL,
    PROJECT_ROOT,
    _load_config,
    _load_region_bbox,
    _year_cache_path,
    fetch_year,
)

# ---------------------------------------------------------------------------
# Derived paths
# ---------------------------------------------------------------------------
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
STATES_DIR   = DATA_DERIVED / "states_grid"
PLOTS_DIR    = PROJECT_ROOT / "outputs" / "plots"


# ---------------------------------------------------------------------------
# Climatology loader
# ---------------------------------------------------------------------------
def _load_climatology(
    cfg: dict,
    region_id: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (theta90, mu, lats, lons) from precomputed Zarr files.

    Returns
    -------
    theta90 : (366, n_lat, n_lon) float32
    mu      : (366, n_lat, n_lon) float32
    lats    : (n_lat,)
    lons    : (n_lon,)
    """
    paths = cfg["climatology"]["outputs"]["paths"]
    theta90_path = str(PROJECT_ROOT / paths["theta90"]).replace(".zarr", f"_{region_id}.zarr")
    mu_path      = str(PROJECT_ROOT / paths["mu"]).replace(".zarr", f"_{region_id}.zarr")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t_ds = xr.open_zarr(theta90_path, consolidated=False)
        m_ds = xr.open_zarr(mu_path,      consolidated=False)
    theta90 = t_ds["theta90"].values.astype(np.float32)
    mu      = m_ds["mu"].values.astype(np.float32)
    lats    = t_ds["lat"].values
    lons    = t_ds["lon"].values
    t_ds.close()
    m_ds.close()
    return theta90, mu, lats, lons


# ---------------------------------------------------------------------------
# Running state container
# ---------------------------------------------------------------------------
class StateBuffer:
    """Mutable running state for the MHW state engine (one per region/grid)."""

    def __init__(self, n_lat: int, n_lon: int, confirm_days: int) -> None:
        shape = (n_lat, n_lon)
        self.G      = np.zeros(shape, dtype=np.float32)   # gap counter
        self.Dtilde = np.zeros(shape, dtype=np.float32)   # exceedance counter
        self.C      = np.zeros(shape, dtype=np.float32)   # cumulative intensity
        self.A_prev = np.zeros(shape, dtype=bool)          # A on previous day
        self.I_prev = np.zeros(shape, dtype=np.float32)   # I on previous day
        # Rolling buffer for physical_start onset.
        # Size: confirm_days+1  (index 0 = oldest = t−confirm_days, index −1 = current).
        self.I_buf  = np.zeros((confirm_days + 1, n_lat, n_lon), dtype=np.float32)


# ---------------------------------------------------------------------------
# Per-day state update (Section 6 equations)
# ---------------------------------------------------------------------------
def _update_one_day(
    sst:   np.ndarray,   # (n_lat, n_lon) — may contain NaN
    ice:   np.ndarray,   # (n_lat, n_lon) fraction [0, 1]
    theta: np.ndarray,   # (n_lat, n_lon) θ₉₀ for this DOY
    mu_t:  np.ndarray,   # (n_lat, n_lon) μ   for this DOY
    state: StateBuffer,
    *,
    gap_days:     int,
    confirm_days: int,
    int_ref:      str,   # "threshold" | "climatological_mean"
    onset_ref:    str,   # "physical_start" | "at_confirmation"
    k_days:       int,
    apply_ice:    bool,
    ice_thresh:   float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Apply Section 6 equations for one day. Updates state in-place.

    Returns (x, A, D, I, C, O) — all shape (n_lat, n_lon).
    """
    # ---- Valid mask ----
    ice_mask = (ice > ice_thresh) if apply_ice else np.zeros_like(sst, dtype=bool)
    valid    = ~ice_mask & np.isfinite(sst) & np.isfinite(theta)

    # ---- 6.1  Threshold exceedance ----
    x   = np.where(valid, np.maximum(0.0, sst - theta), 0.0).astype(np.float32)
    exc = x > 0  # bool

    # ---- 6.2  Gap counter + Dtilde ----
    new_G = np.where(exc, 0.0, state.G + 1.0)
    new_Dtilde = np.where(
        exc,
        state.Dtilde + 1.0,
        np.where(new_G <= gap_days, state.Dtilde + 1.0, 0.0),
    )
    # Ice-covered / NaN cells → reset all running state
    state.G      = np.where(valid, new_G,      0.0).astype(np.float32)
    state.Dtilde = np.where(valid, new_Dtilde, 0.0).astype(np.float32)

    # ---- 6.3  Confirmed event indicator ----
    A = (state.Dtilde >= confirm_days).astype(np.uint8)

    # ---- 6.4  Intensity (raw — not conditioned on A) ----
    if int_ref == "threshold":
        I = x.copy()
    else:  # "climatological_mean"
        I = np.where(valid, np.maximum(0.0, sst - mu_t), 0.0).astype(np.float32)

    # ---- 6.4  Duration ----
    D = np.where(A, state.Dtilde, 0.0).astype(np.float32)

    # ---- 6.4  Cumulative intensity ----
    # Accumulates on exceedance days; resets to 0 on any sub-threshold day
    # (including bridged gap days — see README note on C independence from A).
    state.C = np.where(exc & valid, state.C + I, 0.0).astype(np.float32)

    # ---- 6.4  Onset rate ----
    O = np.zeros_like(I)

    if onset_ref == "physical_start":
        # Shift buffer left; insert current I at the newest slot.
        state.I_buf = np.roll(state.I_buf, -1, axis=0)
        state.I_buf[-1] = I
        # Onset computed only on the confirmation day (A just turned on).
        just_confirmed = (A == 1) & (~state.A_prev)
        if np.any(just_confirmed):
            # After rolling:
            #   I_buf[0]       = I at t−confirm_days = I at s_g − 1
            #   I_buf[k_days]  = I at t−confirm_days+k = I at s_g + k − 1
            # O = (I[s_g+k−1] − I[s_g−1]) / k  (telescoped slope)
            onset_val = (state.I_buf[k_days] - state.I_buf[0]) / k_days
            O = np.where(just_confirmed, onset_val, 0.0).astype(np.float32)

    elif onset_ref == "at_confirmation":
        # Forward-only: onset during first k days of confirmed event (D = 5..4+k).
        in_window = (
            (A == 1)
            & (D >= confirm_days)
            & (D <= confirm_days - 1 + k_days)
        )
        O = np.where(in_window, I - state.I_prev, 0.0).astype(np.float32)

    # ---- Update lingering state ----
    state.A_prev = A.astype(bool)
    state.I_prev = I.copy()

    return x, A, D, I, state.C.copy(), O


# ---------------------------------------------------------------------------
# Main engine loop
# ---------------------------------------------------------------------------
def run_state_engine(
    region_id:     str,
    start_date:    date,
    end_date:      date,
    cfg:           dict,
    *,
    use_cache:     bool         = True,
    initial_state: StateBuffer | None = None,
    verbose:       bool         = True,
) -> tuple[xr.Dataset, StateBuffer]:
    """Run the MHW state engine from start_date to end_date (inclusive).

    Parameters
    ----------
    initial_state : StateBuffer, optional
        Pass in a StateBuffer to continue from a previous run (backfill).
        If None, all state is initialised to zero.

    Returns
    -------
    ds    : xr.Dataset with variables [x, A, D, I, C, O] on [time, lat, lon]
    state : final StateBuffer (pass to next call for continuous backfill)
    """
    # --- Config ---
    mhw          = cfg["mhw_definition"]
    gap_days     = mhw["gap_days"]
    confirm_days = mhw["confirm_days"]
    int_ref      = mhw["intensity_reference"]

    onset_cfg = cfg["onset"]
    k_days    = onset_cfg["k_days"]
    onset_ref = onset_cfg["onset_reference"]

    masking    = cfg["climatology"]["masking"]
    apply_ice  = masking["apply_ice_mask"]
    ice_thresh = masking["ice_threshold_percent"] / 100.0  # fraction

    # --- Load climatology ---
    theta90, mu_arr, lats, lons = _load_climatology(cfg, region_id)
    n_lat, n_lon = len(lats), len(lons)

    # --- Date range ---
    n_days     = (end_date - start_date).days + 1
    date_range = [start_date + timedelta(days=i) for i in range(n_days)]
    years      = sorted(set(d.year for d in date_range))

    bbox  = _load_region_bbox(region_id)
    state = initial_state or StateBuffer(n_lat, n_lon, confirm_days)

    # --- Output arrays ---
    out_x = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
    out_A = np.zeros((n_days, n_lat, n_lon), dtype=np.uint8)
    out_D = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
    out_I = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
    out_C = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
    out_O = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)

    # --- Open remote connection if needed ---
    need_remote = any(
        not (use_cache and _year_cache_path(region_id, yr).exists())
        for yr in years
    )
    remote_ds = None
    if need_remote:
        if verbose:
            print("  Connecting to PFEG ERDDAP …", flush=True)
        remote_ds = xr.open_dataset(PFEG_URL, engine="netcdf4")
        if verbose:
            print("  Connected.\n", flush=True)

    # Map each date in our range → output array index
    day_to_oi = {d: i for i, d in enumerate(date_range)}

    for year in years:
        if verbose:
            print(f"  Year {year}: loading SST …", flush=True)
        ds_yr = fetch_year(region_id, year, bbox, remote_ds, use_cache=use_cache)

        # Map time axis → Python date objects
        yr_dates = pd.DatetimeIndex(ds_yr.time.values).date.tolist()
        yr_date_to_i = {d: i for i, d in enumerate(yr_dates)}

        sst_vals = ds_yr["sst"].values  # (n_time, n_lat, n_lon)
        ice_vals = ds_yr["ice"].values

        # Verify grid alignment
        if sst_vals.shape[1:] != (n_lat, n_lon):
            raise RuntimeError(
                f"SST grid {sst_vals.shape[1:]} != theta90 grid ({n_lat}, {n_lon}). "
                "Ensure the same region bbox is used for both climatology and states."
            )

        days_in_range = [d for d in yr_dates if d in day_to_oi]
        if verbose:
            print(f"         processing {len(days_in_range)} days …", flush=True)

        for d in days_in_range:
            oi   = day_to_oi[d]
            yr_i = yr_date_to_i[d]
            doy  = d.timetuple().tm_yday  # 1–366

            x, A, D, I, C, O = _update_one_day(
                sst_vals[yr_i], ice_vals[yr_i],
                theta90[doy - 1], mu_arr[doy - 1],
                state,
                gap_days=gap_days, confirm_days=confirm_days,
                int_ref=int_ref, onset_ref=onset_ref, k_days=k_days,
                apply_ice=apply_ice, ice_thresh=ice_thresh,
            )
            out_x[oi] = x
            out_A[oi] = A
            out_D[oi] = D
            out_I[oi] = I
            out_C[oi] = C
            out_O[oi] = O

        ds_yr.close()
        if verbose and days_in_range:
            last_oi = day_to_oi[days_in_range[-1]]
            n_active = int(out_A[last_oi].sum())
            print(f"         done  (active cells on {days_in_range[-1]}: {n_active})",
                  flush=True)

    if remote_ds is not None:
        remote_ds.close()

    # --- Build output Dataset ---
    times = np.array([np.datetime64(str(d)) for d in date_range])
    ds = xr.Dataset(
        {
            "x": (["time", "lat", "lon"], out_x,
                  {"long_name": "SST exceedance above theta90", "units": "degC"}),
            "A": (["time", "lat", "lon"], out_A,
                  {"long_name": "Confirmed active MHW flag", "units": "1"}),
            "D": (["time", "lat", "lon"], out_D,
                  {"long_name": "MHW duration", "units": "1"}),
            "I": (["time", "lat", "lon"], out_I,
                  {"long_name": "MHW intensity", "units": "degC"}),
            "C": (["time", "lat", "lon"], out_C,
                  {"long_name": "Cumulative MHW intensity", "units": "degC days"}),
            "O": (["time", "lat", "lon"], out_O,
                  {"long_name": "Onset rate", "units": "degC/day"}),
        },
        coords={
            "time": ("time", times),
            "lat":  ("lat",  lats),
            "lon":  ("lon",  lons),
        },
        attrs={
            "region":              region_id,
            "start_date":          str(start_date),
            "end_date":            str(end_date),
            "gap_days":            gap_days,
            "confirm_days":        confirm_days,
            "intensity_reference": int_ref,
            "onset_reference":     onset_ref,
        },
    )
    return ds, state


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def _states_path(region_id: str, start_date: date, end_date: date) -> Path:
    return STATES_DIR / f"states_{region_id}_{start_date}_{end_date}.zarr"


def save_states(ds: xr.Dataset, path: Path) -> None:
    STATES_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.rmtree(path)
    ds.to_zarr(str(path), mode="w")
    print(f"  States saved → {path}")


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------
def _active_fraction_series(A_arr: np.ndarray) -> np.ndarray:
    """Unweighted spatial mean of active flag per day."""
    return A_arr.mean(axis=(1, 2))


def _pick_best_cell(A_arr: np.ndarray) -> tuple[int, int]:
    """Return (lat_i, lon_i) of cell with highest mean active fraction."""
    mean_A    = A_arr.mean(axis=0)
    best_flat = int(np.argmax(mean_A))
    return np.unravel_index(best_flat, mean_A.shape)


# ---------------------------------------------------------------------------
# Plotly visualisation
# ---------------------------------------------------------------------------
def plot_states_plotly(
    ds:        xr.Dataset,
    region_id: str,
    out_dir:   Path,
) -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    lats     = ds.lat.values
    lons     = ds.lon.values
    times    = pd.DatetimeIndex(ds.time.values)
    A_arr    = ds["A"].values          # (n_days, n_lat, n_lon)
    I_arr    = ds["I"].values
    x_arr    = ds["x"].values

    act_frac = _active_fraction_series(A_arr)
    pi       = int(np.argmax(act_frac))
    peak_dt  = times[pi].strftime("%Y-%m-%d")

    # ---- 1. Map: active flag A ----
    fig_A = go.Figure(go.Heatmap(
        z=A_arr[pi].astype(float), x=lons, y=lats,
        colorscale=[[0, "white"], [1, "crimson"]],
        zmin=0, zmax=1,
        colorbar=dict(title="A (0/1)"),
    ))
    fig_A.update_layout(
        title=f"Active MHW flag — {region_id.upper()} — {peak_dt} (peak active day)",
        height=400, width=900,
    )
    out_A = out_dir / f"states_A_map_{region_id}.html"
    fig_A.write_html(str(out_A))
    fig_A.write_image(str(out_A.with_suffix(".png")), scale=2)
    fig_A.show()
    print(f"  Plot (A map Plotly)       → {out_A.with_suffix('.png')}")

    # ---- 2. Map: intensity I ----
    vmax_I = float(np.nanmax(I_arr)) or 1.0
    fig_I = go.Figure(go.Heatmap(
        z=I_arr[pi], x=lons, y=lats,
        colorscale="RdYlBu_r",
        zmin=0, zmax=vmax_I,
        colorbar=dict(title="I (°C)"),
    ))
    fig_I.update_layout(
        title=f"MHW Intensity — {region_id.upper()} — {peak_dt}",
        height=400, width=900,
    )
    out_I = out_dir / f"states_I_map_{region_id}.html"
    fig_I.write_html(str(out_I))
    fig_I.write_image(str(out_I.with_suffix(".png")), scale=2)
    fig_I.show()
    print(f"  Plot (I map Plotly)       → {out_I.with_suffix('.png')}")

    # ---- 3. Time series: spatially-averaged active fraction ----
    fig_ts = go.Figure(go.Scatter(
        x=times, y=act_frac, mode="lines",
        line=dict(color="crimson", width=2),
    ))
    fig_ts.update_layout(
        title=f"Active MHW Fraction — {region_id.upper()} — "
              f"{ds.attrs['start_date']} to {ds.attrs['end_date']}",
        xaxis_title="Date", yaxis_title="Active cell fraction",
        yaxis=dict(range=[0, max(0.05, float(act_frac.max()) * 1.1)]),
        height=400, width=1000,
    )
    out_ts = out_dir / f"states_active_frac_{region_id}.html"
    fig_ts.write_html(str(out_ts))
    fig_ts.write_image(str(out_ts.with_suffix(".png")), scale=2)
    fig_ts.show()
    print(f"  Plot (active frac Plotly) → {out_ts.with_suffix('.png')}")

    # ---- 4. Single-cell: exceedance x, intensity I, A shading ----
    bi, bj      = _pick_best_cell(A_arr)
    cell_lat    = float(lats[bi])
    cell_lon    = float(lons[bj])
    x_cell      = x_arr[:, bi, bj]
    I_cell      = I_arr[:, bi, bj]
    A_cell      = A_arr[:, bi, bj]

    fig_cell = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        subplot_titles=[
            f"Exceedance x (SST − θ₉₀) at ({cell_lat:.2f}°N, {cell_lon:.2f}°E)",
            "Intensity I (°C)  —  orange shading = confirmed MHW (A=1)",
        ],
        vertical_spacing=0.12,
    )
    fig_cell.add_trace(go.Scatter(
        x=times, y=x_cell, mode="lines", name="x (exceedance)",
        line=dict(color="steelblue", width=1.5),
    ), row=1, col=1)

    # Shade confirmed-MHW periods on intensity panel
    in_event = False
    t_start  = None
    shapes   = []
    for t_py, a_val in zip(times.to_pydatetime(), A_cell):
        if a_val and not in_event:
            t_start  = t_py
            in_event = True
        elif not a_val and in_event:
            shapes.append(dict(
                type="rect", xref="x2", yref="paper",
                x0=t_start, x1=t_py, y0=0, y1=1,
                fillcolor="rgba(255,165,0,0.25)", line_width=0,
            ))
            in_event = False
    if in_event:
        shapes.append(dict(
            type="rect", xref="x2", yref="paper",
            x0=t_start, x1=times[-1].to_pydatetime(), y0=0, y1=1,
            fillcolor="rgba(255,165,0,0.25)", line_width=0,
        ))

    fig_cell.add_trace(go.Scatter(
        x=times, y=I_cell, mode="lines", name="I (intensity)",
        line=dict(color="crimson", width=1.5),
    ), row=2, col=1)
    fig_cell.update_layout(
        shapes=shapes,
        height=600, width=1000,
        title=f"Single-cell MHW state — {region_id.upper()}",
    )
    out_cell = out_dir / f"states_cell_{region_id}.html"
    fig_cell.write_html(str(out_cell))
    fig_cell.write_image(str(out_cell.with_suffix(".png")), scale=2)
    fig_cell.show()
    print(f"  Plot (single cell Plotly) → {out_cell.with_suffix('.png')}")


# ---------------------------------------------------------------------------
# Cartopy visualisation
# ---------------------------------------------------------------------------
def plot_states_cartopy(
    ds:        xr.Dataset,
    region_id: str,
    out_dir:   Path,
) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.patches import Patch
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    lats     = ds.lat.values
    lons     = ds.lon.values
    times    = pd.DatetimeIndex(ds.time.values)
    A_arr    = ds["A"].values
    I_arr    = ds["I"].values
    x_arr    = ds["x"].values

    act_frac = _active_fraction_series(A_arr)
    pi       = int(np.argmax(act_frac))
    peak_dt  = times[pi].strftime("%Y-%m-%d")

    proj   = ccrs.PlateCarree()
    extent = [lons.min() - 0.5, lons.max() + 0.5,
              lats.min() - 0.5, lats.max() + 0.5]

    def _decorate(ax: "cartopy.mpl.geoaxes.GeoAxes") -> None:
        ax.set_extent(extent, crs=proj)
        ax.set_aspect("auto")
        ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=2)
        ax.coastlines(resolution="50m", linewidth=0.8, zorder=3)
        gl = ax.gridlines(draw_labels=True, linewidth=0.4,
                          color="gray", alpha=0.5, linestyle="--")
        gl.top_labels   = False
        gl.right_labels = False

    # ---- 1 + 2. Side-by-side A and I maps ----
    fig, axes = plt.subplots(
        1, 2, figsize=(18, 6),
        subplot_kw={"projection": proj},
        constrained_layout=False,
    )
    plt.subplots_adjust(left=0.04, right=0.90, top=0.88, bottom=0.08, wspace=0.18)
    fig.suptitle(
        f"MHW State Maps — {region_id.upper()} — {peak_dt} (peak active day)",
        fontsize=13,
    )

    cmap_A = mcolors.ListedColormap(["white", "crimson"])
    im0 = axes[0].pcolormesh(lons, lats, A_arr[pi].astype(float),
                             cmap=cmap_A, vmin=0, vmax=1, transform=proj)
    _decorate(axes[0])
    axes[0].set_title("Active flag (A)", fontsize=11)
    cax0 = fig.add_axes([0.455, 0.15, 0.012, 0.65])
    fig.colorbar(im0, cax=cax0).set_label("A (0/1)")

    vmax_I = float(np.nanmax(I_arr)) or 1.0
    im1 = axes[1].pcolormesh(lons, lats, I_arr[pi],
                             cmap="RdYlBu_r", vmin=0, vmax=vmax_I, transform=proj)
    _decorate(axes[1])
    axes[1].set_title("Intensity I (°C)", fontsize=11)
    cax1 = fig.add_axes([0.915, 0.15, 0.012, 0.65])
    fig.colorbar(im1, cax=cax1).set_label("I (°C)")

    out_maps = out_dir / f"states_maps_{region_id}_cartopy.png"
    fig.savefig(out_maps, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    print(f"  Plot (A+I maps Cartopy)   → {out_maps}")

    # ---- 3. Active fraction time series ----
    dates_py = times.to_pydatetime()
    fig2, ax = plt.subplots(figsize=(12, 4))
    ax.plot(dates_py, act_frac, color="crimson", linewidth=1.5)
    ax.fill_between(dates_py, act_frac, alpha=0.25, color="crimson")
    ax.set_ylim(0, max(0.05, float(act_frac.max()) * 1.15))
    ax.set_xlabel("Date")
    ax.set_ylabel("Active cell fraction")
    ax.set_title(
        f"Active MHW Fraction — {region_id.upper()} — "
        f"{ds.attrs['start_date']} to {ds.attrs['end_date']}"
    )
    ax.grid(True, linewidth=0.4, alpha=0.5)
    fig2.tight_layout()
    out_ts = out_dir / f"states_active_frac_{region_id}_cartopy.png"
    fig2.savefig(out_ts, dpi=150)
    plt.show()
    plt.close(fig2)
    print(f"  Plot (active frac Cartopy)→ {out_ts}")

    # ---- 4. Single-cell: exceedance + intensity with MHW shading ----
    bi, bj   = _pick_best_cell(A_arr)
    cell_lat = float(lats[bi])
    cell_lon = float(lons[bj])
    x_cell   = x_arr[:, bi, bj]
    I_cell   = I_arr[:, bi, bj]
    A_cell   = A_arr[:, bi, bj]

    fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    ax3a.plot(dates_py, x_cell, color="steelblue", linewidth=1.5, label="x (exceedance)")
    ax3a.axhline(0, color="k", linewidth=0.5)
    ax3a.set_ylabel("SST − θ₉₀ (°C)")
    ax3a.set_title(f"Cell ({cell_lat:.2f}°N, {cell_lon:.2f}°E) — {region_id.upper()}")
    ax3a.grid(True, linewidth=0.4, alpha=0.5)
    ax3a.legend(loc="upper left")

    ax3b.plot(dates_py, I_cell, color="crimson", linewidth=1.5, label="I (intensity)")
    # Shade confirmed-MHW periods
    in_event, t_start = False, None
    for t_py, a_val in zip(dates_py, A_cell):
        if a_val and not in_event:
            t_start  = t_py
            in_event = True
        elif not a_val and in_event:
            ax3b.axvspan(t_start, t_py, alpha=0.25, color="orange")
            in_event = False
    if in_event:
        ax3b.axvspan(t_start, dates_py[-1], alpha=0.25, color="orange")

    ax3b.set_ylabel("Intensity (°C)")
    ax3b.set_xlabel("Date")
    ax3b.grid(True, linewidth=0.4, alpha=0.5)
    ax3b.legend(handles=[
        ax3b.get_lines()[0],
        Patch(facecolor="orange", alpha=0.4, label="Confirmed MHW (A=1)"),
    ], loc="upper left")

    fig3.tight_layout()
    out_cell = out_dir / f"states_cell_{region_id}_cartopy.png"
    fig3.savefig(out_cell, dpi=150)
    plt.show()
    plt.close(fig3)
    print(f"  Plot (single cell Cartopy)→ {out_cell}")


# ---------------------------------------------------------------------------
# CLI: mhw-run-states
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run MHW state engine for a test period."
    )
    parser.add_argument("--region",  default="goa",
                        help="Region ID (default: goa)")
    parser.add_argument("--start",   required=True,
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end",     required=True,
                        help="End date YYYY-MM-DD")
    parser.add_argument("--plot",    action="store_true",
                        help="Generate diagnostic plots")
    parser.add_argument("--backend", choices=["plotly", "cartopy"], default="plotly",
                        help="Plot backend (default: plotly)")
    parser.add_argument("--no-cache", dest="no_cache", action="store_true",
                        help="Re-download even if yearly NetCDF cache exists")
    args = parser.parse_args(argv)

    cfg   = _load_config()
    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    print(f"=== MHW State Engine: region={args.region}  {start} → {end} ===")
    print(f"    gap_days={cfg['mhw_definition']['gap_days']}  "
          f"confirm_days={cfg['mhw_definition']['confirm_days']}  "
          f"intensity_ref={cfg['mhw_definition']['intensity_reference']}\n")

    ds, _ = run_state_engine(
        args.region, start, end, cfg,
        use_cache=not args.no_cache,
    )

    A_arr    = ds["A"].values
    act_frac = _active_fraction_series(A_arr)
    peak_idx = int(np.argmax(act_frac))
    peak_day = pd.DatetimeIndex(ds.time.values)[peak_idx].strftime("%Y-%m-%d")

    print(f"\nSummary:")
    print(f"  Days processed     : {len(ds.time)}")
    print(f"  Days with any MHW  : {int((act_frac > 0).sum())}")
    print(f"  Peak active frac   : {act_frac.max():.3f}  ({peak_day})")
    print(f"  Max duration       : {float(ds['D'].values.max()):.0f} days")
    print(f"  Max intensity      : {float(ds['I'].values.max()):.2f} °C")

    out_path = _states_path(args.region, start, end)
    save_states(ds, out_path)

    if args.plot:
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)
        print("\nGenerating plots …")
        if args.backend == "cartopy":
            plot_states_cartopy(ds, args.region, PLOTS_DIR)
        else:
            plot_states_plotly(ds, args.region, PLOTS_DIR)

    print("\nDone.")


# ---------------------------------------------------------------------------
# CLI: mhw-backfill
# ---------------------------------------------------------------------------
def backfill_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Backfill MHW states + aggregates year-by-year, then rebuild risk table."
    )
    parser.add_argument("--start",     default="1982-01-01",
                        help="Start date (default: 1982-01-01)")
    parser.add_argument("--end",       default=str(date.today()),
                        help="End date (default: today)")
    parser.add_argument("--region",    default="goa",
                        help="Region ID (default: goa)")
    parser.add_argument("--no-cache",  dest="no_cache",   action="store_true",
                        help="Re-download even if yearly NetCDF cache exists")
    parser.add_argument("--skip-risk", dest="skip_risk",  action="store_true",
                        help="Skip risk-table rebuild at end")
    parser.add_argument("--skip-zarr", dest="skip_zarr",  action="store_true",
                        help="Do not save per-year state zarr files (saves ~50 MB/yr)")
    args = parser.parse_args(argv)

    cfg   = _load_config()
    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    print(f"=== MHW Backfill: region={args.region}  {start} → {end} ===")
    print(f"    save_zarr={not args.skip_zarr}  skip_risk={args.skip_risk}\n")

    # Lazy-import aggregation + risk helpers to avoid circular imports at module level
    from mhw.states.aggregates import (
        AGGREGATES_DIR, _load_mask_weights, aggregate_region, save_aggregates,
    )
    from mhw.states.risk import compute_risk_table, save_risk_table

    years = list(range(start.year, end.year + 1))
    state: StateBuffer | None = None   # carry state across year boundaries
    mask    = None
    weights = None

    completed = 0
    for year in years:
        yr_start = max(start, date(year, 1, 1))
        yr_end   = min(end,   date(year, 12, 31))
        print(f"--- {year}  ({yr_start} → {yr_end}) ---", flush=True)

        ds_yr, state = run_state_engine(
            args.region, yr_start, yr_end, cfg,
            use_cache=not args.no_cache,
            initial_state=state,
        )

        # Load mask + weights once (grid is constant across all years)
        if mask is None:
            mask, weights = _load_mask_weights(
                args.region,
                ds_yr["lat"].values,
                ds_yr["lon"].values,
            )
            n_mask = int(mask.sum())
            print(f"    Mask loaded: {n_mask} cells in '{args.region}'", flush=True)

        # Summary stats
        A_arr    = ds_yr["A"].values
        act_frac = _active_fraction_series(A_arr)
        peak_f   = float(act_frac.max())
        mhw_days = int((act_frac > 0).sum())
        print(f"    MHW days: {mhw_days}  peak frac: {peak_f:.3f}", flush=True)

        # Save per-year zarr (full-date naming matches _find_states_zarr convention)
        if not args.skip_zarr:
            out_zarr = STATES_DIR / f"states_{args.region}_{yr_start}_{yr_end}.zarr"
            save_states(ds_yr, out_zarr)

        # Aggregate and upsert into region_daily parquet
        df_yr = aggregate_region(ds_yr, mask, weights)
        save_aggregates(df_yr, args.region)

        ds_yr.close()
        completed += 1
        print(f"    [{completed}/{len(years)}] done", flush=True)

    # Rebuild risk percentile table from the full backfill distribution (frozen mode)
    if not args.skip_risk and completed > 0:
        print(f"\nRebuilding risk table from full distribution ({completed} years) …",
              flush=True)
        agg_path = AGGREGATES_DIR / f"region_daily_{args.region}.parquet"
        full_df  = pd.read_parquet(agg_path)
        full_df["date"] = pd.to_datetime(full_df["date"]).dt.date
        risk_df  = compute_risk_table(full_df)
        risk_out = save_risk_table(risk_df, args.region)
        print(f"  Risk table → {risk_out}  ({len(risk_df)} rows)")

    total_rows = 0
    agg_path = DATA_DERIVED / "aggregates_region" / f"region_daily_{args.region}.parquet"
    if agg_path.exists():
        total_rows = len(pd.read_parquet(agg_path))
    print(f"\nBackfill complete. {completed} years processed, "
          f"{total_rows} total rows in parquet.")


if __name__ == "__main__":
    main()
