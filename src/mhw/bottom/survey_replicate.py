"""Survey-replicated model–vs–observation comparison (the literature-standard method).

The defensible way to compare a regional ocean model's cold pool to the AFSC bottom-trawl
survey is **survey replication**: sample the model at each survey haul's location and date,
then compare to the observed gear (bottom) temperature — and compute any index identically
for model and survey. This is the method of Kearney (2021) and Seelanki et al. (2025):

    "Simulated daily bottom temperature on the Bering Sea shelf was sampled each year
     following the AFSC Groundfish Bottom Trawl Survey; the 'survey replicate' model
     output is then compared with bottom trawl data." — Seelanki et al. 2025

This is distinct from our full-shelf (depth ≤ 200 m) model product: that answers "what was
the whole-shelf cold pool" (the model's own view, including places/years the survey can't
see); survey replication answers "does the model match the survey, on the survey's terms"
(validation). Co-locating in space and time removes the footprint/cadence artifacts that
inflate a naive domain-average comparison.

CLI: mhw-build-survey-replicate --source bering10k
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from mhw.bottom.loader import load_bottom_temp, open_bottom_dataset
from mhw.bottom.regrid import normalize_lon
from mhw.bottom.sources import SOURCES, BottomSource, BERING10K_K20_CORECFS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HAULS_PARQUET = PROJECT_ROOT / "data" / "raw" / "coldpool_hauls_observed.parquet"
DERIVED = PROJECT_ROOT / "data" / "derived" / "cold_pool"

# Summer window to load per year (hauls fall within it; we co-locate in time inside it).
_SUMMER_START_MD = "05-01"
_SUMMER_END_MD = "09-30"


def load_hauls() -> pd.DataFrame:
    if not HAULS_PARQUET.exists():
        raise FileNotFoundError(
            f"{HAULS_PARQUET} not found — run mhw-fetch-coldpool first."
        )
    return pd.read_parquet(HAULS_PARQUET)


def _ocean_kdtree(da):
    """Build a cKDTree over the model's *ocean* cell centres (finite at some time).

    Returns (tree, flat_ocean_index, n_x) so a query result maps back to (y, x).
    Excluding land cells stops coastal hauls from snapping onto NaN land points.
    """
    from scipy.spatial import cKDTree

    lat2d = np.asarray(da.lat.values, dtype="float64")
    lon2d = normalize_lon(np.asarray(da.lon.values))
    ocean = np.isfinite(da.values).any(axis=0).ravel()
    flat_ocean = np.flatnonzero(ocean)
    pts = np.column_stack([lon2d.ravel()[flat_ocean], lat2d.ravel()[flat_ocean]])
    return cKDTree(pts), flat_ocean, lat2d.shape[1]


def build_survey_replicate(
    source: BottomSource = BERING10K_K20_CORECFS,
    hauls: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Sample *source* bottom temperature at each haul's location and nearest time.

    Returns one row per haul with the observed and modelled bottom temperature.
    """
    hauls = load_hauls() if hauls is None else hauls
    ds = open_bottom_dataset(source)

    tree = flat_ocean = n_x = None  # grid is fixed across years → build tree once
    out = []
    for year, g in hauls.groupby("year"):
        da = load_bottom_temp(source, start=f"{year}-{_SUMMER_START_MD}",
                              end=f"{year}-{_SUMMER_END_MD}", ds=ds)
        if da.sizes["time"] == 0:
            continue  # year outside this model's coverage
        da = da.load()  # pull the year's summer window once; index in memory
        if tree is None:
            tree, flat_ocean, n_x = _ocean_kdtree(da)
        arr = da.values
        times = da["time"].values

        q_lon = normalize_lon(g["longitude"].to_numpy())
        q_lat = g["latitude"].to_numpy()
        _, k = tree.query(np.column_stack([q_lon, q_lat]))
        flat = flat_ocean[k]
        yy, xx = np.divmod(flat, n_x)
        haul_t = g["datetime"].to_numpy().astype("datetime64[ns]")
        ti = np.abs(times[None, :] - haul_t[:, None]).argmin(axis=1)

        model_t = arr[ti, yy, xx]
        rows = g[["year", "stationid", "datetime", "latitude", "longitude",
                  "gear_temperature"]].copy()
        rows["model_bottom_temp"] = model_t
        out.append(rows)
        print(f"  {year}: {len(g)} hauls sampled")

    df = pd.concat(out, ignore_index=True)
    df = df.rename(columns={"gear_temperature": "obs_bottom_temp"})
    df["source"] = source.id
    df = df.dropna(subset=["model_bottom_temp", "obs_bottom_temp"])
    return df


# ---------------------------------------------------------------------------
# Skill metrics
# ---------------------------------------------------------------------------

def haul_skill(df: pd.DataFrame) -> dict:
    """Overall co-located skill: bias, RMSE, correlation over all hauls."""
    d = df["model_bottom_temp"] - df["obs_bottom_temp"]
    return {
        "n_hauls": int(len(df)),
        "bias_c": round(float(d.mean()), 3),
        "rmse_c": round(float(np.sqrt((d ** 2).mean())), 3),
        "corr": round(float(np.corrcoef(df["model_bottom_temp"], df["obs_bottom_temp"])[0, 1]), 3),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
    }


def annual_means(df: pd.DataFrame) -> pd.DataFrame:
    """Per-year survey-replicated means (model and obs over the same haul set)."""
    g = df.groupby("year")
    out = pd.DataFrame({
        "year": g.size().index,
        "n_hauls": g.size().to_numpy(),
        "obs_mean_bottom_temp": g["obs_bottom_temp"].mean().to_numpy().round(4),
        "model_mean_bottom_temp": g["model_bottom_temp"].mean().to_numpy().round(4),
    })
    out["bias_c"] = (out["model_mean_bottom_temp"] - out["obs_mean_bottom_temp"]).round(4)
    return out.reset_index(drop=True)


def save(df: pd.DataFrame, annual: pd.DataFrame, source: BottomSource) -> tuple[Path, Path]:
    DERIVED.mkdir(parents=True, exist_ok=True)
    hauls_out = DERIVED / f"survey_replicate_{source.id}.parquet"
    annual_out = DERIVED / f"survey_replicate_annual_{source.id}.parquet"
    df.to_parquet(hauls_out, index=False)
    annual.to_parquet(annual_out, index=False)
    print(f"  Saved → {hauls_out}")
    print(f"  Saved → {annual_out}")
    return hauls_out, annual_out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build survey-replicated model-vs-survey comparison (co-located in space/time)."
    )
    p.add_argument("--source", default="bering10k", choices=sorted(SOURCES))
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source = SOURCES[args.source]
    df = build_survey_replicate(source)
    annual = annual_means(df)
    skill = haul_skill(df)
    print(f"\n{source.id} survey-replicated skill (co-located at hauls):")
    print(f"  n={skill['n_hauls']:,} hauls, {skill['year_min']}–{skill['year_max']}")
    print(f"  bias = {skill['bias_c']:+.3f} °C   RMSE = {skill['rmse_c']:.3f} °C   r = {skill['corr']:.3f}")
    save(df, annual, source)


if __name__ == "__main__":
    main()
