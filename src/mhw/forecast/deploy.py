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
                              band_lo, band_hi, l1_prob   (+ module_version, fit_vintage attrs)
    onset_sebs.parquet      : date, state, threshold      (+ module_version, fit_vintage attrs)

CLI: (none yet — a script entry is added when the module is vendored)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "forecast.yml"
AGG_DIR = PROJECT_ROOT / "data" / "derived" / "aggregates_region"
FORECAST_DIR = PROJECT_ROOT / "data" / "derived" / "forecast"

# Artifact column contracts (kept in one place so the producer, API, and panel agree).
FORECAST_COLUMNS = [
    "lead", "lead_months", "confidence", "method",
    "point", "ar1_var", "band_lo", "band_hi", "l1_prob",
]
ONSET_COLUMNS = ["date", "state", "threshold"]


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
# Producer (stub until LOFRA's module is vendored + pinned)
# ---------------------------------------------------------------------------

def run_forecast(zone: str, cfg: dict | None = None) -> Path:
    """Run the forward forecast for *zone* and write its artifact. **Not yet wired.**

    On delivery: verify the SHA-256 seal, vendor LOFRA's ``forecast/`` module, pin
    ``module_version``/``fit_vintage`` in ``config/forecast.yml``, then fit-on-latest →
    forecast-forward over ``read_area_frac_monthly(zone)`` and write ``FORECAST_COLUMNS`` to
    ``forecast_artifact_path(zone)`` (frozen coefficients — no re-estimation here).
    """
    cfg = cfg or load_forecast_config()
    if cfg.get("module_version") is None:
        raise NotImplementedError(
            "Forecast module not yet delivered/pinned. Awaiting LOFRA's `forecast/` module + "
            "obl029 chain + v1 coefficient manifest (Thread: forecast-transfer). Set "
            "`module_version` in config/forecast.yml once vendored."
        )
    raise NotImplementedError("run_forecast wiring lands with the vendored module")
