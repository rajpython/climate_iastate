"""NOAA FOSS Commercial Landings — statewide Alaska landings (tons) + ex-vessel value ($).

The board's first **commercial harvest** (fishery-*dependent*) layer, the counterpart to the
fishery-*independent* survey CPUE already shown. Pulls NOAA's public **FOSS** ``landings`` REST
table (same infra as the survey ``haul``/``catch`` tables) and returns a tidy per-species/year
frame of statewide-Alaska commercial landings and ex-vessel value, cached to parquet.

Two design points (mirroring ``fetch/foss_catch.py``)
-----------------------------------------------------
1. **No ``$in`` operator.** The FOSS WAF blocks ``$in``; filter on a single scalar
   (``state_name``) in the ``q`` param, page by ``offset``, and keep ``collection == Commercial``
   client-side.
2. **Statewide only.** FOSS landings resolve to statewide Alaska (``region_name`` is a coarse
   NMFS region, not a survey/NPFMC sub-area), so every row is ``area_group="statewide"`` — this
   is honest labelling, not a limitation to hide. Region-wise groundfish is the later AKFIN track.

CLI: mhw-fetch-landings-foss --start 1985 --end 2024
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from mhw.econ.confidential import mark_confidential
from mhw.econ.sources import FOSS_LANDINGS, LandingsSource, TONNE_PER_LB

# ---------------------------------------------------------------------------
# Project paths & source
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

_PAGE = 10000          # FOSS caps a page at 10000 rows
_MAX_TIME = 120        # per-request timeout (s)

# Final tidy column order (the LandingsSource schema).
TIDY_COLS = [
    "year", "area_group", "area_native", "species", "species_code",
    "landings_t", "value_usd", "catch_or_landings", "collection", "source", "confidential",
]


# ---------------------------------------------------------------------------
# FOSS REST client (paged; never uses the WAF-blocked $in operator)
# ---------------------------------------------------------------------------

def _foss_get_all(base: str, table: str, where: dict | None = None) -> list[dict]:
    """Return every row of *table* matching the scalar *where* filter, paging by offset.

    *where* must be flat scalar equality (e.g. ``{"state_name": "ALASKA"}``) — **never**
    ``$in`` (the WAF rejects it). Paging follows the API's ``hasMore`` flag.
    """
    params = {"limit": _PAGE}
    if where:
        params["q"] = json.dumps(where, separators=(",", ":"))
    rows: list[dict] = []
    offset = 0
    while True:
        params["offset"] = offset
        url = f"{base}/{table}/?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=_MAX_TIME) as resp:
            payload = json.load(resp)
        items = payload.get("items", [])
        rows.extend(items)
        if not payload.get("hasMore") or not items:
            break
        offset += len(items)
    return rows


def fetch_landings_raw(source: LandingsSource = FOSS_LANDINGS,
                       state: str = "ALASKA") -> list[dict]:
    """Fetch every FOSS landings row for *state* (all collections/years), as raw dicts."""
    print(f"Fetching FOSS landings: state_name={state} …")
    rows = _foss_get_all(source.base_url, source.table, {"state_name": state})
    print(f"  Rows: {len(rows):,}")
    return rows


# ---------------------------------------------------------------------------
# Pure transforms (network-free, unit-testable)
# ---------------------------------------------------------------------------

def tidy_landings(rows: list[dict], source: LandingsSource = FOSS_LANDINGS,
                  collection: str = "Commercial") -> pd.DataFrame:
    """Turn raw FOSS landings rows into the tidy board schema.

    Renames source columns via ``source.field_map``, keeps only *collection* (commercial
    harvest, dropping recreational), coerces numerics, drops rows with no landed weight, derives
    ``landings_t`` from pounds, stamps ``area_group="statewide"`` / ``catch_or_landings="landings"``,
    and flags confidentiality (statewide public feed → all False). Network-free.
    """
    if not rows:
        return pd.DataFrame(columns=TIDY_COLS)

    df = pd.DataFrame(rows)
    keep = {src: dst for src, dst in source.field_map.items() if src in df.columns}
    df = df[list(keep)].rename(columns=keep)

    if collection and "collection" in df.columns:
        df = df[df["collection"].astype(str).str.strip().str.casefold()
                == collection.casefold()]

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["pounds"] = pd.to_numeric(df["pounds"], errors="coerce")
    df["value_usd"] = pd.to_numeric(df.get("value_usd"), errors="coerce")
    # Drop rows with no landed weight (no year or null/zero pounds carry no landings signal).
    df = df[df["year"].notna() & df["pounds"].notna() & (df["pounds"] > 0)].copy()

    df["year"] = df["year"].astype(int)
    if "species" in df.columns:   # FOSS names carry trailing whitespace
        df["species"] = df["species"].astype(str).str.strip()
    df["landings_t"] = df["pounds"] * TONNE_PER_LB
    df["area_group"] = "statewide"
    df["catch_or_landings"] = "landings"
    if "species_code" in df.columns:
        df["species_code"] = df["species_code"].astype(str)
    for opt in ("area_native", "collection", "source"):
        if opt not in df.columns:
            df[opt] = None

    df = mark_confidential(df)  # statewide public feed → confidential=False
    df = df[TIDY_COLS].sort_values(["year", "species"]).reset_index(drop=True)
    return df


def landings_summary(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Per-species landings/value totals over the record + value share (headline KPIs).

    Sorted by total ex-vessel value descending. Network-free — used for the spot-check and the
    dashboard's headline cards.
    """
    if df.empty:
        return pd.DataFrame(columns=["species", "landings_t", "value_usd", "value_share"])
    g = (df.groupby("species", as_index=False)
           .agg(landings_t=("landings_t", "sum"), value_usd=("value_usd", "sum")))
    total_val = g["value_usd"].sum()
    g["value_share"] = g["value_usd"] / total_val if total_val else float("nan")
    g = g.sort_values("value_usd", ascending=False).reset_index(drop=True)
    return g.head(top) if top else g


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_landings(source: LandingsSource = FOSS_LANDINGS, collection: str = "Commercial",
                   start: int | None = None, end: int | None = None) -> pd.DataFrame:
    """Fetch → tidy → clip to [*start*, *end*] the statewide-AK landings frame."""
    t0 = time.time()
    rows = fetch_landings_raw(source)
    df = tidy_landings(rows, source, collection=collection)
    if start is not None:
        df = df[df["year"] >= start]
    if end is not None:
        df = df[df["year"] <= end]
    df = df.reset_index(drop=True)
    if not df.empty:
        print(f"  {collection} landings: {len(df):,} rows, {df['species'].nunique()} species, "
              f"{df['year'].min()}–{df['year'].max()} [{time.time() - t0:.0f}s]")
    return df


def save_parquet(df: pd.DataFrame, source: LandingsSource = FOSS_LANDINGS) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / f"landings_{source.id}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch NOAA FOSS statewide-Alaska commercial landings (tons) + ex-vessel value.")
    p.add_argument("--collection", default="Commercial",
                   help="FOSS collection to keep (default Commercial; drops Recreational)")
    p.add_argument("--start", type=int, default=None, help="First year (inclusive)")
    p.add_argument("--end", type=int, default=None, help="Last year (inclusive)")
    p.add_argument("--summary", action="store_true",
                   help="Also print the top-species landings/value summary")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df = build_landings(collection=args.collection, start=args.start, end=args.end)
    if df.empty:
        print("No landings produced — check connectivity / filters.")
        return
    save_parquet(df)
    if args.summary:
        with pd.option_context("display.max_rows", None, "display.width", 120):
            print(landings_summary(df).to_string(index=False))


if __name__ == "__main__":
    main()
