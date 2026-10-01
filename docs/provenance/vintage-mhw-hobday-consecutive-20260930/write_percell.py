import sys; sys.path.insert(0, sys.argv[1])
from pathlib import Path
import numpy as np, pandas as pd
from keys import load_xA, kx, kA
out = Path(sys.argv[2])
for z in sys.argv[3:]:
    x, A, t, lat, lon = load_xA("/Users/rajpython/dev/climate_rebuild", z)
    t = pd.DatetimeIndex(t).normalize().values.astype("datetime64[D]")
    xs = np.ascontiguousarray(np.nan_to_num(x, nan=0.0).astype("<f4")); As = np.ascontiguousarray(A.astype("<u1"))
    np.savez_compressed(out / f"x_{z}.npz", x=xs, lat=lat.astype("<f8"), lon=lon.astype("<f8"), time=t)
    np.savez_compressed(out / f"A_{z}.npz", A=As, lat=lat.astype("<f8"), lon=lon.astype("<f8"), time=t)
    d = np.load(out / f"x_{z}.npz"); e = np.load(out / f"A_{z}.npz")
    print(z, kx(d["x"]), kA(e["A"]), d["x"].shape, str(d["time"][0]), str(d["time"][-1]), flush=True)
