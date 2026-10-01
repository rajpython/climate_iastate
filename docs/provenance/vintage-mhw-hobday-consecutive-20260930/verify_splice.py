"""Independent check of the 2026-09-30 OISST gap-fill splice.

For every zone-year input file the rebuild read that differs from the 20260722 cache:
  (1) every day present in the 20260722 file is present in the rebuilt file with bit-identical sst and ice;
  (2) the ONLY added time steps are days listed in config/filled_days.json;
  (3) each added day equals the NCEI per-day file subset at the file's own lat/lon grid (lon taken mod 360),
      bit-identical, NaN pattern included.
Usage: verify_splice.py <old_raw_dir> <new_raw_dir> <ncei_dir> <filled_days.json>
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
old, new, ncei, fdj = map(Path, sys.argv[1:5])
filled = set(json.loads(fdj.read_text())["days"])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def same(a, b): return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)
changed = [p.name for p in sorted(new.glob("oisst_*.nc")) if sha(p) != sha(old / p.name)]
bad, added_total = [], 0
for name in changed:
    o = xr.open_dataset(old / name); n = xr.open_dataset(new / name)
    if not (np.array_equal(o.lat, n.lat) and np.array_equal(o.lon, n.lon)):
        bad.append(f"{name}: grid differs"); continue
    ot, nt = pd.DatetimeIndex(o.time.values), pd.DatetimeIndex(n.time.values)
    if not ot.isin(nt).all():
        bad.append(f"{name}: lost days"); continue
    for v in ("sst", "ice"):
        if not same(o[v].values, n[v].sel(time=ot).values):
            bad.append(f"{name}: {v} changed on an original day")
    added = nt[~nt.isin(ot)]
    for t in added:
        d = t.strftime("%Y-%m-%d"); added_total += 1
        if d not in filled:
            bad.append(f"{name}: added {d} not in filled_days.json"); continue
        src = xr.open_dataset(ncei / f"oisst.{t:%Y%m%d}.nc").squeeze(["time", "zlev"], drop=True)
        sub = src.sel(lat=n.lat.values, lon=(n.lon.values % 360))
        if not (np.array_equal(sub.lat.values, n.lat.values) and np.allclose(sub.lon.values, n.lon.values % 360)):
            bad.append(f"{name}: {d} NCEI grid mismatch"); continue
        for v in ("sst", "ice"):
            if not same(sub[v].values.astype(n[v].dtype), n[v].sel(time=t).values):
                bad.append(f"{name}: {d} {v} != NCEI")
print(json.dumps(dict(files_changed=len(changed), days_added=added_total, failures=bad,
                      verdict="PASS" if not bad else "FAIL"), indent=1))
