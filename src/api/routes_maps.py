"""Routes for spatial MHW grid maps."""
from __future__ import annotations

import re
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from fastapi import APIRouter, HTTPException, Query

from api.schema import MapCell, MapPayload

router = APIRouter()

ROOT       = Path(__file__).parents[2]
STATES_DIR = ROOT / "data" / "derived" / "states_grid"
RAW_DIR    = ROOT / "data" / "raw"

METRIC_UNITS = {
    "A": "flag (0/1)",
    "I": "°C",
    "D": "days",
    "C": "°C·days",
    "x": "°C",
}

_FILE_PATTERN = re.compile(
    r"states_(\w+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.zarr$"
)

# In-memory cache: path_str → (lats, lons, dates, arrays)
_zarr_cache: dict[str, dict] = {}


def _find_zarr(region: str, query_date: date) -> Path | None:
    """Return the zarr path whose date range covers query_date."""
    for p in sorted(STATES_DIR.iterdir()):
        m = _FILE_PATTERN.match(p.name)
        if not m:
            continue
        if m.group(1) != region:
            continue
        z_start = date.fromisoformat(m.group(2))
        z_end   = date.fromisoformat(m.group(3))
        if z_start <= query_date <= z_end:
            return p
    return None


def _load_zarr(path: Path) -> dict:
    key = str(path)
    if key in _zarr_cache:
        return _zarr_cache[key]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds = xr.open_zarr(key, consolidated=False)

    lats  = ds["lat"].values.astype(float)
    lons  = ds["lon"].values.astype(float)
    dates = pd.DatetimeIndex(ds["time"].values).date.tolist()

    arrays: dict[str, np.ndarray] = {}
    for var in ("A", "I", "C", "x"):
        if var in ds:
            arrays[var] = ds[var].values.astype(np.float32)

    if "D" in ds:
        D_raw = ds["D"].values
        if np.issubdtype(D_raw.dtype, np.timedelta64):
            arrays["D"] = (
                D_raw.astype("timedelta64[ns]").astype(np.int64)
                / 86_400_000_000_000
            ).astype(np.float32)
        else:
            arrays["D"] = D_raw.astype(np.float32)

    ds.close()
    result = {"lats": lats, "lons": lons, "dates": dates, **arrays}
    _zarr_cache[key] = result
    return result


def _land_mask(region: str, lats: np.ndarray, lons: np.ndarray) -> np.ndarray | None:
    """True where cell is land (NaN in OISST)."""
    candidates = sorted(RAW_DIR.glob(f"oisst_{region}_????.nc"))
    if not candidates:
        return None
    import xarray as xr
    with xr.open_dataset(str(candidates[0])) as ds:
        sst = ds["sst"].isel(time=0).values
    return np.isnan(sst)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/map/mhw", response_model=MapPayload)
def get_map(
    region: str = Query(..., description="Region ID, e.g. 'goa'"),
    date:   date = Query(..., description="Date YYYY-MM-DD"),
    metric: str  = Query("I", description="State variable: A, I, D, C, or x"),
):
    """Return per-cell metric values for a region/date as a list of {lat,lon,value}."""
    if metric not in METRIC_UNITS:
        raise HTTPException(
            status_code=422,
            detail=f"metric must be one of {list(METRIC_UNITS)}"
        )

    zarr_path = _find_zarr(region, date)
    if zarr_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No state zarr found for region='{region}' covering {date}"
        )

    data = _load_zarr(zarr_path)

    if metric not in data:
        raise HTTPException(status_code=404, detail=f"Metric '{metric}' not in zarr")

    if date not in data["dates"]:
        raise HTTPException(status_code=404, detail=f"Date {date} not in zarr")

    t_idx = data["dates"].index(date)
    values = data[metric][t_idx]  # (n_lat, n_lon)

    land = _land_mask(region, data["lats"], data["lons"])

    cells: list[MapCell] = []
    for i, lat in enumerate(data["lats"]):
        for j, lon in enumerate(data["lons"]):
            v = float(values[i, j])
            is_land = bool(land[i, j]) if land is not None else False
            if is_land or v <= 0:
                cells.append(MapCell(lat=round(lat, 4), lon=round(lon, 4), value=None))
            else:
                cells.append(MapCell(lat=round(lat, 4), lon=round(lon, 4),
                                     value=round(v, 4)))

    return MapPayload(
        region=region,
        date=str(date),
        metric=metric,
        units=METRIC_UNITS[metric],
        cells=cells,
    )
