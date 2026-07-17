"""Deploy-side forecast wrapper — run LOFRA's damped-persistence module on our own data.

This is the **dashboard-side** adapter for the settled forecast product (division of labor
resolved 2026-07-08, ``Thread: forecast-transfer``). It is deliberately distinct from the internal
grid AR(1) engine in this package (``baselines``/``exceedance``/``regional`` + ``io``), which
targeted the superseded per-cell MVP. The deployed product forecasts each zone's monthly
``area_frac`` with LOFRA's module (the source of truth), so the only data adapter persistence needs
is a monthly ``area_frac`` reader over the sealed aggregation contract.

Responsibilities:
* ``load_forecast_config`` / ``zone_role`` — read ``config/forecast.yml`` (the tile-wiring source).
* ``monthly_area_frac`` — pure daily→monthly reducer (unit-tested on small frames).
* ``read_area_frac_monthly`` — the module input, straight from ``region_daily_{id}.parquet``.
* ``run_forecast`` — writes ``data/derived/forecast/`` artifacts. **Stubbed** until LOFRA delivers
  and we vendor + pin the module (``module_version`` in the config flips from ``null`` to ``v1``).

Artifacts (schema fixed now so the API/panel can be built against it):
    forecast_{zone}.parquet : lead, lead_months, confidence, method, point, ar1_var,
                              band_lo, band_hi, l1_prob, target_date   (+ provenance metadata:
                              module_version, fit_vintage, coefficient_vintage, origin_date)
    onset_sebs.parquet      : date, state, threshold      (deferred — see run_onset_watch)

CLI: mhw-run-forecast [--zones ...] [--out-dir DIR]  → writes forecast_{zone}.parquet for all zones.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "forecast.yml"
AGG_DIR = PROJECT_ROOT / "data" / "derived" / "aggregates_region"
FORECAST_DIR = PROJECT_ROOT / "data" / "derived" / "forecast"

# The delivered LOFRA module is vendored verbatim (forecast/ + scripts/ siblings, per its README).
VENDOR_DIR = PROJECT_ROOT / "vendor" / "forecast-module-v1"

# 90% two-sided predictive band (z for the 0.95 quantile of a standard normal). The band is a
# DISPLAY device around the unclipped point forecast; points/vars are used exactly as scored.
_BAND_Z = 1.6448536269514722

# Artifact column contracts (kept in one place so the producer, API, and panel agree). The API
# reads the first nine by name; ``target_date`` is an extra the panel uses and the API ignores.
FORECAST_COLUMNS = [
    "lead", "lead_months", "confidence", "method",
    "point", "ar1_var", "band_lo", "band_hi", "l1_prob",
]
ONSET_COLUMNS = ["date", "state", "threshold"]

# Provenance keys embedded in each artifact's parquet metadata (shown on the tiles).
_META_KEYS = ("module_version", "fit_vintage", "coefficient_vintage", "origin_date")


# ---------------------------------------------------------------------------
# Config (pure) — the tile-wiring source of truth
# ---------------------------------------------------------------------------

def load_forecast_config(path: Path | None = None) -> dict:
    """Parse ``config/forecast.yml`` into a plain dict."""
    return yaml.safe_load((path or CONFIG_PATH).read_text())


def zone_role(zone: str, cfg: dict | None = None) -> str:
    """Return the display role for *zone* (``persistence`` | ``climatology``).

    Raises ``KeyError`` for an unknown zone so callers can map it to a 404.
    """
    cfg = cfg or load_forecast_config()
    return cfg["zones"][zone]["role"]


def forecast_artifact_path(zone: str) -> Path:
    return FORECAST_DIR / f"forecast_{zone}.parquet"


def onset_artifact_path() -> Path:
    return FORECAST_DIR / "onset_sebs.parquet"


# ---------------------------------------------------------------------------
# Data adapter (pure, network-free, unit-tested)
# ---------------------------------------------------------------------------

def monthly_area_frac(daily: pd.DataFrame) -> pd.DataFrame:
    """Reduce a daily ``region_daily_*`` frame to a monthly ``area_frac`` series.

    The module input is the monthly per-zone occurrence share under the sealed contract
    ``area_frac = Σ(w·A)/Σ(w)``. We take the calendar-month mean of the daily ``area_frac``
    (month-start timestamps). Pure: operates on an in-memory frame, no IO.
    """
    if "date" not in daily.columns or "area_frac" not in daily.columns:
        raise ValueError("expected columns 'date' and 'area_frac'")
    df = daily[["date", "area_frac"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    out = (
        df.set_index("date")["area_frac"]
        .resample("MS")            # month-start; label each month by its first day
        .mean()
        .rename("area_frac")
        .reset_index()
    )
    return out


def read_area_frac_monthly(zone: str, agg_dir: Path | None = None) -> pd.DataFrame:
    """Load a zone's daily aggregates and return its monthly ``area_frac`` series."""
    p = (agg_dir or AGG_DIR) / f"region_daily_{zone}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"no aggregates for zone {zone!r}: {p}")
    return monthly_area_frac(pd.read_parquet(p))


# ---------------------------------------------------------------------------
# Vendored LOFRA module — frozen operational entry point (pinned coefficients)
# ---------------------------------------------------------------------------

_MANIFEST = None  # lazily loaded once; the pinned manifest is immutable


def _forecast_module():
    """Import the vendored top-level ``forecast`` package (distinct from this ``mhw.forecast``).

    The package resolves its sibling ``scripts/`` relative to itself, so we only need the vendor
    root on ``sys.path``; the absolute ``import forecast`` then binds to ``vendor/…/forecast``.
    """
    if not VENDOR_DIR.exists():
        raise FileNotFoundError(
            f"vendored forecast module missing at {VENDOR_DIR}. Extract "
            "data/incoming/forecast-module-v1-*.tar.gz into vendor/ (see config/forecast.yml)."
        )
    if str(VENDOR_DIR) not in sys.path:
        sys.path.insert(0, str(VENDOR_DIR))
    import forecast  # noqa: PLC0415  (deferred: vendored, path-shimmed above)
    return forecast


def _manifest():
    """Return the pinned coefficient manifest (loaded once).

    The coefficient-manifest filename is pinned in ``config/forecast.yml``
    (``coefficient_manifest``) and resolved inside the vendored ``forecast/`` dir, so a
    versioned re-fit (v1 → v2 → …) is a config bump, not a code edit. Defaults to the v1
    file when unset (back-compat with the vendored module's own ``DEFAULT_MANIFEST``).
    """
    global _MANIFEST
    if _MANIFEST is None:
        name = load_forecast_config().get("coefficient_manifest")
        json_path = (VENDOR_DIR / "forecast" / name) if name else None
        _MANIFEST = _forecast_module().load_manifest(json_path)
    return _MANIFEST


# ---------------------------------------------------------------------------
# Producer — apply the FROZEN coefficients forward over our own monthly area_frac
# ---------------------------------------------------------------------------

def _clip01(x: float) -> float:
    """Clip a forecast to [0, 1] for display (points/bands are unclipped as scored)."""
    return float(min(1.0, max(0.0, x)))


def _forecast_rows(out: dict, cfg: dict) -> pd.DataFrame:
    """Map a frozen ``forecast_frozen`` result onto the fixed ``forecast_{zone}`` schema.

    Pure: takes the module's return dict + the lead config, returns the artifact frame. The
    honesty-ladder id/confidence come from ``config/forecast.yml`` (keyed by lead month); the
    model/point/variance/occurrence come straight from the frozen path.
    """
    by_month = {int(lead["months"]): lead for lead in cfg["leads"]}
    rows = []
    for h, entry in out["leads"].items():
        lead_cfg = by_month.get(int(h), {})
        point = entry["point_area_frac"]
        var = float(entry["predictive_variance"])
        half = _BAND_Z * float(np.sqrt(var)) if var >= 0 else float("nan")
        l1 = entry.get("occurrence_prob_q90")
        rows.append({
            "lead": lead_cfg.get("id", f"L{h}"),
            "lead_months": int(h),
            "confidence": lead_cfg.get("confidence", ""),
            "method": out["model"],
            "point": _clip01(point),
            "ar1_var": var,
            "band_lo": _clip01(point - half),
            "band_hi": _clip01(point + half),
            "l1_prob": None if l1 is None else float(l1),
            "target_date": entry["target_date"],
        })
    df = pd.DataFrame(rows).sort_values("lead_months").reset_index(drop=True)
    return df[FORECAST_COLUMNS + ["target_date"]]


def _write_with_meta(df: pd.DataFrame, path: Path, meta: dict) -> None:
    """Write *df* to parquet with string provenance embedded in the file-level metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    existing = table.schema.metadata or {}
    kv = {**existing, **{k.encode(): str(v).encode() for k, v in meta.items()}}
    pq.write_table(table.replace_schema_metadata(kv), path)


def read_forecast_artifact(zone: str) -> tuple[pd.DataFrame, dict]:
    """Load a zone's forecast artifact as ``(frame, provenance_metadata)``.

    The panel uses this so tiles can show ``coefficient_vintage`` / ``origin_date`` without the
    API. Raises ``FileNotFoundError`` if the artifact has not been produced yet.
    """
    p = forecast_artifact_path(zone)
    if not p.exists():
        raise FileNotFoundError(f"no forecast artifact for {zone!r}: {p} — run `mhw-run-forecast`")
    schema_meta = pq.read_schema(p).metadata or {}
    meta = {k: schema_meta.get(k.encode(), b"").decode() or None for k in _META_KEYS}
    return pd.read_parquet(p), meta


def hindcast_series(zone: str, n_months: int = 9, cfg: dict | None = None) -> pd.DataFrame:
    """One-month-ahead FROZEN hindcast over the last *n_months* — for the outlook chart.

    For each recent month *m*, applies the same pinned v1 coefficients at origin *m−1* and reads
    the lead-1 forecast for *m* (`forecast.forecast_frozen`, leads=(1,)). This is the deployed
    frozen model rolled one step at a time across history, so it can be shown against the actuals
    to convey tracking. Returns ``date, point, ar1_var, actual`` (point/var unclipped, as scored).

    Honesty note: the coefficients are pinned at the 2026-04 fit vintage, so hindcast months on or
    before that vintage are in-sample — treat the overlay as illustrative of tracking, not a clean
    out-of-sample skill score (that is the research cell's rolling-origin hindcast).
    """
    cfg = cfg or load_forecast_config()
    if zone not in cfg["zones"]:
        raise KeyError(f"unknown forecast zone {zone!r}; known: {sorted(cfg['zones'])}")
    monthly = read_area_frac_monthly(zone).reset_index(drop=True)
    mod, mani = _forecast_module(), _manifest()
    n = len(monthly)
    rows = []
    # Start at target index 2 at the earliest: the frozen path validates a >=2-month contiguous
    # origin frame (the persistence lag is positional), so a 1-row origin is rejected.
    for j in range(min(max(2, n - n_months), n), n):   # target month j, origin j-1
        out = mod.forecast_frozen(monthly.iloc[:j], zone, mani, leads=(1,))
        e = out["leads"][1]
        rows.append({
            "date": monthly["date"].iloc[j],
            "point": float(e["point_area_frac"]),
            "ar1_var": float(e["predictive_variance"]),
            "actual": float(monthly["area_frac"].iloc[j]),
        })
    return pd.DataFrame(rows, columns=["date", "point", "ar1_var", "actual"])


def run_forecast(zone: str, cfg: dict | None = None) -> Path:
    """Run the frozen forward forecast for *zone* and write ``forecast_{zone}.parquet``.

    Applies LOFRA's PINNED coefficients (``forecast.forecast_frozen``); the only live input is the
    origin observation (the last row of our monthly ``area_frac``). Nothing is re-estimated here.
    """
    cfg = cfg or load_forecast_config()
    if cfg.get("module_version") is None:
        raise RuntimeError(
            "config/forecast.yml has module_version: null — pin the vendored module version first."
        )
    if zone not in cfg["zones"]:
        raise KeyError(f"unknown forecast zone {zone!r}; known: {sorted(cfg['zones'])}")

    leads = tuple(int(lead["months"]) for lead in cfg["leads"])
    monthly = read_area_frac_monthly(zone)
    out = _forecast_module().forecast_frozen(monthly, zone, _manifest(), leads=leads)

    df = _forecast_rows(out, cfg)
    meta = {
        "module_version": cfg.get("module_version"),
        "fit_vintage": cfg.get("fit_vintage"),
        "coefficient_vintage": out.get("coefficient_vintage"),
        "origin_date": out.get("origin_date"),
    }
    path = forecast_artifact_path(zone)
    _write_with_meta(df, path, meta)
    return path


def run_onset_watch(cfg: dict | None = None) -> Path:
    """SEBS onset watch — **deferred**. Needs the obl029 broad-basin OISST field rebuilt locally.

    The frozen onset path (``forecast.sebs_onset_watch_frozen``) requires a monthly broad-basin
    OISST anomaly NetCDF on the fit-vintage grid/baseline, built via the vendored obl029 chain.
    Until that field exists the onset artifact is not produced and ``/v1/forecast/onset/sebs``
    stays live-safe at 503. See the plan's "Out of scope" follow-up.
    """
    raise NotImplementedError(
        "SEBS onset watch needs the obl029 broad-basin field rebuild "
        "(vendor/forecast-module-v1/scripts/obl029_*) — deferred follow-up."
    )


# ---------------------------------------------------------------------------
# CLI — mhw-run-forecast
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mhw-run-forecast",
        description="Apply the pinned LOFRA forecast module forward over our monthly area_frac and "
                    "write data/derived/forecast/forecast_{zone}.parquet for each zone.",
    )
    p.add_argument("--zones", nargs="*", default=None,
                   help="zones to run (default: every zone in config/forecast.yml)")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="override output dir (default: data/derived/forecast/)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = load_forecast_config()
    if args.out_dir is not None:
        global FORECAST_DIR
        FORECAST_DIR = args.out_dir
    zones = args.zones or list(cfg["zones"])
    for zone in zones:
        path = run_forecast(zone, cfg)
        _, meta = read_forecast_artifact(zone)
        print(f"[mhw-run-forecast] {zone:<11} -> {path}  "
              f"(coef {meta['coefficient_vintage']}, origin {meta['origin_date']})")
    print(f"[mhw-run-forecast] wrote {len(zones)} artifact(s) to {FORECAST_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
