"""Build mu[doy,lat,lon] and theta90[doy,lat,lon] climatology for a region.

Data source : PFEG CoastWatch ERDDAP OPeNDAP (aggregated, 1981–present)
  Dataset : ncdcOisst21Agg  (OISST v2.1 Final, AVHRR Only)
  URL     : https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg
  Variables: sst, ice  (ice is in fraction [0, 1])
  Config `ice_threshold_percent` (default 15) is divided by 100 for comparison.

All paths and parameters are read from config/climatology.yml — nothing is hardcoded.

CLI: mhw-build-climatology --region goa [--plot] [--no-cache]
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import xarray as xr
import yaml

from mhw.climatology.smooth_doy import compute_mu_theta, doy_window
from mhw.climatology.storage import save_climatology

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_RAW = PROJECT_ROOT / "data" / "raw"

PFEG_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg"


def _load_config() -> dict:
    with open(CONFIG_DIR / "climatology.yml") as f:
        return yaml.safe_load(f)


def _load_region_bbox(region_id: str) -> dict:
    with open(CONFIG_DIR / "regions.geojson") as f:
        fc = json.load(f)
    for feat in fc["features"]:
        if feat["properties"]["id"] == region_id:
            coords = feat["geometry"]["coordinates"][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return {
                "lat_min": min(lats), "lat_max": max(lats),
                "lon_min": min(lons), "lon_max": max(lons),
            }
    raise ValueError(f"Region '{region_id}' not found in regions.geojson")


# ---------------------------------------------------------------------------
# Year-level fetch with local NetCDF cache
# ---------------------------------------------------------------------------

def _year_cache_path(region_id: str, year: int) -> Path:
    return DATA_RAW / f"oisst_{region_id}_{year}.nc"


def fetch_year(
    region_id: str,
    year: int,
    bbox: dict,
    remote_ds: xr.Dataset,
    *,
    use_cache: bool = True,
) -> xr.Dataset:
    """Fetch one full year of SST + ice for *region_id* from an already-open remote dataset.

    Uses a persistent OPeNDAP connection (remote_ds) to avoid reconnection overhead.
    Caches each year as NetCDF in data/raw/ — subsequent runs load from cache instantly.
    Ice variable `ice` is in fraction [0, 1].
    Longitude is returned in [-180, 180) convention, coordinates named `lat`/`lon`.
    """
    cache = _year_cache_path(region_id, year)
    if use_cache and cache.exists():
        ds = xr.open_dataset(cache)
        if "sst" in ds.data_vars and "ice" in ds.data_vars:
            # Current-year files are still growing: invalidate when the last
            # cached day is ≥2 days behind today (OISST publishes ~1 day late;
            # 2-day buffer gives one extra day of margin).
            if year == date.today().year:
                stale_threshold = (
                    np.datetime64(date.today(), "D") - np.timedelta64(2, "D")
                )
                if ds["time"].values[-1].astype("datetime64[D]") < stale_threshold:
                    ds.close()
                    cache.unlink()  # stale current-year cache — re-fetch below
                else:
                    return ds
            else:
                return ds
        else:
            ds.close()
            cache.unlink()  # corrupt/incomplete — re-fetch

    lon_min_360 = bbox["lon_min"] % 360
    lon_max_360 = bbox["lon_max"] % 360

    sub = remote_ds[["sst", "ice"]].sel(
        time=slice(f"{year}-01-01", f"{year}-12-31"),
        zlev=0.0,
        latitude=slice(bbox["lat_min"], bbox["lat_max"]),
        longitude=slice(lon_min_360, lon_max_360),
    ).load()

    # Rename coords to lat/lon; convert longitude to [-180, 180)
    sub = sub.rename({"latitude": "lat", "longitude": "lon"})
    lon = sub.lon.values.copy()
    lon = ((lon + 180) % 360) - 180
    sub = sub.assign_coords(lon=lon).sortby("lon")

    # Strip ERDDAP metadata attrs that can collide with NetCDF reserved names
    sub.attrs = {}
    for v in sub.data_vars:
        sub[v].attrs = {}

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(".tmp.nc")
    sub.to_netcdf(tmp)        # write to temp first
    tmp.rename(cache)         # atomic rename on success
    return xr.open_dataset(cache)


# ---------------------------------------------------------------------------
# Main climatology build
# ---------------------------------------------------------------------------

def build_climatology(
    region_id: str,
    cfg: dict,
    *,
    use_cache: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fetch baseline years, apply ice masking, compute mu and theta90 per DOY.

    Returns
    -------
    mu       : (366, n_lat, n_lon) float32
    theta90  : (366, n_lat, n_lon) float32
    lats     : (n_lat,) coordinate array
    lons     : (n_lon,) coordinate array
    """
    baseline = cfg["climatology"]["baseline"]
    start_yr = baseline["start_year"]
    end_yr   = baseline["end_year"]
    years    = list(range(start_yr, end_yr + 1))

    smoothing    = cfg["climatology"]["smoothing"]
    half_window  = smoothing["half_window"]
    percentile   = cfg["climatology"]["threshold"]["percentile"] * 100  # 0.90 → 90.0

    masking      = cfg["climatology"]["masking"]
    apply_mask   = masking["apply_ice_mask"]
    ice_thresh   = masking["ice_threshold_percent"] / 100.0  # fraction

    bbox = _load_region_bbox(region_id)

    # -----------------------------------------------------------------------
    # Phase 1: load / fetch all baseline years
    # -----------------------------------------------------------------------
    print(f"Baseline: {start_yr}–{end_yr} ({len(years)} years)")
    print(f"Ice masking: {'ON' if apply_mask else 'OFF'} (threshold {ice_thresh:.2f} fraction)")
    print(f"Source: PFEG CoastWatch ERDDAP (ncdcOisst21Agg)\n")
    print(f"Fetching / loading yearly cache …\n")

    sst_arrays: list[np.ndarray] = []
    doy_arrays: list[np.ndarray] = []
    lats = lons = None

    # Open remote dataset once — reused for every uncached year
    need_remote = any(
        not (use_cache and _year_cache_path(region_id, yr).exists())
        for yr in years
    )
    remote_ds = None
    if need_remote:
        print(f"  Opening PFEG ERDDAP connection …", flush=True)
        remote_ds = xr.open_dataset(PFEG_URL, engine="netcdf4")
        print(f"  Connected.\n")

    t0 = time.time()
    for i, year in enumerate(years, 1):
        cache = _year_cache_path(region_id, year)
        cached = use_cache and cache.exists()
        tag = "cached" if cached else "fetching from ERDDAP"
        print(f"  {year} ({i:2d}/{len(years)}) … {tag}", end="", flush=True)
        t_yr = time.time()

        ds = fetch_year(region_id, year, bbox, remote_ds, use_cache=use_cache)
        sst = ds["sst"].values.astype(np.float32)   # (days, lat, lon)
        icec = ds["ice"].values.astype(np.float32)

        if lats is None:
            lats = ds["lat"].values
            lons = ds["lon"].values

        # Ice masking: NaN SST where ice fraction exceeds threshold
        if apply_mask:
            sst[icec > ice_thresh] = np.nan

        # Day-of-year for each time step
        doys = ds["time"].dt.dayofyear.values   # int, 1..366
        ds.close()

        sst_arrays.append(sst)
        doy_arrays.append(doys)
        print(f"  ({len(doys)} days, {time.time()-t_yr:.1f}s)")

    if remote_ds is not None:
        remote_ds.close()
    print(f"\nAll years loaded in {time.time()-t0:.1f}s")

    # -----------------------------------------------------------------------
    # Phase 2: assemble full time-series
    # -----------------------------------------------------------------------
    all_sst = np.concatenate(sst_arrays, axis=0)   # (n_days_total, n_lat, n_lon)
    all_doy = np.concatenate(doy_arrays, axis=0)   # (n_days_total,)
    n_days, n_lat, n_lon = all_sst.shape
    print(f"\nAssembled: {n_days} days × {n_lat} lat × {n_lon} lon")

    # -----------------------------------------------------------------------
    # Phase 3: DOY statistics
    # -----------------------------------------------------------------------
    print(f"\nComputing DOY statistics (half_window={half_window}, p={percentile:.0f}) …")
    mu      = np.full((366, n_lat, n_lon), np.nan, dtype=np.float32)
    theta90 = np.full((366, n_lat, n_lon), np.nan, dtype=np.float32)

    for d in range(1, 367):
        window_doys = doy_window(d, half_window=half_window, n_doys=366)
        row_mask    = np.isin(all_doy, window_doys)
        stack       = all_sst[row_mask]           # (n_window_samples, n_lat, n_lon)

        if stack.shape[0] > 0:
            mu[d - 1], theta90[d - 1] = compute_mu_theta(stack, percentile=percentile)

        if d % 60 == 0 or d == 1 or d == 366:
            n_valid = int(np.sum(np.isfinite(mu[d - 1])))
            print(f"  DOY {d:3d}/366 — {stack.shape[0]:4d} samples, {n_valid:,} valid cells")

    return mu, theta90, lats, lons


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_climatology_plotly(
    mu: np.ndarray,
    theta90: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    region_id: str,
) -> None:
    """Four theta90 maps (DOY 1/90/180/270) + one-cell annual cycle."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Figure 1: theta90 maps for 4 DOYs ----
    doy_labels = {1: "DOY 1 (Jan 1)", 90: "DOY 90 (Apr 1)", 180: "DOY 180 (Jun 29)", 270: "DOY 270 (Sep 27)"}
    fig_maps = make_subplots(
        rows=2, cols=2,
        subplot_titles=list(doy_labels.values()),
        vertical_spacing=0.12,
        horizontal_spacing=0.06,
    )
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    vmin = float(np.nanmin(theta90))
    vmax = float(np.nanmax(theta90))

    for (row, col), doy in zip(positions, doy_labels.keys()):
        fig_maps.add_trace(
            go.Heatmap(
                z=theta90[doy - 1],
                x=lons,
                y=lats,
                colorscale="RdYlBu_r",
                zmin=vmin,
                zmax=vmax,
                colorbar=dict(title="θ90 (°C)", len=0.4, x=1.02, y=0.5) if (row, col) == (1, 2) else dict(showticklabels=False, len=0),
                showscale=(row == 1 and col == 2),
            ),
            row=row, col=col,
        )

    fig_maps.update_layout(
        title_text=f"theta90 — {region_id.upper()} — Seasonal Snapshots",
        title_x=0.5,
        height=600,
        width=900,
    )
    maps_html = out_dir / f"climatology_theta90_maps_{region_id}.html"
    fig_maps.write_html(str(maps_html))
    print(f"  Plot (maps HTML)  → {maps_html}")
    try:
        fig_maps.write_image(str(maps_html).replace(".html", ".png"))
        print(f"  Plot (maps PNG)   → {str(maps_html).replace('.html', '.png')}")
    except Exception:
        pass

    # ---- Figure 2: single-cell annual cycle ----
    # Pick a mid-GOA cell
    lat_idx = np.argmin(np.abs(lats - 57.0))
    lon_idx = np.argmin(np.abs(lons - (-150.0)))
    cell_lat = float(lats[lat_idx])
    cell_lon = float(lons[lon_idx])
    doys = np.arange(1, 367)

    fig_cycle = go.Figure()
    fig_cycle.add_trace(go.Scatter(
        x=doys, y=mu[:, lat_idx, lon_idx],
        mode="lines", name="Mean",
        line=dict(color="steelblue", width=2),
    ))
    fig_cycle.add_trace(go.Scatter(
        x=doys, y=theta90[:, lat_idx, lon_idx],
        mode="lines", name="90th Percentile",
        line=dict(color="crimson", width=2),
    ))
    fig_cycle.update_layout(
        title=f"Annual Cycle — {region_id.upper()} cell ({cell_lat:.2f}°N, {cell_lon:.2f}°E)",
        xaxis_title="Day of Year",
        yaxis_title="SST (°C)",
        legend=dict(x=0.02, y=0.98),
        width=900,
        height=450,
    )
    cycle_html = out_dir / f"climatology_annual_cycle_{region_id}.html"
    fig_cycle.write_html(str(cycle_html))
    print(f"  Plot (cycle HTML) → {cycle_html}")
    try:
        fig_cycle.write_image(str(cycle_html).replace(".html", ".png"))
        print(f"  Plot (cycle PNG)  → {str(cycle_html).replace('.html', '.png')}")
    except Exception:
        pass

    fig_maps.show()
    fig_cycle.show()


# ---------------------------------------------------------------------------
# Cartopy plots
# ---------------------------------------------------------------------------

def plot_climatology_cartopy(
    mu: np.ndarray,
    theta90: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    region_id: str,
) -> None:
    """Four theta90 maps (DOY 1/90/180/270) with Cartopy coastlines."""
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    doy_labels = {
        1:   "DOY 1 (Jan 1)",
        90:  "DOY 90 (Apr 1)",
        180: "DOY 180 (Jun 29)",
        270: "DOY 270 (Sep 27)",
    }
    vmin = float(np.nanmin(theta90))
    vmax = float(np.nanmax(theta90))
    cmap = plt.get_cmap("RdYlBu_r")
    proj = ccrs.PlateCarree()

    extent = [
        float(lons.min()) - 0.5, float(lons.max()) + 0.5,
        float(lats.min()) - 0.5, float(lats.max()) + 0.5,
    ]

    fig, axes = plt.subplots(
        2, 2, figsize=(18, 10),
        subplot_kw={"projection": proj},
        constrained_layout=False,
    )
    plt.subplots_adjust(
        left=0.05, right=0.88,
        top=0.92, bottom=0.08,
        wspace=0.15, hspace=0.25,
    )
    fig.suptitle(
        f"90th Percentile SST — {region_id.upper()} — Seasonal Snapshots",
        fontsize=13,
    )

    im = None
    for ax, (doy, label) in zip(axes.flat, doy_labels.items()):
        im = ax.pcolormesh(
            lons, lats, theta90[doy - 1],
            cmap=cmap, vmin=vmin, vmax=vmax,
            transform=proj,
        )
        ax.set_extent(extent, crs=proj)
        ax.set_aspect("auto")
        ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=2)
        ax.coastlines(resolution="50m", linewidth=0.8, zorder=3)
        ax.set_title(label, fontsize=10)
        gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="gray",
                          alpha=0.5, linestyle="--")
        gl.top_labels = False
        gl.right_labels = False

    cax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("90th Percentile SST (°C)", fontsize=10)

    out_png = out_dir / f"climatology_theta90_maps_{region_id}_cartopy.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"  Plot (maps Cartopy PNG) → {out_png}")
    plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build mu and theta90 climatology from OISST baseline.",
    )
    parser.add_argument("--region", default="goa",
                        help="Region ID (default: goa)")
    parser.add_argument("--plot", action="store_true",
                        help="Generate seasonal maps and annual cycle plot")
    parser.add_argument("--backend", choices=["plotly", "cartopy"], default="plotly",
                        help="Plot backend for snapshot maps (default: plotly)")
    parser.add_argument("--no-cache", dest="no_cache", action="store_true",
                        help="Re-download even if yearly NetCDF cache exists")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    cfg  = _load_config()

    print(f"=== Climatology build: region={args.region} ===\n")

    mu, theta90, lats, lons = build_climatology(
        args.region, cfg, use_cache=not args.no_cache
    )

    # Sanity checks
    n_theta_gt_mu = int(np.sum(theta90 > mu))
    n_total_valid = int(np.sum(np.isfinite(mu)))
    pct = 100.0 * n_theta_gt_mu / max(n_total_valid, 1)
    print(f"\nSanity: theta90 > mu in {pct:.2f}% of valid cells (expect ~100%)")
    print(f"mu    range: {np.nanmin(mu):.2f} – {np.nanmax(mu):.2f} °C")
    print(f"theta90 range: {np.nanmin(theta90):.2f} – {np.nanmax(theta90):.2f} °C")

    # Save
    out_paths  = cfg["climatology"]["outputs"]["paths"]
    chunking   = cfg["climatology"]["outputs"]["chunking"]
    baseline   = cfg["climatology"]["baseline"]
    attrs = {
        "region": args.region,
        "baseline_start": baseline["start_year"],
        "baseline_end": baseline["end_year"],
        "source": "NOAA PSL THREDDS OPeNDAP",
        "created": str(date.today()),
    }

    out_paths_abs = {
        k: str(PROJECT_ROOT / v).replace(".zarr", f"_{args.region}.zarr")
        for k, v in out_paths.items()
        if k in ("mu", "theta90")
    }

    print("\nSaving Zarr …")
    save_climatology(mu, theta90, lats, lons, out_paths_abs, chunking, attrs=attrs)

    if args.plot:
        print("\nGenerating plots …")
        if args.backend == "cartopy":
            plot_climatology_cartopy(mu, theta90, lats, lons, args.region)
        else:
            plot_climatology_plotly(mu, theta90, lats, lons, args.region)

    print("\nDone.")


def plot_main(argv: list[str] | None = None) -> None:
    """Load mu/theta90 from saved Zarr files and generate plots only."""
    parser = argparse.ArgumentParser(
        description="Plot mu and theta90 climatology from saved Zarr files.",
    )
    parser.add_argument("--region", default="goa",
                        help="Region ID (default: goa)")
    parser.add_argument("--backend", choices=["plotly", "cartopy"], default="plotly",
                        help="Plot backend for snapshot maps (default: plotly)")
    args = parser.parse_args(argv)

    cfg = _load_config()
    out_paths = cfg["climatology"]["outputs"]["paths"]

    mu_path     = PROJECT_ROOT / out_paths["mu"]
    theta90_path = PROJECT_ROOT / out_paths["theta90"]

    print(f"Loading mu      from {mu_path}")
    print(f"Loading theta90 from {theta90_path}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mu_da      = xr.open_zarr(mu_path,      consolidated=False)["mu"]
        theta90_da = xr.open_zarr(theta90_path, consolidated=False)["theta90"]

    mu      = mu_da.values
    theta90 = theta90_da.values
    lats    = mu_da.lat.values
    lons    = mu_da.lon.values

    print("\nGenerating plots …")
    if args.backend == "cartopy":
        plot_climatology_cartopy(mu, theta90, lats, lons, args.region)
    else:
        plot_climatology_plotly(mu, theta90, lats, lons, args.region)

    print("Done.")


if __name__ == "__main__":
    main()
