#!/usr/bin/env python3
"""
stage3_harness.py — Leakage-free out-of-sample / verification harness
=====================================================================
Reusable module for the sst-forecast-method-review Stage-3 build. It is the
YARDSTICK every later model (LIM, hurdle/beta, VAR-in-EOF) must plug into and
beat. This file carries NO project-specific driver logic; it is the library.
The baseline driver is scripts/stage3_02_baselines_oos.py.

Design (governed by metrica-to-lofra-stage3-modeling-strategy-20260701.md §C.2):
  * Rolling-origin / EXPANDING-window chronological hold-out. NO random split
    (the monthly series are autocorrelated -> a random split leaks).
  * ALL calibration (seasonal climatology, linear trend, AR(1) phi, PNT alpha,
    the q90 exceedance threshold, the event base rate) is estimated on the
    TRAINING window ONLY, RE-ESTIMATED every origin. This is the load-bearing
    leakage control given the ~2014 regime: no post-origin information — not
    the threshold, not the climatology, not the trend — ever touches a forecast.
  * Detrend/de-regime is done fold-wise on training data (linear trend fit on
    train, extrapolated to the target).
  * Skill is scored deterministically (RMSE/MAE/ACC/MSSS) and probabilistically
    (Brier + Murphy decomposition, BSS, SEDI, ROC/AUC, reliability) against BOTH
    the climatology and the (damped-)persistence benchmark.

Forecaster contract (so LIM/hurdle plug into the SAME harness later):
    A forecaster is fit on a training frame and then, for a fixed origin (the
    last training row) and a lead h, exposes
        .point(h)      -> float         point forecast on the modelled scale
        .residuals(h)  -> np.ndarray    training h-step forecast errors
                                        (obs - forecast), used to build the
                                        distribution-free predictive
                                        distribution for exceedance probability
    Any object implementing .fit(train_df) and returning point/residuals via the
    Forecaster ABC below is harness-compatible.

Author/owner: Metrica.  Run via the project venv; save, never inline-only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Callable

# --------------------------------------------------------------------------
# 1. Data loading (from the SEALED snapshot — read-only)
# --------------------------------------------------------------------------
ZONES = ["sebs", "nbs", "wgoa", "egoa",
         "ai_west", "ai_central", "ai_east", "chukchi", "beaufort"]
ARCTIC_WEAK = {"chukchi", "beaufort"}          # weak-signal, per diagnostics
GOA_AI_PRIMARY = {"wgoa", "egoa", "ai_west", "ai_central", "ai_east"}

def load_zone_monthly(snapshot_outputs: str, zone: str) -> pd.DataFrame:
    """Load one zone's monthly predictand from the sealed snapshot outputs dir.
    Returns date-sorted frame with an integer month index t = 0..N-1."""
    import os
    df = pd.read_csv(os.path.join(snapshot_outputs, f"{zone}_monthly.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["t"] = np.arange(len(df))
    df["cal_month"] = df["date"].dt.month
    return df


# --------------------------------------------------------------------------
# 2. Calibration helpers — ALL take TRAIN-ONLY arrays
# --------------------------------------------------------------------------
def seasonal_climatology(y: np.ndarray, cal_month: np.ndarray) -> np.ndarray:
    """Return length-12 array clim[m-1] = train mean of y for calendar month m."""
    clim = np.full(12, np.nan)
    for m in range(1, 13):
        sel = cal_month == m
        if sel.any():
            clim[m - 1] = y[sel].mean()
    # fill any empty month with global mean (robustness; rare on 20yr+ train)
    if np.isnan(clim).any():
        clim[np.isnan(clim)] = np.nanmean(y)
    return clim

def linear_trend(y: np.ndarray, t: np.ndarray) -> tuple[float, float]:
    """OLS y = a + b*t on train; returns (a, b). Used for fold-wise detrend."""
    A = np.column_stack([np.ones_like(t, dtype=float), t.astype(float)])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(coef[0]), float(coef[1])

def ar1_phi(anom: np.ndarray) -> float:
    """AR(1) coefficient of the (mean-zero) anomaly via lag-1 OLS through origin.
    Clipped to [0, 0.999] for a stable damped-persistence decay."""
    x0, x1 = anom[:-1], anom[1:]
    denom = np.dot(x0, x0)
    if denom <= 0:
        return 0.0
    phi = float(np.dot(x0, x1) / denom)
    return float(np.clip(phi, 0.0, 0.999))

def quantile_threshold(y: np.ndarray, q: float = 0.90) -> float:
    return float(np.quantile(y, q))


# --------------------------------------------------------------------------
# 3. Forecasters (baselines). Each implements .fit / .point / .residuals
# --------------------------------------------------------------------------
class Forecaster:
    """ABC. LIM / hurdle / beta models implement this same interface later."""
    name = "abstract"
    raw_only = False   # True => defined only on the non-negative raw series
    def fit(self, train: pd.DataFrame, ycol: str) -> "Forecaster":
        raise NotImplementedError
    def point(self, h: int) -> float:
        raise NotImplementedError
    def residuals(self, h: int) -> np.ndarray:
        raise NotImplementedError


class Climatology(Forecaster):
    """Per-zone SEASONAL climatology, train-window only. Forecast = clim(target
    calendar month). Reference benchmark #1."""
    name = "climatology"
    def fit(self, train, ycol):
        self.y = train[ycol].to_numpy(float)
        self.cm = train["cal_month"].to_numpy(int)
        self.origin_month = int(self.cm[-1])
        self.clim = seasonal_climatology(self.y, self.cm)
        return self
    def _target_month(self, h):
        return (self.origin_month - 1 + h) % 12 + 1
    def point(self, h):
        return float(self.clim[self._target_month(h) - 1])
    def residuals(self, h):
        # training h-step errors of the climatology forecast
        anom = self.y - self.clim[self.cm - 1]
        return anom[h:]                     # obs - clim(target month) = anomaly


class Persistence(Forecaster):
    """LAST-OBSERVED ANOMALY carried forward (field-standard anomaly
    persistence). Forecast = clim(target month) + anomaly(origin). Reference
    benchmark #2 (undamped)."""
    name = "persistence"
    def fit(self, train, ycol):
        self.y = train[ycol].to_numpy(float)
        self.cm = train["cal_month"].to_numpy(int)
        self.origin_month = int(self.cm[-1])
        self.clim = seasonal_climatology(self.y, self.cm)
        self.anom = self.y - self.clim[self.cm - 1]
        self.a_origin = float(self.anom[-1])
        return self
    def _target_month(self, h):
        return (self.origin_month - 1 + h) % 12 + 1
    def point(self, h):
        return float(self.clim[self._target_month(h) - 1] + self.a_origin)
    def residuals(self, h):
        # obs_{t+h} - [clim(target) + anom_t]  == anom_{t+h} - anom_t
        return self.anom[h:] - self.anom[:-h]


class DampedPersistence(Forecaster):
    """AR(1)-damped anomaly persistence. Forecast = clim(target) + phi^h *
    anomaly(origin), phi RE-ESTIMATED per fold. The field's strong high-latitude
    benchmark (Smith & Spillman 2024; McAdam 2023)."""
    name = "damped_persistence"
    def fit(self, train, ycol):
        self.y = train[ycol].to_numpy(float)
        self.cm = train["cal_month"].to_numpy(int)
        self.origin_month = int(self.cm[-1])
        self.clim = seasonal_climatology(self.y, self.cm)
        self.anom = self.y - self.clim[self.cm - 1]
        self.a_origin = float(self.anom[-1])
        self.phi = ar1_phi(self.anom)
        return self
    def _target_month(self, h):
        return (self.origin_month - 1 + h) % 12 + 1
    def point(self, h):
        return float(self.clim[self._target_month(h) - 1]
                     + (self.phi ** h) * self.a_origin)
    def residuals(self, h):
        return self.anom[h:] - (self.phi ** h) * self.anom[:-h]


class PNTPersistence(Forecaster):
    """Lee & Tzeng (2012) Persistence Neutralization Transformation — ADAPTATION.

    EXACT PNT transform (their Eq.): z(t) = (y(t)+m) / (y(t-tau)+m)^alpha, with
    tau = lead h (so the anchor y(t-tau)=y(origin) is always observed) and
    alpha in [0,1] selected on TRAIN by minimizing the RMSE of the power-damped
    persistence forecast  yhat_dp(t) = (y(t-tau)+m)^alpha - m  against obs
    (exactly the paper's alpha-selection rule).

    STATED DEVIATION from Lee & Tzeng (2012) (labeled per exact-method-labeling):
      (i)  the paper feeds PNT-transformed variables into a MULTIVARIATE LINEAR
           REGRESSION on 48 atmospheric/SST predictors; at the BASELINE stage we
           have NO external predictors, so the neutralized-space forecast zhat is
           a TRAIN climatology of z by target calendar month (the seasonal
           expectation in neutralized space) rather than an MLR fit;
      (ii) target is a bounded, zero-inflated area fraction, not tropical SST
           anomaly — hence the positive offset m (=max(train mean, 0.01)) is
           load-bearing (zeros make the ratio undefined without it).
    Consequently the paper's ">= damped persistence" GUARANTEE (which is proven
    for the MLR-on-PNT setup) is NOT asserted here; we report the empirical
    comparison instead. Forecast: yhat = zhat * (y_origin+m)^alpha - m.
    When zhat == 1 this reduces exactly to the power-damped persistence.
    """
    name = "pnt_persistence"
    raw_only = True    # ratio transform requires a NON-NEGATIVE series
    def __init__(self, alpha_grid=None):
        self.alpha_grid = (np.linspace(0.0, 1.0, 41)
                           if alpha_grid is None else np.asarray(alpha_grid))
    def fit(self, train, ycol):
        self.y = train[ycol].to_numpy(float)
        self.cm = train["cal_month"].to_numpy(int)
        self.origin_month = int(self.cm[-1])
        self.y_origin = float(self.y[-1])
        self.m = max(float(self.y.mean()), 0.01)   # positive offset for zeros
        self._alpha = {}          # per-lead alpha
        self._zclim = {}          # per-lead length-12 z-climatology
        self._resid = {}          # per-lead training errors
        return self
    def _target_month(self, h):
        return (self.origin_month - 1 + h) % 12 + 1
    def _prep_lead(self, h):
        if h in self._alpha:
            return
        y, m = self.y, self.m
        anchor = y[:-h] + m            # y(t-tau)+m, tau=h
        target = y[h:]                 # y(t)
        tmonth = self.cm[h:]           # calendar month of target
        # alpha: minimize RMSE of power-damped persistence vs obs (paper's rule)
        best_a, best_rmse = 0.0, np.inf
        for a in self.alpha_grid:
            dp = anchor ** a - m
            rmse = np.sqrt(np.mean((target - dp) ** 2))
            if rmse < best_rmse:
                best_rmse, best_a = rmse, a
        # PNT-transformed variable z(t) = (y(t)+m)/(y(t-tau)+m)^alpha
        z = (target + m) / (anchor ** best_a)
        zclim = np.full(12, np.nan)
        for mm in range(1, 13):
            sel = tmonth == mm
            if sel.any():
                zclim[mm - 1] = z[sel].mean()
        if np.isnan(zclim).any():
            zclim[np.isnan(zclim)] = np.nanmean(z)
        # training residuals of the PNT forecast (leakage-free, in-train)
        fcst = zclim[tmonth - 1] * (anchor ** best_a) - m
        self._alpha[h] = best_a
        self._zclim[h] = zclim
        self._resid[h] = target - fcst
    def point(self, h):
        self._prep_lead(h)
        a = self._alpha[h]
        zc = self._zclim[h][self._target_month(h) - 1]
        return float(zc * (self.y_origin + self.m) ** a - self.m)
    def residuals(self, h):
        self._prep_lead(h)
        return self._resid[h]


# --------------------------------------------------------------------------
# 4. Verification metrics
# --------------------------------------------------------------------------
def det_scores(obs: np.ndarray, fc: np.ndarray, clim_ref: np.ndarray,
               pers_ref: np.ndarray) -> dict:
    """Deterministic skill. MSSS vs BOTH climatology and persistence.
    ACC = correlation of forecast anomaly vs obs anomaly (anomaly = obs-clim_ref)."""
    obs, fc = np.asarray(obs, float), np.asarray(fc, float)
    err = fc - obs
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    mse = float(np.mean(err ** 2))
    mse_clim = float(np.mean((clim_ref - obs) ** 2))
    mse_pers = float(np.mean((pers_ref - obs) ** 2))
    msss_clim = 1.0 - mse / mse_clim if mse_clim > 0 else np.nan
    msss_pers = 1.0 - mse / mse_pers if mse_pers > 0 else np.nan
    # anomaly correlation (obs & forecast anomalies wrt the climatology ref)
    oa, fa = obs - clim_ref, fc - clim_ref
    if oa.std() > 0 and fa.std() > 0:
        acc = float(np.corrcoef(oa, fa)[0, 1])
    else:
        acc = np.nan
    return dict(n=len(obs), rmse=rmse, mae=mae, mse=mse,
                msss_clim=msss_clim, msss_pers=msss_pers, acc=acc)

def brier_decomposition(prob: np.ndarray, event: np.ndarray, nbins: int = 10):
    """Murphy (1973) decomposition BS = REL - RES + UNC (equal-width bins)."""
    prob = np.asarray(prob, float); event = np.asarray(event, float)
    n = len(event); obar = event.mean()
    bs = float(np.mean((prob - event) ** 2))
    edges = np.linspace(0.0, 1.0, nbins + 1)
    idx = np.clip(np.digitize(prob, edges[1:-1]), 0, nbins - 1)
    rel = res = 0.0
    bins = []
    for k in range(nbins):
        sel = idx == k
        nk = int(sel.sum())
        if nk == 0:
            continue
        pk = prob[sel].mean(); ok = event[sel].mean()
        rel += nk * (pk - ok) ** 2
        res += nk * (ok - obar) ** 2
        bins.append(dict(bin=k, n=nk, p_mean=float(pk), o_freq=float(ok)))
    rel /= n; res /= n; unc = float(obar * (1 - obar))
    return dict(brier=bs, reliability=float(rel), resolution=float(res),
                uncertainty=unc, base_rate=float(obar), rel_bins=bins)

def brier_skill_score(prob, event, prob_ref):
    prob = np.asarray(prob, float); event = np.asarray(event, float)
    bs = np.mean((prob - event) ** 2)
    bs_ref = np.mean((np.asarray(prob_ref, float) - event) ** 2)
    return float(1.0 - bs / bs_ref) if bs_ref > 0 else np.nan

def sedi(prob, event, decision_p):
    """Symmetric Extremal Dependence Index (Ferro & Stephenson 2011) at a
    probability decision threshold. Robust to base rate for rare events."""
    fc = (np.asarray(prob, float) >= decision_p).astype(int)
    ev = np.asarray(event, int)
    H = TP = int(((fc == 1) & (ev == 1)).sum())
    FP = int(((fc == 1) & (ev == 0)).sum())
    FN = int(((fc == 0) & (ev == 1)).sum())
    TN = int(((fc == 0) & (ev == 0)).sum())
    nP = TP + FN; nN = FP + TN
    if nP == 0 or nN == 0:
        return np.nan
    h = TP / nP; f = FP / nN
    eps = 1e-6
    h = min(max(h, eps), 1 - eps); f = min(max(f, eps), 1 - eps)
    num = (np.log(f) - np.log(h) - np.log(1 - f) + np.log(1 - h))
    den = (np.log(f) + np.log(h) + np.log(1 - f) + np.log(1 - h))
    return float(num / den) if den != 0 else np.nan

def roc_auc(prob, event):
    from sklearn.metrics import roc_auc_score
    ev = np.asarray(event, int)
    if ev.min() == ev.max():
        return np.nan
    return float(roc_auc_score(ev, np.asarray(prob, float)))


# --------------------------------------------------------------------------
# 5. Expanding-window OOS driver
# --------------------------------------------------------------------------
def exceedance_prob(point: float, resid: np.ndarray, thr: float) -> float:
    """Distribution-free predictive exceedance probability:
    P(Y > thr) ~ fraction of (point + training residuals) exceeding thr.
    Respects skew / zero-inflation (no Gaussian tail assumption)."""
    return float(np.mean((point + resid) > thr))


@dataclass
class HarnessConfig:
    min_train_years: int = 20          # expanding-window seed
    leads: tuple = (1, 2, 3, 6)        # months
    q_event: float = 0.90              # exceedance-event quantile
    split_year: int = 2014             # pre/post regime stratification
    detrend_modes: tuple = (False, True)


def run_zone(df: pd.DataFrame, zone: str, cfg: HarnessConfig,
             forecaster_factories: dict[str, Callable[[], Forecaster]]) -> pd.DataFrame:
    """Run the full expanding-window OOS for one zone. Returns a long
    per-(target,forecaster,lead,detrend) record frame with point forecast,
    obs, exceedance probability (raw scale only) and the binary event."""
    y_all = df["area_frac"].to_numpy(float)
    t_all = df["t"].to_numpy(int)
    cm_all = df["cal_month"].to_numpy(int)
    dates = df["date"].to_numpy()
    n = len(df)
    seed = cfg.min_train_years * 12
    maxlead = max(cfg.leads)
    records = []

    for k in range(seed - 1, n - 1):            # origin index (last train row)
        origin_t = k
        # thresholds & event base rate — TRAIN ONLY, per origin
        thr = quantile_threshold(y_all[:k + 1], cfg.q_event)

        for detrend in cfg.detrend_modes:
            # fold-wise detrend on TRAIN, extrapolated to targets
            if detrend:
                a, b = linear_trend(y_all[:k + 1], t_all[:k + 1])
                trend_all = a + b * t_all
                ys = y_all - trend_all          # detrended series (all indices)
            else:
                ys = y_all
            train = pd.DataFrame({"area_frac_s": ys[:k + 1],
                                  "cal_month": cm_all[:k + 1]})
            # fit each forecaster once on this train window; raw-only
            # forecasters (e.g. PNT) are undefined on a signed detrended series
            fits = {}
            for fname, factory in forecaster_factories.items():
                obj = factory()
                if detrend and getattr(obj, "raw_only", False):
                    continue
                fits[fname] = obj.fit(train, "area_frac_s")

            for h in cfg.leads:
                tgt = k + h
                if tgt >= n:
                    continue
                obs_s = float(ys[tgt])           # obs on modelled scale
                obs_raw = float(y_all[tgt])
                event = int(y_all[tgt] > thr)    # occurrence on RAW area_frac
                # ONSET calendar — ONE stable, out-of-sample label per target so
                # leads are directly comparable (anticipation). Anchored on the
                # DEEPEST-lead threshold: q90 of data up to (target - maxlead),
                # which is out-of-sample for EVERY lead scored here.
                istart = tgt - maxlead
                thr_s = quantile_threshold(y_all[:istart + 1], cfg.q_event)
                base_rate_s = float((y_all[:istart + 1] > thr_s).mean())
                event_s = int(y_all[tgt] > thr_s)
                event_prev_s = int(y_all[tgt - 1] > thr_s)   # month before target
                at_risk = int(event_prev_s == 0)             # quiescent prior mo
                onset = int(event_s == 1 and event_prev_s == 0)  # 0->1 transition
                tgt_date = dates[tgt]
                yr = pd.Timestamp(tgt_date).year
                for fname, fc in fits.items():
                    pt = fc.point(h)
                    rec = dict(zone=zone, forecaster=fname, lead=h,
                               detrend=detrend, origin_date=dates[origin_t],
                               target_date=tgt_date, target_year=yr,
                               obs=obs_s, fcst=pt)
                    if not detrend:
                        # probabilistic (raw scale, physical event) only
                        resid = fc.residuals(h)
                        rec["prob"] = exceedance_prob(pt, resid, thr)
                        rec["event"] = event
                        rec["at_risk"] = at_risk
                        rec["onset"] = onset
                        rec["onset_decision_p"] = base_rate_s  # warn-above-clim
                        rec["obs_raw"] = obs_raw
                    records.append(rec)
    return pd.DataFrame.from_records(records)


def deterministic_table(long_df: pd.DataFrame, cfg: HarnessConfig) -> pd.DataFrame:
    """Aggregate deterministic skill by (zone, forecaster, lead, detrend, stratum),
    with climatology & persistence references aligned per (target)."""
    rows = []
    strata = [("all", None),
              (f"pre{cfg.split_year}", lambda y: y < cfg.split_year),
              (f"post{cfg.split_year}", lambda y: y >= cfg.split_year)]
    for (zone, lead, detrend), g in long_df.groupby(["zone", "lead", "detrend"]):
        wide = g.pivot_table(index="target_date", columns="forecaster",
                             values="fcst", aggfunc="first")
        obs = g.pivot_table(index="target_date", columns="forecaster",
                            values="obs", aggfunc="first").iloc[:, 0]
        yrs = pd.to_datetime(wide.index).year
        clim_ref = wide["climatology"].to_numpy(float)
        pers_ref = wide["persistence"].to_numpy(float)
        for sname, sfun in strata:
            mask = np.ones(len(wide), bool) if sfun is None else sfun(yrs)
            if mask.sum() < 12:
                continue
            for fname in wide.columns:
                sc = det_scores(obs.to_numpy(float)[mask],
                                wide[fname].to_numpy(float)[mask],
                                clim_ref[mask], pers_ref[mask])
                rows.append(dict(zone=zone, forecaster=fname, lead=lead,
                                 detrend=detrend, stratum=sname, **sc))
    return pd.DataFrame(rows)


def probabilistic_table(long_df: pd.DataFrame, cfg: HarnessConfig):
    """Aggregate probabilistic skill (raw scale only) by
    (zone, forecaster, lead, stratum). BSS vs climatology AND persistence."""
    rows, rel_records = [], []
    raw = long_df[~long_df["detrend"]].copy()
    strata = [("all", None),
              (f"pre{cfg.split_year}", lambda y: y < cfg.split_year),
              (f"post{cfg.split_year}", lambda y: y >= cfg.split_year)]
    for (zone, lead), g in raw.groupby(["zone", "lead"]):
        probw = g.pivot_table(index="target_date", columns="forecaster",
                              values="prob", aggfunc="first")
        evt = g.pivot_table(index="target_date", columns="forecaster",
                            values="event", aggfunc="first").iloc[:, 0].to_numpy(int)
        yrs = pd.to_datetime(probw.index).year
        ref_clim = probw["climatology"].to_numpy(float)
        ref_pers = probw["persistence"].to_numpy(float)
        for sname, sfun in strata:
            mask = np.ones(len(probw), bool) if sfun is None else sfun(yrs)
            if mask.sum() < 12 or evt[mask].sum() == 0:
                continue
            for fname in probw.columns:
                p = probw[fname].to_numpy(float)[mask]
                e = evt[mask]
                dec = brier_decomposition(p, e)
                row = dict(zone=zone, forecaster=fname, lead=lead, stratum=sname,
                           n=int(mask.sum()),
                           brier=dec["brier"], reliability=dec["reliability"],
                           resolution=dec["resolution"], uncertainty=dec["uncertainty"],
                           base_rate=dec["base_rate"],
                           bss_clim=brier_skill_score(p, e, ref_clim[mask]),
                           bss_pers=brier_skill_score(p, e, ref_pers[mask]),
                           sedi_climrate=sedi(p, e, dec["base_rate"]),
                           sedi_p50=sedi(p, e, 0.5),
                           auc=roc_auc(p, e))
                rows.append(row)
                if sname == "all":
                    for b in dec["rel_bins"]:
                        rel_records.append(dict(zone=zone, forecaster=fname,
                                                lead=lead, **b))
    return pd.DataFrame(rows), pd.DataFrame(rel_records)


# --------------------------------------------------------------------------
# 6. ONSET early-warning dimension (SDL-021, utility target #3)
# --------------------------------------------------------------------------
# Manager question: when the system is currently QUIESCENT, can a method warn
# that an MHW is about to START, how early, and at what false-alarm cost?
#
# Design (Metrica-owned; leakage-free; inherited by LIM/hurdle/dynamical):
#   * Onset event  = a 0->1 transition INTO the q90-occurrence state, on ONE
#     stable OUT-OF-SAMPLE threshold anchored maxlead months before the target
#     (so every lead scores the SAME onset calendar; see run_zone).
#   * At-risk set  = target months whose prior month was quiescent (onset
#     possible). Restricting discrimination to at-risk months SEPARATES onset
#     skill from ongoing-event persistence (which trivially "detects" an event
#     that already started).
#   * Score        = the forecaster's occurrence probability P(area_frac>q90).
#   * Decision rule (deterministic warning) = warn iff prob >= the climatological
#     occurrence rate (~0.10, train-only) — "warn above climatology".
#
# Two products:
#   (A) onset DISCRIMINATION per (zone,forecaster,lead): AUC (threshold-free
#       headline) + POD/POFD/FAR/SEDI at the warn-above-clim rule, on at-risk mo.
#   (B) ANTICIPATION per (zone,forecaster): lead-time-to-detection. For each
#       observed onset, the SUSTAINED lead = the largest H such that a warning
#       is issued at EVERY lead 1..H (a continuous warning as the event nears),
#       plus the fraction of onsets flagged at each individual lead.

def _contingency(warn, event):
    warn = np.asarray(warn, int); event = np.asarray(event, int)
    TP = int(((warn == 1) & (event == 1)).sum())
    FP = int(((warn == 1) & (event == 0)).sum())
    FN = int(((warn == 0) & (event == 1)).sum())
    TN = int(((warn == 0) & (event == 0)).sum())
    nP, nN = TP + FN, FP + TN
    pod = TP / nP if nP else np.nan            # hit rate / probability of detection
    pofd = FP / nN if nN else np.nan           # false-alarm RATE (of non-onsets)
    far = FP / (TP + FP) if (TP + FP) else np.nan   # false-alarm RATIO (of warnings)
    return dict(TP=TP, FP=FP, FN=FN, TN=TN, n_onset=nP, n_nononset=nN,
                pod=pod, pofd=pofd, far=far)

def onset_discrimination_table(long_df: pd.DataFrame, cfg: HarnessConfig) -> pd.DataFrame:
    """Product (A): onset discrimination on the AT-RISK subset, per
    (zone, forecaster, lead, stratum)."""
    raw = long_df[~long_df["detrend"]].copy()
    raw = raw[raw["at_risk"] == 1]                     # quiescent prior month
    strata = [("all", None),
              (f"pre{cfg.split_year}", lambda y: y < cfg.split_year),
              (f"post{cfg.split_year}", lambda y: y >= cfg.split_year)]
    rows = []
    for (zone, fname, lead), g in raw.groupby(["zone", "forecaster", "lead"]):
        yrs = g["target_year"].to_numpy(int)
        for sname, sfun in strata:
            m = np.ones(len(g), bool) if sfun is None else sfun(yrs)
            gg = g[m]
            if len(gg) < 12 or gg["onset"].sum() == 0:
                continue
            p = gg["prob"].to_numpy(float)
            ev = gg["onset"].to_numpy(int)
            warn = (p >= gg["onset_decision_p"].to_numpy(float)).astype(int)
            ct = _contingency(warn, ev)
            rows.append(dict(zone=zone, forecaster=fname, lead=lead, stratum=sname,
                             n_at_risk=int(len(gg)), n_onset=int(ev.sum()),
                             onset_rate=float(ev.mean()),
                             onset_auc=roc_auc(p, ev),
                             pod=ct["pod"], pofd=ct["pofd"], far=ct["far"],
                             sedi=sedi(p, ev, float(gg["onset_decision_p"].mean()))))
    return pd.DataFrame(rows)

def anticipation_table(long_df: pd.DataFrame, cfg: HarnessConfig):
    """Product (B): lead-time-to-detection. Returns
    (summary per zone,forecaster; POD-of-onset per zone,forecaster,lead)."""
    raw = long_df[~long_df["detrend"]].copy()
    leads = sorted(cfg.leads)
    summ, podlead = [], []
    for (zone, fname), g in raw.groupby(["zone", "forecaster"]):
        g = g.copy()
        g["warn"] = (g["prob"].to_numpy(float)
                     >= g["onset_decision_p"].to_numpy(float)).astype(int)
        warnw = g.pivot_table(index="target_date", columns="lead",
                              values="warn", aggfunc="first")
        onsetw = g.pivot_table(index="target_date", columns="lead",
                               values="onset", aggfunc="first")
        # observed onsets = target months flagged onset (lead-invariant calendar)
        is_onset = (onsetw.max(axis=1) == 1)
        onset_targets = warnw.index[is_onset]
        if len(onset_targets) == 0:
            continue
        sustained = []
        pod_by_lead = {h: [] for h in leads}
        for tgt in onset_targets:
            wrow = warnw.loc[tgt]
            for h in leads:
                if h in wrow.index and not np.isnan(wrow[h]):
                    pod_by_lead[h].append(int(wrow[h]))
            # sustained lead = largest H with warn at every lead 1..H present
            H = 0
            for h in leads:
                if h in wrow.index and wrow.get(h, np.nan) == 1:
                    H = h
                else:
                    break
            sustained.append(H)
        sustained = np.array(sustained, float)
        summ.append(dict(zone=zone, forecaster=fname, n_onsets=len(onset_targets),
                         mean_sustained_lead=float(np.mean(sustained)),
                         median_sustained_lead=float(np.median(sustained)),
                         frac_warned_ge1=float(np.mean(sustained >= 1)),
                         frac_warned_ge2=float(np.mean(sustained >= 2)),
                         frac_warned_ge3=float(np.mean(sustained >= 3))))
        for h in leads:
            v = pod_by_lead[h]
            podlead.append(dict(zone=zone, forecaster=fname, lead=h,
                                n_onset=len(v),
                                pod_onset=float(np.mean(v)) if v else np.nan))
    return pd.DataFrame(summ), pd.DataFrame(podlead)
