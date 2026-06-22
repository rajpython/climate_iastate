"""FOSS catch × bottom-state adapter — survey catch joined to its haul bottom temp.

Phase 0 foundation for the Alaska-shelf board's *biological* layer (see
``docs/alaska_shelf_expansion_plan.md`` §4). Every AFSC summer bottom-trawl tow records
**both** its bottom temperature *and* what it caught, joined by one key (``hauljoin``).
This module pulls NOAA's public **FOSS** REST API and returns a tidy **per-haul** frame —
``(year, region, lat, lon, depth, bottom_temperature_c, species_code, common_name,
cpue_kgkm2, cpue_nokm2)`` — cached to parquet. It feeds both the planned catch page and the
catch × bottom-temperature view (the snow-crab "share inside the cold pool" story, A.4).

Two design points that make the output defensible
--------------------------------------------------
1. **Left join + zero-fill (presence *and* absence).** The FOSS ``catch`` table has a row
   only where a species was caught. A naive inner join silently drops every haul that
   caught *none* of the species — which biases any thermal profile warm/cold and makes
   "share of biomass inside the cold pool" meaningless. We therefore take **all hauls** in
   the requested regions/years and **left-join** the species' catch, filling absent CPUE
   with **0**. Each row is then a true presence/absence observation at a known bottom temp.
2. **No ``$in`` operator.** The FOSS WAF blocks the ``$in`` query operator, so we filter on
   a **single** scalar (``species_code`` for catch, ``srvy`` for haul) and intersect/concat
   client-side — never ``$in``.

CLI: mhw-fetch-catch --species 68580 --regions EBS NBS --start 1982 --end 2025
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Project paths & source
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

FOSS_BASE = "https://apps-st.fisheries.noaa.gov/ods/foss"
_HAUL_TABLE = "afsc_groundfish_survey_haul"
_CATCH_TABLE = "afsc_groundfish_survey_catch"
_SPECIES_TABLE = "afsc_groundfish_survey_species"

_PAGE = 10000          # FOSS caps a page at 10000 rows
_MAX_TIME = 120        # per-request timeout (s)

# The five survey regions with bottom-trawl catch (FOSS `srvy` codes). The Chukchi and
# Beaufort have no routine survey, so they are absent here by construction.
SURVEY_REGIONS = ("EBS", "NBS", "GOA", "AI", "BSS")

# A few headline species codes (extend freely; names come from the FOSS species table).
SPECIES = {
    "snow_crab": 68580,
    "red_king_crab": 69322,
    "pacific_cod": 21720,
    "walleye_pollock": 21740,
    "arrowtooth_flounder": 10110,
}

# Haul fields we keep, renamed to the tidy schema. Catch lat/lon use the tow *start*.
_HAUL_KEEP = {
    "year": "year",
    "srvy": "region",
    "hauljoin": "hauljoin",
    "date_time": "date_time",
    "latitude_dd_start": "latitude",
    "longitude_dd_start": "longitude",
    "depth_m": "depth_m",
    "bottom_temperature_c": "bottom_temperature_c",
    "surface_temperature_c": "surface_temperature_c",
}


# ---------------------------------------------------------------------------
# FOSS REST client (paged; never uses the WAF-blocked $in operator)
# ---------------------------------------------------------------------------

def _foss_get_all(table: str, where: dict | None = None) -> list[dict]:
    """Return every row of *table* matching the scalar *where* filter, paging by offset.

    *where* must be flat scalar equality (e.g. ``{"species_code": 68580}`` or
    ``{"srvy": "EBS"}``) — **never** ``$in`` (the WAF rejects it). Paging follows the
    API's ``hasMore`` flag.
    """
    params = {"limit": _PAGE}
    if where:
        params["q"] = json.dumps(where, separators=(",", ":"))
    rows: list[dict] = []
    offset = 0
    while True:
        params["offset"] = offset
        url = f"{FOSS_BASE}/{table}/?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=_MAX_TIME) as resp:
            payload = json.load(resp)
        items = payload.get("items", [])
        rows.extend(items)
        if not payload.get("hasMore") or not items:
            break
        offset += len(items)
    return rows


def fetch_hauls(regions: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Fetch all survey hauls (optionally restricted to *regions*) as a tidy frame.

    One scalar request per region (``$in`` is blocked), concatenated client-side. With
    *regions* ``None`` every survey region is pulled.
    """
    regions = tuple(regions) if regions else SURVEY_REGIONS
    frames = []
    for srvy in regions:
        print(f"Fetching FOSS hauls: srvy={srvy} …")
        raw = _foss_get_all(_HAUL_TABLE, {"srvy": srvy})
        if raw:
            frames.append(pd.DataFrame(raw))
    if not frames:
        return pd.DataFrame(columns=list(_HAUL_KEEP.values()))
    df = pd.concat(frames, ignore_index=True)
    df = df[[c for c in _HAUL_KEEP if c in df.columns]].rename(columns=_HAUL_KEEP)
    df["year"] = df["year"].astype(int)
    print(f"  Hauls: {len(df):,} across {df['region'].nunique()} region(s), "
          f"{df['year'].min()}–{df['year'].max()}")
    return df


def fetch_catch(species_code: int) -> pd.DataFrame:
    """Fetch every catch record for a single *species_code* (paged) as a tidy frame."""
    print(f"Fetching FOSS catch: species_code={species_code} …")
    raw = _foss_get_all(_CATCH_TABLE, {"species_code": species_code})
    cols = ["hauljoin", "species_code", "cpue_kgkm2", "cpue_nokm2", "count", "weight_kg"]
    if not raw:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(raw)[[c for c in cols if c in raw[0]]]
    print(f"  Catch rows: {len(df):,}")
    return df


def fetch_species_name(species_code: int) -> str:
    """Return the FOSS common name for *species_code* (falls back to the code)."""
    raw = _foss_get_all(_SPECIES_TABLE, {"species_code": species_code})
    if raw and raw[0].get("common_name"):
        return str(raw[0]["common_name"])
    return str(species_code)


# ---------------------------------------------------------------------------
# Pure join (network-free, unit-testable)
# ---------------------------------------------------------------------------

def join_catch_to_hauls(hauls: pd.DataFrame, catch: pd.DataFrame,
                        species_code: int, common_name: str) -> pd.DataFrame:
    """Left-join *catch* onto *hauls* on ``hauljoin``, zero-filling absent catch.

    Every haul in *hauls* becomes one row: where the species was caught it carries the
    survey CPUE; where it was not, CPUE is **0** (a true absence at a known bottom temp,
    not a dropped record). This presence/absence frame is what makes thermal-profile and
    "share inside the cold pool" statistics correct.
    """
    catch = catch[["hauljoin", "cpue_kgkm2", "cpue_nokm2"]].drop_duplicates("hauljoin")
    df = hauls.merge(catch, on="hauljoin", how="left")
    for col in ("cpue_kgkm2", "cpue_nokm2"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["species_code"] = species_code
    df["common_name"] = common_name
    return df.sort_values(["year", "region", "hauljoin"]).reset_index(drop=True)


def cold_pool_summary(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Per-(region, year) share of biomass and hauls inside the ≤*threshold* band.

    Quantifies the A.4 snow-crab story for any species: of the surveyed biomass (CPUE
    summed over hauls), what fraction sat in hauls with bottom temp ≤ *threshold*, and
    what fraction of hauls those were. Hauls with no bottom temperature are excluded.
    """
    d = df.dropna(subset=["bottom_temperature_c"]).copy()
    d["in_band"] = d["bottom_temperature_c"] <= threshold
    out = []
    for (region, year), g in d.groupby(["region", "year"]):
        biomass = g["cpue_kgkm2"].sum()
        in_biomass = g.loc[g["in_band"], "cpue_kgkm2"].sum()
        out.append({
            "region": region,
            "year": year,
            "threshold_c": threshold,
            "n_hauls": len(g),
            "frac_hauls_in_band": round(g["in_band"].mean(), 4),
            "mean_cpue_in_band": round(g.loc[g["in_band"], "cpue_kgkm2"].mean(), 2) if g["in_band"].any() else 0.0,
            "mean_cpue_out_band": round(g.loc[~g["in_band"], "cpue_kgkm2"].mean(), 2) if (~g["in_band"]).any() else 0.0,
            "frac_biomass_in_band": round(in_biomass / biomass, 4) if biomass > 0 else float("nan"),
            "corr_bt_cpue": round(g["bottom_temperature_c"].corr(g["cpue_kgkm2"]), 4),
        })
    return pd.DataFrame(out).sort_values(["region", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_catch_bottom_state(species_code: int, regions: tuple[str, ...] | None = None,
                             start: int | None = None, end: int | None = None) -> pd.DataFrame:
    """Build the per-haul catch × bottom-state frame for one species.

    Pulls hauls (per region) and the species' catch, left-joins on ``hauljoin`` with
    zero-fill, then clips to [*start*, *end*]. Returns the tidy per-haul frame.
    """
    t0 = time.time()
    hauls = fetch_hauls(regions)
    catch = fetch_catch(species_code)
    name = fetch_species_name(species_code)
    df = join_catch_to_hauls(hauls, catch, species_code, name)
    if start is not None:
        df = df[df["year"] >= start]
    if end is not None:
        df = df[df["year"] <= end]
    df = df.reset_index(drop=True)
    caught = (df["cpue_kgkm2"] > 0).sum()
    print(f"  {name} (#{species_code}): {len(df):,} hauls, {caught:,} with catch, "
          f"{df['region'].nunique()} region(s), {df['year'].min()}–{df['year'].max()} "
          f"[{time.time() - t0:.0f}s]")
    return df


def save_parquet(df: pd.DataFrame, species_code: int) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / f"catch_bottom_state_{species_code}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch FOSS survey catch joined to haul bottom temperature (per haul).")
    p.add_argument("--species", type=int, default=SPECIES["snow_crab"],
                   help="FOSS species_code (default 68580 = snow crab)")
    p.add_argument("--regions", nargs="*", default=None, metavar="SRVY",
                   help=f"Survey regions to include (default all of {', '.join(SURVEY_REGIONS)})")
    p.add_argument("--start", type=int, default=None, help="First year (inclusive)")
    p.add_argument("--end", type=int, default=None, help="Last year (inclusive)")
    p.add_argument("--summary", action="store_true",
                   help="Also print the per-region/year cold-pool (≤2 °C) catch summary")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    regions = tuple(r.upper() for r in args.regions) if args.regions else None
    df = build_catch_bottom_state(args.species, regions=regions, start=args.start, end=args.end)
    if df.empty:
        print("No hauls produced — check connectivity / filters.")
        return
    save_parquet(df, args.species)
    if args.summary:
        summ = cold_pool_summary(df)
        with pd.option_context("display.max_rows", None, "display.width", 120):
            print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
