"""Cached loaders for the NOAA PSL marine-heatwave forecast page.

Every loader reads only the small derived artifacts written by
``mhw-build-psl-mhw`` (config/psl_mhw.yml → ``derived``) and returns numpy /
DataFrame / dict values, never a live xarray handle — so the NetCDF cube is
opened once per flavor per session and every widget interaction after that just
slices cached arrays. Mirrors the caching conventions in ``components.map_mhw``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import xarray as xr
import yaml

ROOT = Path(__file__).parents[3]
CONFIG_PATH = ROOT / "config" / "psl_mhw.yml"


@st.cache_resource
def config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text())


def _derived(key: str, flavor: str | None = None) -> Path:
    p = config()["derived"][key]
    if flavor is not None:
        p = p.format(flavor=flavor)
    return ROOT / p


@st.cache_data(show_spinner="Loading forecast probabilities …", ttl=3600)
def load_prob_cube(flavor: str) -> dict | None:
    """Alaska probability cube for one flavor → dict of numpy arrays, or None.

    Keys: lats, lons (1-D), inits (list of pd.Timestamp), leads (1-D),
    prob (init, lead, lat, lon) float32 in [0, 1]. This is the ONLY function
    that opens the forecast NetCDF; Streamlit caches it on ``flavor``.
    """
    path = _derived("prob_cube", flavor)
    if not path.exists():
        return None
    var = config()["schema"]["prob"]["var"]
    init_dim = config()["schema"]["prob"]["init_dim"]
    lead_dim = config()["schema"]["prob"]["lead_dim"]
    with xr.open_dataset(path) as ds:
        da = ds[var].transpose(init_dim, lead_dim, "lat", "lon")
        out = {
            "lats": da["lat"].values.astype("float64"),
            "lons": da["lon"].values.astype("float64"),
            "inits": [pd.Timestamp(t) for t in pd.to_datetime(da[init_dim].values)],
            "leads": da[lead_dim].values.astype("float64"),
            "prob": da.values.astype("float32"),
        }
    return out


@st.cache_data(show_spinner="Loading zone series …", ttl=3600)
def load_zone_series(flavor: str) -> pd.DataFrame:
    path = _derived("zone_series", flavor)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner="Loading observed status …", ttl=3600)
def load_obs_status() -> pd.DataFrame:
    path = _derived("obs_status")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner="Loading zone masks …", ttl=3600)
def load_zone_meta() -> pd.DataFrame:
    """Per-zone ice fraction and effective cell count (for UI caveats)."""
    path = _derived("masks_weights")
    if not path.exists():
        return pd.DataFrame()
    with xr.open_dataset(path) as ds:
        return pd.DataFrame({
            "zone": ds["zone"].values,
            "ice_frac": ds["ice_frac"].values,
            "n_cells": ds["n_cells"].values,
        })


@st.cache_data(show_spinner=False, ttl=3600)
def load_zone_coverage(zone: str) -> np.ndarray | None:
    """Per-cell coverage fraction (lat, lon) for one zone, on the cube grid.

    >0 where the 1° cell overlaps the zone polygon; used to mask the probability
    map down to the selected zone. None if the masks artifact / zone is missing.
    """
    path = _derived("masks_weights")
    if not path.exists():
        return None
    with xr.open_dataset(path) as ds:
        if zone not in ds["zone"].values:
            return None
        return ds["coverage"].sel(zone=zone).values.astype("float32")


@st.cache_data(show_spinner="Loading skill map …", ttl=3600)
def load_sedi() -> dict | None:
    """SEDI skill artifact → dict of arrays, or None when it hasn't been built."""
    path = _derived("sedi")
    if not path.exists():
        return None
    lead_dim = config()["schema"]["prob"]["lead_dim"]
    with xr.open_dataset(path) as ds:
        out = {
            "lats": ds["lat"].values.astype("float64"),
            "lons": ds["lon"].values.astype("float64"),
            "leads": ds[lead_dim].values.astype("float64"),
            "zones": ds["zone"].values.tolist(),
        }
        for flavor in ("trend", "detrend"):
            out[f"sedi_{flavor}"] = ds[f"sedi_{flavor}"].transpose(
                lead_dim, "lat", "lon").values.astype("float32")
            out[f"zone_sedi_{flavor}"] = ds[f"zone_sedi_{flavor}"].transpose(
                "zone", lead_dim).values.astype("float32")
    return out


@st.cache_data(show_spinner="Building cell polygons …", ttl=3600)
def make_grid_geojson(lats: tuple[float, ...], lons: tuple[float, ...],
                      resolution_deg: float = 1.0) -> dict:
    """GeoJSON FeatureCollection of one rectangle per grid cell.

    Cached on the (lats, lons) tuples — constant per session. Longitudes are
    emitted in the −180..180 frame the basemap expects (the cube is 0–360).
    """
    half = resolution_deg / 2.0
    features = []
    idx = 0
    for lat in lats:
        for lon in lons:
            lon180 = ((lon + 180.0) % 360.0) - 180.0
            features.append({
                "type": "Feature",
                "id": str(idx),
                "geometry": {"type": "Polygon", "coordinates": [[
                    [lon180 - half, lat - half],
                    [lon180 + half, lat - half],
                    [lon180 + half, lat + half],
                    [lon180 - half, lat + half],
                    [lon180 - half, lat - half],
                ]]},
                "properties": {},
            })
            idx += 1
    return {"type": "FeatureCollection", "features": features}


def lon_to_180(lons: np.ndarray) -> np.ndarray:
    """Wrap 0–360 longitudes to −180..180 for the basemap."""
    return ((np.asarray(lons) + 180.0) % 360.0) - 180.0


@st.cache_data(show_spinner=False, ttl=3600)
def zone_outline(zone_id: str) -> dict | None:
    """Boundary line + centre + zoom for one ESR zone, for the map overlay.

    Longitudes are emitted in whichever frame keeps the zone contiguous on the
    basemap: dateline-straddling Aleutian zones come back in 0–360 (so the line
    doesn't streak across the map), everything else in −180..180. Returns
    ``{lon, lat, center, zoom}`` with ``None`` separators between polygon rings,
    or None if the id is unknown.
    """
    import json
    import math

    from shapely.geometry import shape

    path = ROOT / "config" / "regions.geojson"
    fc = json.loads(path.read_text())
    feat = next((ft for ft in fc["features"] if ft["properties"]["id"] == zone_id), None)
    if feat is None:
        return None

    geom = shape(feat["geometry"])
    polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    all_lon = [x for p in polys for x in p.exterior.coords.xy[0]]
    span180 = max(all_lon) - min(all_lon)
    span360 = max(x % 360 for x in all_lon) - min(x % 360 for x in all_lon)
    use360 = span360 < span180

    def tx(lon: float) -> float:
        return lon % 360.0 if use360 else lon

    lons: list[float | None] = []
    lats: list[float | None] = []
    for p in polys:
        xs, ys = p.exterior.coords.xy
        lons.extend([tx(x) for x in xs] + [None])
        lats.extend(list(ys) + [None])

    tlon = [tx(x) for x in all_lon]
    tlat = [y for p in polys for y in p.exterior.coords.xy[1]]
    lon_span, lat_span = max(tlon) - min(tlon), max(tlat) - min(tlat)
    zoom = max(2.0, min(5.5, math.log2(360.0 / max(lon_span, lat_span, 1e-6)) - 1.6))
    return {
        "lon": lons, "lat": lats,
        "center": {"lat": (min(tlat) + max(tlat)) / 2, "lon": (min(tlon) + max(tlon)) / 2},
        "zoom": zoom,
    }
