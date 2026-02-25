"""OISST ERDDAP fetcher — fetch daily SST for a region bounding box.

CLI: mhw-fetch-sst --region goa --date 2024-06-15 --plot
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import xarray as xr

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# ---------------------------------------------------------------------------
# ERDDAP configuration
# ---------------------------------------------------------------------------
ERDDAP_OPENDAP_URLS = [
    {
        "url": "https://www.ncei.noaa.gov/erddap/griddap/ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon",
        "label": "NCEI ERDDAP (OPeNDAP)",
    },
]

# ---------------------------------------------------------------------------
# Region bounding boxes (loaded from config/regions.geojson)
# ---------------------------------------------------------------------------

def load_region_bbox(region_id: str) -> dict:
    """Return {"lon_min", "lon_max", "lat_min", "lat_max"} for *region_id*."""
    geojson_path = CONFIG_DIR / "regions.geojson"
    with open(geojson_path) as f:
        fc = json.load(f)
    for feat in fc["features"]:
        if feat["properties"]["id"] == region_id:
            coords = feat["geometry"]["coordinates"][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return {
                "lon_min": min(lons),
                "lon_max": max(lons),
                "lat_min": min(lats),
                "lat_max": max(lats),
            }
    available = [f["properties"]["id"] for f in fc["features"]]
    raise ValueError(f"Region '{region_id}' not found. Available: {available}")


def _lon_to_360(lon: float) -> float:
    """Convert longitude from [-180, 180) to [0, 360) for ERDDAP OISST."""
    return lon % 360


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_sst(
    region_id: str,
    target_date: date,
    *,
    variables: tuple[str, ...] = ("sst",),
) -> xr.Dataset:
    """Fetch SST for *region_id* on *target_date* via OPeNDAP.

    The ERDDAP OISST dataset uses 0–360 longitude. This function converts
    the region bbox, subsets via xarray .sel(), and converts longitude back
    to [-180, 180) before returning.
    """
    bbox = load_region_bbox(region_id)
    lon_min_360 = _lon_to_360(bbox["lon_min"])
    lon_max_360 = _lon_to_360(bbox["lon_max"])
    target_str = str(target_date)

    last_err = None
    for srv in ERDDAP_OPENDAP_URLS:
        try:
            print(f"Connecting to {srv['label']} …")
            ds = xr.open_dataset(srv["url"], engine="netcdf4")

            sub = ds[list(variables)].sel(
                time=target_str,
                depth=0.0,
                latitude=slice(bbox["lat_min"], bbox["lat_max"]),
                longitude=slice(lon_min_360, lon_max_360),
            ).load()
            ds.close()

            # Squeeze depth
            if "depth" in sub.dims:
                sub = sub.squeeze("depth", drop=True)

            # Convert longitude back to [-180, 180)
            if "longitude" in sub.coords:
                lon = sub["longitude"].values.copy()
                lon = ((lon + 180) % 360) - 180
                sub = sub.assign_coords(longitude=lon)
                sub = sub.sortby("longitude")

            print(f"  Fetched {dict(sub.sizes)}")
            return sub

        except Exception as exc:
            last_err = exc
            print(f"  {exc}")
            continue

    raise RuntimeError(f"All servers failed. Last error: {last_err}")


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_netcdf(ds: xr.Dataset, region_id: str, target_date: date) -> Path:
    """Save dataset as NetCDF in data/raw/."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    fname = f"oisst_{region_id}_{target_date:%Y%m%d}.nc"
    out_path = DATA_RAW / fname
    ds.to_netcdf(out_path)
    print(f"Saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_sst_plotly(ds: xr.Dataset, region_id: str, target_date: date) -> Path:
    """Render an interactive Plotly map of SST and save as HTML."""
    import plotly.graph_objects as go

    sst = ds["sst"].squeeze()
    lats = sst["latitude"].values
    lons = sst["longitude"].values

    fig = go.Figure(
        data=go.Heatmap(
            z=sst.values,
            x=lons,
            y=lats,
            colorscale="RdYlBu_r",
            colorbar=dict(title="SST (°C)"),
            zmin=float(sst.min()),
            zmax=float(sst.max()),
        )
    )
    fig.update_layout(
        title=f"OISST SST — {region_id.upper()} — {target_date}",
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        width=900,
        height=600,
    )

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / f"sst_{region_id}_{target_date:%Y%m%d}.html"
    fig.write_html(str(html_path))
    print(f"Plot (HTML) → {html_path}")

    try:
        png_path = out_dir / f"sst_{region_id}_{target_date:%Y%m%d}.png"
        fig.write_image(str(png_path))
        print(f"Plot (PNG)  → {png_path}")
    except Exception:
        print("  (PNG export skipped — install kaleido for static image export)")

    fig.show()
    return html_path


def plot_sst_cartopy(ds: xr.Dataset, region_id: str, target_date: date) -> Path:
    """Render a Cartopy projected map of SST and save as PNG."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt

    sst = ds["sst"].squeeze()
    lats = sst["latitude"].values
    lons = sst["longitude"].values

    fig, ax = plt.subplots(
        figsize=(10, 6),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    mesh = ax.pcolormesh(
        lons, lats, sst.values,
        cmap="RdYlBu_r",
        transform=ccrs.PlateCarree(),
    )
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=":")
    ax.gridlines(draw_labels=True, linewidth=0.3)
    plt.colorbar(mesh, ax=ax, label="SST (°C)", shrink=0.7)
    ax.set_title(f"OISST SST — {region_id.upper()} — {target_date}")

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"sst_{region_id}_{target_date:%Y%m%d}_cartopy.png"
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"Plot (PNG) → {png_path}")
    plt.show()
    return png_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch OISST SST for a region and date.",
    )
    parser.add_argument(
        "--region", default="goa",
        help="Region ID from config/regions.geojson (default: goa)",
    )
    parser.add_argument(
        "--date", default=None,
        help="Date as YYYY-MM-DD (default: 2 days ago)",
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Generate and display a map plot",
    )
    parser.add_argument(
        "--backend", default="plotly", choices=["plotly", "cartopy"],
        help="Plot backend (default: plotly)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today() - timedelta(days=2)

    print(f"Fetching OISST for region={args.region}, date={target_date}")
    ds = fetch_sst(args.region, target_date)

    # Print summary
    sst = ds["sst"].squeeze()
    print(f"\nData shape: {dict(sst.sizes)}")
    print(f"Lat range:  {float(sst.latitude.min()):.2f} to {float(sst.latitude.max()):.2f}")
    print(f"Lon range:  {float(sst.longitude.min()):.2f} to {float(sst.longitude.max()):.2f}")
    print(f"SST range:  {float(sst.min()):.2f} to {float(sst.max()):.2f} °C")
    print(f"Grid res:   ~{float(sst.latitude[1] - sst.latitude[0]):.2f}° (expected 0.25°)")

    save_netcdf(ds, args.region, target_date)

    if args.plot:
        if args.backend == "cartopy":
            plot_sst_cartopy(ds, args.region, target_date)
        else:
            plot_sst_plotly(ds, args.region, target_date)


if __name__ == "__main__":
    main()
