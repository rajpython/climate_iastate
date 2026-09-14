"""Verify the ``ai_west`` western boundary against the US-Russia maritime boundary.

Reproduces the two measurements the dashboard cell reported to LOFRA on 2026-09-14
(handoff ``dashboard-to-admin-mini-m4-cc-m1-20260914-01``), which the programme accepted as
the measurement of record for closing the ``ai_west`` boundary question (PI ruling: no trim).

Background. The ``ai_west`` polygon's western edge sits at 167.64 E, which a July 2026 audit
recorded as an "overshoot" of a nominal 170 E boundary. That framing was withdrawn: 50 CFR 679
Fig. 1 bounds Area 543 "on the south and west by the limits of the US EEZ" and never states
170 E, and the 2024 AI ESR (p.9) says the western boundary "is considered the U.S.-Russia
maritime boundary at 170 E". This script shows the polygon implements that boundary.

What it measures:
  1. distance from each 1990 Agreement Annex turning point to our polygon boundary;
  2. distance from the polygon's western apex to Cape Wrangell (the 200-nm EEZ check);
  3. the counterfactual cost of trimming to 170 E, on the full per-cell state record.

The turning-point coordinates are lofra-mini/cobra's decode of the deposited UN treaty PDF
(``2026-09-13-area-543-western-boundary-verification.md``); they are inputs here, not our
measurement. The 1990 Agreement is provisionally applied pending entry into force, so prefer
"U.S.-Russia maritime boundary" / "U.S. EEZ limit" over "treaty line" in any write-up.

CLI:
    python scripts/verify_ai_west_boundary.py [--skip-trim]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 1990 USA-USSR Maritime Boundary Agreement, Annex turning points spanning the Aleutian band.
# Source: cobra decode of the deposited UN treaty text (see module docstring).
TREATY_POINTS = {
    63: (55.007, 172.116), 68: (54.097, 170.823), 71: (53.546, 170.091),
    72: (53.363, 169.876), 76: (52.629, 169.027), 80: (51.887, 168.200),
    82: (51.514, 167.795), 83: (51.327, 167.594), 84: (51.189, 167.448),
    86: (51.153, 167.200), 87: (50.978, 167.000),
}
# Point 83 is the last before the line gives way to the 200-nm arcs.
LAST_GEODETIC_PT = 83

# Westernmost point of Attu I. — the westernmost US baseline point in the Aleutians.
CAPE_WRANGELL = (52.92, 172.44)
NM_KM = 1.852


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    radius = 6371.0088
    rad = math.radians
    a = (math.sin(rad(lat2 - lat1) / 2) ** 2
         + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(rad(lon2 - lon1) / 2) ** 2)
    return 2 * radius * math.asin(math.sqrt(a))


def load_exterior_ring(geojson_path: Path) -> np.ndarray:
    """Return the ai_west exterior ring as an (n, 2) array of (lon, lat)."""
    features = json.loads(geojson_path.read_text())["features"]
    feature = next(f for f in features if f["properties"]["id"] == "ai_west")
    return np.asarray(feature["geometry"]["coordinates"][0])


def point_to_ring_km(lat: float, lon: float, ring: np.ndarray, samples: int = 60) -> float:
    """Min distance from a point to the ring, densifying each segment."""
    best = math.inf
    for (lon1, lat1), (lon2, lat2) in zip(ring[:-1], ring[1:]):
        for t in np.linspace(0.0, 1.0, samples):
            best = min(best, haversine_km(lat, lon,
                                          lat1 + t * (lat2 - lat1),
                                          lon1 + t * (lon2 - lon1)))
    return best


def report_treaty_agreement(ring: np.ndarray) -> None:
    print("Turning point -> distance to our ai_west boundary")
    print(f"{'pt':>4} {'lat N':>8} {'lon E':>9} {'km':>8} {'nm':>7}")
    on_line = []
    for pt, (lat, lon) in TREATY_POINTS.items():
        d = point_to_ring_km(lat, lon, ring)
        past = "  (past line terminus -> 200-nm arc)" if pt > LAST_GEODETIC_PT else ""
        if pt <= LAST_GEODETIC_PT:
            on_line.append(d)
        print(f"{pt:>4} {lat:8.3f} {lon:9.3f} {d:8.2f} {d / NM_KM:7.2f}{past}")
    print(f"\ngeodetic segment (pts 63-{LAST_GEODETIC_PT}): "
          f"mean {np.mean(on_line):.2f} km, max {np.max(on_line):.2f} km")

    apex_idx = int(np.argmin(ring[:, 0]))
    apex_lon, apex_lat = ring[apex_idx]
    d = haversine_km(CAPE_WRANGELL[0], CAPE_WRANGELL[1], apex_lat, apex_lon)
    print(f"apex ({apex_lon:.3f} E, {apex_lat:.3f} N) to Cape Wrangell: "
          f"{d:.1f} km = {d / NM_KM:.1f} nm  (200-nm EEZ limit)")

    print("\nWestern boundary vs the withdrawn 170 E comparator, by latitude:")
    for lon, lat in sorted(ring[ring[:, 0] < 171.5], key=lambda p: -p[1]):
        print(f"  lat {lat:6.3f}  lon {lon:8.3f}   "
              f"{'WEST' if lon < 170 else 'EAST'} of 170 E")


def report_trim_impact() -> None:
    """Counterfactual: restrict the existing mask to >=170 E and recompute area_frac.

    Scope bound: this restricts the mask rather than rebuilding the polygon, so a true
    re-trim could differ by a cell or two through cell-centre inclusion. The AR(1) phi here
    is a plain lag-1 autocorrelation of monthly anomalies -- NOT LOFRA's OLS estimator on
    the deseasonalised anomaly -- and is comparable only within this calculation.
    """
    import pandas as pd
    import xarray as xr

    masks = xr.open_zarr(PROJECT_ROOT / "data/derived/masks/region_masks.zarr", consolidated=False)
    mask = masks["ai_west"].values.astype(bool)
    lat = masks["lat"].values
    lon = masks["lon"].values
    lon360 = np.broadcast_to(np.where(lon < 0, lon + 360, lon)[None, :], mask.shape)

    cos_lat = np.cos(np.deg2rad(lat))[:, None] * np.ones((1, len(lon)))
    w_full = cos_lat * mask
    w_trim = cos_lat * (mask & (lon360 >= 170.0))
    print(f"\nmask cells {mask.sum()}, west of 170 E {(mask & (lon360 < 170)).sum()} "
          f"({100 * (1 - w_trim.sum() / w_full.sum()):.2f}% of weight a trim would remove)")

    frames = []
    for path in sorted(glob.glob(str(PROJECT_ROOT / "data/derived/states_grid/states_ai_west_*.zarr"))):
        ds = xr.open_zarr(path, consolidated=False)
        active = ds["A"].values.astype(np.float32)
        rows = np.searchsorted(lat, ds["lat"].values)
        cols = np.searchsorted(lon, ds["lon"].values)
        wf = w_full[np.ix_(rows, cols)]
        wt = w_trim[np.ix_(rows, cols)]
        frames.append(pd.DataFrame({
            "date": pd.to_datetime(ds["time"].values),
            "af_full": (active * wf[None]).sum((1, 2)) / wf.sum(),
            "af_trim": (active * wt[None]).sum((1, 2)) / wt.sum(),
        }))

    if not frames:
        print("no per-cell state grids found -- skipping the trim-impact half")
        return

    df = pd.concat(frames).sort_values("date").reset_index(drop=True)
    diff = df["af_trim"] - df["af_full"]
    print(f"days {len(df)} ({df.date.min().date()} .. {df.date.max().date()})")
    print(f"  mean area_frac  current {df.af_full.mean():.5f}  trimmed {df.af_trim.mean():.5f}")
    print(f"  daily r {np.corrcoef(df.af_full, df.af_trim)[0, 1]:.4f}   "
          f"mean |diff| {diff.abs().mean():.5f}")
    print(f"  MHW-days (>0.05)  current {int((df.af_full > 0.05).sum())}  "
          f"trimmed {int((df.af_trim > 0.05).sum())}")

    monthly = df.set_index("date").resample("MS").mean()
    print(f"  monthly r {np.corrcoef(monthly.af_full, monthly.af_trim)[0, 1]:.4f}")
    for name in ("af_full", "af_trim"):
        values = monthly[name].values
        clim = monthly[name].groupby(monthly.index.month).transform("mean").values
        anom = values - clim
        phi = np.corrcoef(anom[:-1], anom[1:])[0, 1]
        label = "current" if name == "af_full" else "trimmed"
        print(f"  lag-1 phi ({label}): {phi:.4f}  half-life {np.log(0.5) / np.log(phi):.2f} months")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-trim", action="store_true",
                        help="only verify the boundary; skip the trim counterfactual "
                             "(which needs the per-cell state grids)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ring = load_exterior_ring(PROJECT_ROOT / "config" / "regions.geojson")
    report_treaty_agreement(ring)
    if not args.skip_trim:
        report_trim_impact()
    return 0


if __name__ == "__main__":
    sys.exit(main())
