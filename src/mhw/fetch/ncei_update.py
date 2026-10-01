"""Nightly OISST input update from NCEI per-day files -- the operational replacement for the PFEG re-pull.

CLI: mhw-update-ncei [--through YYYY-MM-DD] [--lookback-days 60] [--ncei-dir DIR] [--dry-run]

Why this exists
---------------
The nightly refresh used to re-download the whole current year from the PFEG ERDDAP aggregate
(``ncdcOisst21Agg``) and replace the cache with it. That aggregate is itself incomplete (2026-06-08
is absent there to this day; ~1,200 historical days are missing) and serves superseded versions of
files NCEI has re-issued (2024-04-22..26). Each nightly re-pull therefore silently re-opened the
holes the 2026-09-30 rebuild had closed. This module keeps the cache as the authority and only ever
ADDS to it, from NCEI's per-day files:

  * a day the cache lacks            -> appended: the FINAL file if NCEI has one, else the
                                        ``_preliminary`` file (recorded as preliminary);
  * a day held as preliminary        -> REPLACED by the final file once NCEI publishes it
                                        (``mhw.fetch.ncei_daily.replace``: same axis, other days
                                        bit-identical, checked on the written bytes);
  * any other held day               -> never touched.

Preliminary days are listed in ``data/raw/oisst_preliminary_days.json``; a day leaves the list only
when its final file has been written into every zone. A year file that does not exist yet (Jan 1)
is created on the previous year's grid. The engine then runs with ``MHW_FROZEN_INPUTS=1`` so it
reads the cache only.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.fetch.ncei_daily import NCEI_BASE, VARS, parse_ncei_name, replace, splice, subset_day

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
NCEI_CACHE = PROJECT_ROOT / "data" / "incoming" / "ncei_daily"
PRELIM_FILE = "oisst_preliminary_days.json"
_LISTING_RE = re.compile(r'href="(oisst-avhrr-v02r01\.\d{8}(?:_preliminary)?\.nc)"')


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def parse_listing(html: str) -> dict[date, dict[str, str]]:
    """NCEI month directory HTML -> {day: {"final": name, "preliminary": name}} (keys present only if listed)."""
    out: dict[date, dict[str, str]] = {}
    for name in set(_LISTING_RE.findall(html)):
        d, prelim = parse_ncei_name(name)
        out.setdefault(d, {})["preliminary" if prelim else "final"] = name
    return out


def plan_updates(window: list[date], held: set[date], prelim_held: set[date],
                 available: dict[date, dict[str, str]]) -> list[tuple[date, str, str]]:
    """Decide, per day in *window*, what to do. Returns [(day, action, file name)] with action in
    {"append_final", "append_preliminary", "replace_with_final"}; days needing nothing are omitted.

    Rules: never touch a held FINAL day; upgrade a held preliminary day only to a final file; append
    a missing day as final when available, else as preliminary; a day NCEI does not list is skipped.
    """
    plan: list[tuple[date, str, str]] = []
    for d in sorted(window):
        av = available.get(d, {})
        if d in held:
            if d in prelim_held and "final" in av:
                plan.append((d, "replace_with_final", av["final"]))
            continue
        if "final" in av:
            plan.append((d, "append_final", av["final"]))
        elif "preliminary" in av:
            plan.append((d, "append_preliminary", av["preliminary"]))
    return plan


def window_days(today: date, lookback: int) -> list[date]:
    """From min(Jan 1 of today's year, today - lookback) through yesterday."""
    start = min(date(today.year, 1, 1), today - timedelta(days=lookback))
    return [start + timedelta(days=i) for i in range((today - start).days)]


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------
def fetch_listing(yyyymm: str) -> dict[date, dict[str, str]]:
    with urllib.request.urlopen(f"{NCEI_BASE}/{yyyymm}/", timeout=60) as r:
        return parse_listing(r.read().decode())


def download(name: str, ncei_dir: Path) -> Path:
    ncei_dir.mkdir(parents=True, exist_ok=True)
    p = ncei_dir / name
    if p.exists() and p.stat().st_size > 0:
        return p
    d, _ = parse_ncei_name(name)
    tmp = p.with_suffix(".part")
    with urllib.request.urlopen(f"{NCEI_BASE}/{d:%Y%m}/{name}", timeout=120) as r, open(tmp, "wb") as f:
        f.write(r.read())
    tmp.replace(p)
    return p


def load_prelim(raw_dir: Path) -> set[date]:
    p = raw_dir / PRELIM_FILE
    if not p.exists():
        return set()
    return {date.fromisoformat(x) for x in json.loads(p.read_text()).get("days", [])}


def save_prelim(raw_dir: Path, days: set[date]) -> None:
    p = raw_dir / PRELIM_FILE
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps({"_comment": "Days held in data/raw/oisst_*_<year>.nc from NCEI _preliminary files; "
                               "mhw-update-ncei replaces each with the final file when NCEI publishes it.",
                               "days": sorted(d.isoformat() for d in days)}, indent=1) + "\n")
    tmp.replace(p)


def _held_days(path: Path) -> set[date]:
    if not path.exists():
        return set()
    with xr.open_dataset(path) as ds:
        return set(pd.DatetimeIndex(ds["time"].values).normalize().date)


def _zones_for_year(raw_dir: Path, year: int) -> list[str]:
    pat = re.compile(rf"^oisst_(.+)_{year}\.nc$")
    zones = {m.group(1) for p in raw_dir.glob(f"oisst_*_{year}.nc") if (m := pat.match(p.name))}
    zones |= {m.group(1) for p in raw_dir.glob(f"oisst_*_{year - 1}.nc")
              if (m := re.match(rf"^oisst_(.+)_{year - 1}\.nc$", p.name))}
    return sorted(zones)


def apply_zone_year(region: str, year: int, steps: list[tuple[date, str, str]],
                    ncei_dir: Path, raw_dir: Path) -> None:
    """Apply one zone-year's steps: appends via splice, upgrades via replace; atomic, verified write."""
    path = raw_dir / f"oisst_{region}_{year}.nc"
    if path.exists():
        with xr.open_dataset(path) as c:
            cache = c.load()
        grid_lat, grid_lon = cache["lat"].values, cache["lon"].values
    else:
        with xr.open_dataset(raw_dir / f"oisst_{region}_{year - 1}.nc") as t:   # new year: previous year's grid
            grid_lat, grid_lon = t["lat"].values, t["lon"].values
            cache = None
    def day_ds(name):
        with xr.open_dataset(ncei_dir / name) as src:
            return subset_day(src.load(), grid_lat, grid_lon)
    appends = [day_ds(n) for d, a, n in steps if a.startswith("append")]
    upgrades = [day_ds(n) for d, a, n in steps if a == "replace_with_final"]
    if cache is None:
        if not appends:
            return
        out = xr.concat(appends, dim="time").sortby("time")
        n_before = 0
    else:
        n_before = len(cache["time"])
        out = splice(cache, appends) if appends else cache[list(VARS)]
        if upgrades:
            out = replace(out, upgrades)
    tmp = path.with_suffix(".tmp.nc")
    out.to_netcdf(tmp)
    with xr.open_dataset(tmp) as chk:
        ok = len(chk["time"]) == n_before + len(appends)
        if cache is not None and ok:
            told = pd.DatetimeIndex(cache["time"].values)
            touched = {pd.Timestamp(d) for d, a, _ in steps if a == "replace_with_final"}
            keep = ~told.normalize().isin(list(touched))
            tnew = pd.DatetimeIndex(chk["time"].values)
            idx = tnew.get_indexer(told[keep])
            ok = (idx >= 0).all() and all(
                np.array_equal(chk[v].values[idx], cache[v].values[keep], equal_nan=True) for v in VARS)
    if not ok:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{path.name}: update would shrink the cache or alter a held day; refused")
    tmp.replace(path)


def run(today: date, lookback: int, ncei_dir: Path, raw_dir: Path, dry_run: bool = False,
        listing=fetch_listing) -> list[tuple[str, date, str]]:
    window = window_days(today, lookback)
    available: dict[date, dict[str, str]] = {}
    for ym in sorted({d.strftime("%Y%m") for d in window}):
        available.update(listing(ym))
    prelim = load_prelim(raw_dir)
    report: list[tuple[str, date, str]] = []
    finalized: set[date] = set()
    still_prelim: set[date] = set(prelim)
    any_failed = False
    for year in sorted({d.year for d in window}):
        ydays = [d for d in window if d.year == year]
        for z in _zones_for_year(raw_dir, year):
            held = _held_days(raw_dir / f"oisst_{z}_{year}.nc")
            steps = plan_updates(ydays, held, prelim, available)
            for d, a, n in steps:
                report.append((z, d, a))
            if dry_run or not steps:
                continue
            for _, _, n in steps:
                download(n, ncei_dir)
            try:
                apply_zone_year(z, year, steps, ncei_dir, raw_dir)
            except Exception:
                any_failed = True
                raise
            for d, a, _ in steps:
                if a == "append_preliminary":
                    still_prelim.add(d)
                elif a == "replace_with_final":
                    finalized.add(d)
    if not dry_run and not any_failed:
        save_prelim(raw_dir, (still_prelim | set()) - finalized)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="mhw-update-ncei", description=__doc__.split("\n")[0])
    ap.add_argument("--through", help="treat this as 'today' (default: UTC today); days up to the day before")
    ap.add_argument("--lookback-days", type=int, default=60)
    ap.add_argument("--ncei-dir", type=Path, default=NCEI_CACHE)
    ap.add_argument("--raw-dir", type=Path, default=DATA_RAW)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--print-last-day", action="store_true",
                    help="print the last day held in EVERY zone file of the current year (the safe engine end date) and exit")
    return ap.parse_args(argv)


def last_common_day(raw_dir: Path, year: int) -> date | None:
    """The last calendar day held in every zone's file for *year* (None if no file)."""
    lasts = []
    for p in sorted(Path(raw_dir).glob(f"oisst_*_{year}.nc")):
        held = _held_days(p)
        if held:
            lasts.append(max(held))
    return min(lasts) if lasts else None


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    today = date.fromisoformat(a.through) if a.through else pd.Timestamp.utcnow().date()
    if a.print_last_day:
        d = last_common_day(a.raw_dir, today.year) or last_common_day(a.raw_dir, today.year - 1)
        if d is None:
            raise SystemExit("mhw-update-ncei: no OISST cache files found")
        print(d.isoformat())
        return 0
    rep = run(today, a.lookback_days, a.ncei_dir, a.raw_dir, dry_run=a.dry_run)
    counts: dict[str, int] = {}
    for _, _, act in rep:
        counts[act] = counts.get(act, 0) + 1
    days = sorted({d for _, d, _ in rep})
    span = f"{days[0]}..{days[-1]}" if days else "none"
    print(f"mhw-update-ncei: {'planned' if a.dry_run else 'applied'} {counts or 'nothing'} over days {span}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
