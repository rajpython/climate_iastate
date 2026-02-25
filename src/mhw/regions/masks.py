"""Rasterize region polygons onto the OISST 0.25° grid and compute cos(lat) weights.

Reads paths and dtype from config/climatology.yml:
  regions.geojson_path        → config/regions.geojson
  regions.masks_output_path   → data/derived/masks/region_masks.zarr
  regions.mask_dtype          → uint8
  weights.store_path          → data/derived/weights/weights.zarr

CLI: mhw-build-masks [--plot]
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import shapely
import xarray as xr
import yaml
from shapely.geometry import shape

from mhw.regions.weights import build_weights

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_config() -> dict:
    with open(CONFIG_DIR / "climatology.yml") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

def oisst_grid() -> tuple[np.ndarray, np.ndarray]:
    """Return (lats, lons) for the global OISST 0.25° grid in [-180, 180) convention."""
    lats = np.arange(-89.875, 90.0, 0.25, dtype=np.float64)   # 720 points
    lons = np.arange(-179.875, 180.0, 0.25, dtype=np.float64)  # 1440 points
    return lats, lons


# ---------------------------------------------------------------------------
# Rasterisation
# ---------------------------------------------------------------------------

def rasterize_region(
    poly: shapely.Geometry,
    lats: np.ndarray,
    lons: np.ndarray,
    dtype: str = "uint8",
) -> np.ndarray:
    """Return a 2-D binary mask (lat × lon) for *poly* on the given grid.

    Uses shapely.contains_xy for vectorised point-in-polygon testing.
    A grid cell is in the region when its centre point falls inside the polygon.
    """
    lon_2d, lat_2d = np.meshgrid(lons, lats)           # both (720, 1440)
    inside = shapely.contains_xy(poly, lon_2d.ravel(), lat_2d.ravel())
    return inside.reshape(lon_2d.shape).astype(dtype)


def build_masks(
    geojson_path: Path,
    lats: np.ndarray,
    lons: np.ndarray,
    mask_dtype: str = "uint8",
) -> xr.Dataset:
    """Rasterize all features in *geojson_path* and return an xr.Dataset.

    Each region becomes one DataArray variable keyed by its ``id`` property.
    """
    with open(geojson_path) as f:
        fc = json.load(f)

    data_vars: dict[str, xr.DataArray] = {}
    for feat in fc["features"]:
        rid = feat["properties"]["id"]
        name = feat["properties"]["name"]
        poly = shape(feat["geometry"])

        print(f"  Rasterizing {rid} ({name}) …")
        mask = rasterize_region(poly, lats, lons, dtype=mask_dtype)
        n_cells = int(mask.sum())
        print(f"    → {n_cells:,} grid cells")

        data_vars[rid] = xr.DataArray(
            mask,
            dims=["lat", "lon"],
            coords={"lat": lats, "lon": lons},
            attrs={"region_name": name, "region_id": rid, "dtype": mask_dtype},
        )

    return xr.Dataset(data_vars, coords={"lat": lats, "lon": lons})


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def save_zarr(ds: xr.Dataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds.to_zarr(path, mode="w", consolidated=False)
    print(f"  Saved → {path}")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_masks_plotly(
    ds_masks: xr.Dataset,
    ds_weights: xr.Dataset,
    region_meta: list[dict],
) -> Path:
    """6-panel Plotly figure: 5 region masks + cos(lat) weight field."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    region_ids = [f["properties"]["id"] for f in region_meta]
    region_names = [f["properties"]["name"] for f in region_meta]

    # 2-row × 3-col grid: 5 region masks + weights overview
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=region_names + ["cos(lat) Weights — Alaska"],
        vertical_spacing=0.12,
        horizontal_spacing=0.06,
    )

    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]

    lats = ds_masks.coords["lat"].values
    lons = ds_masks.coords["lon"].values

    for (row, col), rid, rname in zip(positions, region_ids, region_names):
        mask = ds_masks[rid].values.astype(float)
        mask[mask == 0] = np.nan  # transparent outside

        fig.add_trace(
            go.Heatmap(
                z=mask,
                x=lons,
                y=lats,
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "royalblue"]],
                showscale=False,
                zmin=0,
                zmax=1,
                name=rid,
            ),
            row=row, col=col,
        )

        # Zoom to region bbox + 5° buffer
        region_lons = lons[~np.isnan(mask).all(axis=0)]
        region_lats = lats[~np.isnan(mask).all(axis=1)]
        buf = 5.0
        fig.update_xaxes(
            range=[region_lons.min() - buf, region_lons.max() + buf],
            row=row, col=col,
        )
        fig.update_yaxes(
            range=[region_lats.min() - buf, region_lats.max() + buf],
            row=row, col=col,
        )

    # Panel 6: cos(lat) weights for Alaska extent
    wts = ds_weights["weights"].values
    alaska_lat = (lats >= 50) & (lats <= 76)
    alaska_lon = (lons >= -185) & (lons <= -125)
    fig.add_trace(
        go.Heatmap(
            z=wts[np.ix_(alaska_lat, alaska_lon)],
            x=lons[alaska_lon],
            y=lats[alaska_lat],
            colorscale="Viridis",
            colorbar=dict(title="cos(lat)", len=0.4, y=0.15, x=1.02),
            zmin=0.0,
            zmax=1.0,
            name="weights",
        ),
        row=2, col=3,
    )
    fig.update_xaxes(range=[-185, -125], row=2, col=3)
    fig.update_yaxes(range=[48, 78], row=2, col=3)

    fig.update_layout(
        title_text="OISST Region Masks & cos(lat) Weights",
        title_x=0.5,
        height=700,
        width=1100,
    )

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "region_masks.html"
    fig.write_html(str(html_path))
    print(f"  Plot (HTML) → {html_path}")

    try:
        png_path = out_dir / "region_masks.png"
        fig.write_image(str(png_path))
        print(f"  Plot (PNG)  → {png_path}")
    except Exception:
        print("  (PNG export skipped)")

    fig.show()
    return html_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rasterize region masks and compute cos(lat) weights onto OISST grid.",
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Generate and display mask + weight plots (Plotly)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    cfg = _load_config()

    geojson_path = PROJECT_ROOT / cfg["regions"]["geojson_path"]
    masks_path = PROJECT_ROOT / cfg["regions"]["masks_output_path"]
    weights_path = PROJECT_ROOT / cfg["weights"]["store_path"]
    mask_dtype = cfg["regions"]["mask_dtype"]

    lats, lons = oisst_grid()
    print(f"Grid: {len(lats)} lats × {len(lons)} lons (0.25° OISST)\n")

    # --- Masks ---
    print("Building region masks …")
    ds_masks = build_masks(geojson_path, lats, lons, mask_dtype=mask_dtype)
    save_zarr(ds_masks, masks_path)

    # --- Weights ---
    print("\nBuilding cos(lat) weights …")
    w_da = build_weights(lats, lons)
    alaska_lat_mask = (lats >= 50) & (lats <= 76)
    w_alaska = w_da.values[alaska_lat_mask]
    print(f"  Weight range (50–76°N): {w_alaska.min():.4f} – {w_alaska.max():.4f}")
    ds_weights = xr.Dataset({"weights": w_da})
    save_zarr(ds_weights, weights_path)

    # --- Summary ---
    print("\nMask cell counts:")
    for var in ds_masks.data_vars:
        n = int(ds_masks[var].values.sum())
        print(f"  {var:12s}: {n:5,} cells")

    if args.plot:
        print("\nGenerating plots …")
        with open(geojson_path) as f:
            region_meta = json.load(f)["features"]
        plot_masks_plotly(ds_masks, ds_weights, region_meta)


if __name__ == "__main__":
    main()
