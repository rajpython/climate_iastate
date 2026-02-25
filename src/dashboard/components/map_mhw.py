"""Panel 1 — Live MHW State Map.

Displays a Plotly heatmap of any state variable (A, I, D, C, x) for a
user-selected date and region.

Run:
    streamlit run src/dashboard/components/map_mhw.py
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xarray as xr

# ---------------------------------------------------------------------------
# Paths (resolve from this file's location up to project root)
# ---------------------------------------------------------------------------
ROOT       = Path(__file__).parents[3]
STATES_DIR = ROOT / "data" / "derived" / "states_grid"

# ---------------------------------------------------------------------------
# Metric definitions  {key: (label, colorscale, vmin, vmax, fmt)}
# ---------------------------------------------------------------------------
METRICS = {
    "A": ("Active Flag",              "Reds",       0,   1,    ".0f"),
    "I": ("Intensity (°C)",           "YlOrRd",     0,   3.5,  ".2f"),
    "D": ("Duration (days)",          "Purples",    0,   50,   ".0f"),
    "C": ("Cumulative Intensity (°C·days)", "Oranges", 0, 80, ".1f"),
    "x": ("Threshold Exceedance (°C)","Blues",      0,   4,    ".2f"),
}

# ---------------------------------------------------------------------------
# Data loaders (cached so zarr opens only once per session)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Scanning available state files …", ttl=3600)
def find_available_states() -> list[dict]:
    """Return list of dicts {region, start, end, path_str} from zarr filenames."""
    pattern = re.compile(r"states_(\w+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.zarr$")
    results = []
    for p in sorted(STATES_DIR.iterdir()):
        m = pattern.match(p.name)
        if m:
            results.append({"region": m.group(1), "start": m.group(2),
                             "end": m.group(3), "path": str(p)})
    return results


@st.cache_data(show_spinner="Loading state arrays …", ttl=3600)
def load_states(path_str: str) -> dict:
    """Load all state arrays from zarr; return dict of numpy arrays + coords."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds = xr.open_zarr(path_str, consolidated=False)

    lats  = ds["lat"].values.astype(np.float32)
    lons  = ds["lon"].values.astype(np.float32)
    dates = pd.DatetimeIndex(ds["time"].values).date.tolist()

    arrays: dict[str, np.ndarray] = {}
    for var in ["A", "I", "C", "x"]:
        if var in ds:
            arrays[var] = ds[var].values.astype(np.float32)

    # D may be timedelta64 — convert to days (float32)
    if "D" in ds:
        D_raw = ds["D"].values
        if np.issubdtype(D_raw.dtype, np.timedelta64):
            arrays["D"] = (D_raw.astype("timedelta64[ns]").astype(np.int64)
                           / 86_400_000_000_000).astype(np.float32)
        else:
            arrays["D"] = D_raw.astype(np.float32)

    ds.close()
    return {"lats": lats, "lons": lons, "dates": dates, **arrays}


@st.cache_data(show_spinner="Loading ocean mask …", ttl=3600)
def load_land_mask(region: str) -> np.ndarray | None:
    """Return boolean array (n_lat, n_lon), True = land cell.

    Derived from OISST NaN pattern — land cells are always NaN in OISST.
    Cached per region since coastlines don't change.
    """
    raw_dir = ROOT / "data" / "raw"
    candidates = sorted(raw_dir.glob(f"oisst_{region}_????.nc"))
    if not candidates:
        return None
    with xr.open_dataset(str(candidates[0])) as ds:
        sst = ds["sst"].isel(time=0).values   # (n_lat, n_lon)
    return np.isnan(sst)


@st.cache_data(show_spinner="Building cell polygons …", ttl=3600)
def make_grid_geojson(path_str: str) -> dict:
    """Build a GeoJSON FeatureCollection of rectangles — one per grid cell.

    Cached per zarr path: the lat/lon grid is constant across all dates so
    this only runs once per session per zarr file.
    """
    data = load_states(path_str)
    lats = data["lats"].astype(float)
    lons = data["lons"].astype(float)
    dlat = float(abs(lats[1] - lats[0])) / 2 if len(lats) > 1 else 0.125
    dlon = float(abs(lons[1] - lons[0])) / 2 if len(lons) > 1 else 0.125

    features = []
    idx = 0
    for lat in lats:
        for lon in lons:
            features.append({
                "type": "Feature",
                "id": str(idx),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon - dlon, lat - dlat],
                        [lon + dlon, lat - dlat],
                        [lon + dlon, lat + dlat],
                        [lon - dlon, lat + dlat],
                        [lon - dlon, lat - dlat],
                    ]]
                },
                "properties": {},
            })
            idx += 1
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Live MHW Map", layout="wide", page_icon="🗺️")
    st.title("🗺️ Live MHW State Map")

    # ---- Sidebar ----
    st.sidebar.header("Controls")

    available = find_available_states()
    if not available:
        st.error(f"No state zarr files found in {STATES_DIR}.\n"
                 "Run: `mhw-run-states --region goa --start 2023-01-01 --end 2023-12-31`")
        return

    # Region/period selector
    labels = [f"{r['region'].upper()}  {r['start']} → {r['end']}" for r in available]
    choice = st.sidebar.selectbox("Region / Period", range(len(labels)),
                                  format_func=lambda i: labels[i])
    info   = available[choice]

    data = load_states(info["path"])
    dates = data["dates"]

    # Metric selector
    available_metrics = {k: v for k, v in METRICS.items() if k in data}
    metric_key = st.sidebar.selectbox(
        "Metric",
        list(available_metrics.keys()),
        format_func=lambda k: available_metrics[k][0],
        index=1,   # default to Intensity
    )

    # Date slider
    date_idx = st.sidebar.slider("Date index", 0, len(dates) - 1, len(dates) - 1)
    selected_date = dates[date_idx]

    st.sidebar.markdown(f"**Selected date:** {selected_date}")

    # ---- Build map ----
    values = data[metric_key][date_idx]           # (n_lat, n_lon)
    label, colorscale, vmin, vmax, fmt = available_metrics[metric_key]

    # Stats
    valid_mask = np.isfinite(values)
    n_active   = int((values > 0).sum()) if metric_key == "A" else None

    # Flatten grid for choropleth; mask land cells → NaN → transparent
    lons_2d, lats_2d = np.meshgrid(data["lons"], data["lats"])
    lat_flat  = lats_2d.flatten()
    lon_flat  = lons_2d.flatten()
    val_flat  = values.flatten().astype(float)
    land_mask = load_land_mask(info["region"])
    if land_mask is not None:
        val_flat[land_mask.flatten()] = np.nan
    # Also hide ocean cells with no activity — only show where metric > 0
    val_flat[val_flat <= 0] = np.nan
    ids = [str(i) for i in range(len(val_flat))]

    geojson = make_grid_geojson(info["path"])

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson,
        locations=ids,
        z=val_flat,
        colorscale=colorscale,
        zmin=vmin,
        zmax=vmax,
        marker_opacity=0.65,
        marker_line_width=0,
        colorbar=dict(title=label, thickness=15),
        customdata=np.column_stack([lat_flat, lon_flat]),
        hovertemplate=(
            "Lat: %{customdata[0]:.3f}<br>Lon: %{customdata[1]:.3f}<br>"
            + label + ": %{z:" + fmt + "}<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=dict(
            text=f"{label} — {info['region'].upper()} — {selected_date}",
            font={"size": 16},
        ),
        map=dict(
            style="open-street-map",
            center={"lat": float(data["lats"].mean()),
                    "lon": float(data["lons"].mean())},
            zoom=3.5,
        ),
        height=500,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---- Summary stats ----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Min",  f"{np.nanmin(values):{fmt}}")
    col2.metric("Max",  f"{np.nanmax(values):{fmt}}")
    col3.metric("Mean (valid)", f"{np.nanmean(values[valid_mask]):{fmt}}" if valid_mask.any() else "—")
    if n_active is not None:
        n_total = values.size
        col4.metric("Active cells", f"{n_active} / {n_total}  ({100*n_active/n_total:.1f}%)")

    # ---- Quick daily context ----
    if "A" in data:
        A_day = data["A"][date_idx]
        area_frac_day = float(np.nanmean(A_day))
        st.caption(f"Regional active fraction on {selected_date}: **{area_frac_day:.4f}** "
                   f"({100*area_frac_day:.2f}% of grid cells)")


if __name__ == "__main__":
    main()
