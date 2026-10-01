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
On an outage day a cell's ice status is UNKNOWN. It is taken from the zone's last non-outage day
before the outage and its first non-outage day after it: the effective ice is the larger of the two
(no value = 0). The existing ``ice > threshold`` test then masks the cell unless it was ice-free on
BOTH sides. Only BLANK cells are substituted; a cell with an observed ice value keeps it. Consequences: cells that never carry ice (GOA, Aleutians, the open southern shelf) are
untouched; a cell ice-covered on either side is treated as missing, which is what "ice-covered cells
are treated as missing" has always meant. Inputs are never altered -- the substitution happens in
memory, after reading.

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


def bracket_ice(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Effective ice for an outage day: max of the bracketing days, a missing value counting as 0."""
    return np.fmax(np.nan_to_num(before, nan=0.0), np.nan_to_num(after, nan=0.0)).astype(np.float32)


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
    return json.loads(p.read_text()) if p.exists() else {}


def _ice_on(region_id: str, d: date, raw_dir: Path) -> np.ndarray | None:
    p = Path(raw_dir) / f"oisst_{region_id}_{d.year}.nc"
    with xr.open_dataset(p) as ds:
        t = pd.DatetimeIndex(ds["time"].values).normalize()
        hit = np.flatnonzero(t == pd.Timestamp(d))
        return ds["ice"].values[hit[0]].astype(np.float32) if len(hit) else None


def _nearest_good(region_id: str, start: date, step: int, bad: set[date], raw_dir: Path,
                  limit: int = 60) -> np.ndarray:
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
def effective_ice_fields(region_id: str, raw_dir: str = str(DATA_RAW),
                         config: str = str(OUTAGE_CONFIG)) -> dict[date, np.ndarray]:
    """{outage day: effective ice field} for *region_id*, bracketing each run of outage days."""
    bad = outage_days_for(load_outage_doc(config), region_id)
    eff: dict[date, np.ndarray] = {}
    for first, last in runs(bad):
        before = _nearest_good(region_id, first, -1, bad, Path(raw_dir))
        after = _nearest_good(region_id, last, +1, bad, Path(raw_dir))
        field = bracket_ice(before, after)
        d = first
        while d <= last:
            eff[d] = field
            d += timedelta(days=1)
    return eff


def apply_ice_outages(region_id: str, ds: xr.Dataset, raw_dir: Path = DATA_RAW,
                      config: Path = OUTAGE_CONFIG) -> np.ndarray:
    """The ice array of a zone-year dataset with outage days replaced by their effective fields."""
    times = pd.DatetimeIndex(ds["time"].values).normalize().date.tolist()
    ice = ds["ice"].values
    if not Path(config).exists():
        return np.asarray(ice, dtype=np.float32)
    eff = effective_ice_fields(region_id, str(raw_dir), str(config))
    if not any(t in eff for t in times):
        return np.asarray(ice, dtype=np.float32)
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
        eff = effective_ice_fields(z)
        masked = sum(int((f > a.threshold).sum()) for f in eff.values())
        print(f"  {z}: {len(days)} outage days; cell-days masked by the bracket rule: {masked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
