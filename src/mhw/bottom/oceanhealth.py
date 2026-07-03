"""Modelled bottom ocean-health indicators from a regional ocean model.

The ocean-health layer surfaces **observed-first** shelf conditions beyond bottom temperature
— starting with **bottom salinity** (the AFSC survey measures gear salinity; the model is the
comparison). This module derives the *modelled* annual shelf-mean of a chosen bottom field on
a region's shelf, reusing the cold-pool engine's shelf mask + regrid + area-weighted mean.

It is deliberately thin: an ocean-health variable is just "the area-weighted shelf mean of a
different bottom field", so all the geometry (shelf mask, 0.25° regrid, cosine-area weights)
is imported unchanged from :mod:`mhw.bottom.coldpool`. Unlike the cold pool there is **no
area-below-threshold index** — salinity/oxygen conditions are intensive means, not a
cold-pool-style footprint.

Source-agnostic via :mod:`mhw.bottom.loader`; only sources that actually carry the variable
(see ``BottomSource.variables``) are valid — e.g. MOM6 NEP carries ``sob`` (bottom salinity),
Bering10K's bottom5m bundle does not.

CLI: mhw-build-ocean-health --variable salinity --source mom6_nep --region sebs --start 1993 --end 2024
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.bottom.coldpool import (
    SURVEY_TARGET_MD,
    build_shelf_mask,
    cell_area_km2,
    mean_shelf_bottom_temp,  # generic area-weighted shelf mean (variable-agnostic)
)
from mhw.bottom.loader import load_bottom_field, open_bottom_dataset, resolve_variable
from mhw.bottom.regions import BOTTOM_REGIONS, EBS, BottomRegion, get_region
from mhw.bottom.regrid import regrid_curvilinear_to_regular
from mhw.bottom.sources import SOURCES, MOM6_NEP, BottomSource

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DERIVED = PROJECT_ROOT / "data" / "derived" / "ocean_health"

# Model unit transforms (applied to the model field before regrid so the modelled shelf mean
# lands in the observed unit). O₂: MOM6 mol kg-1 → ml/l (AFSC survey-CTD unit); the standard
# 1 ml/l = 44.6596 µmol/l with ρ ≈ 1.025 kg/l. pH: MOM6 carries bottom H+ (mol/kg), not pH, so
# pH = -log10([H+]) on the total scale.
O2_MOLKG_TO_MLL = 1.0e6 * 1.025 / 44.6596


def _o2_molkg_to_mll(x: np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype="float64") * O2_MOLKG_TO_MLL


def _htotal_to_ph(x: np.ndarray) -> np.ndarray:
    a = np.asarray(x, dtype="float64")
    return -np.log10(np.where(a > 0, a, np.nan))


# Observed products (raw parquet filename + rebuild command), keyed by product id.
#   "coldpool"   = the AFSC cold-pool index (salinity, EBS/NBS only, long record).
#   "survey_ctd" = the gapctd survey-CTD product (O₂/pH for EBS/NBS; salinity for GOA/AI too).
OBS_PRODUCT_FILE = {
    "coldpool": "coldpool_index_observed_{region}.parquet",
    "survey_ctd": "survey_ctd_observed_{region}.parquet",
}
OBS_PRODUCT_FETCH = {
    "coldpool": "mhw-fetch-coldpool --region {region}",
    "survey_ctd": "mhw-fetch-survey-ctd --region {region}",
}

# Canonical ocean-health variables. ``col`` is the output/observed column name so a modelled
# series lines up directly with the observed product. ``obs_products`` lists candidate observed
# products in priority order — salinity comes from the cold-pool index where it exists (EBS/NBS,
# 2008–) and falls back to the survey-CTD product (GOA/AI). ``model_transform`` (optional)
# converts the model field to the observed unit; ``provisional`` flags a sensor-drift caveat (pH).
VARIABLES: dict[str, dict] = {
    "salinity": {"units": "psu", "label": "Bottom salinity", "col": "mean_bottom_salinity",
                 "obs_products": ("coldpool", "survey_ctd")},
    "oxygen": {"units": "ml/l", "label": "Bottom dissolved oxygen", "col": "mean_bottom_oxygen",
               "obs_products": ("survey_ctd",), "model_transform": _o2_molkg_to_mll},
    "ph": {"units": "", "label": "Bottom pH", "col": "mean_bottom_ph",
           "obs_products": ("survey_ctd",), "model_transform": _htotal_to_ph, "provisional": True},
}


def resolve_observed(variable: str, region: str, raw_dir):
    """Return ``(product, Path, col)`` for the first observed product that actually carries a
    non-null value of *variable* for *region*, else ``None``. Shared by the API + dashboard so
    salinity transparently reads the cold-pool product (EBS/NBS) or the survey-CTD product
    (GOA/AI). ``raw_dir`` is the ``data/raw`` directory (Path)."""
    import pandas as pd
    meta = VARIABLES[variable]
    col = meta["col"]
    for product in meta["obs_products"]:
        p = raw_dir / OBS_PRODUCT_FILE[product].format(region=region)
        if not p.exists():
            continue
        cols = pd.read_parquet(p, columns=None).columns
        if col not in cols:
            continue
        if pd.read_parquet(p, columns=[col])[col].notna().any():
            return product, p, col
    return None


# ---------------------------------------------------------------------------
# Model ingest (mirrors coldpool._nearest_summer_field, variable-aware)
# ---------------------------------------------------------------------------

def nearest_summer_field(
    source: BottomSource, ds: xr.Dataset, year: int, variable: str,
    target_md: str = SURVEY_TARGET_MD, monthly: bool = False,
):
    """Return the model *variable* field for *year*'s survey window (May 15 – Sep 15).

    ``monthly=False``: the single time step nearest *target_md* (weekly snapshot for
    Bering10K, the July month for MOM6). ``monthly=True``: the July monthly mean. Mirrors the
    cold-pool selector so ocean-health and cold-pool land on identical cadence rules.
    """
    da = load_bottom_field(source, variable, start=f"{year}-05-15", end=f"{year}-09-15", ds=ds)
    if da.sizes["time"] == 0:
        return None
    if monthly:
        jul = da.sel(time=da["time"].dt.month == 7)
        if jul.sizes["time"] == 0:
            return None
        return jul.mean("time")
    target = np.datetime64(f"{year}-{target_md}")
    idx = int(np.abs(da["time"].values - target).argmin())
    return da.isel(time=idx)


def build_model_variable_series(
    source: BottomSource = MOM6_NEP,
    variable: str = "salinity",
    start: int = 1993,
    end: int = 2024,
    target_md: str = SURVEY_TARGET_MD,
    monthly: bool = False,
    region: BottomRegion = EBS,
) -> pd.DataFrame:
    """Annual modelled shelf-mean of *variable* over *region* (intensive, no area index).

    Reuses the cold-pool shelf mask + 0.25° regrid + cosine-area weights so the ocean-health
    mean shares the exact footprint the temperature/cold-pool products use — directly
    comparable across variables and to the observed survey mean.
    """
    if variable not in VARIABLES:
        raise ValueError(f"Unknown ocean-health variable {variable!r}; have {list(VARIABLES)}.")
    _, url = resolve_variable(source, variable)   # raises if the source lacks the variable
    ds = open_bottom_dataset(source, url=url)
    lats, lons = region.analysis_lats, region.analysis_lons
    shelf = build_shelf_mask(region)              # shared footprint (identical to temp/cold-pool)
    areas = cell_area_km2(lats, lons)
    meta = VARIABLES[variable]
    print(f"{source.id}: {region.id.upper()} {variable} — shelf cells = {int(shelf.sum())} "
          f"(~{areas[shelf].sum():,.0f} km²){' [July monthly mean]' if monthly else ''}")

    rows = []
    for year in range(start, end + 1):
        field = nearest_summer_field(source, ds, year, variable, target_md, monthly=monthly)
        if field is None:
            continue
        transform = meta.get("model_transform")
        vals = field.values if transform is None else transform(field.values)
        grid = regrid_curvilinear_to_regular(
            field.lat.values, field.lon.values, vals, lats, lons, fill_nearest=False)
        val = mean_shelf_bottom_temp(grid, shelf, areas)   # area-weighted shelf mean of the field
        rows.append({"year": year, "source": source.id, meta["col"]: round(val, 4)})
        print(f"  {year}: mean {variable} = {val:.3f} {meta['units']}")
    return pd.DataFrame(rows)


def save_parquet(df: pd.DataFrame, source: BottomSource, variable: str,
                 monthly: bool = False, region: BottomRegion = EBS) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    suffix = "_monthly" if monthly else ""
    out = DERIVED / f"oceanhealth_{variable}_{source.id}_{region.id}{suffix}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a modelled annual shelf-mean ocean-health series (e.g. bottom salinity).")
    p.add_argument("--variable", default="salinity", choices=sorted(VARIABLES), help="Ocean-health variable")
    p.add_argument("--source", default="mom6_nep", choices=sorted(SOURCES), help="Bottom source id")
    p.add_argument("--region", default="sebs", choices=sorted(BOTTOM_REGIONS), help="Bottom region id")
    p.add_argument("--start", type=int, default=1993, help="First year")
    p.add_argument("--end", type=int, default=2024, help="Last year")
    p.add_argument("--monthly", action="store_true",
                   help="Use the July monthly mean (matches MOM6's cadence).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source = SOURCES[args.source]
    region = get_region(args.region)
    df = build_model_variable_series(source, variable=args.variable, start=args.start,
                                     end=args.end, monthly=args.monthly, region=region)
    if df.empty:
        print("No years produced — check connectivity / year range / source-variable support.")
        return
    save_parquet(df, source, args.variable, monthly=args.monthly, region=region)


if __name__ == "__main__":
    main()
