"""Independent check of the 2024-04-22..26 replacement (does not import the splice module).
Usage: verify_replace.py <backup_2024_dir> <new_raw_dir> <ncei_dir>
For each oisst_<zone>_2024.nc: same time axis; every day other than the five bit-identical to the backup;
each of the five bit-identical to its NCEI file on the cache grid (lon mod 360) and different from the backup."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
old_d, new_d, ncei = map(Path, sys.argv[1:4])
five = pd.to_datetime([f"2024-04-{d}" for d in range(22, 27)])
bad = []; n = 0
for op in sorted(old_d.glob("oisst_*_2024.nc")):
    o = xr.open_dataset(op).load(); nw = xr.open_dataset(new_d / op.name).load()
    if not np.array_equal(o.time.values, nw.time.values): bad.append(f"{op.name}: time axis"); continue
    t = pd.DatetimeIndex(o.time.values).normalize(); keep = ~t.isin(five)
    for v in ("sst", "ice"):
        if not np.array_equal(o[v].values[keep], nw[v].values[keep], equal_nan=True): bad.append(f"{op.name}: {v} changed off the five days")
    for d in five:
        i = int(np.flatnonzero(t == d)[0]); n += 1
        src = xr.open_dataset(ncei / f"oisst-avhrr-v02r01.{d:%Y%m%d}.nc").load().isel(zlev=0).squeeze("time", drop=True)
        sub = src.sel(lat=nw.lat.values, lon=nw.lon.values % 360)
        for v in ("sst", "ice"):
            if not np.array_equal(sub[v].values.astype(nw[v].dtype), nw[v].values[i], equal_nan=True): bad.append(f"{op.name}: {d.date()} {v} != NCEI")
        if np.array_equal(o.sst.values[i], nw.sst.values[i], equal_nan=True): bad.append(f"{op.name}: {d.date()} unchanged (not replaced)")
print(json.dumps(dict(files=len(list(old_d.glob('oisst_*_2024.nc'))), zone_days_checked=n, failures=bad, verdict="PASS" if not bad else "FAIL"), indent=1))
