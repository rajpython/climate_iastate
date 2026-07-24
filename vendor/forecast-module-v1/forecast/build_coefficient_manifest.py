#!/usr/bin/env python3
"""
forecast/build_coefficient_manifest.py — pin the deployed coefficients (v1)
============================================================================
Emits forecast/coefficient_manifest_v1.json: the exact coefficients the
forward wrappers produce when fit at the sealed fit-vintage, so the dashboard
can pin (and later drift-check) the deployed models.

Pinned at fit-vintage snap-obl028-predictand-20260701 (predictand; persistence
origin 2026-07 = last predictand month) and snap-obl029-broadfield-20260701
(LIM field; LIM origin 2026-06 = last field month, the latest common origin):
  * per-zone damped-persistence phi & sigma_eps + 12-month seasonal
    climatology + train q90 occurrence threshold (7 damped zones);
  * per-zone seasonal climatology (chukchi, beaufort);
  * SEBS LIM: EOF truncation K (+ shared-eig set), one-month propagator G1,
    zone read-off vector/constant, EOF variance fraction;
  * SEBS isotonic-link knots (X/y thresholds; sklearn linear interpolation,
    out_of_bounds='clip');
  * SEBS onset decision thresholds at the paper operating point
    (warn-above-climatology base rates, leads 1-2).

No new science: every number is produced by the same frozen code paths the
identity check validated (forecast/core.py -> stage3_harness / stage3_lim).

Run: ~/dev/acfr/.venv/bin/python forecast/build_coefficient_manifest.py
Author/owner: Metrica, 2026-07-08.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ))
sys.path.insert(0, str(PROJ / "scripts"))

from forecast import core  # noqa: E402
import stage3_harness as H  # noqa: E402

SNAP028 = PROJ / "data/snapshots/snap-obl028-predictand-20260701"
SNAP029 = PROJ / "data/snapshots/snap-obl029-broadfield-20260701"
OUT = PROJ / "forecast/coefficient_manifest_v1.json"
OUT_NPZ = PROJ / "forecast/coefficient_manifest_v1_frozen_basis.npz"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_sha_from_manifest(snap: Path, rel_path: str) -> str | None:
    man = json.loads((snap / "manifest.json").read_text())
    for rec in man.get("files", []):
        if rec["path"] == rel_path:
            return rec.get("sha256")
    return None


def load_zone(zone: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP028 / "outputs" / f"{zone}_monthly.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_frozen(field, npz_out: dict) -> dict:
    """Build the FROZEN operational coefficient section.

    Distinct from the drift-check blocks above (pinned at the last raw data
    row, 2026-07 / 2026-06). The FROZEN coefficients are pinned at the last
    rolling-origin at which the paper hindcast has a SCORED record for every
    deployed lead, so the frozen path reproduces those records bit-for-bit
    (that is what makes them 'paper-validated'):
      * persistence / climatology origin = last_predictand - max(magnitude lead)
        = 2026-04 (leads 1-3 all scored);
      * SEBS onset origin = min(last_field, last_predictand - max(onset lead))
        = 2026-05 (leads 1-2 scored).
    Bulky arrays (EOF basis, frozen residual sets) go to the companion npz;
    `npz_out` is filled in place. Nothing here is re-estimated at deploy time —
    this is the one build-time fit whose output is then frozen.
    """
    import stage3_lim as L
    from sklearn.isotonic import IsotonicRegression

    # ---- persistence / climatology at the last common SCORED origin --------
    max_mag_lead = max(max(spec["magnitude_leads"])
                       for spec in core.DEPLOY_MAP.values())
    zblocks = {}
    persistence_origin = None
    for zone, spec in core.DEPLOY_MAP.items():
        df = load_zone(zone)
        kp = len(df) - 1 - max_mag_lead                 # frozen origin index
        origin_date = str(df["date"].iloc[kp].date())
        persistence_origin = persistence_origin or origin_date
        tr = df.iloc[:kp + 1]
        y = tr["area_frac"].to_numpy(float)
        cm = tr["date"].dt.month.to_numpy(int)
        train = pd.DataFrame({"area_frac": y, "cal_month": cm})
        blk = {"origin_date": origin_date, "n_train": int(len(y)),
               "magnitude_model": spec["magnitude_model"]}
        if spec["magnitude_model"] == "damped_persistence":
            fc = H.DampedPersistence().fit(train, "area_frac")
            r1 = fc.residuals(1)
            blk.update({
                "phi": float(fc.phi),
                "sigma_eps": float(np.sqrt(np.mean(r1 ** 2))),
                "seasonal_climatology_jan_dec": [float(v) for v in fc.clim],
                "q90_threshold": float(H.quantile_threshold(y, core.Q_EVENT)),
                "frozen_residuals_1step_npz_key": f"resid1_{zone}",
                "n_residuals_1step": int(len(r1)),
            })
            npz_out[f"resid1_{zone}"] = np.asarray(r1, float)
        else:
            fc = H.Climatology().fit(train, "area_frac")
            pv = {f"lead_{h}": float(np.mean(np.asarray(fc.residuals(h), float) ** 2))
                  for h in spec["magnitude_leads"]}
            blk.update({
                "seasonal_climatology_jan_dec": [float(v) for v in fc.clim],
                "predictive_variance_by_lead": pv,
            })
        zblocks[zone] = blk

    # ---- SEBS onset at the last common SCORED LIM origin -------------------
    onset_leads = core.DEPLOY_MAP["sebs"]["onset_watch_leads"]
    max_onset_lead = max(onset_leads)
    dfs = load_zone("sebs")
    dkeys = dfs["date"].map(core._month_key).to_numpy(int)
    fkeys = np.array([core._month_key(d) for d in field.dates])
    ko_key = int(min(fkeys[-1], dkeys[-1] - max_onset_lead))
    kidx = int(np.where(dkeys == ko_key)[0][0])
    onset_origin = str(dfs["date"].iloc[kidx].date())
    y = dfs["area_frac"].to_numpy(float)[:kidx + 1]
    trm = fkeys <= ko_key
    fit = L.build_many(field.A[trm], field.sw, field.dates[trm],
                       field.zone_cw, core.LIM_KS)[core.LIM_K_PRIMARY]
    k2r = {int(kk): i for i, kk in enumerate(dkeys[:kidx + 1])}
    trk = fkeys[trm]
    tr_rows = np.array([k2r.get(int(kk), -1) for kk in trk])
    valid = tr_rows >= 0
    zm_tr = fit.zone_mean_series("sebs")
    link = IsotonicRegression(increasing=True, out_of_bounds="clip")
    link.fit(zm_tr[valid], y[tr_rows[valid]])
    thr_raw = float(H.quantile_threshold(y, core.Q_EVENT))

    # frozen EOF basis + native cell coordinates -> companion npz
    use = fit._use
    from forecast.frozen import load_live_field
    lf = load_live_field(L.FIELD_NC)                    # frozen-cell-order coords
    npz_out["lim_V"] = np.asarray(fit.V_, float)
    npz_out["lim_mean"] = np.asarray(fit.mean_, float)
    npz_out["lim_sw"] = np.asarray(field.sw[use], float)
    npz_out["lim_cell_lat"] = np.asarray(lf.cell_lat, float)
    npz_out["lim_cell_lon"] = np.asarray(lf.cell_lon, float)

    # per-lead frozen onset residual sets + decision thresholds
    dec_thresholds = {}
    for h in onset_leads:
        tgt = np.array([k2r.get(int(kk) + h, -1) for kk in trk])
        vh = (tgt >= 0) & (tgt <= kidx)
        zmf_all = fit.const_z["sebs"] + (fit.X_[vh] @ fit.Gpow(h).T) @ fit.a_z["sebs"]
        resid = y[tgt[vh]] - link.predict(zmf_all)
        npz_out[f"onset_resid_l{h}"] = np.asarray(resid, float)
        istart = kidx + h - core.MAXLEAD
        thr_s = H.quantile_threshold(y[:istart + 1], core.Q_EVENT)
        dec_thresholds[f"lead_{h}"] = {
            "paper_default_decision_threshold": float((y[:istart + 1] > thr_s).mean()),
            "anchor_q90_threshold": float(thr_s),
            "onset_resid_npz_key": f"onset_resid_l{h}",
            "n_onset_residuals": int(len(resid)),
        }

    return {
        "note": (
            "FROZEN operational coefficients — applied by forecast/frozen.py, "
            "NOT re-estimated at deploy time. Pinned at the last SCORED hindcast "
            "origin per deployed lead (so frozen==paper is exact). The 'zones' / "
            "'sebs_onset_watch' blocks above are the last-data-row drift-check "
            "vintage for the re-fit path (forecast/core.py); this block is the "
            "operational default."),
        "companion_npz": OUT_NPZ.name,
        "companion_npz_sha256": None,           # filled after the npz is written
        "persistence_climatology": {
            "fit_origin_date": persistence_origin,
            "max_magnitude_lead": int(max_mag_lead),
            "zones": zblocks,
        },
        "sebs_onset": {
            "fit_origin_date": onset_origin,
            "n_train_field": int(trm.sum()),
            "n_train_predictand": int(len(y)),
            "eof_truncation_K": core.LIM_K_PRIMARY,
            "shared_eig_truncation_set": list(core.LIM_KS),
            "eof_variance_fraction": float(fit.var_frac_),
            "eof_basis_npz_keys": {"V": "lim_V", "mean": "lim_mean",
                                    "sw": "lim_sw", "cell_lat": "lim_cell_lat",
                                    "cell_lon": "lim_cell_lon"},
            "n_cells": int(use.sum()),
            "propagator_G1": [[float(v) for v in row] for row in fit.G1_],
            "zone_readoff_a_sebs": [float(v) for v in fit.a_z["sebs"]],
            "zone_readoff_const_sebs": float(fit.const_z["sebs"]),
            "isotonic_link": {
                "X_thresholds": [float(v) for v in link.X_thresholds_],
                "y_thresholds": [float(v) for v in link.y_thresholds_],
                "n_knots": int(len(link.X_thresholds_)),
            },
            "q90_threshold": thr_raw,
            "decision_thresholds": dec_thresholds,
        },
    }


def main():
    manifest = {
        "manifest_version": "v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "owner": "Metrica (ACFR research cell)",
        "paper_reference": "sst-forecast-method-review working paper v14 (2026-07-07)",
        "fit_vintage": {
            "predictand_snapshot": core.FIT_VINTAGE_PREDICTAND,
            "predictand_manifest_sha256": sha256_of(SNAP028 / "manifest.json"),
            "field_snapshot": core.FIT_VINTAGE_FIELD,
            "field_manifest_sha256": sha256_of(SNAP029 / "manifest.json"),
            "field_nc_sha256": file_sha_from_manifest(
                SNAP029, "outputs/broadbasin_oisst_monthly.nc"),
        },
        "code_provenance": {
            "harness": "scripts/stage3_harness.py",
            "harness_sha256": sha256_of(PROJ / "scripts/stage3_harness.py"),
            "lim_lib": "scripts/stage3_lim.py",
            "lim_lib_sha256": sha256_of(PROJ / "scripts/stage3_lim.py"),
            "core": "forecast/core.py",
            "core_sha256": sha256_of(PROJ / "forecast/core.py"),
            "frozen": "forecast/frozen.py",
            "frozen_sha256": sha256_of(PROJ / "forecast/frozen.py"),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "conventions": {
            "q_event": core.Q_EVENT,
            "onset_threshold_anchor_months": core.MAXLEAD,
            "ar1_variance_note": (
                "AR(1) h-step forecast-error variance "
                "sigma_eps^2*(1-phi^{2h})/(1-phi^2) — standard/canonical; the "
                "finite-h form of the paper's Eq 7b (which displays its "
                "h->inf limit). Source: Hamilton (1994), Time Series "
                "Analysis, Ch.4 §4.2 (pp.77-84); OA-verified equivalent "
                "Hyndman & Athanasopoulos, Forecasting: Principles and "
                "Practice (3rd ed.) §9.8; canonical Brockwell & Davis "
                "(2016). Confirmed-in-kind by Cobra 2026-07-08 "
                "(handoffs/cobra-to-lofra-ar1-variance-provenance-"
                "20260708.md); accepted at metadata-level attribution. "
                "Evaluated on phi and sigma_eps as pinned in this manifest "
                "(frozen operational path) or re-fit on the caller's frame "
                "(validation/replication path only)."),
            "isotonic_link_note": (
                "sklearn IsotonicRegression(increasing=True, "
                "out_of_bounds='clip'); predict = linear interpolation "
                "between (X_thresholds, y_thresholds) knots, clipped."),
        },
        "zones": {},
        "sebs_onset_watch": {},
    }

    # ---- per-zone persistence / climatology coefficients ------------------
    for zone, spec in core.DEPLOY_MAP.items():
        df = load_zone(zone)
        y = df["area_frac"].to_numpy(float)
        cm = df["date"].dt.month.to_numpy(int)
        train = pd.DataFrame({"area_frac": y, "cal_month": cm})
        entry = {
            "deploy": {k: (list(v) if isinstance(v, tuple) else v)
                       for k, v in spec.items()},
            "source_csv": f"outputs/{zone}_monthly.csv",
            "source_csv_sha256": file_sha_from_manifest(
                SNAP028, f"outputs/{zone}_monthly.csv"),
            "origin_date": str(df["date"].iloc[-1].date()),
            "n_train": int(len(y)),
        }
        if spec["magnitude_model"] == "damped_persistence":
            fc = H.DampedPersistence().fit(train, "area_frac")
            entry.update({
                "phi": float(fc.phi),
                "sigma_eps": float(np.sqrt(np.mean(fc.residuals(1) ** 2))),
                "seasonal_climatology_jan_dec": [float(v) for v in fc.clim],
                "q90_threshold": float(H.quantile_threshold(y, core.Q_EVENT)),
            })
        else:
            fc = H.Climatology().fit(train, "area_frac")
            entry.update({
                "seasonal_climatology_jan_dec": [float(v) for v in fc.clim],
            })
        manifest["zones"][zone] = entry

    # ---- SEBS onset-watch coefficients (LIM + link + thresholds) ----------
    field = core.load_default_field()
    df = load_zone("sebs")
    fkeys = np.array([core._month_key(d) for d in field.dates])
    last_field_key = int(fkeys[-1])
    dkeys = df["date"].map(core._month_key).to_numpy(int)
    k = int(np.where(dkeys == last_field_key)[0][0])   # latest common origin
    df_o = df.iloc[:k + 1]
    y = df_o["area_frac"].to_numpy(float)

    import stage3_lim as L
    from sklearn.isotonic import IsotonicRegression
    tr_mask = fkeys <= last_field_key
    fit = L.build_many(field.A[tr_mask], field.sw, field.dates[tr_mask],
                       field.zone_cw, core.LIM_KS)[core.LIM_K_PRIMARY]
    key_to_row = {int(kk): i for i, kk in enumerate(dkeys[:k + 1])}
    tr_rows = np.array([key_to_row.get(int(kk), -1) for kk in fkeys[tr_mask]])
    valid = tr_rows >= 0
    zm_tr = fit.zone_mean_series("sebs")
    link = IsotonicRegression(increasing=True, out_of_bounds="clip")
    link.fit(zm_tr[valid], y[tr_rows[valid]])

    dec_thresholds = {}
    for h in core.DEPLOY_MAP["sebs"]["onset_watch_leads"]:
        istart = k + h - core.MAXLEAD
        thr_s = H.quantile_threshold(y[:istart + 1], core.Q_EVENT)
        dec_thresholds[f"lead_{h}"] = {
            "paper_default_decision_threshold": float(
                (y[:istart + 1] > thr_s).mean()),
            "anchor_q90_threshold": float(thr_s),
        }

    manifest["sebs_onset_watch"] = {
        "model": "lim_k12 -> train-only isotonic link -> q90 exceedance "
                 "-> warn-above-climatology (extracted stage3_03_lim_oos.py)",
        "origin_date": str(df_o["date"].iloc[-1].date()),
        "n_train_field": int(tr_mask.sum()),
        "n_train_predictand": int(len(y)),
        "eof_truncation_K": core.LIM_K_PRIMARY,
        "shared_eig_truncation_set": list(core.LIM_KS),
        "eof_variance_fraction": float(fit.var_frac_),
        "propagator_G1": [[float(v) for v in row] for row in fit.G1_],
        "zone_readoff_a_sebs": [float(v) for v in fit.a_z["sebs"]],
        "zone_readoff_const_sebs": float(fit.const_z["sebs"]),
        "isotonic_link": {
            "X_thresholds": [float(v) for v in link.X_thresholds_],
            "y_thresholds": [float(v) for v in link.y_thresholds_],
            "n_knots": int(len(link.X_thresholds_)),
        },
        "q90_threshold": float(H.quantile_threshold(y, core.Q_EVENT)),
        "decision_thresholds": dec_thresholds,
    }

    # ---- FROZEN operational section (+ companion npz) ---------------------
    npz_arrays: dict = {}
    manifest["frozen"] = build_frozen(field, npz_arrays)
    # write the bulky binary companion FIRST, then record its sha in the JSON
    np.savez_compressed(OUT_NPZ, **npz_arrays)
    manifest["frozen"]["companion_npz_sha256"] = sha256_of(OUT_NPZ)

    OUT.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"WROTE {OUT}")
    print(f"WROTE {OUT_NPZ}  ({OUT_NPZ.stat().st_size/1e6:.1f} MB, "
          f"{len(npz_arrays)} arrays)")
    fz = manifest["frozen"]
    print(f"  frozen persistence origin: {fz['persistence_climatology']['fit_origin_date']}"
          f"  onset origin: {fz['sebs_onset']['fit_origin_date']}")
    print(f"  zones: {list(manifest['zones'].keys())}")
    for z, e in manifest["zones"].items():
        if "phi" in e:
            print(f"  {z:11s} phi={e['phi']:.4f} sigma_eps={e['sigma_eps']:.4f} "
                  f"q90={e['q90_threshold']:.4f}")
        else:
            print(f"  {z:11s} climatology-only")
    s = manifest["sebs_onset_watch"]
    print(f"  sebs onset: K={s['eof_truncation_K']} var_frac={s['eof_variance_fraction']:.3f} "
          f"link_knots={s['isotonic_link']['n_knots']} origin={s['origin_date']}")
    print(f"  decision thresholds: "
          + ", ".join(f"{k}={v['paper_default_decision_threshold']:.4f}"
                      for k, v in s["decision_thresholds"].items()))


if __name__ == "__main__":
    main()
