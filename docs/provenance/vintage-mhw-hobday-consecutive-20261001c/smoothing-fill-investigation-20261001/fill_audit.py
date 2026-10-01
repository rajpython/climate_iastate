"""Thresholds defined only by the NaN-aware 31-day smoothing fill: no valid baseline sample within the 11-day window."""
import json, sys
import numpy as np, pandas as pd, xarray as xr
from mhw.climatology.ice_outage import apply_ice_outages
def theta(d, z):
    ds = xr.open_zarr(f"data/derived/{d}/theta90_{z}.zarr", consolidated=False); v = ds[list(ds.data_vars)[0]]
    dd = [x for x in v.dims if x not in ("lat", "lon")][0]; return v.transpose(dd, "lat", "lon").values  # native order = engine order
res = {}
for z in sys.argv[1:]:
    out = {}
    for tag, clim, rule in (("v3", "climatology_v3", False), ("v5", "climatology", True)):
        cnt = None
        for y in range(1991, 2021):
            ds = xr.open_dataset(f"data/raw/oisst_{z}_{y}.nc").load()
            ice = apply_ice_outages(z, ds) if rule else ds.ice.values
            valid = np.isfinite(ds.sst.values) & ~(np.nan_to_num(ice) > 0.15)
            doy = pd.DatetimeIndex(ds.time.values).dayofyear.values - 1
            if cnt is None: cnt = np.zeros((366,) + valid.shape[1:], np.int32)
            np.add.at(cnt, doy, valid.astype(np.int32))
        win = sum(np.roll(cnt, k, axis=0) for k in range(-5, 6))          # pooled samples in the 11-day window (wrap)
        th = theta(clim, z); fin = np.isfinite(th)
        filled = fin & (win == 0)
        out[tag] = dict(theta_finite=int(fin.sum()), filled_by_smoothing_only=int(filled.sum()),
                        filled_share=round(float(filled.sum() / max(fin.sum(), 1)), 4),
                        thin_1to3_samples=int((fin & (win >= 1) & (win <= 3)).sum()))
        if tag == "v5":
            np.save(f"/tmp/filled_{z}.npy", filled)
    res[z] = out; print(z, out, flush=True)
json.dump(res, open(sys.argv[0].replace("fill_audit.py", "fill_audit.json"), "w"), indent=1)
