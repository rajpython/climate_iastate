"""Per-cell masks of #5 thresholds that exist only through the NaN-aware 31-day smoothing (no valid baseline sample in the
11-day window), plus the window sample count. Orientation = audit5 layout: (doy 1..366, lat asc, lon asc).
Usage: borrowed_masks.py <out_dir> <audit5_layout_dir> zone ..."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
from mhw.climatology.ice_outage import apply_ice_outages
out, ref, zones = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
summary = {}
for z in zones:
    cnt = None
    for y in range(1991, 2021):
        ds = xr.open_dataset(f"data/raw/oisst_{z}_{y}.nc").load()
        valid = np.isfinite(ds.sst.values) & ~(np.nan_to_num(apply_ice_outages(z, ds)) > 0.15)
        doy = pd.DatetimeIndex(ds.time.values).dayofyear.values - 1
        if cnt is None:
            cnt = np.zeros((366,) + valid.shape[1:], np.int32); lat, lon = ds.lat.values, ds.lon.values
        np.add.at(cnt, doy, valid.astype(np.int32))
    win = sum(np.roll(cnt, k, axis=0) for k in range(-5, 6))
    da = xr.DataArray(win, dims=("doy", "lat", "lon"), coords={"doy": np.arange(1, 367, dtype="int32"), "lat": lat.astype("float32"), "lon": lon.astype("float32")}).sortby(["lat", "lon"])
    a5 = xr.open_dataset(ref / f"theta90_{z}.nc")
    assert np.array_equal(a5.lat.values, da.lat.values) and np.array_equal(a5.lon.values, da.lon.values)
    th = a5.theta90.values; fin = np.isfinite(th)
    borrowed = fin & (da.values == 0)
    o = xr.Dataset({"borrowed": (("doy", "lat", "lon"), borrowed.astype("uint8"), {"meaning": "1 = theta90/mu_clim finite in vintage #5 only through the NaN-aware 31-day DOY smoothing: no valid baseline (1991-2020) sample in the cell's 11-day window"}),
                    "n_window_samples": (("doy", "lat", "lon"), da.values.astype("int32"), {"meaning": "valid baseline samples (SST finite, effective ice <= 0.15, 1991-2020, ice-outage rule applied) pooled in the 11-day DOY window"})},
                   coords={"doy": da.doy.values, "lat": da.lat.values, "lon": da.lon.values},
                   attrs={"zone": z, "vintage_id": "mhw-hobday-consecutive-20261001c", "theta90_sha256": a5.attrs["canonical_theta90_sha256"]})
    o.to_netcdf(out / f"borrowed_thresholds_{z}.nc", encoding={v: {"zlib": True, "complevel": 4} for v in o.data_vars})
    summary[z] = dict(theta_finite=int(fin.sum()), borrowed=int(borrowed.sum()), share=round(float(borrowed.sum() / max(fin.sum(), 1)), 4),
                      window_1to3=int((fin & (da.values >= 1) & (da.values <= 3)).sum()), theta_eq_mu_single_sample=int((fin & (np.abs(th - a5.mu_clim.values) < 1e-6)).sum()))
    print(z, summary[z], flush=True)
json.dump(summary, open(out / "BORROWED-SUMMARY.json", "w"), indent=2)
