"""Identity keys per mini's intake_lib recipes: x/A (time,lat,lon) ascending; x '<f4' 0-filled; A '<u1'; theta90 (doy,lat,lon) '<f4' NaN kept."""
import hashlib, sys
from pathlib import Path
import numpy as np, xarray as xr
def h(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def load_xA(root, z):
    st = Path(root) / "data/derived/states_grid"
    xs, As, ts = [], [], []
    for y in range(1982, 2027):
        end = "2026-07-01" if y == 2026 else f"{y}-12-31"
        ds = xr.open_zarr(str(st / f"states_{z}_{y}-01-01_{end}.zarr"), consolidated=False).sortby(["lat", "lon"])
        xs.append(ds["x"].values); As.append(ds["A"].values); ts.append(ds["time"].values)
        lat, lon = ds["lat"].values, ds["lon"].values; ds.close()
    return np.concatenate(xs), np.concatenate(As), np.concatenate(ts), lat, lon
def kx(x): return h(np.nan_to_num(x, nan=0.0).astype("<f4"))
def kA(A): return h(A.astype("<u1"))
def kth(root, z):
    ds = xr.open_zarr(str(Path(root) / f"data/derived/climatology/theta90_{z}.zarr"), consolidated=False)
    v = ds[list(ds.data_vars)[0]]
    dims = [d for d in v.dims]
    doy = [d for d in dims if d not in ("lat", "lon")][0]
    v = v.sortby(["lat", "lon"]).transpose(doy, "lat", "lon")
    return h(v.values.astype("<f4"))
if __name__ == "__main__":
    root, zones = sys.argv[1], sys.argv[2:]
    for z in zones:
        x, A, t, lat, lon = load_xA(root, z)
        print(z, "x", kx(x), "A", kA(A), "theta90", kth(root, z), x.shape, flush=True)
