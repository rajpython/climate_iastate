"""Independent check of the 2026-10-01 extension splice (does not import the splice module).

Usage: verify_extend.py <backup_2026_dir> <new_raw_dir> <ncei_dir> <first_new_day> <last_day>
For each oisst_<zone>_2026.nc: (1) every day in the backup is bit-identical in the new file; (2) the added days
are exactly the calendar days after the backup's last day through <last_day>, none outside; (3) each added day is
bit-identical to the NCEI per-day file at the cache grid (lon mod 360); (4) the new file covers 2026-01-01..<last_day>
with no gap.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
old_d, new_d, ncei, first, last = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5]
bad, added = [], 0
for op in sorted(old_d.glob("oisst_*_2026.nc")):
    o = xr.open_dataset(op).load(); n = xr.open_dataset(new_d / op.name).load()
    ot, nt = pd.DatetimeIndex(o.time.values), pd.DatetimeIndex(n.time.values)
    if not (np.array_equal(o.lat, n.lat) and np.array_equal(o.lon, n.lon)): bad.append(f"{op.name}: grid"); continue
    if not ot.isin(nt).all(): bad.append(f"{op.name}: lost days"); continue
    for v in ("sst", "ice"):
        if not np.array_equal(o[v].values, n[v].sel(time=ot).values, equal_nan=True): bad.append(f"{op.name}: {v} changed")
    new_days = nt[~nt.isin(ot)].normalize()
    expect = pd.date_range(ot.normalize().max() + pd.Timedelta(days=1), last)
    if not new_days.equals(expect): bad.append(f"{op.name}: added {len(new_days)} != expected {len(expect)}")
    if pd.Timestamp(first) > new_days.min(): bad.append(f"{op.name}: added before {first}")
    cal = pd.date_range("2026-01-01", last)
    if not cal.isin(nt.normalize()).all(): bad.append(f"{op.name}: calendar gap")
    for t in new_days:
        added += 1
        src = xr.open_dataset(ncei / f"oisst-avhrr-v02r01.{t:%Y%m%d}.nc").load().isel(zlev=0).squeeze("time", drop=True)
        sub = src.sel(lat=n.lat.values, lon=n.lon.values % 360)
        for v in ("sst", "ice"):
            if not np.array_equal(sub[v].values.astype(n[v].dtype), n[v].sel(time=t + pd.Timedelta(hours=12)).values, equal_nan=True):
                bad.append(f"{op.name}: {t.date()} {v} != NCEI")
print(json.dumps(dict(files=len(list(old_d.glob('oisst_*_2026.nc'))), zone_days_added=added, failures=bad,
                      verdict="PASS" if not bad else "FAIL"), indent=1))
