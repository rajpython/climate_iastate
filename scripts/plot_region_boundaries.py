"""Render all MHW zone polygons (config/regions.geojson) on one annotated map.

Shows the 9 ESR leaf zones with their outer coast/shelf-following edges and the straight
internal management divides (60°N SEBS|NBS, 147°W WGOA|EGOA, 156.47°W Chukchi|Beaufort,
177°E / 170°W Aleutians). Companion to docs/region_provenance.md.

Run: .venv/bin/python scripts/plot_region_boundaries.py [--out PATH]
Needs the [geo] extra (cartopy, shapely).
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely.geometry import shape

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAVES = ["sebs", "nbs", "wgoa", "egoa", "ai_west", "ai_central", "ai_east", "chukchi", "beaufort"]
# Plain-English on-map labels (two lines where the name is long) — no internal codes.
LABELS = {
    "sebs": "Southeastern\nBering Sea", "nbs": "Northern\nBering Sea",
    "wgoa": "Western Gulf\nof Alaska", "egoa": "Eastern Gulf\nof Alaska",
    "ai_west": "Western\nAleutians", "ai_central": "Central\nAleutians",
    "ai_east": "Eastern\nAleutians", "chukchi": "Chukchi Sea", "beaufort": "Beaufort Sea",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "docs" / "region_boundaries.png")
    args = ap.parse_args(argv)
    feats = {f["properties"]["id"]: f for f in
             json.loads((PROJECT_ROOT / "config" / "regions.geojson").read_text())["features"]}
    colors = plt.cm.tab10.colors + plt.cm.Set3.colors
    proj = ccrs.PlateCarree(central_longitude=180)
    fig = plt.figure(figsize=(15, 9))
    ax = plt.axes(projection=proj)
    ax.set_extent([-16, 52, 46, 77], crs=proj)  # proj coords = lon-180 → covers 164°E..232°E
    ax.add_feature(cfeature.LAND, facecolor="#efece3", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#888", zorder=3)
    ax.gridlines(draw_labels=True, linewidth=0.3, color="gray", alpha=0.5,
                 xlocs=[-180, -170, -160, -150, -140, -130, 170, 180],
                 ylocs=[50, 55, 60, 65, 70, 75])
    for i, r in enumerate(LEAVES):
        geom = shape(feats[r]["geometry"])
        ax.add_geometries([geom], crs=ccrs.PlateCarree(), facecolor=colors[i],
                          edgecolor="k", linewidth=0.9, alpha=0.55, zorder=2)
        c = geom.representative_point()
        ax.text(c.x, c.y, LABELS[r], transform=ccrs.PlateCarree(), fontsize=7, ha="center",
                va="center", weight="bold", zorder=4,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))

    def divide(lon, lat, txt, rot=90):
        ax.text(lon, lat, txt, transform=ccrs.PlateCarree(), fontsize=8.5, color="crimson",
                weight="bold", ha="center", va="center", rotation=rot, zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="crimson", alpha=0.85))
    divide(-147, 56.5, "147°W")
    divide(-172, 60.3, "60°N", rot=0)
    divide(-156.47, 72.6, "156.47°W  Point Barrow")
    divide(177, 52.0, "177°E")
    divide(-170, 52.0, "170°W  Samalga Pass")
    ax.set_title("Alaska Marine Ecosystem Study Regions\n"
                 "Nine core zones — outer edges follow the coast and shelf; the red lines are the "
                 "NOAA ecosystem boundaries between zones", fontsize=12)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out, dpi=115, bbox_inches="tight")
    print("saved", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
