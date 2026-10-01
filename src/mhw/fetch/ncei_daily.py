"""Splice NCEI per-day OISST v2.1 files into the producer's zone-year input cache.

CLI: mhw-splice-ncei --ncei-dir DIR --start YYYY-MM-DD --end YYYY-MM-DD [--region R ...] [--dry-run]
     mhw-splice-ncei --ncei-dir DIR --replace YYYY-MM-DD [YYYY-MM-DD ...] [--region R ...] [--dry-run]

Why this exists
---------------
The PFEG ``ncdcOisst21Agg`` aggregate the cache was built from is itself missing ~1,200
days (7.3% of its span, inside the 1991-2020 baseline), so history is NEVER re-fetched
from it. Days the cache lacks -- the eight repaired 2026-09-30, and the 2026-07-02..08-31
extension of 2026-10-01 -- come instead from NCEI's per-day files, the same product (agrees
with PFEG to 4.8e-07 degC on an overlapping day), one immutable file per day:

    https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/
        access/avhrr/<YYYYMM>/oisst-avhrr-v02r01.<YYYYMMDD>.nc

Rules enforced here (each one is a defect this project has already paid for):
  * Final files only: a ``_preliminary`` file is refused.
  * The day is subset onto the cache file's OWN lat/lon grid (lon taken mod 360), so a
    spliced day is cell-for-cell the grid the engine already reads. A grid mismatch raises.
  * Append-only by default: a day the cache already holds is never overwritten, and the
    result must hold every time step the cache held (never-shrink). The write is temp-file +
    atomic rename, as in ``build_mu_theta.fetch_year``.
  * Replacement is a separate, explicit mode (``--replace DAY ...``) for days NCEI has
    RE-ISSUED (e.g. 2024-04-22..26, re-issued 2024-06-05; every ERDDAP/PSL copy is stale).
    Only the days named one by one are replaced; each must already be in the cache; the time
    axis and the day count must come out unchanged (never-shrink, checked on the written
    bytes); and every other day must be bit-identical before and after. Old and new values
    are hashed per day and returned for the record.
"""
from __future__ import annotations

import argparse
import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
NCEI_BASE = (
    "https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/"
    "v2.1/access/avhrr"
)
_NAME_RE = re.compile(r"^oisst-avhrr-v02r01\.(\d{8})(_preliminary)?\.nc$")
VARS = ("sst", "ice")


# ---------------------------------------------------------------------------
# Pure helpers (network- and disk-free; unit-tested)
# ---------------------------------------------------------------------------
def ncei_filename(day: date) -> str:
    return f"oisst-avhrr-v02r01.{day:%Y%m%d}.nc"


def ncei_url(day: date) -> str:
    return f"{NCEI_BASE}/{day:%Y%m}/{ncei_filename(day)}"


def parse_ncei_name(name: str) -> tuple[date, bool]:
    """``oisst-avhrr-v02r01.YYYYMMDD[_preliminary].nc`` -> (day, is_preliminary)."""
    m = _NAME_RE.match(name)
    if not m:
        raise ValueError(f"not an NCEI OISST v2.1 per-day file name: {name!r}")
    return pd.Timestamp(m.group(1)).date(), bool(m.group(2))


def subset_day(src: xr.Dataset, lat: np.ndarray, lon: np.ndarray) -> xr.Dataset:
    """One NCEI global day -> (time, lat, lon) on the cache grid, ``sst`` and ``ice`` only.

    ``lon`` is the cache's own longitude (either convention); NCEI is 0-360, so the
    selection uses ``lon % 360`` and the result carries the cache's coordinates back.
    Exact-match selection: a cache cell absent from the NCEI grid raises KeyError.
    """
    ds = src[list(VARS)]
    if "zlev" in ds.dims:
        ds = ds.isel(zlev=0, drop=True)
    elif "zlev" in ds.coords:
        ds = ds.drop_vars("zlev")
    sub = ds.sel(lat=np.asarray(lat), lon=np.asarray(lon) % 360)
    if not np.array_equal(sub["lat"].values, np.asarray(lat)):
        raise ValueError("NCEI latitude grid does not match the cache grid")
    return sub.assign_coords(lon=np.asarray(lon))


def splice(cache: xr.Dataset, days: list[xr.Dataset]) -> xr.Dataset:
    """Append new days to a zone-year cache; refuse overlap, keep time sorted.

    Pure: callers handle IO. The result holds every time step the cache held
    (never-shrink) plus exactly the new ones.
    """
    if not days:
        return cache
    old_t = pd.DatetimeIndex(cache["time"].values)
    new = xr.concat(days, dim="time")
    new_t = pd.DatetimeIndex(new["time"].values)
    if new_t.has_duplicates:
        raise ValueError("duplicate days in the splice set")
    clash = new_t.normalize().intersection(old_t.normalize())
    if len(clash):
        raise ValueError(f"cache already holds {len(clash)} of these days, e.g. {clash[0].date()}")
    for v in VARS:
        new[v] = new[v].astype(cache[v].dtype)
    out = xr.concat([cache[list(VARS)], new[list(VARS)]], dim="time").sortby("time")
    out.attrs = dict(cache.attrs)
    for v in VARS:
        out[v].attrs = dict(cache[v].attrs)
    if len(out["time"]) != len(old_t) + len(new_t):
        raise AssertionError("splice changed the number of existing time steps")
    return out


def replace(cache: xr.Dataset, days: list[xr.Dataset]) -> xr.Dataset:
    """Replace held days with re-issued ones; every replaced day must already be in the cache.

    Pure. The time axis is unchanged, so the result holds exactly the cache's time steps.
    """
    out = cache[list(VARS)].copy(deep=True)
    out.attrs = dict(cache.attrs)
    t = pd.DatetimeIndex(out["time"].values).normalize()
    for d in days:
        day = pd.DatetimeIndex(d["time"].values).normalize()
        if len(day) != 1:
            raise ValueError("replace expects one-day datasets")
        hit = np.flatnonzero(t == day[0])
        if len(hit) != 1:
            raise ValueError(f"cannot replace {day[0].date()}: not held exactly once in the cache")
        for v in VARS:
            out[v].values[hit[0]] = d[v].values[0].astype(out[v].dtype)
    return out


def day_sha256(ds: xr.Dataset, day: date) -> str:
    """sha256 of one day's (sst, ice) on the zone grid, '<f4' C-order, NaN kept -- a content key."""
    import hashlib
    t = pd.DatetimeIndex(ds["time"].values).normalize()
    i = int(np.flatnonzero(t == pd.Timestamp(day))[0])
    h = hashlib.sha256()
    for v in VARS:
        h.update(np.ascontiguousarray(ds[v].values[i].astype("<f4")).tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------
def load_ncei_day(ncei_dir: Path, day: date) -> xr.Dataset:
    p = Path(ncei_dir) / ncei_filename(day)
    if not p.exists():
        prelim = list(Path(ncei_dir).glob(f"oisst-avhrr-v02r01.{day:%Y%m%d}_preliminary.nc"))
        raise FileNotFoundError(
            f"{p.name} missing" + (" (only a _preliminary file exists; refused)" if prelim else "")
        )
    d, is_prelim = parse_ncei_name(p.name)
    if is_prelim or d != day:
        raise ValueError(f"refusing {p.name}")
    return xr.open_dataset(p).load()


def splice_into_cache(region: str, year: int, ncei_dir: Path, wanted: list[date],
                      raw_dir: Path = DATA_RAW, dry_run: bool = False) -> int:
    """Splice the wanted days the cache lacks into ``oisst_<region>_<year>.nc``. Returns days added."""
    cache_p = Path(raw_dir) / f"oisst_{region}_{year}.nc"
    with xr.open_dataset(cache_p) as c:
        cache = c.load()
    have = set(pd.DatetimeIndex(cache["time"].values).normalize().date)
    todo = [d for d in wanted if d.year == year and d not in have]
    if not todo or dry_run:
        return len(todo)
    lat, lon = cache["lat"].values, cache["lon"].values
    new = []
    for d in todo:
        with load_ncei_day(ncei_dir, d) as src:
            new.append(subset_day(src, lat, lon))
    out = splice(cache, new)
    tmp = cache_p.with_suffix(".tmp.nc")
    out.to_netcdf(tmp)
    with xr.open_dataset(tmp) as chk:            # never-shrink, checked on the written bytes
        if len(chk["time"]) != len(cache["time"]) + len(todo):
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"{cache_p.name}: written file has the wrong number of days")
    tmp.replace(cache_p)
    return len(todo)


def replace_in_cache(region: str, year: int, ncei_dir: Path, days: list[date],
                     raw_dir: Path = DATA_RAW, dry_run: bool = False) -> list[dict]:
    """Replace the named days of ``oisst_<region>_<year>.nc`` with NCEI's current files.

    Returns one record per day: old/new per-day content sha256 and max |dSST|.
    """
    cache_p = Path(raw_dir) / f"oisst_{region}_{year}.nc"
    with xr.open_dataset(cache_p) as c:
        cache = c.load()
    todo = [d for d in days if d.year == year]
    if not todo:
        return []
    lat, lon = cache["lat"].values, cache["lon"].values
    new = []
    for d in todo:
        with load_ncei_day(ncei_dir, d) as src:
            new.append(subset_day(src, lat, lon))
    out = replace(cache, new)
    recs = []
    for d, n in zip(todo, new):
        a = cache["sst"].sel(time=cache["time"].values[pd.DatetimeIndex(cache["time"].values).normalize() == pd.Timestamp(d)][0]).values
        recs.append(dict(zone=region, day=d.isoformat(), old_day_sha256=day_sha256(cache, d),
                         new_day_sha256=day_sha256(out, d),
                         max_abs_dsst=float(np.nanmax(np.abs(a - n["sst"].values[0]))) if np.isfinite(a).any() else 0.0))
    if dry_run:
        return recs
    keep = ~pd.DatetimeIndex(cache["time"].values).normalize().isin(pd.to_datetime(todo))
    tmp = cache_p.with_suffix(".tmp.nc")
    out.to_netcdf(tmp)
    with xr.open_dataset(tmp) as chk:
        ok = (len(chk["time"]) == len(cache["time"])
              and np.array_equal(chk["time"].values, cache["time"].values)
              and all(np.array_equal(chk[v].values[keep], cache[v].values[keep], equal_nan=True) for v in VARS))
    if not ok:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{cache_p.name}: replacement changed the time axis or an untouched day; refused")
    tmp.replace(cache_p)
    return recs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="mhw-splice-ncei", description=__doc__.split("\n")[0])
    ap.add_argument("--ncei-dir", type=Path, required=True)
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--replace", nargs="+", metavar="YYYY-MM-DD",
                    help="replace these held days with NCEI's current (re-issued) files; named one by one")
    ap.add_argument("--region", nargs="*", default=None,
                    help="zones (default: every oisst_<zone>_<year>.nc present for the years)")
    ap.add_argument("--raw-dir", type=Path, default=DATA_RAW)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    if a.replace:
        days = [date.fromisoformat(x) for x in a.replace]
        for y in sorted({d.year for d in days}):
            zones = a.region or sorted(
                p.name[len("oisst_"):-len(f"_{y}.nc")] for p in Path(a.raw_dir).glob(f"oisst_*_{y}.nc")
            )
            for z in zones:
                for r in replace_in_cache(z, y, a.ncei_dir, days, raw_dir=a.raw_dir, dry_run=a.dry_run):
                    print(f"  {r['zone']} {r['day']}: {'would replace' if a.dry_run else 'replaced'} "
                          f"old {r['old_day_sha256'][:12]} -> new {r['new_day_sha256'][:12]}  max|dSST| {r['max_abs_dsst']:.3f}")
        return 0
    if not (a.start and a.end):
        raise SystemExit("mhw-splice-ncei: give --start and --end (append), or --replace DAY ...")
    s, e = date.fromisoformat(a.start), date.fromisoformat(a.end)
    wanted = [s + timedelta(n) for n in range((e - s).days + 1)]
    years = sorted({d.year for d in wanted})
    for y in years:
        zones = a.region or sorted(
            p.name[len("oisst_"):-len(f"_{y}.nc")] for p in Path(a.raw_dir).glob(f"oisst_*_{y}.nc")
        )
        for z in zones:
            n = splice_into_cache(z, y, a.ncei_dir, wanted, raw_dir=a.raw_dir, dry_run=a.dry_run)
            print(f"  {z} {y}: {'would add' if a.dry_run else 'added'} {n} day(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
