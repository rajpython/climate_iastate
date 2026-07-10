#!/usr/bin/env python3
"""
stage3_lim.py — Linear Inverse Model (LIM-in-EOF) library for the Stage-3 contest
=================================================================================
The reduced-rank spatiotemporal statistical instrument of the head-to-head
(SDL-021), governed by metrica-to-lofra-stage3-modeling-strategy-20260701.md.

METHOD (exact definition, Penland & Sardeshmukh 1995; Alexander et al. 2008):
  * State x_t in R^K = leading EOF-PC amplitudes of the cosine-weighted, per-cell
    deseasonalised broad-basin SST anomaly field (snap-obl029, drop all-NaN 1982-03).
  * Lag-0 / lag-tau covariances C0 = <x_t x_t^T>, C_tau = <x_{t+tau} x_t^T> from
    CALENDAR-CONSECUTIVE month pairs only (the 1982-03 gap breaks 2 pairs).
  * Green function (propagator) at lag tau:  G(tau) = C_tau C0^{-1}.
  * Dynamical operator L = logm(G(tau))/tau ; forecast at lead h (months, tau=1):
        x_hat(t+h|t) = G(1)^h x_t        (== exp(L h) x_t)
  * Predictive error covariance (stationary LIM):
        Sigma(h) = C0 - G(h) C0 G(h)^T .

ZONE READ-OFF (adaptation of derive-then-threshold; labelled as such):
  The k~10 EOF reconstruction is too spatially smooth to resolve reliable
  sub-zone MHW COVERAGE by per-cell thresholding (rejected — methods-history).
  Instead the LIM field forecast is read off as the cosine-area-weighted ZONE-MEAN
  anomaly zm_z = const_z + a_z^T x  (a_z = V^T (c_z ./ sw)), then mapped to the
  observed area_frac scale by a TRAIN-ONLY monotone (isotonic) link. This keeps
  the LIM on the harness's area_frac target for an apples-to-apples contest, and
  the exceedance probability uses the SAME distribution-free (point + train
  residuals) mechanism as the baselines. Deviation from the field's per-cell
  Hobday spatial threshold is stated explicitly (proxy/adaptation).

Author/owner: Metrica. Library only — drivers are stage3_03_lim_oos.py etc.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr
import zarr
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache

PROJ = Path("/Users/rajpython/dev/acfr/projects/sst-forecast-method-review")
FIELD_NC = PROJ / "data/snapshots/snap-obl029-broadfield-20260701/outputs/broadbasin_oisst_monthly.nc"
MASKS_ZARR = PROJ / "data/work/obl028-unpack/data/derived/masks/region_masks.zarr"

ZONES = ["sebs", "nbs", "wgoa", "egoa",
         "ai_west", "ai_central", "ai_east", "chukchi", "beaufort"]

# global OISST 0.25deg grid (from obl029_04)
GLOBAL_LAT0 = -89.875
GLOBAL_LON0 = -179.875
GRID_STEP = 0.25


# --------------------------------------------------------------------------
# 1. Field + zone-weight loading (cached module-level; sealed, read-only)
# --------------------------------------------------------------------------
@dataclass
class FieldState:
    dates: pd.DatetimeIndex      # (Nf,) calendar dates of field rows (1982-03 dropped)
    A: np.ndarray                # (Nf, M) unweighted ocean anomaly, deg C
    sw: np.ndarray               # (M,)   sqrt(cos lat) EOF weight per ocean cell
    zone_cw: dict                # zone -> (M,) normalised cos-lat area weight (0 outside)
    zone_ice: dict               # zone -> (M,) mean ice-flag fraction per ocean cell
    ocean_ice_frac: np.ndarray   # (M,) overall mean ice-flag fraction per ocean cell


def _lat_to_row(lat):
    return np.round((lat - GLOBAL_LAT0) / GRID_STEP).astype(int)

def _lon_to_col(lon_0_360):
    lon180 = np.where(lon_0_360 > 180.0, lon_0_360 - 360.0, lon_0_360)
    return np.round((lon180 - GLOBAL_LON0) / GRID_STEP).astype(int)


_FIELD_CACHE = {}

def load_field() -> FieldState:
    if "fs" in _FIELD_CACHE:
        return _FIELD_CACHE["fs"]
    d = xr.open_dataset(str(FIELD_NC))
    times = pd.DatetimeIndex(d.time.values)
    anom = d["sst_monthly_anom"].values          # (534,240,480)
    ice = d["ice_flag_monthly"].values           # (534,240,480), 1=ice
    lat = d.lat.values; lon = d.lon.values
    nlat, nlon = lat.size, lon.size
    keep = np.array([t.strftime("%Y-%m") != "1982-03" for t in times])
    A_all = anom[keep]                            # (533,240,480)
    ice_all = ice[keep]
    dates = times[keep]
    T = A_all.shape[0]
    flat = A_all.reshape(T, -1)
    ocean = np.isfinite(flat).all(axis=0)         # (115200,) valid all kept months
    A = flat[:, ocean]                            # (533, M) unweighted anomaly
    # EOF weight sqrt(cos lat)
    w2d = np.sqrt(np.cos(np.deg2rad(lat)))[:, None] * np.ones((nlat, nlon))
    sw = w2d.reshape(-1)[ocean]
    # cos-lat area weight (for zone means)
    aw2d = np.cos(np.deg2rad(lat))[:, None] * np.ones((nlat, nlon))
    aw = aw2d.reshape(-1)[ocean]
    # ocean-cell -> global grid indices for mask lookup
    rows = _lat_to_row(lat)                       # (240,)
    cols = _lon_to_col(lon)                       # (480,)
    rows2d = np.broadcast_to(rows[:, None], (nlat, nlon)).reshape(-1)[ocean]
    cols2d = np.broadcast_to(cols[None, :], (nlat, nlon)).reshape(-1)[ocean]
    # ice fraction per ocean cell (mean over time of ice flag)
    ice_flat = ice_all.reshape(T, -1)[:, ocean]
    ocean_ice_frac = np.nanmean((ice_flat == 1).astype(float), axis=0)
    # zone weights
    zm = zarr.open(str(MASKS_ZARR), mode="r")
    zone_cw, zone_ice = {}, {}
    for z in ZONES:
        gmask = zm[z][:].astype(bool)             # (720,1440)
        valid_rc = (rows2d >= 0) & (rows2d < 720) & (cols2d >= 0) & (cols2d < 1440)
        inz = np.zeros(A.shape[1], bool)
        inz[valid_rc] = gmask[rows2d[valid_rc], cols2d[valid_rc]]
        cw = np.where(inz, aw, 0.0)
        s = cw.sum()
        cw = cw / s if s > 0 else cw
        zone_cw[z] = cw
        zone_ice[z] = np.where(inz, ocean_ice_frac, np.nan)
    d.close()
    fs = FieldState(dates=dates, A=A, sw=sw, zone_cw=zone_cw,
                    zone_ice=zone_ice, ocean_ice_frac=ocean_ice_frac)
    _FIELD_CACHE["fs"] = fs
    return fs


# --------------------------------------------------------------------------
# 2. LIM fit (EOF reduction + propagator) on a TRAIN window
# --------------------------------------------------------------------------
class LIMFit:
    """Stationary LIM on the leading K EOF-PCs. Fit on a train slice of the
    (already-loaded) ocean anomaly matrix. Consecutive-pair covariances respect
    the calendar gap. ridge = small Tikhonov on C0 for a stable inverse."""

    def __init__(self, K: int = 12, ridge: float = 1e-6, ice_mask: np.ndarray | None = None):
        self.K = K
        self.ridge = ridge
        self.ice_mask = ice_mask   # optional boolean (M,) True=DROP this ocean cell from state

    def fit(self, A_tr: np.ndarray, sw: np.ndarray, dates_tr: pd.DatetimeIndex,
            zone_cw: dict):
        """A_tr (N,M) unweighted anomaly (train rows); sw (M,) EOF weight;
        zone_cw dict zone->(M,) area weight. Builds EOF basis + propagator."""
        M = A_tr.shape[1]
        use = np.ones(M, bool)
        if self.ice_mask is not None:
            use = ~self.ice_mask
        A = A_tr[:, use]
        sw_u = sw[use]
        self._use = use
        self.mean_ = A.mean(axis=0)                       # (Mu,) train cell mean
        Ac = A - self.mean_[None, :]
        Y = Ac * sw_u[None, :]                            # weighted, centered
        # temporal-Gram EOF (N<<Mu): eig of Y Y^T
        G = Y @ Y.T                                        # (N,N)
        evals, U = np.linalg.eigh(G)
        order = np.argsort(evals)[::-1]
        evals = evals[order][:self.K]
        U = U[:, order][:, :self.K]                        # (N,K)
        evals = np.clip(evals, 1e-12, None)
        V = (Y.T @ U) / np.sqrt(evals)[None, :]            # (Mu,K) spatial patterns (wtd)
        self.V_ = V
        self.evals_ = evals
        self.var_frac_ = float(evals.sum() / (np.linalg.eigvalsh(G).sum()))
        X = Y @ V                                          # (N,K) PC amplitudes (state)
        self.X_ = X
        self.dates_tr = dates_tr
        # covariances from CALENDAR-CONSECUTIVE pairs
        mo = np.array([d.year * 12 + (d.month - 1) for d in dates_tr])
        pair = np.where(np.diff(mo) == 1)[0]               # index t s.t. (t,t+1) consecutive
        N = X.shape[0]
        C0 = (X.T @ X) / (N - 1)
        C0 += self.ridge * np.trace(C0) / self.K * np.eye(self.K)
        X0 = X[pair]; X1 = X[pair + 1]
        C1 = (X1.T @ X0) / (len(pair) - 1)
        self.C0_ = C0
        self.C1_ = C1
        self.C0inv_ = np.linalg.inv(C0)
        self.G1_ = C1 @ self.C0inv_
        self._pair = pair
        self._mo = mo
        # zone read-off vectors a_z = V^T (c_z ./ sw)  (restricted to used cells)
        self.a_z, self.const_z = {}, {}
        for z, cw in zone_cw.items():
            cwu = cw[use]
            self.a_z[z] = self.V_.T @ (cwu / sw_u)         # (K,)
            self.const_z[z] = float(cwu @ self.mean_)      # zone mean of train mean field
        self._Gpow = {1: self.G1_}
        return self

    def Gpow(self, h: int) -> np.ndarray:
        if h not in self._Gpow:
            self._Gpow[h] = np.linalg.matrix_power(self.G1_, h)
        return self._Gpow[h]

    def forecast_state(self, x0: np.ndarray, h: int) -> np.ndarray:
        return self.Gpow(h) @ x0

    def zone_mean_series(self, z: str) -> np.ndarray:
        """Reduced-rank zone-mean anomaly at every train time (for link fit)."""
        return self.const_z[z] + self.X_ @ self.a_z[z]

    def zone_mean_forecast(self, z: str, x0: np.ndarray, h: int) -> float:
        return float(self.const_z[z] + self.a_z[z] @ self.forecast_state(x0, h))

    def sigma_zone(self, z: str, h: int) -> float:
        """Predictive variance of the zone-mean anomaly at lead h."""
        Gh = self.Gpow(h)
        Sig = self.C0_ - Gh @ self.C0_ @ Gh.T
        a = self.a_z[z]
        return float(a @ Sig @ a)

    # --- diagnostics -----------------------------------------------------
    def propagator_eigs(self):
        """Eigenvalues of G(1) and of L=logm(G1); decay times & periods."""
        from scipy.linalg import logm
        wG = np.linalg.eigvals(self.G1_)
        L = logm(self.G1_)
        wL = np.linalg.eigvals(L)                 # per-month growth rates
        # decay time (months) = -1/Re(wL); period = 2pi/Im(wL)
        out = []
        for lam in sorted(wL, key=lambda z: z.real, reverse=True):  # slowest-decay first
            dtime = (-1.0 / lam.real) if lam.real < 0 else np.inf
            period = (2 * np.pi / abs(lam.imag)) if abs(lam.imag) > 1e-9 else np.inf
            out.append(dict(re=float(lam.real), im=float(lam.imag),
                            decay_months=float(dtime), period_months=float(period)))
        return dict(G1_eig_mod=sorted(np.abs(wG).tolist(), reverse=True), L_modes=out)


def build_many(A_tr, sw, dates_tr, zone_cw, Ks, ridge=1e-6, ice_mask=None):
    """Fit stationary LIMs for several truncations Ks SHARING one eigendecomposition
    (the expensive step). Returns {K: LIMFit}. Used for the OOS K-sensitivity so the
    contest costs one eig per origin, not len(Ks)."""
    use = np.ones(A_tr.shape[1], bool)
    if ice_mask is not None:
        use = ~ice_mask
    A = A_tr[:, use]; sw_u = sw[use]
    mean_ = A.mean(axis=0)
    Y = (A - mean_[None, :]) * sw_u[None, :]
    Gt = Y @ Y.T
    evals_all, U_all = np.linalg.eigh(Gt)
    order = np.argsort(evals_all)[::-1]
    evals_all = evals_all[order]; U_all = U_all[:, order]
    tot = float(np.clip(evals_all, 0, None).sum())
    Kmax = max(Ks)
    evals = np.clip(evals_all[:Kmax], 1e-12, None)
    U = U_all[:, :Kmax]
    Vmax = (Y.T @ U) / np.sqrt(evals)[None, :]          # (Mu,Kmax)
    Xmax = Y @ Vmax                                      # (N,Kmax)
    mo = np.array([d.year * 12 + (d.month - 1) for d in dates_tr])
    cons = np.where(np.diff(mo) == 1)[0]
    N = Xmax.shape[0]
    cwu = {z: zone_cw[z][use] for z in zone_cw}
    out = {}
    for K in Ks:
        f = LIMFit(K=K, ridge=ridge, ice_mask=ice_mask)
        f._use = use; f.mean_ = mean_
        f.V_ = Vmax[:, :K]; f.evals_ = evals[:K]
        f.var_frac_ = float(evals[:K].sum() / tot) if tot > 0 else np.nan
        X = Xmax[:, :K]; f.X_ = X; f.dates_tr = dates_tr
        C0 = (X.T @ X) / (N - 1)
        C0 += ridge * np.trace(C0) / K * np.eye(K)
        X0 = X[cons]; X1 = X[cons + 1]
        C1 = (X1.T @ X0) / (len(cons) - 1)
        f.C0_ = C0; f.C1_ = C1; f.C0inv_ = np.linalg.inv(C0)
        f.G1_ = C1 @ f.C0inv_
        f._pair = cons; f._mo = mo
        f.a_z, f.const_z = {}, {}
        for z in zone_cw:
            f.a_z[z] = f.V_.T @ (cwu[z] / sw_u)
            f.const_z[z] = float(cwu[z] @ mean_)
        f._Gpow = {1: f.G1_}
        out[K] = f
    return out


def tau_independence(A_tr, sw, dates_tr, zone_cw, K=12, taus=(1, 2, 3, 6, 12)):
    """LIM internal validity: eigenvalues of L=logm(G(tau))/tau should be
    stable across the training lag tau. Returns leading-mode decay/period per tau."""
    from scipy.linalg import logm
    fit = LIMFit(K=K).fit(A_tr, sw, dates_tr, zone_cw)
    X = fit.X_
    mo = fit._mo
    N = X.shape[0]
    C0 = fit.C0_
    C0inv = fit.C0inv_
    res = {}
    for tau in taus:
        # pairs (i, i+tau) that are exactly tau CALENDAR months apart
        idx = np.arange(N - tau)
        good = (mo[idx + tau] - mo[idx]) == tau
        pair = idx[good]
        if len(pair) < K + 5:
            continue
        X0 = X[pair]; Xt = X[pair + tau]
        Ctau = (Xt.T @ X0) / (len(pair) - 1)
        Gtau = Ctau @ C0inv
        try:
            L = logm(Gtau) / tau
        except Exception:
            continue
        wL = np.linalg.eigvals(L)
        # leading (slowest-decaying) mode
        lead = max(wL, key=lambda z: z.real)
        dtime = (-1.0 / lead.real) if lead.real < 0 else np.inf
        period = (2 * np.pi / abs(lead.imag)) if abs(lead.imag) > 1e-9 else np.inf
        res[tau] = dict(n_pairs=int(len(pair)),
                        lead_decay_months=float(dtime),
                        lead_period_months=float(period),
                        lead_re=float(lead.real), lead_im=float(lead.imag),
                        all_re=sorted([float(z.real) for z in wL]))
    return res


# --------------------------------------------------------------------------
# 3. Cyclostationary LIM (month-dependent propagator, shrunk to stationary)
# --------------------------------------------------------------------------
class CSLIMFit(LIMFit):
    """CS-LIM: origin-month-dependent propagator G_m = C1_m C0^{-1}, each shrunk
    toward the stationary G by  G_m* = (1-w_m) G_stationary + w_m G_m_raw, with
    w_m = n_m/(n_m + kappa) (data-count shrinkage; kappa the effective prior
    strength). Short-record identifiability lever (strategy memo C.3)."""

    def __init__(self, K=12, ridge=1e-6, kappa=40.0, ice_mask=None):
        super().__init__(K=K, ridge=ridge, ice_mask=ice_mask)
        self.kappa = kappa

    def fit(self, A_tr, sw, dates_tr, zone_cw):
        super().fit(A_tr, sw, dates_tr, zone_cw)
        X = self.X_; mo = self._mo
        cons = np.where(np.diff(mo) == 1)[0]
        origin_month = np.array([dates_tr[i].month for i in cons])
        self.Gm_ = {}
        for m in range(1, 13):
            sel = origin_month == m
            n_m = int(sel.sum())
            if n_m < 3:
                self.Gm_[m] = self.G1_
                continue
            X0 = X[cons[sel]]; X1 = X[cons[sel] + 1]
            C1m = (X1.T @ X0) / max(n_m - 1, 1)
            Gm_raw = C1m @ self.C0inv_
            w = n_m / (n_m + self.kappa)
            self.Gm_[m] = (1 - w) * self.G1_ + w * Gm_raw
        return self

    def forecast_state(self, x0, h, origin_month=None):
        # step month-by-month with the month-appropriate propagator
        x = x0.copy()
        m = origin_month
        for _ in range(h):
            G = self.Gm_.get(m, self.G1_) if m is not None else self.G1_
            x = G @ x
            if m is not None:
                m = m % 12 + 1
        return x

    def zone_mean_forecast(self, z, x0, h, origin_month=None):
        xf = self.forecast_state(x0, h, origin_month=origin_month)
        return float(self.const_z[z] + self.a_z[z] @ xf)

    def forecast_state_batch(self, X, origin_months, h):
        """Vectorised h-step forecast for many rows, each with its own origin
        month. X (N,K); origin_months (N,). Returns (N,K)."""
        Xf = X.copy()
        m = np.asarray(origin_months, int).copy()
        for _ in range(h):
            for mm in range(1, 13):
                sel = m == mm
                if sel.any():
                    Xf[sel] = Xf[sel] @ self.Gm_.get(mm, self.G1_).T
            m = m % 12 + 1
        return Xf

    def zone_mean_batch(self, z, X, origin_months, h):
        Xf = self.forecast_state_batch(X, origin_months, h)
        return self.const_z[z] + Xf @ self.a_z[z]
