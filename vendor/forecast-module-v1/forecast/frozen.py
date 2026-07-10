#!/usr/bin/env python3
"""
forecast/frozen.py — FROZEN-coefficient operational path (v1)
=============================================================
The OPERATIONAL DEFAULT for the Alaska dashboard. Every quantity that the
paper validated is APPLIED FROM THE PINNED COEFFICIENT MANIFEST
(forecast/coefficient_manifest_v1.json + its companion npz) and NOTHING is
re-estimated from the caller's live data:

  * per-zone damped-persistence  phi, sigma_eps, 12-month seasonal climatology,
    train q90 threshold, and the frozen one-step residual set (occurrence);
  * climatology-zone 12-month seasonal climatology + frozen per-lead
    predictive variances;
  * SEBS LIM: frozen EOF basis (mean, sqrt-cos-lat weight, spatial patterns V),
    one-month propagator G1, zone read-off vector/const, the frozen isotonic
    link knots, q90 threshold, per-lead onset residual set, and the paper
    warn-above-climatology decision thresholds.

The ONLY thing taken from the caller's live frame / field is the ORIGIN
OBSERVATION(S) needed to project forward:
  * persistence/climatology: the current anomaly y_origin (and its calendar
    month) — point = clim(target_month) + phi^h * (y_origin - clim(origin_month));
  * SEBS onset: the live field's origin STATE x0, obtained by projecting the
    live origin anomaly onto the FROZEN EOF basis (no re-fit of the LIM, the
    link, or any threshold).

Contrast with forecast/core.py (`run_latest_origin`, `sebs_onset_watch`),
which RE-FITS every coefficient on the caller-supplied frame each call. That
re-fit path is the VALIDATION / REPLICATION path — it reproduces the paper's
per-origin rolling hindcast bit-for-bit and MUST keep doing so — but it is NOT
the operational path: run forward monthly it would silently re-estimate phi,
sigma_eps, the LIM operator, the isotonic link, and the onset threshold as the
live record grows. This module is the operational path: coefficients frozen,
only the origin observation live.

Fit vintage of the FROZEN coefficients (see §"Vintage" below): the latest
rolling-origin at which the paper hindcast has a SCORED record for every
deployed lead — persistence/climatology origin 2026-04 (leads 1-3 all scored),
SEBS onset origin 2026-05 (leads 1-2 scored). Freezing at the last SCORED
origin (not the last raw data row) is what makes the pinned coefficients
literally "paper-validated": the frozen path reproduces those hindcast records
to machine precision (forecast/selftest_identity_check.py, section [5]/[6]).

No new equations beyond the AR(1) h-step predictive-variance formula reused
from forecast/core.py (standard/canonical, Hamilton 1994 Ch.4 §4.2;
confirmed-in-kind by Cobra 2026-07-08 — full provenance note at the use-site
below and in forecast/core.py).

Author/owner: Metrica. Build date 2026-07-08.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

_PROJ = Path(__file__).resolve().parents[1]
_SCRIPTS = _PROJ / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from forecast.core import DEPLOY_MAP, Q_EVENT, MAXLEAD, _month_key, _prep  # noqa: E402

DEFAULT_MANIFEST = _PROJ / "forecast/coefficient_manifest_v1.json"


# ---------------------------------------------------------------------------
# Manifest loading (JSON scalars/small vectors + companion npz for bulky
# arrays: the EOF basis and the frozen residual sets).
# ---------------------------------------------------------------------------
@dataclass
class FrozenManifest:
    meta: dict            # full parsed JSON
    frozen: dict          # the "frozen" section of the JSON
    arrays: dict          # companion npz arrays (lazy-loaded)


def load_manifest(json_path: str | Path | None = None) -> FrozenManifest:
    """Load the pinned manifest JSON and its companion npz (frozen basis +
    residual sets). No coefficient is computed here — pure read of pinned
    artifacts."""
    jp = Path(json_path) if json_path is not None else DEFAULT_MANIFEST
    meta = json.loads(Path(jp).read_text())
    if "frozen" not in meta:
        raise ValueError(f"{jp} has no 'frozen' section — rebuild via "
                         "forecast/build_coefficient_manifest.py")
    npz_rel = meta["frozen"]["companion_npz"]
    npz_path = Path(jp).resolve().parent / npz_rel
    if not npz_path.exists():
        raise FileNotFoundError(
            f"frozen companion npz missing: {npz_path} — regenerate via "
            "forecast/build_coefficient_manifest.py (it is a gitignored, "
            "fully-regenerable binary product).")
    arrays = dict(np.load(npz_path))
    return FrozenManifest(meta=meta, frozen=meta["frozen"], arrays=arrays)


# ---------------------------------------------------------------------------
# 1. Frozen persistence / climatology
# ---------------------------------------------------------------------------
def forecast_frozen(area_frac_df: pd.DataFrame, zone: str,
                    manifest: FrozenManifest,
                    leads: tuple = (1, 2, 3)) -> dict:
    """FROZEN-coefficient magnitude/occurrence forecast (operational default).

    Applies the pinned per-zone coefficients; the caller's frame supplies ONLY
    the origin observation (last row) — nothing is re-estimated.

    Per lead:
      * point_area_frac      — damped: clim(target) + phi^h*(y_origin -
                               clim(origin_month)); climatology: clim(target).
                               UNCLIPPED (exactly as scored; clip for display).
      * predictive_variance  — damped: pinned sigma_eps^2*(1-phi^{2h})/(1-phi^2)
                               (AR(1) h-step formula, standard/canonical,
                               Cobra-confirmed 2026-07-08 — see use-site note);
                               climatology: the FROZEN per-lead train residual
                               variance from the manifest (not re-derived).
      * occurrence_prob_q90  — L1, damped zones only: P(area_frac > pinned q90)
                               via the FROZEN one-step residual set
                               (exceedance_prob against frozen quantities).
    """
    if zone not in DEPLOY_MAP:
        raise ValueError(f"unknown zone '{zone}'; valid: {tuple(DEPLOY_MAP)}")
    spec = DEPLOY_MAP[zone]
    fz = manifest.frozen["persistence_climatology"]["zones"][zone]
    df = _prep(area_frac_df)
    y = df["area_frac"].to_numpy(float)
    origin_date = pd.Timestamp(df["date"].iloc[-1])
    origin_month = int(df["cal_month"].iloc[-1])
    y_origin = float(y[-1])

    clim = np.asarray(fz["seasonal_climatology_jan_dec"], float)   # pinned (12,)
    damped = spec["magnitude_model"] == "damped_persistence"

    out = {
        "zone": zone,
        "model": spec["magnitude_model"],
        "path": "frozen",
        "coefficient_vintage": manifest.frozen["persistence_climatology"]["fit_origin_date"],
        "origin_date": str(origin_date.date()),
        "leads": {},
    }
    if damped:
        phi = float(fz["phi"])
        sigma_eps2 = float(fz["sigma_eps"]) ** 2
        thr = float(fz["q90_threshold"])
        resid1 = np.asarray(manifest.arrays[f"resid1_{zone}"], float)   # frozen
        out.update({"phi": phi, "sigma_eps": float(fz["sigma_eps"]),
                    "q90_threshold": thr})
        a_origin = y_origin - float(clim[origin_month - 1])
    else:
        pvar = fz["predictive_variance_by_lead"]                        # frozen

    for h in leads:
        h = int(h)
        target_month = (origin_month - 1 + h) % 12 + 1
        if damped:
            pt = float(clim[target_month - 1] + (phi ** h) * a_origin)
            # AR(1) h-step forecast-error variance
            # sigma_eps^2*(1-phi^{2h})/(1-phi^2) — standard/canonical; the
            # finite-h form of the paper's Eq 7b (which displays its h->inf
            # limit). Source: Hamilton (1994), Time Series Analysis, Ch.4
            # §4.2 (pp.77-84); OA-verified equivalent Hyndman &
            # Athanasopoulos, Forecasting: Principles and Practice (3rd ed.)
            # §9.8; canonical Brockwell & Davis (2016). Confirmed-in-kind by
            # Cobra 2026-07-08 (handoffs/cobra-to-lofra-ar1-variance-
            # provenance-20260708.md); accepted at metadata-level
            # attribution. Evaluated on FROZEN phi, sigma_eps.
            var_h = sigma_eps2 * (1.0 - phi ** (2 * h)) / (1.0 - phi ** 2)
            entry = {
                "target_date": str((origin_date + pd.DateOffset(months=h)).date()),
                "point_area_frac": pt,
                "predictive_variance": float(var_h),
                "predictive_variance_kind": "ar1_hstep_formula_frozen",
            }
            if h == 1 and spec["occurrence_l1"]:
                # occurrence against FROZEN quantities: pinned q90 + frozen
                # one-step residual set (no live re-estimation of the residual
                # distribution).
                entry["occurrence_prob_q90"] = float(np.mean((pt + resid1) > thr))
        else:
            pt = float(clim[target_month - 1])
            entry = {
                "target_date": str((origin_date + pd.DateOffset(months=h)).date()),
                "point_area_frac": pt,
                "predictive_variance": float(pvar[f"lead_{h}"]),
                "predictive_variance_kind": "empirical_train_residual_variance_frozen",
            }
        out["leads"][h] = entry
    return out


# ---------------------------------------------------------------------------
# 2. Live-field ingestion (arbitrary NetCDF -> projectable field state)
# ---------------------------------------------------------------------------
@dataclass
class LiveField:
    """Minimal field state for the FROZEN onset path: the ocean-cell anomaly
    matrix + native cell coordinates (for alignment onto the frozen EOF cells).
    Deliberately carries NO zone weights / masks-zarr dependency — the frozen
    onset applies pinned zone read-off vectors, so the live field supplies only
    the origin state."""
    dates: pd.DatetimeIndex   # (Nf,)
    A: np.ndarray             # (Nf, M) unweighted ocean anomaly, deg C
    cell_lat: np.ndarray      # (M,) native latitude of each ocean cell
    cell_lon: np.ndarray      # (M,) native longitude (0-360) of each ocean cell


def load_live_field(nc_path: str | Path,
                    anom_var: str = "sst_monthly_anom",
                    drop_month: str = "1982-03") -> LiveField:
    """Read an arbitrary broad-basin OISST-anomaly NetCDF (the dashboard
    rebuilds it locally via obl029) into a LiveField.

    Mirrors scripts/stage3_lim.load_field's ocean-cell construction EXACTLY
    (finite-all-kept-months ocean mask; same 1982-03 drop) so that, on the
    sealed field, it reproduces the fit-vintage ocean-cell matrix bit-for-bit
    and the frozen projection is exact. The dashboard owns this field's QA;
    this helper only reads it into the projectable shape.
    """
    import xarray as xr
    d = xr.open_dataset(str(nc_path))
    times = pd.DatetimeIndex(d.time.values)
    anom = d[anom_var].values                       # (T, nlat, nlon)
    lat = d.lat.values
    lon = d.lon.values
    nlat, nlon = lat.size, lon.size
    keep = np.array([t.strftime("%Y-%m") != drop_month for t in times])
    A_all = anom[keep]
    dates = times[keep]
    T = A_all.shape[0]
    flat = A_all.reshape(T, -1)
    ocean = np.isfinite(flat).all(axis=0)
    A = flat[:, ocean]
    lat2d = np.broadcast_to(lat[:, None], (nlat, nlon)).reshape(-1)[ocean]
    lon2d = np.broadcast_to(lon[None, :], (nlat, nlon)).reshape(-1)[ocean]
    d.close()
    return LiveField(dates=dates, A=A, cell_lat=lat2d, cell_lon=lon2d)


def _align_to_frozen_cells(field: LiveField, frozen_lat: np.ndarray,
                           frozen_lon: np.ndarray) -> np.ndarray:
    """Column indices into field.A that place the live ocean cells in the
    FROZEN cell order (matched by native lat/lon). Raises if any frozen cell is
    absent from the live field (a dashboard-side QA problem — never silently
    truncate the basis)."""
    key = {(round(float(la), 4), round(float(lo), 4)): i
           for i, (la, lo) in enumerate(zip(field.cell_lat, field.cell_lon))}
    cols = np.empty(len(frozen_lat), dtype=int)
    missing = 0
    for j, (la, lo) in enumerate(zip(frozen_lat, frozen_lon)):
        idx = key.get((round(float(la), 4), round(float(lo), 4)), -1)
        cols[j] = idx
        missing += (idx < 0)
    if missing:
        raise ValueError(
            f"live field is missing {missing} of {len(frozen_lat)} frozen EOF "
            "cells (grid/mask mismatch) — the frozen basis cannot be projected. "
            "Rebuild the live field on the fit-vintage grid/baseline (obl029).")
    return cols


# ---------------------------------------------------------------------------
# 3. Frozen SEBS onset watch
# ---------------------------------------------------------------------------
def sebs_onset_watch_frozen(area_frac_df: pd.DataFrame, field: LiveField,
                            manifest: FrozenManifest,
                            leads: tuple = (1, 2),
                            threshold: float | None = None) -> dict:
    """FROZEN-coefficient SEBS onset watch (operational default).

    Applies the pinned LIM (EOF basis + propagator G1 + zone read-off), the
    pinned isotonic link, the pinned q90 threshold and the pinned per-lead
    warn-above-climatology decision threshold to the LIVE field's origin state
    x0. NOTHING is re-fit: the live field supplies only x0 (its origin anomaly
    projected onto the frozen EOF basis).

    x0 is formed as the last row of the full frozen projection
    Y_live @ V_frozen (Y_live = (A_aligned - mean)*sw, over the frozen cells,
    rows up to the origin month) — the same arithmetic path the fit produced,
    so at the fit vintage x0 == the paper's origin state bit-for-bit.
    """
    fz = manifest.frozen["sebs_onset"]
    arr = manifest.arrays
    df = _prep(area_frac_df)
    okey = _month_key(df["date"].iloc[-1])
    origin_date = pd.Timestamp(df["date"].iloc[-1])

    # --- frozen basis + operators (all pinned) ---
    V = np.asarray(arr["lim_V"], float)              # (M,K)
    mean_ = np.asarray(arr["lim_mean"], float)       # (M,)
    sw = np.asarray(arr["lim_sw"], float)            # (M,)
    fr_lat = np.asarray(arr["lim_cell_lat"], float)
    fr_lon = np.asarray(arr["lim_cell_lon"], float)
    G1 = np.asarray(fz["propagator_G1"], float)      # (K,K)
    a_z = np.asarray(fz["zone_readoff_a_sebs"], float)
    const = float(fz["zone_readoff_const_sebs"])
    thr_raw = float(fz["q90_threshold"])
    Xk = np.asarray(fz["isotonic_link"]["X_thresholds"], float)
    yk = np.asarray(fz["isotonic_link"]["y_thresholds"], float)

    # --- live field origin state x0 (projection onto FROZEN basis) ---
    fkey = np.array([_month_key(d) for d in field.dates])
    tr_mask = fkey <= okey
    if not tr_mask.any():
        raise ValueError("live field has no months at or before the origin")
    if fkey[tr_mask][-1] != okey:
        raise ValueError(
            f"origin month (key {okey}) absent from the live field (last field "
            f"key {int(fkey[tr_mask][-1])}). Truncate area_frac_df to the field's "
            "last month.")
    cols = _align_to_frozen_cells(field, fr_lat, fr_lon)
    A_aligned = field.A[np.ix_(tr_mask, cols)]       # (Ntr, M) frozen-cell order
    Y = (A_aligned - mean_[None, :]) * sw[None, :]
    x0 = (Y @ V)[-1]                                 # full matmul, last row

    out = {
        "zone": "sebs",
        "model": "FROZEN lim_k12 -> pinned isotonic link -> q90 exceedance "
                 "-> warn-above-climatology",
        "path": "frozen",
        "coefficient_vintage": fz["fit_origin_date"],
        "origin_date": str(origin_date.date()),
        "q90_threshold": thr_raw,
        "leads": {},
    }
    for h in leads:
        h = int(h)
        Gh = np.linalg.matrix_power(G1, h)           # from pinned G1
        zm_fc = float(const + a_z @ (Gh @ x0))
        pt = float(_iso_predict(zm_fc, Xk, yk))
        resid = np.asarray(arr[f"onset_resid_l{h}"], float)   # frozen residuals
        prob = (float(np.mean((pt + resid) > thr_raw))
                if len(resid) else float("nan"))
        base_rate = float(fz["decision_thresholds"][f"lead_{h}"]
                          ["paper_default_decision_threshold"])
        dec = float(threshold) if threshold is not None else base_rate
        out["leads"][h] = {
            "target_date": str((origin_date + pd.DateOffset(months=h)).date()),
            "zone_mean_anom_forecast_degC": zm_fc,
            "point_area_frac": pt,
            "onset_prob_q90": prob,
            "decision_threshold": dec,
            "paper_default_threshold": base_rate,
            "watch": ("elevated" if (np.isfinite(prob) and prob >= dec)
                      else "normal"),
        }
    return out


def _iso_predict(x: float, Xk: np.ndarray, yk: np.ndarray) -> float:
    """Reproduce sklearn IsotonicRegression(out_of_bounds='clip').predict on a
    scalar from the frozen (X_thresholds_, y_thresholds_) knots: linear
    interpolation, clipped to the knot range. Rebuilt via scipy.interp1d — the
    same interpolator sklearn stores as f_ — so it matches bit-for-bit."""
    from scipy.interpolate import interp1d
    f = interp1d(Xk, yk, kind="linear", bounds_error=False,
                 fill_value=(yk[0], yk[-1]))
    return float(f(x))
