"""Apples-to-apples cold-pool AREA: krige model temps the way AFSC kriges the survey.

The AFSC *observed* cold-pool index (:mod:`mhw.fetch.coldpool`) is **ordinary kriging** of
survey gear temperatures onto a 5 km grid (EPSG:3338) masked to the survey area, integrating
the area at or below a threshold (count of cells × 25 km²). Our *modelled* full-shelf area
(:mod:`mhw.bottom.coldpool`) instead counts ≤-threshold cells over a depth-masked domain — a
**different method**, so the two areas are not comparable (the Model-Comparison page therefore
only ever shows z-scored / pattern area, never absolute).

This module closes that gap. It takes the **survey-replicated** model temperatures (each model
sampled at every haul's nearest grid cell + nearest time step; :mod:`mhw.bottom.survey_replicate`)
and pushes the model column through AFSC's **exact** kriging → grid → count pipeline. The
modelled area then differs from the observed area **only in the temperatures**, not the method —
fully comparable (EBS/NBS, the cold-pool regions).

Reproduction verified: kriging the OBSERVED haul temps through this same pipeline reproduces the
published ``cold_pool_index`` across all EBS years (mean abs error ~0.6 %, r = 0.99996).

AFSC spec (reverse-engineered from ``afsc-gap-products/coldpool`` + ``akgfmaps``)
--------------------------------------------------------------------------------
Ordinary kriging, ``var ~ 1``, ``nmax = Inf``; variogram **"Ste"** with ``fit.kappa=FALSE`` →
kappa stays at the ``vgm()`` default 0.5 → Matérn smoothness 0.5 = **exponential** covariance
⇒ PyKrige ``variogram_model="exponential"``. Grid 5 km, **EPSG:3338**; SEBS prediction raster
``xmin=-1625000, xmax=-35000, ymin=379500, ymax=1969500`` (318×318); mask = ``afsc_bts_strata``
``survey_area`` (``SURVEY_DEFINITION_ID`` 98 = SEBS/EBS-shelf, 143 = NBS extension). Area =
``count(cells ≤ thr) × (res²/1e6)`` km² (= ×25 for 5 km cells).

CLI: mhw-build-kriged-area --source bering10k --region ebs [--observed]
"""
from __future__ import annotations

import argparse
import urllib.request
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from mhw.bottom.coldpool import THRESHOLDS_C, _THRESH_COL
from mhw.bottom.regions import EBS, BottomRegion, get_region
from mhw.bottom.sources import SOURCES, BottomSource, BERING10K_K20_CORECFS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW = PROJECT_ROOT / "data" / "raw"
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

# AFSC interpolation constants (see module docstring).
INTERP_CRS = "EPSG:3338"
CELL_RES_M = 5000.0
KM2_PER_CELL = (CELL_RES_M ** 2) / 1e6          # 25.0 km² for a 5 km cell
VARIOGRAM = "exponential"                         # Ste(kappa=0.5) == Matérn(nu=0.5) == exponential
NLAGS = 20

# Where the trimmed survey-area polygons live (SEBS+NBS), and how to (re)build them.
_STRATA_GPKG = RAW / "akgfmaps" / "afsc_bts_strata.gpkg"
_SURVEY_AREA_GEOJSON = RAW / "akgfmaps" / "survey_area_ebs_nbs.geojson"
_STRATA_URL = ("https://raw.githubusercontent.com/afsc-gap-products/akgfmaps/main/"
               "inst/extdata/afsc_bts_strata.gpkg")


@dataclass(frozen=True)
class KrigeSpec:
    """Per-region kriging config: which survey polygon + the prediction-raster extent."""
    survey_definition_id: int
    # (xmin, xmax, ymin, ymax) in EPSG:3338 metres, or None to derive from the polygon bounds.
    extent: tuple[float, float, float, float] | None


# EBS uses AFSC's hard-coded SEBS raster (matches the published index exactly). NBS derives its
# box from the survey-area bounds (snapped to the 5 km grid) — validate before trusting (NBS
# published areas were not all multiples of 25; see the kickoff brief).
KRIGE_SPECS: dict[str, KrigeSpec] = {
    "sebs": KrigeSpec(98, (-1625000.0, -35000.0, 379500.0, 1969500.0)),
    "nbs": KrigeSpec(143, None),
}


# ---------------------------------------------------------------------------
# Pure helpers (network-free, unit-testable)
# ---------------------------------------------------------------------------

def make_grid(extent: tuple[float, float, float, float], res: float = CELL_RES_M
              ) -> tuple[np.ndarray, np.ndarray]:
    """Cell-centre coordinates (xc, yc) of a regular grid spanning *extent*.

    Mirrors ``terra::rast(xmin,xmax,ymin,ymax, resolution=res)``: the grid has
    ``round((xmax-xmin)/res)`` columns, centres at ``xmin + res/2 + i·res``.
    """
    xmin, xmax, ymin, ymax = extent
    ncol = int(round((xmax - xmin) / res))
    nrow = int(round((ymax - ymin) / res))
    xc = xmin + res / 2 + np.arange(ncol) * res
    yc = ymin + res / 2 + np.arange(nrow) * res
    return xc, yc


def snap_extent(bounds: tuple[float, float, float, float], res: float = CELL_RES_M,
                pad: float = 0.0) -> tuple[float, float, float, float]:
    """Snap polygon *bounds* (minx,miny,maxx,maxy) outward to a clean *res* grid (+pad cells)."""
    minx, miny, maxx, maxy = bounds
    xmin = np.floor(minx / res) * res - pad * res
    ymin = np.floor(miny / res) * res - pad * res
    xmax = np.ceil(maxx / res) * res + pad * res
    ymax = np.ceil(maxy / res) * res + pad * res
    return (float(xmin), float(xmax), float(ymin), float(ymax))


def area_le(field: np.ndarray, inside: np.ndarray, threshold: float,
            cell_km2: float = KM2_PER_CELL) -> float:
    """Area (km²) of in-mask cells with value ≤ *threshold* (NaN-safe) — AFSC ``cpa_from_raster``."""
    sel = inside & np.isfinite(field) & (field <= threshold)
    return float(np.count_nonzero(sel)) * cell_km2


def krige_to_grid(px: np.ndarray, py: np.ndarray, z: np.ndarray,
                  xc: np.ndarray, yc: np.ndarray,
                  variogram: str = VARIOGRAM, nlags: int = NLAGS) -> np.ndarray:
    """Ordinary-krige scattered (px,py,z) onto the regular grid (xc,yc) → 2D field (nrow,ncol).

    Pure given inputs (no IO). Uses PyKrige with a pseudo-inverse so duplicated/colinear haul
    coordinates don't make the kriging system singular.
    """
    from pykrige.ok import OrdinaryKriging

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ok = OrdinaryKriging(px, py, z, variogram_model=variogram, nlags=nlags,
                             pseudo_inv=True)
        field, _ = ok.execute("grid", xc, yc)
    return np.asarray(field)


# ---------------------------------------------------------------------------
# Survey-area polygon + grid mask (IO; small geospatial dependency)
# ---------------------------------------------------------------------------

def build_survey_area_geojson(force: bool = False) -> Path:
    """(Re)build the trimmed SEBS+NBS survey-area geojson from the akgfmaps strata gpkg.

    Downloads the 44 MB gpkg once (if absent) and keeps only ``SURVEY_DEFINITION_ID`` 98 & 143,
    most-recent design year each, in EPSG:3338 — a ~180 KB local asset the build reads.
    """
    import geopandas as gpd

    if _SURVEY_AREA_GEOJSON.exists() and not force:
        return _SURVEY_AREA_GEOJSON
    if not _STRATA_GPKG.exists():
        _STRATA_GPKG.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading akgfmaps strata → {_STRATA_GPKG} …")
        urllib.request.urlretrieve(_STRATA_URL, _STRATA_GPKG)
    sa = gpd.read_file(_STRATA_GPKG, layer="survey_area")
    keep = [sa[sa.SURVEY_DEFINITION_ID == sid].sort_values("DESIGN_YEAR").iloc[[-1]]
            for sid in (98, 143)]
    out = gpd.GeoDataFrame(pd.concat(keep), crs=sa.crs)[
        ["SURVEY_DEFINITION_ID", "DESIGN_YEAR", "AREA_M2", "geometry"]]
    _SURVEY_AREA_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(_SURVEY_AREA_GEOJSON, driver="GeoJSON")
    print(f"  Saved survey-area polygons → {_SURVEY_AREA_GEOJSON}")
    return _SURVEY_AREA_GEOJSON


def load_survey_area(region: BottomRegion):
    """Return the (unioned) survey-area shapely polygon for *region* in EPSG:3338."""
    import geopandas as gpd

    spec = KRIGE_SPECS[region.id]
    build_survey_area_geojson()
    sa = gpd.read_file(_SURVEY_AREA_GEOJSON)
    g = sa[sa.SURVEY_DEFINITION_ID == spec.survey_definition_id]
    if g.empty:
        raise ValueError(f"No survey_area polygon for id {spec.survey_definition_id} ({region.id}).")
    return g.geometry.union_all()


def grid_mask(xc: np.ndarray, yc: np.ndarray, geom) -> np.ndarray:
    """Boolean (nrow,ncol) mask: True where the cell centre falls inside *geom* (EPSG:3338)."""
    import geopandas as gpd

    XX, YY = np.meshgrid(xc, yc)
    pts = gpd.GeoSeries(gpd.points_from_xy(XX.ravel(), YY.ravel()), crs=INTERP_CRS)
    return pts.within(geom).to_numpy().reshape(XX.shape)


# ---------------------------------------------------------------------------
# Build the kriged-area series
# ---------------------------------------------------------------------------

def _project_to_3338(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    from pyproj import Transformer

    tf = Transformer.from_crs("EPSG:4326", INTERP_CRS, always_xy=True)
    x, y = tf.transform(np.asarray(lon), np.asarray(lat))
    return np.asarray(x), np.asarray(y)


def _replicate_path(source: BottomSource, region: BottomRegion) -> Path:
    return DERIVED / f"survey_replicate_{source.id}_{region.id}.parquet"


def build_kriged_area_series(source: BottomSource = BERING10K_K20_CORECFS,
                             region: BottomRegion = EBS,
                             observed: bool = False) -> pd.DataFrame:
    """Krige the (model or observed) survey-replicate temps per year → annual cold-pool areas.

    Reads ``survey_replicate_<src>_<region>.parquet`` (one row per haul, with ``obs_bottom_temp``
    and ``model_bottom_temp``). For each year: project the hauls to EPSG:3338, clip to the survey
    area, ordinary-krige the chosen temperature column onto the masked 5 km grid, and integrate
    the area at or below each threshold. ``observed=True`` kriges ``obs_bottom_temp`` (the
    validation gate — should reproduce AFSC); otherwise ``model_bottom_temp`` (the apples-to-apples
    modelled area).
    """
    if region.id not in KRIGE_SPECS:
        raise ValueError(f"Region {region.id!r} is not a kriged-area (cold-pool) region.")
    path = _replicate_path(source, region)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `mhw-build-survey-replicate --source {source.id} "
            f"--region {region.id}` first.")
    df = pd.read_parquet(path)
    col = "obs_bottom_temp" if observed else "model_bottom_temp"
    df = df.dropna(subset=[col, "latitude", "longitude"])

    geom = load_survey_area(region)
    spec = KRIGE_SPECS[region.id]
    extent = spec.extent or snap_extent(geom.bounds)
    xc, yc = make_grid(extent)
    inside = grid_mask(xc, yc, geom)
    print(f"{source.id} {region.id.upper()} [{'observed' if observed else 'model'}]: "
          f"grid {inside.shape[0]}×{inside.shape[1]}, {int(inside.sum())} cells in survey area "
          f"(~{int(inside.sum()) * KM2_PER_CELL:,.0f} km²)")

    import geopandas as gpd

    rows = []
    for year, g in df.groupby("year"):
        px, py = _project_to_3338(g["longitude"].to_numpy(), g["latitude"].to_numpy())
        inh = gpd.GeoSeries(gpd.points_from_xy(px, py), crs=INTERP_CRS).within(geom).to_numpy()
        if inh.sum() < 5:
            continue
        px, py, z = px[inh], py[inh], g[col].to_numpy()[inh]
        field = krige_to_grid(px, py, z, xc, yc)
        field = np.where(inside, field, np.nan)
        row = {"year": int(year), "source": source.id, "n_points": int(inh.sum())}
        for thr in THRESHOLDS_C:
            row[_THRESH_COL[thr]] = round(area_le(field, inside, thr), 1)
        rows.append(row)
        print(f"  {year}: ≤2 °C = {row['area_lte2_km2']:,.0f} km²  (n={row['n_points']})")
    return pd.DataFrame(rows)


def save_parquet(df: pd.DataFrame, source: BottomSource, region: BottomRegion,
                 observed: bool = False) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    stem = f"kriged_area_observed_{region.id}" if observed else f"kriged_area_{source.id}_{region.id}"
    out = DERIVED / f"{stem}.parquet"
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Krige survey-replicated temps to a cold-pool AREA the AFSC way "
                    "(apples-to-apples model vs. observed).")
    p.add_argument("--source", default="bering10k", choices=sorted(SOURCES))
    p.add_argument("--region", default="sebs", choices=sorted(KRIGE_SPECS),
                   help="Cold-pool region (sebs/nbs)")
    p.add_argument("--observed", action="store_true",
                   help="Krige observed gear temps (validation gate vs AFSC) instead of the model.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source = SOURCES[args.source]
    region = get_region(args.region)
    df = build_kriged_area_series(source, region=region, observed=args.observed)
    if df.empty:
        print("No years produced — check the survey-replicate input / year coverage.")
        return
    save_parquet(df, source, region, observed=args.observed)


if __name__ == "__main__":
    main()
