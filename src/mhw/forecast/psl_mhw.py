"""Derive Alaska-window artifacts from the raw NOAA PSL marine-heatwave files.

Reads the raw NetCDFs fetched by ``mhw-fetch-psl-mhw`` (config/psl_mhw.yml)
and writes the small artifacts the dashboard consumes:

* ``alaska_prob_{flavor}.nc``     — the probability cube sliced to the Alaska
  window, dims (start_time, lead_time, lat, lon), float32, ~8 MB per flavor.
* ``zone_series_{flavor}.parquet``— tidy per-zone series: one row per
  (zone, init, lead) with the NaN-aware area-weighted mean probability.
* ``zone_obs_status.parquet``     — observed monthly MHW area fraction per zone
  (anomaly > month's 90th percentile), both flavors; the "what happened" line.
* ``alaska_sedi.nc`` (``--sedi``) — SEDI skill from the static 1991–2020
  hindcast vs observed flags. Heavy inputs (~1.1 GB/flavor raw, lazily sliced)
  — run locally and rsync; the VM cron never passes ``--sedi``.

The zone masks/weights artifact (``mhw.regions.nmme_masks``) is rebuilt
automatically when missing or when config/regions.geojson is newer.

Zonal means here renormalize over *finite* cells rather than reusing
``mhw.forecast.regional.regional_probability``, whose plain ``nansum`` would
count a NaN cell as probability zero and bias coastal zones low.

CLI: mhw-build-psl-mhw [--flavor trend|detrend|both] [--sedi] [--force]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mhw.fetch.psl_mhw import load_config
from mhw.regions.nmme_masks import GEOJSON_PATH, build_zone_masks

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FLAVORS = ("trend", "detrend")


# ---------------------------------------------------------------------------
# Pure helpers (no IO — unit-testable)
# ---------------------------------------------------------------------------

def zonal_mean_cube(cube: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """NaN-aware area-weighted mean over the trailing (lat, lon) axes.

    ``cube`` is (..., lat, lon); ``weight`` is (lat, lon). Cells where the
    field is NaN are excluded and the weights renormalized over the finite
    cells, so a masked cell never counts as probability zero. Returns an array
    of the leading dims; all-NaN slices give NaN.
    """
    c = np.asarray(cube, dtype="float64")
    w = np.asarray(weight, dtype="float64")
    finite = np.isfinite(c)
    num = np.nansum(np.where(finite, c, 0.0) * w, axis=(-2, -1))
    den = np.sum(finite * w, axis=(-2, -1))
    with np.errstate(invalid="ignore", divide="ignore"):
        out = num / den
    return np.where(den > 0, out, np.nan)


def mhw_flags(anom: np.ndarray, q90_by_month: np.ndarray, months: np.ndarray) -> np.ndarray:
    """Observed MHW flag per cell/time: anomaly above that calendar month's q90.

    ``anom`` is (time, lat, lon); ``q90_by_month`` is (12, lat, lon) indexed by
    calendar month 1–12; ``months`` is (time,) of calendar months. NaN anomaly
    (land) → NaN so downstream weighting can exclude it.
    """
    thr = q90_by_month[np.asarray(months) - 1]           # (time, lat, lon)
    flags = (np.asarray(anom) > thr).astype("float64")
    flags[~np.isfinite(anom)] = np.nan
    return flags


def sedi_from_counts(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Symmetrical Extremal Dependence Index from 2×2 contingency counts.

    a=hits, b=false alarms, c=misses, d=correct negatives (arrays broadcast).
    SEDI = (lnF − lnH − ln(1−F) + ln(1−H)) / (lnF + lnH + ln(1−F) + ln(1−H)),
    H = a/(a+c), F = b/(b+d). Degenerate rates (H or F in {0, 1}) → NaN.
    """
    a, b, c, d = (np.asarray(x, dtype="float64") for x in (a, b, c, d))
    with np.errstate(invalid="ignore", divide="ignore"):
        h = a / (a + c)
        f = b / (b + d)
        valid = (h > 0) & (h < 1) & (f > 0) & (f < 1)
        h = np.where(valid, h, 0.5)                      # placeholder, masked below
        f = np.where(valid, f, 0.5)
        num = np.log(f) - np.log(h) - np.log1p(-f) + np.log1p(-h)
        den = np.log(f) + np.log(h) + np.log1p(-f) + np.log1p(-h)
        out = num / den
    return np.where(valid & (den != 0), out, np.nan)


# ---------------------------------------------------------------------------
# Config-driven paths
# ---------------------------------------------------------------------------

def _raw(cfg: dict, key: str) -> Path:
    files = {**cfg["source"]["latest_files"], **cfg["source"]["static_files"],
             **cfg["source"]["hindcast_files"]}
    return PROJECT_ROOT / cfg["source"]["raw_dir"] / files[key]


def _derived(cfg: dict, key: str, flavor: str | None = None) -> Path:
    p = cfg["derived"][key]
    if flavor is not None:
        p = p.format(flavor=flavor)
    return PROJECT_ROOT / p


def _window(cfg: dict) -> dict:
    return cfg["alaska_window"]


def _sel_window(ds: xr.Dataset | xr.DataArray, cfg: dict) -> xr.Dataset | xr.DataArray:
    w = _window(cfg)
    return ds.sel(lat=slice(w["lat_min"], w["lat_max"]), lon=slice(w["lon_min"], w["lon_max"]))


# ---------------------------------------------------------------------------
# Zone masks/weights (static artifact)
# ---------------------------------------------------------------------------

def ensure_zone_masks(cfg: dict, force: bool = False) -> xr.Dataset:
    """Load the static masks/weights artifact, rebuilding it when stale."""
    out = _derived(cfg, "masks_weights")
    stale = (
        force
        or not out.exists()
        or GEOJSON_PATH.stat().st_mtime > out.stat().st_mtime
    )
    if stale:
        print("Building NMME zone masks/weights …")
        ds = build_zone_masks(cfg["zones"], _raw(cfg, "mask"), window=_window(cfg))
        out.parent.mkdir(parents=True, exist_ok=True)
        ds.to_netcdf(out)
        print(f"  Saved → {out}")
        return ds
    return xr.load_dataset(out)


# ---------------------------------------------------------------------------
# Forecast probability: Alaska cube + tidy zone series
# ---------------------------------------------------------------------------

def build_prob_artifacts(cfg: dict, flavor: str, masks: xr.Dataset) -> None:
    schema = cfg["schema"]["prob"]
    raw_path = _raw(cfg, f"prob_{flavor}")
    print(f"Slicing {raw_path.name} to the Alaska window …")

    with xr.open_dataset(raw_path) as ds:
        da = _sel_window(ds[schema["var"]], cfg)
        cube = (
            da.transpose(schema["init_dim"], schema["lead_dim"], "lat", "lon")
            .astype("float32")
            .load()
        )

    out_nc = _derived(cfg, "prob_cube", flavor)
    out_nc.parent.mkdir(parents=True, exist_ok=True)
    cube.to_dataset(name=schema["var"]).to_netcdf(out_nc)
    print(f"  Saved → {out_nc}  ({dict(cube.sizes)})")

    # Tidy per-zone series — NaN-aware weighted mean per (zone, init, lead).
    inits = pd.to_datetime(cube[schema["init_dim"]].values)
    leads = cube[schema["lead_dim"]].values
    frames = []
    for zid in masks["zone"].values:
        w = masks["weight"].sel(zone=zid).values
        zm = zonal_mean_cube(cube.values, w)             # (init, lead)
        frames.append(pd.DataFrame({
            "zone": zid,
            "init_time": np.repeat(inits, leads.size),
            "lead_months": np.tile(leads, inits.size),
            "prob": zm.ravel(),
            "flavor": flavor,
        }))
    df = pd.concat(frames, ignore_index=True)
    df["init_year"] = df["init_time"].dt.year
    df["init_month"] = df["init_time"].dt.month

    out_pq = _derived(cfg, "zone_series", flavor)
    df.to_parquet(out_pq, index=False)
    print(f"  Saved → {out_pq}  ({len(df):,} rows, "
          f"{inits.min().date()} → {inits.max().date()})")


# ---------------------------------------------------------------------------
# Observed zone MHW status ("what happened")
# ---------------------------------------------------------------------------

def build_obs_status(cfg: dict, masks: xr.Dataset) -> None:
    obs_schema = cfg["schema"]["obs"]
    frames = []
    for flavor in FLAVORS:
        anom_p = _raw(cfg, f"obs_anom_{flavor}")
        q90_p = _raw(cfg, f"obs_q90_{flavor}")
        print(f"Observed MHW status ({flavor}) from {anom_p.name} …")
        with xr.open_dataset(anom_p) as ds_a, xr.open_dataset(q90_p) as ds_q:
            anom = _sel_window(ds_a[obs_schema["anom_var"]], cfg).load()
            q90 = _sel_window(ds_q[obs_schema["q90_var"]], cfg).load()
        times = pd.to_datetime(anom[obs_schema["time_dim"]].values)
        flags = mhw_flags(anom.values, q90.values, times.month.values)
        for zid in masks["zone"].values:
            w = masks["weight"].sel(zone=zid).values
            frames.append(pd.DataFrame({
                "zone": zid,
                "date": times,
                "obs_mhw_area_frac": zonal_mean_cube(flags, w),
                "flavor": flavor,
            }))
    df = pd.concat(frames, ignore_index=True)
    out = _derived(cfg, "obs_status")
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}  ({len(df):,} rows)")


# ---------------------------------------------------------------------------
# SEDI skill (local one-time build; never from cron)
# ---------------------------------------------------------------------------

def build_sedi(cfg: dict, masks: xr.Dataset) -> None:
    """Cell- and zone-level SEDI from the 1991–2020 hindcast vs observed flags.

    Forecast event = hindcast probability ≥ ``sedi.decision_threshold``
    (NOAA's exact recipe is unpublished; the threshold is a documented config
    knob). Contingency counts are pooled over **all 360 hindcast initializations
    at each lead** (not stratified by calendar month) — per-month bins have only
    ~30 samples, so at longer leads almost every cell has a degenerate hit or
    false-alarm rate and SEDI is undefined (blank map). Pooling per lead gives a
    dense, statistically meaningful "skill at lead N" map. Zone SEDI pools the
    weighted counts over the zone's cells before the SEDI transform.
    """
    schema = cfg["schema"]["prob"]
    obs_schema = cfg["schema"]["obs"]
    thr = float(cfg["sedi"]["decision_threshold"])
    init_dim, lead_dim = schema["init_dim"], schema["lead_dim"]

    out_vars = {}
    for flavor in FLAVORS:
        hind_p = _raw(cfg, f"hindcast_{flavor}")
        if not hind_p.exists():
            raise FileNotFoundError(
                f"{hind_p} missing — run `mhw-fetch-psl-mhw --include-hindcast` first."
            )
        print(f"SEDI ({flavor}) from {hind_p.name} …")
        with xr.open_dataset(hind_p) as ds:
            hind = _sel_window(ds[schema["var"]], cfg)
            hind = hind.transpose(init_dim, lead_dim, "lat", "lon").load()

        with xr.open_dataset(_raw(cfg, f"obs_anom_{flavor}")) as ds_a, \
                xr.open_dataset(_raw(cfg, f"obs_q90_{flavor}")) as ds_q:
            anom = _sel_window(ds_a[obs_schema["anom_var"]], cfg).load()
            q90 = _sel_window(ds_q[obs_schema["q90_var"]], cfg).load()
        obs_times = pd.to_datetime(anom[obs_schema["time_dim"]].values)
        obs_flags = mhw_flags(anom.values, q90.values, obs_times.month.values)
        obs_index = {(t.year, t.month): i for i, t in enumerate(obs_times)}

        inits = pd.to_datetime(hind[init_dim].values)
        leads = hind[lead_dim].values
        lats, lons = hind["lat"].values, hind["lon"].values

        # Contingency accumulators pooled over all inits: (lead, lat, lon)
        shape = (leads.size, lats.size, lons.size)
        counts = {k: np.zeros(shape) for k in "abcd"}

        fc_event = hind.values >= thr                     # (init, lead, lat, lon)
        fc_valid = np.isfinite(hind.values)
        for i, t0 in enumerate(inits):
            for il, lead in enumerate(leads):
                target = t0 + pd.DateOffset(months=int(lead))   # lead 0.5 → init month
                io = obs_index.get((target.year, target.month))
                if io is None:
                    continue
                o = obs_flags[io]                          # (lat, lon), NaN over land
                valid = fc_valid[i, il] & np.isfinite(o)
                f, ob = fc_event[i, il], o > 0.5
                counts["a"][il] += valid & f & ob
                counts["b"][il] += valid & f & ~ob
                counts["c"][il] += valid & ~f & ob
                counts["d"][il] += valid & ~f & ~ob

        cell_sedi = sedi_from_counts(counts["a"], counts["b"], counts["c"], counts["d"])
        out_vars[f"sedi_{flavor}"] = xr.DataArray(
            cell_sedi.astype("float32"),
            dims=(lead_dim, "lat", "lon"),
            coords={lead_dim: leads, "lat": lats, "lon": lons},
        )

        # Zone reduction: pool weighted counts over the zone, then SEDI.
        zone_vals = np.full((masks.sizes["zone"], leads.size), np.nan, "float32")
        for k, zid in enumerate(masks["zone"].values):
            w = masks["weight"].sel(zone=zid).values      # (lat, lon)
            pooled = [np.sum(counts[key] * w, axis=(-2, -1)) for key in "abcd"]
            zone_vals[k] = sedi_from_counts(*pooled)
        out_vars[f"zone_sedi_{flavor}"] = xr.DataArray(
            zone_vals,
            dims=("zone", lead_dim),
            coords={"zone": masks["zone"].values, lead_dim: leads},
        )

    out = _derived(cfg, "sedi")
    xr.Dataset(
        out_vars,
        attrs={
            "description": "SEDI (Symmetric Extremal Dependence Index) skill of the PSL NMME "
                           "MHW hindcast (1991–2020) vs observed OISST MHW flags, Alaska "
                           "window; pooled over all initializations per lead.",
            "decision_threshold": thr,
        },
    ).to_netcdf(out)
    print(f"  Saved → {out}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Alaska-window derived artifacts from raw PSL MHW files.",
    )
    parser.add_argument(
        "--flavor", choices=[*FLAVORS, "both"], default="both",
        help="Which probability flavor(s) to rebuild (default: both)",
    )
    parser.add_argument(
        "--sedi", action="store_true",
        help="Also build the SEDI skill artifact from the 1991-2020 hindcast "
             "(heavy; run locally, never from cron)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Rebuild even when derived artifacts are newer than the raw files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    cfg = load_config()

    masks = ensure_zone_masks(cfg, force=args.force)

    flavors = FLAVORS if args.flavor == "both" else (args.flavor,)
    for flavor in flavors:
        raw_path = _raw(cfg, f"prob_{flavor}")
        out_path = _derived(cfg, "prob_cube", flavor)
        if (not args.force and out_path.exists()
                and out_path.stat().st_mtime >= raw_path.stat().st_mtime):
            print(f"{out_path.name} newer than {raw_path.name} — skipping (use --force)")
            continue
        build_prob_artifacts(cfg, flavor, masks)

    build_obs_status(cfg, masks)

    if args.sedi:
        build_sedi(cfg, masks)


if __name__ == "__main__":
    main()
