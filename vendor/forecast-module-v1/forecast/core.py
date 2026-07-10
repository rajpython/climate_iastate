#!/usr/bin/env python3
"""
forecast/core.py — Forward-mode operational forecast wrappers (v1)
===================================================================
Packaging build ONLY. This module introduces NO new science and NO new
equations: every model is imported from the paper-validated Stage-3 code
(scripts/stage3_harness.py, scripts/stage3_lim.py) and run at the latest
available origin instead of inside the rolling-origin scoring loop. The
selftest (forecast/selftest_identity_check.py) proves that, run at the final
hindcast origin on the sealed snapshots, these wrappers reproduce the paper's
rolling-origin records to machine precision.

Validated against (paper v14, LOFRA-accepted):
  * Baselines hindcast: results/stage-3-baselines/oos_long_records.parquet
    (generator scripts/stage3_02_baselines_oos.py)
  * LIM hindcast:       results/stage-3-lim/lim_long_records.parquet
    (generator scripts/stage3_03_lim_oos.py; SEBS onset read-off extracted
    from its main loop, lines ~107-216, forecaster 'lim_k12', detrend=False)

Sealed fit-vintage inputs (validation only — the entry points are
data-agnostic and accept the caller's own live monthly area_frac frame):
  * snap-obl028-predictand-20260701  (per-zone monthly area_frac)
  * snap-obl029-broadfield-20260701  (broad-basin SST anomaly field, LIM state)

Deployment contract (LOFRA-verified against paper v14) is encoded in
DEPLOY_MAP below; run_latest_origin routes by it so a zone cannot be
misrouted to a model the paper did not validate for it.

Author/owner: Metrica. Build date 2026-07-08.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- import the frozen, paper-validated model code (never reimplemented) ---
_PROJ = Path(__file__).resolve().parents[1]
_SCRIPTS = _PROJ / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import stage3_harness as H  # noqa: E402  (DampedPersistence, Climatology, helpers)

FIT_VINTAGE_PREDICTAND = "snap-obl028-predictand-20260701"
FIT_VINTAGE_FIELD = "snap-obl029-broadfield-20260701"

# Harness constants inherited from the paper run (HarnessConfig defaults).
Q_EVENT = 0.90          # occurrence event = exceedance of the train q90
MAXLEAD = 6             # max lead of the paper harness; anchors the onset
                        # threshold window (see stage3_harness.run_zone)
LIM_K_PRIMARY = 12      # paper's a-priori primary EOF truncation
LIM_KS = (8, 10, 12, 15)  # the driver's shared-eig truncation set; kept so the
                        # extracted read-off follows the EXACT numerical path
                        # of stage3_03_lim_oos.py line 127 (build_many)

# ---------------------------------------------------------------------------
# Deployment map — LOFRA-verified against paper v14. Encodes which product is
# validated for which zone. Callers route through run_latest_origin, which
# enforces this map; sebs_onset_watch is SEBS-only by construction.
# ---------------------------------------------------------------------------
DEPLOY_MAP = {
    # magnitude/area point forecast + AR(1) predictive variance + L1 occurrence
    "sebs":       {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": True,  "magnitude_leads": (1, 2, 3), "onset_watch_leads": (1, 2)},
    "nbs":        {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "wgoa":       {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "egoa":       {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "ai_west":    {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "ai_central": {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "ai_east":    {"magnitude_model": "damped_persistence", "occurrence_l1": True,  "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    # climatology-only zones: damped persistence falls below seasonal
    # climatology by L2 in the paper's tables; Beaufort ~80% zeros. Magnitude
    # (area) product only — no occurrence probability, no LIM/onset product.
    "chukchi":    {"magnitude_model": "climatology", "occurrence_l1": False, "onset_watch": False, "magnitude_leads": (1, 2, 3)},
    "beaufort":   {"magnitude_model": "climatology", "occurrence_l1": False, "onset_watch": False, "magnitude_leads": (1, 2, 3)},
}

ZONES = tuple(DEPLOY_MAP.keys())


# ---------------------------------------------------------------------------
# Input validation / preparation
# ---------------------------------------------------------------------------
def _month_key(ts) -> int:
    """Calendar month serial (year*12 + month-1). Same as stage3_03_lim_oos.month_key."""
    ts = pd.Timestamp(ts)
    return ts.year * 12 + (ts.month - 1)


def _prep(area_frac_df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalise the caller's monthly frame.

    Requires columns 'date' and 'area_frac'; a contiguous monthly calendar
    (the AR(1)/persistence lag structure is positional — a gap would corrupt
    phi); and no NaNs in area_frac."""
    if not {"date", "area_frac"}.issubset(area_frac_df.columns):
        raise ValueError("area_frac_df must have columns 'date' and 'area_frac'")
    df = area_frac_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if df["area_frac"].isna().any():
        raise ValueError("area_frac contains NaN — fill or drop before calling")
    keys = df["date"].map(_month_key).to_numpy(int)
    if len(keys) < 2 or (np.diff(keys) != 1).any():
        raise ValueError("date column must be a contiguous monthly calendar "
                         "(the persistence lag structure is positional)")
    df["cal_month"] = df["date"].dt.month
    return df


# ---------------------------------------------------------------------------
# 1. Latest-origin persistence / climatology forecast (per DEPLOY_MAP)
# ---------------------------------------------------------------------------
def run_latest_origin(area_frac_df: pd.DataFrame, zone: str,
                      leads: tuple = (1, 2, 3)) -> dict:
    """VALIDATION / REPLICATION PATH — re-fits coefficients on the caller's
    frame every call. NOT the operational path.

    Use `forecast.frozen.forecast_frozen` for deployment: it applies the pinned,
    paper-validated coefficients and re-estimates NOTHING. This function instead
    RE-FITS phi, sigma_eps, the climatology and the q90 threshold on all supplied
    rows — exactly reproducing the paper's per-origin rolling hindcast (that is
    why the identity check passes bit-for-bit), but run forward monthly it would
    silently re-estimate every coefficient as the live record grows. Keep it for
    reproducing the paper hindcast and for drift-checking the frozen path; do not
    deploy it.

    Fits the paper-validated forecaster for `zone` (per DEPLOY_MAP) on ALL
    supplied data — the exact per-origin fit the rolling-origin hindcast
    performed at each origin, now performed once at the live origin.

    Returns a dict with per-lead:
      * point_area_frac  — point forecast on the area_frac scale (UNCLIPPED,
                           exactly as scored in the paper; may fall slightly
                           outside [0,1] — clip for display only)
      * predictive_variance — damped zones: the h-step stationary-AR(1)
                           forecast-error variance (see note below);
                           climatology zones: the empirical variance of the
                           train h-step residuals (same distribution-free
                           residual set the exceedance mechanism uses)
      * occurrence_prob_q90 — L1 only, damped zones only (per DEPLOY_MAP):
                           distribution-free P(area_frac > train q90) via
                           stage3_harness.exceedance_prob
    """
    if zone not in DEPLOY_MAP:
        raise ValueError(f"unknown zone '{zone}'; valid: {ZONES}")
    spec = DEPLOY_MAP[zone]
    df = _prep(area_frac_df)
    y = df["area_frac"].to_numpy(float)
    train = pd.DataFrame({"area_frac": y, "cal_month": df["cal_month"].to_numpy(int)})

    damped = spec["magnitude_model"] == "damped_persistence"
    if damped:
        fc = H.DampedPersistence().fit(train, "area_frac")
        phi = float(fc.phi)
        # sigma_eps read from the forecaster's own one-step residuals
        # (anom[1:] - phi*anom[:-1] are exactly the fitted AR(1) innovations);
        # mean-square (no ddof), consistent with ar1_phi's through-origin OLS.
        r1 = fc.residuals(1)
        sigma_eps2 = float(np.mean(r1 ** 2))
    else:
        fc = H.Climatology().fit(train, "area_frac")
        phi = None
        sigma_eps2 = None

    thr = H.quantile_threshold(y, Q_EVENT)     # train-only q90 (all data = train)
    origin_date = pd.Timestamp(df["date"].iloc[-1])

    out = {
        "zone": zone,
        "model": spec["magnitude_model"],
        "fit_vintage_note": "coefficients re-fit on the caller-supplied frame; "
                            f"pinned reference vintage = {FIT_VINTAGE_PREDICTAND}",
        "origin_date": str(origin_date.date()),
        "n_train": int(len(y)),
        "phi": phi,
        "sigma_eps": (float(np.sqrt(sigma_eps2)) if sigma_eps2 is not None else None),
        "q90_threshold": thr,
        "leads": {},
    }
    for h in leads:
        h = int(h)
        pt = float(fc.point(h))
        if damped:
            # AR(1) h-step forecast-error variance,
            # Var[y_{t+h}|y_t] = sigma_eps^2 * (1 - phi^(2h)) / (1 - phi^2)
            # (= sigma_eps^2 * sum_{j=0}^{h-1} phi^(2j)) — standard/canonical;
            # the finite-h form of the paper's Eq 7b (which displays its
            # h->inf limit). Source: Hamilton (1994), Time Series Analysis,
            # Ch.4 §4.2 (pp.77-84); OA-verified equivalent Hyndman &
            # Athanasopoulos, Forecasting: Principles and Practice (3rd ed.)
            # §9.8; canonical Brockwell & Davis (2016). Confirmed-in-kind by
            # Cobra 2026-07-08 (handoffs/cobra-to-lofra-ar1-variance-
            # provenance-20260708.md); accepted at metadata-level attribution.
            # Method fingerprint: "AR(1) h-step forecast-error variance;
            # geometric sum of squared MA weights; train-only phi & sigma_eps".
            # phi is clipped to <=0.999 upstream (ar1_phi), so 1-phi^2 > 0.
            var_h = sigma_eps2 * (1.0 - phi ** (2 * h)) / (1.0 - phi ** 2)
            var_label = "ar1_hstep_formula"
        else:
            # Empirical train h-step residual variance (distribution-free; the
            # same residual set the paper's exceedance mechanism draws from).
            # No closed form asserted.
            var_h = float(np.mean(np.asarray(fc.residuals(h), float) ** 2))
            var_label = "empirical_train_residual_variance"
        entry = {
            "target_date": str((origin_date + pd.DateOffset(months=h)).date()),
            "point_area_frac": pt,
            "predictive_variance": float(var_h),
            "predictive_variance_kind": var_label,
        }
        if h == 1 and spec["occurrence_l1"]:
            entry["occurrence_prob_q90"] = float(
                H.exceedance_prob(pt, fc.residuals(1), thr))
        out["leads"][h] = entry
    return out


# ---------------------------------------------------------------------------
# 2. SEBS onset watch — the LIM -> isotonic -> exceedance read-off, extracted
#    verbatim from scripts/stage3_03_lim_oos.py (main loop, non-detrended,
#    forecaster lim_k12). Numerics unchanged; only the rolling loop removed.
# ---------------------------------------------------------------------------
def load_default_field():
    """Load the sealed broad-basin field state (snap-obl029) via the frozen
    stage3_lim loader. Heavy (~380 MB NetCDF); cached module-level."""
    import stage3_lim as L
    return L.load_field()


def sebs_onset_watch(area_frac_df: pd.DataFrame, field=None,
                     leads: tuple = (1, 2), threshold: float | None = None) -> dict:
    """VALIDATION / REPLICATION PATH — re-fits the LIM, the isotonic link and
    the thresholds on the caller's frame/field every call. NOT the operational
    path.

    Use `forecast.frozen.sebs_onset_watch_frozen` for deployment: it applies the
    pinned LIM propagator, EOF basis, isotonic link and thresholds and re-fits
    NOTHING (the live field supplies only the origin state x0). This function
    instead RE-FITS the whole LIM (build_many), the isotonic link and the q90 /
    decision thresholds — reproducing the paper hindcast bit-for-bit, but not for
    forward deployment.

    Two-state SEBS MHW onset watch ('elevated' / 'normal') at the latest
    common origin of the area_frac frame and the broad-basin field.

    Pipeline (extracted from stage3_03_lim_oos.py; numerics identical):
      LIM (K=12, shared-eig path of build_many with Ks=(8,10,12,15), exactly
      the driver's lim_k12) fit on field months <= origin
      -> zone-mean anomaly forecast at lead h
      -> TRAIN-ONLY isotonic link (sklearn IsotonicRegression, increasing,
         out_of_bounds='clip') zone-mean anomaly -> observed area_frac
      -> distribution-free exceedance probability vs the train q90 threshold
      -> watch state: 'elevated' iff prob >= decision threshold.

    `threshold`: decision threshold on the onset probability. Default None =
    the paper operating point ("warn above climatology"): the train-only
    climatological q90-occurrence base rate, anchored MAXLEAD months before
    the target (per-lead, identical to the hindcast's onset_decision_p).
    Pass a float to override for all leads.

    `field`: a stage3_lim.FieldState (default: sealed snap-obl029 via
    load_default_field()). The LAST month of area_frac_df must be present in
    the field (the LIM origin state) — truncate the frame to the field's last
    month if your area_frac vintage leads the field vintage.

    SEBS only — other zones have no validated LIM/onset product (DEPLOY_MAP).
    """
    from sklearn.isotonic import IsotonicRegression
    import stage3_lim as L

    df = _prep(area_frac_df)
    y = df["area_frac"].to_numpy(float)
    k = len(df) - 1                               # origin row index
    okey = _month_key(df["date"].iloc[k])

    if field is None:
        field = load_default_field()
    field_key = np.array([_month_key(d) for d in field.dates])
    tr_mask = field_key <= okey
    if not tr_mask.any():
        raise ValueError("field contains no months at or before the origin")
    A_tr = field.A[tr_mask]
    dates_tr = field.dates[tr_mask]
    tr_keys = field_key[tr_mask]
    if tr_keys[-1] != okey:
        raise ValueError(
            f"origin month (key {okey}) absent from the field (last field key "
            f"{tr_keys[-1]}). Truncate area_frac_df to the field's last month.")

    # LIM fit — EXACT driver path (stage3_03 line 127): shared-eig build_many
    # over the full truncation set, primary K selected. Keeps bitwise identity
    # with the hindcast lim_k12 records.
    fit = L.build_many(A_tr, field.sw, dates_tr, field.zone_cw, LIM_KS)[LIM_K_PRIMARY]
    x0 = fit.X_[-1]                               # origin state

    # map field-train rows to predictand rows (contemporaneous), as the driver
    cal_key = df["date"].map(_month_key).to_numpy(int)
    key_to_row = {int(kk): i for i, kk in enumerate(cal_key)}
    tr_rows_pred = np.array([key_to_row.get(int(kk), -1) for kk in tr_keys])
    valid_tr = tr_rows_pred >= 0

    # train-only isotonic link: reduced-rank zone-mean anomaly -> area_frac
    zm_tr = fit.zone_mean_series("sebs")
    link = IsotonicRegression(increasing=True, out_of_bounds="clip")
    link.fit(zm_tr[valid_tr], y[tr_rows_pred[valid_tr]])

    thr_raw = H.quantile_threshold(y[:k + 1], Q_EVENT)   # train q90 (all data)
    origin_date = pd.Timestamp(df["date"].iloc[k])

    out = {
        "zone": "sebs",
        "model": f"lim_k{LIM_K_PRIMARY} -> isotonic link -> q90 exceedance "
                 "(extracted from stage3_03_lim_oos.py)",
        "origin_date": str(origin_date.date()),
        "n_train_predictand": int(len(y)),
        "n_train_field": int(tr_mask.sum()),
        "q90_threshold": float(thr_raw),
        "decision_threshold_mode": ("caller-override" if threshold is not None
                                    else "paper default: warn-above-climatology "
                                         "(train q90-occurrence base rate, "
                                         f"anchored {MAXLEAD} months pre-target)"),
        "leads": {},
    }
    for h in leads:
        h = int(h)
        # per-lead residual set: field-train rows whose h-step-ahead predictand
        # row exists AND is in-train (row <= k) — identical to valid_by_h in
        # the driver (leakage-free)
        tgt_rows = np.array([key_to_row.get(int(kk) + h, -1) for kk in tr_keys])
        vh = (tgt_rows >= 0) & (tgt_rows <= k)
        zm_fc = fit.zone_mean_forecast("sebs", x0, h)
        pt = float(link.predict([zm_fc])[0])
        zmf_all = fit.const_z["sebs"] + (fit.X_[vh] @ fit.Gpow(h).T) @ fit.a_z["sebs"]
        if len(zmf_all):
            resid = y[tgt_rows[vh]] - link.predict(zmf_all)
            prob = float(H.exceedance_prob(pt, resid, thr_raw))
        else:
            prob = float("nan")
        # paper operating point: train base rate anchored MAXLEAD months
        # before the target month (identical to the hindcast onset_decision_p)
        istart = k + h - MAXLEAD
        thr_s = H.quantile_threshold(y[:istart + 1], Q_EVENT)
        base_rate = float((y[:istart + 1] > thr_s).mean())
        dec = float(threshold) if threshold is not None else base_rate
        out["leads"][h] = {
            "target_date": str((origin_date + pd.DateOffset(months=h)).date()),
            "zone_mean_anom_forecast_degC": float(zm_fc),
            "point_area_frac": pt,
            "onset_prob_q90": prob,
            "decision_threshold": dec,
            "paper_default_threshold": base_rate,
            "watch": ("elevated" if (np.isfinite(prob) and prob >= dec) else "normal"),
        }
    return out
