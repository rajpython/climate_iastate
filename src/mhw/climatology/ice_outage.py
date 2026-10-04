"""Ice-field outages in OISST v2.1: days whose sea-ice field is absent, and how the engine treats them.

CLI: mhw-ice-outage-report [--region R ...]   (prints, per zone, the outage days and the cell-days they mask)

The defect (lofra-mini, 2026-10-01)
-----------------------------------
OISST never writes ice = 0: open water carries NO ice value, so a blank ice cell normally means
"ice-free". On some days the ice field is absent from the product altogether -- 171 days with not one
ice value anywhere on Earth (1987-12/1988-01, 2016-01/04/05/06, 2017-01/02, 2020-08, 2020-12) and a
regional outage over the Bering/Chukchi/Beaufort 2024-04-22..26. On those days every ice-covered cell
read as open water: the ``ice > 0.15`` mask is False for NaN, so frozen water at -1.7 degC entered the
baseline AND detection. Beaufort's winter theta90 was built almost entirely from the 2017 outage
(30,212 valid February cell-days against 476 in a normal February), and February 2017 read a
heatwave area of 0.256 against <= 0.015 in every other year.

The rule (applied identically in the baseline and in detection)
---------------------------------------------------------------
On an outage day a BLANK cell's ice status is unknown. Its effective ice is interpolated linearly in
time between the zone's last non-outage day before the outage and its first non-outage day after
it (no value = 0), EXCEPT that a cell whose SST that day is above 2 degC is taken as open water
(ice 0): water under consolidated ice cannot be that warm. The existing ``ice > threshold`` test
then does the rest. A cell carrying an observed ice value keeps it. Inputs are never altered -- the
substitution happens in memory, after reading.

Chosen by back-test, not by argument (2026-10-01): hiding the ice field over outage-shaped windows
(Apr 18-Jun 30, Jan 7-Feb 28, Dec 6-Jan 10) in normal years of sebs/nbs/chukchi/beaufort and scoring
against the real field, this rule catches >= 97% of ice cells in every season while wrongly masking
12% of open water in the melt season (5.5% in winter). The first candidate -- the larger of the two
bracketing days -- caught 99.6% but discarded 39% of melt-season open water (it masked nbs/sebs for
all of Apr-Jun 2016 though 74-91% of those cells were above 0 degC); an SST-only cutoff missed
15-22% of ice. The cells this rule lets through are > 2 degC, so the defect's mechanism -- frozen
water at -1.7 degC scored as open sea -- is closed completely.

The outage list is ``config/ice_outage_days.json`` (dates, scope, evidence). Global days apply to
every zone; regional days to the zones listed.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.exec_record import record_missing, record_open
from mhw.utils.grid import assert_same_grid

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTAGE_CONFIG = PROJECT_ROOT / "config" / "ice_outage_days.json"
DATA_RAW = PROJECT_ROOT / "data" / "raw"


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def outage_days_for(doc: dict, region_id: str) -> set[date]:
    """Outage days that apply to *region_id*: all global days + regional days listing it."""
    out: set[date] = set()
    for d in doc.get("global", {}).get("days", []):
        out.add(date.fromisoformat(d))
    for entry in doc.get("regional", []):
        if region_id in entry.get("zones", []):
            out.update(date.fromisoformat(d) for d in entry["days"])
    return out


def runs(days: set[date]) -> list[tuple[date, date]]:
    """Group days into maximal runs of consecutive calendar days -> [(first, last), ...]."""
    s = sorted(days)
    out: list[tuple[date, date]] = []
    for d in s:
        if out and d == out[-1][1] + timedelta(days=1):
            out[-1] = (out[-1][0], d)
        else:
            out.append((d, d))
    return out


SST_OPEN_WATER = 2.0   # degC: above this a cell is open water whatever the interpolated ice says


def interpolated_ice(before: np.ndarray, after: np.ndarray, frac: float) -> np.ndarray:
    """Ice linearly interpolated between the bracketing days; frac in (0, 1); a missing value counts as 0."""
    b = np.nan_to_num(before, nan=0.0)
    a = np.nan_to_num(after, nan=0.0)
    return ((1.0 - frac) * b + frac * a).astype(np.float32)


def effective_field(before: np.ndarray, after: np.ndarray, frac: float, sst: np.ndarray) -> np.ndarray:
    """Effective ice on an outage day: interpolated ice, zeroed where SST > SST_OPEN_WATER."""
    eff = interpolated_ice(before, after, frac)
    eff[np.nan_to_num(sst, nan=-99.0) > SST_OPEN_WATER] = 0.0
    return eff


def substitute(ice: np.ndarray, times: list[date], effective: dict[date, np.ndarray]) -> np.ndarray:
    """Return a copy of ice (T, lat, lon) in which, on each outage day, every BLANK cell takes its
    effective value. A cell that does carry an ice value on that day keeps it (observed beats inferred)."""
    out = np.array(ice, dtype=np.float32, copy=True)
    for i, d in enumerate(times):
        if d in effective:
            blank = np.isnan(out[i])
            out[i][blank] = effective[d][blank]
    return out


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_outage_doc(path: str = str(OUTAGE_CONFIG)) -> dict:
    p = Path(path)
    record_open(p, "config")
    return json.loads(p.read_text()) if p.exists() else {}


# Grid of the bracketing files, per outage_brackets() key: checked against the dataset the
# brackets are applied to (a raw/raw join, guarded like the SST/threshold join).
_BRACKET_GRID: dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]] = {}


def _ice_on(region_id: str, d: date, raw_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """(ice on day d, lat, lon) from the zone-year file, or None when the file lacks that day."""
    p = Path(raw_dir) / f"oisst_{region_id}_{d.year}.nc"
    if not p.exists():
        record_missing(p, "raw_ice_bracket")
        raise FileNotFoundError(p)
    record_open(p, "raw_ice_bracket")
    with xr.open_dataset(p) as ds:
        t = pd.DatetimeIndex(ds["time"].values).normalize()
        hit = np.flatnonzero(t == pd.Timestamp(d))
        if not len(hit):
            return None
        return ds["ice"].values[hit[0]].astype(np.float32), ds["lat"].values, ds["lon"].values


def _nearest_good(region_id: str, start: date, step: int, bad: set[date], raw_dir: Path,
                  limit: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d = start
    for _ in range(limit):
        d = d + timedelta(days=step)
        if d in bad:
            continue
        try:
            arr = _ice_on(region_id, d, raw_dir)
        except FileNotFoundError:
            arr = None
        if arr is not None:
            return arr
    raise RuntimeError(f"{region_id}: no non-outage day within {limit} days of {start} (step {step})")


@lru_cache(maxsize=64)
def outage_brackets(region_id: str, raw_dir: str = str(DATA_RAW),
                    config: str = str(OUTAGE_CONFIG)) -> dict[date, tuple[np.ndarray, np.ndarray, float]]:
    """{outage day: (ice before, ice after, interpolation fraction)} for *region_id*."""
    bad = outage_days_for(load_outage_doc(config), region_id)
    out: dict[date, tuple[np.ndarray, np.ndarray, float]] = {}
    grid = None
    for first, last in runs(bad):
        before, *g_b = _nearest_good(region_id, first, -1, bad, Path(raw_dir))
        after, *g_a = _nearest_good(region_id, last, +1, bad, Path(raw_dir))
        for g in (g_b, g_a):
            if grid is None:
                grid = g
            assert_same_grid(*grid, *g, where=f"ice-outage bracket files ({region_id})")
        n = (last - first).days + 1
        for k in range(n):
            out[first + timedelta(days=k)] = (before, after, (k + 1) / (n + 1))
    if grid is not None:
        _BRACKET_GRID[(region_id, raw_dir, config)] = tuple(grid)
    return out


def apply_ice_outages(region_id: str, ds: xr.Dataset, raw_dir: Path = DATA_RAW,
                      config: Path = OUTAGE_CONFIG) -> np.ndarray:
    """The ice array of a zone-year dataset with outage days' blank cells given their effective ice."""
    times = pd.DatetimeIndex(ds["time"].values).normalize().date.tolist()
    ice = ds["ice"].values
    if not Path(config).exists():
        return np.asarray(ice, dtype=np.float32)
    # Bracketing reads raw files around EVERY outage run; skip it when this dataset has no outage
    # day, so a host holding only recent years (the VM caches 2025-26) never needs 1987 on disk.
    if not set(times) & outage_days_for(load_outage_doc(str(config)), region_id):
        return np.asarray(ice, dtype=np.float32)
    br = outage_brackets(region_id, str(raw_dir), str(config))
    grid = _BRACKET_GRID.get((region_id, str(raw_dir), str(config)))
    if grid is not None:
        assert_same_grid(ds["lat"].values, ds["lon"].values, *grid,
                         where=f"ice-outage brackets vs zone-year data ({region_id})")
    hits = [(i, t) for i, t in enumerate(times) if t in br]
    if not hits:
        return np.asarray(ice, dtype=np.float32)
    sst = ds["sst"].values
    eff = {t: effective_field(*br[t], sst[i]) for i, t in hits}
    return substitute(ice, times, eff)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="mhw-ice-outage-report", description=__doc__.split("\n")[0])
    ap.add_argument("--region", nargs="*", default=None)
    ap.add_argument("--threshold", type=float, default=0.15)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    doc = load_outage_doc()
    zones = a.region or sorted({p.name.split("_", 1)[1].rsplit("_", 1)[0] for p in DATA_RAW.glob("oisst_*_*.nc")})
    for z in zones:
        days = outage_days_for(doc, z)
        masked = 0
        for y in sorted({d.year for d in days}):
            with xr.open_dataset(DATA_RAW / f"oisst_{z}_{y}.nc") as ds:
                eff = apply_ice_outages(z, ds)
                blank = np.isnan(ds["ice"].values) & np.isfinite(ds["sst"].values)
                masked += int((blank & (eff > a.threshold)).sum())
        print(f"  {z}: {len(days)} outage days; blank SST cell-days masked by the rule: {masked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
