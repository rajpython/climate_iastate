"""Build the 24 predictand CSVs from the rebuilt per-year state stores with the committed code (a672583)."""
import sys, time
from datetime import date
from pathlib import Path
import pandas as pd
import xarray as xr
from mhw.states.aggregates import STATES_DIR, _load_mask_weights, aggregate_region, to_monthly, load_filled_days
out = Path(sys.argv[1]); zones = sys.argv[2:]
fd = load_filled_days()
for z in zones:
    t = time.time(); parts = []; mask = w = None
    for y in range(1982, 2027):
        end = "2026-07-01" if y == 2026 else f"{y}-12-31"
        ds = xr.open_zarr(str(STATES_DIR / f"states_{z}_{y}-01-01_{end}.zarr"), consolidated=False)
        if mask is None:
            mask, w = _load_mask_weights(z, ds["lat"].values, ds["lon"].values)
        parts.append(aggregate_region(ds, mask, w, filled_days=fd)); ds.close()
    d = pd.concat(parts, ignore_index=True); d["date"] = pd.to_datetime(d["date"])
    assert d["date"].is_monotonic_increasing and d["date"].diff().dropna().eq(pd.Timedelta("1D")).all()
    keep = ["date", "area_frac", "Ibar", "Dbar", "Cbar", "Obar", "n_days_input", "n_cells_valid"]
    d[keep].to_csv(out / "daily" / f"predictand_daily_{z}.csv", index=False, date_format="%Y-%m-%d")
    to_monthly(d).to_csv(out / "monthly" / f"predictand_monthly_{z}.csv", index=False, date_format="%Y-%m-%d")
    print(z, len(d), int(mask.sum()), f"{time.time()-t:.0f}s", flush=True)
