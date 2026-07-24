#!/usr/bin/env python3
"""
forecast/selftest_identity_check.py — acceptance gate for the forward wrappers
===============================================================================
Proves the forward-mode wrappers in forecast/core.py are THE SAME MODELS as
the paper's hindcast, not reimplementations: run at the final rolling-origin
of each lead on the sealed snapshots, every wrapper output must reproduce the
corresponding hindcast record to machine precision.

Checks
------
1. Re-runs the snapshot QA gate on both sealed inputs (hard halt on non-zero).
2. run_latest_origin vs results/stage-3-baselines/oos_long_records.parquet:
   for every zone (model per DEPLOY_MAP: damped_persistence x7, climatology
   x2) and leads 1/2/3, at the final origin per lead (origin k = n-1-h):
   point forecast ('fcst'); plus L1 occurrence probability ('prob') for the
   seven damped zones.
3. sebs_onset_watch vs results/stage-3-lim/lim_long_records.parquet
   (forecaster lim_k12, zone sebs, detrend=False), leads 1/2 at the final
   origin per lead: point ('fcst'), onset probability ('prob'), and the paper
   default decision threshold ('onset_decision_p').
4. Diagnostic (not gated): AR(1) h-step variance formula vs the empirical
   mean-square of the train h-step residuals (ratio ~ 1 if AR(1) adequate).

PASS iff every gated max-abs-diff <= 1e-12 (expected: exactly 0.0).
Output tee'd to results/forecast-module/identity_check.txt.

Run: ~/dev/acfr/.venv/bin/python forecast/selftest_identity_check.py
Author/owner: Metrica, 2026-07-08.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ))            # import the forecast package
sys.path.insert(0, str(PROJ / "scripts"))

from forecast import (DEPLOY_MAP, load_default_field, run_latest_origin,
                      sebs_onset_watch)  # noqa: E402
import stage3_harness as H  # noqa: E402  (for the variance diagnostic)

SNAP028 = PROJ / "data/snapshots/snap-obl028-predictand-20260701"
SNAP029 = PROJ / "data/snapshots/snap-obl029-broadfield-20260701"
BASE_REC = PROJ / "results/stage-3-baselines/oos_long_records.parquet"
LIM_REC = PROJ / "results/stage-3-lim/lim_long_records.parquet"
OUT_DIR = PROJ / "results/forecast-module"
TOL = 1e-12

_lines = []


def log(msg=""):
    print(msg)
    _lines.append(str(msg))


def qa_gate(snap: Path):
    r = subprocess.run([sys.executable, str(PROJ / "scripts/qa_gate.py"),
                        "--snapshot-dir", str(snap)],
                       capture_output=True, text=True)
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(no output)"
    log(f"QA gate {snap.name}: exit={r.returncode} :: {tail}")
    if r.returncode != 0:
        log("HARD HALT: QA gate non-zero — snapshot drift. Aborting selftest.")
        _flush()
        sys.exit(1)


def _flush():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "identity_check.txt").write_text("\n".join(_lines) + "\n")


def main():
    log("=" * 78)
    log("forecast/ forward-wrapper identity check vs paper hindcast records")
    log("build 2026-07-08 (Metrica); tolerance %g (expected exact 0)" % TOL)
    log("=" * 78)

    # ---- 1. sealed-input QA gates --------------------------------------
    qa_gate(SNAP028)
    qa_gate(SNAP029)

    base = pd.read_parquet(BASE_REC)
    base = base[~base["detrend"]]
    lim = pd.read_parquet(LIM_REC)
    lim = lim[(~lim["detrend"]) & (lim["forecaster"] == "lim_k12")
              & (lim["zone"] == "sebs")]

    diffs = {"baseline_fcst": [], "baseline_prob_L1": [],
             "lim_fcst": [], "lim_prob": [], "lim_decision_p": [],
             # frozen-path (operational) vs paper hindcast records
             "frozen_baseline_fcst": [], "frozen_baseline_prob_L1": [],
             "frozen_lim_fcst": [], "frozen_lim_prob": [],
             "frozen_lim_decision_p": []}

    # ---- 2. baselines: run_latest_origin at final origin per lead -------
    log("\n[2] run_latest_origin vs oos_long_records.parquet (final origin per lead)")
    for zone, spec in DEPLOY_MAP.items():
        df = pd.read_csv(SNAP028 / "outputs" / f"{zone}_monthly.csv")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        n = len(df)
        model = spec["magnitude_model"]
        for h in (1, 2, 3):
            k = n - 1 - h                       # final origin with a target
            fw = run_latest_origin(df.iloc[:k + 1], zone, leads=(h,))
            rec = base[(base.zone == zone) & (base.forecaster == model)
                       & (base.lead == h)
                       & (base.origin_date == df["date"].iloc[k])]
            assert len(rec) == 1, (zone, model, h, len(rec))
            rec = rec.iloc[0]
            d_pt = abs(fw["leads"][h]["point_area_frac"] - float(rec.fcst))
            diffs["baseline_fcst"].append(d_pt)
            msg = (f"  {zone:11s} {model:18s} L{h} origin={fw['origin_date']} "
                   f"|d_point|={d_pt:.3e}")
            if h == 1 and spec["occurrence_l1"]:
                d_pr = abs(fw["leads"][1]["occurrence_prob_q90"] - float(rec.prob))
                diffs["baseline_prob_L1"].append(d_pr)
                msg += f"  |d_prob|={d_pr:.3e}"
            log(msg)

    # ---- 3. SEBS onset watch vs lim_k12 records --------------------------
    log("\n[3] sebs_onset_watch vs lim_long_records.parquet (lim_k12, final origin per lead)")
    field = load_default_field()
    df = pd.read_csv(SNAP028 / "outputs" / "sebs_monthly.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    n = len(df)
    for h in (1, 2):
        k = n - 1 - h
        fw = sebs_onset_watch(df.iloc[:k + 1], field=field, leads=(h,))
        rec = lim[(lim.lead == h) & (lim.origin_date == df["date"].iloc[k])]
        assert len(rec) == 1, (h, len(rec))
        rec = rec.iloc[0]
        L = fw["leads"][h]
        d_pt = abs(L["point_area_frac"] - float(rec.fcst))
        d_pr = abs(L["onset_prob_q90"] - float(rec.prob))
        d_dp = abs(L["paper_default_threshold"] - float(rec.onset_decision_p))
        diffs["lim_fcst"].append(d_pt)
        diffs["lim_prob"].append(d_pr)
        diffs["lim_decision_p"].append(d_dp)
        log(f"  sebs lim_k12 L{h} origin={fw['origin_date']} "
            f"|d_point|={d_pt:.3e} |d_prob|={d_pr:.3e} "
            f"|d_decision_p|={d_dp:.3e} watch={L['watch']} "
            f"(prob={L['onset_prob_q90']:.4f} vs thr={L['decision_threshold']:.4f})")

    # ---- 4. variance diagnostic (not gated) ------------------------------
    log("\n[4] diagnostic (NOT gated): AR(1) h-step variance formula vs empirical")
    log("    mean-square of train h-step residuals (ratio ~ 1 if AR(1) adequate)")
    for zone, spec in DEPLOY_MAP.items():
        if spec["magnitude_model"] != "damped_persistence":
            continue
        dfz = pd.read_csv(SNAP028 / "outputs" / f"{zone}_monthly.csv")
        dfz["date"] = pd.to_datetime(dfz["date"])
        dfz = dfz.sort_values("date").reset_index(drop=True)
        dfz["cal_month"] = dfz["date"].dt.month
        fc = H.DampedPersistence().fit(
            pd.DataFrame({"area_frac": dfz["area_frac"].to_numpy(float),
                          "cal_month": dfz["cal_month"].to_numpy(int)}),
            "area_frac")
        s2 = float(np.mean(fc.residuals(1) ** 2))
        ratios = []
        for h in (1, 2, 3):
            vf = s2 * (1 - fc.phi ** (2 * h)) / (1 - fc.phi ** 2)
            ve = float(np.mean(fc.residuals(h) ** 2))
            ratios.append(f"L{h}: {vf:.3e}/{ve:.3e}={vf / ve:.3f}")
        log(f"  {zone:11s} phi={fc.phi:.3f} sigma_eps={np.sqrt(s2):.4f}  "
            + "  ".join(ratios))

    # ---- 5. FROZEN persistence/climatology vs paper hindcast records -----
    # The frozen path applies ONE pinned coefficient set, so all deployed
    # leads are tested at the SINGLE latest origin where every lead is scored
    # (persistence/clim origin = last_predictand - max_lead = 2026-04). At that
    # vintage frozen coefficients == coefficients fit through the vintage, so
    # the match must be EXACTLY 0.0.
    from forecast.frozen import (forecast_frozen, load_manifest,  # noqa: E402
                                 load_live_field, sebs_onset_watch_frozen)
    mani = load_manifest()
    max_mag_lead = max(max(s["magnitude_leads"]) for s in DEPLOY_MAP.values())
    log("\n[5] FROZEN forecast_frozen vs oos_long_records.parquet "
        "(pinned coeffs, common scored origin)")
    for zone, spec in DEPLOY_MAP.items():
        df = pd.read_csv(SNAP028 / "outputs" / f"{zone}_monthly.csv")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        kp = len(df) - 1 - max_mag_lead                # common scored origin
        model = spec["magnitude_model"]
        fw = forecast_frozen(df.iloc[:kp + 1], zone, mani, leads=(1, 2, 3))
        for h in (1, 2, 3):
            rec = base[(base.zone == zone) & (base.forecaster == model)
                       & (base.lead == h) & (base.origin_date == df["date"].iloc[kp])]
            assert len(rec) == 1, (zone, model, h, len(rec))
            rec = rec.iloc[0]
            d_pt = abs(fw["leads"][h]["point_area_frac"] - float(rec.fcst))
            diffs["frozen_baseline_fcst"].append(d_pt)
            msg = (f"  {zone:11s} {model:18s} L{h} origin={fw['origin_date']} "
                   f"|d_point|={d_pt:.3e}")
            if h == 1 and spec["occurrence_l1"]:
                d_pr = abs(fw["leads"][1]["occurrence_prob_q90"] - float(rec.prob))
                diffs["frozen_baseline_prob_L1"].append(d_pr)
                msg += f"  |d_prob|={d_pr:.3e}"
            log(msg)

    # ---- 6. FROZEN SEBS onset vs lim_k12 records (via LIVE-field ingest) --
    # Feeds the frozen onset path through load_live_field() on the SEALED nc
    # (exercising point-4 ingestion) at the common scored LIM origin (2026-05).
    log("\n[6] FROZEN sebs_onset_watch_frozen vs lim_long_records.parquet "
        "(pinned coeffs; live field via load_live_field on the sealed nc)")
    live = load_live_field(SNAP029 / "outputs" / "broadbasin_oisst_monthly.nc")
    onset_leads = DEPLOY_MAP["sebs"]["onset_watch_leads"]
    max_onset_lead = max(onset_leads)
    dfs = pd.read_csv(SNAP028 / "outputs" / "sebs_monthly.csv")
    dfs["date"] = pd.to_datetime(dfs["date"])
    dfs = dfs.sort_values("date").reset_index(drop=True)

    def _mk(ts):
        ts = pd.Timestamp(ts)
        return ts.year * 12 + ts.month - 1
    dkeys = dfs["date"].map(_mk).to_numpy(int)
    fkeys = np.array([_mk(d) for d in live.dates])
    ko_key = int(min(fkeys[-1], dkeys[-1] - max_onset_lead))
    kidx = int(np.where(dkeys == ko_key)[0][0])
    fw = sebs_onset_watch_frozen(dfs.iloc[:kidx + 1], live, mani, leads=onset_leads)
    for h in onset_leads:
        rec = lim[(lim.lead == h) & (lim.origin_date == dfs["date"].iloc[kidx])]
        assert len(rec) == 1, (h, len(rec))
        rec = rec.iloc[0]
        Lh = fw["leads"][h]
        d_pt = abs(Lh["point_area_frac"] - float(rec.fcst))
        d_pr = abs(Lh["onset_prob_q90"] - float(rec.prob))
        d_dp = abs(Lh["paper_default_threshold"] - float(rec.onset_decision_p))
        diffs["frozen_lim_fcst"].append(d_pt)
        diffs["frozen_lim_prob"].append(d_pr)
        diffs["frozen_lim_decision_p"].append(d_dp)
        log(f"  sebs lim_k12 L{h} origin={fw['origin_date']} "
            f"|d_point|={d_pt:.3e} |d_prob|={d_pr:.3e} "
            f"|d_decision_p|={d_dp:.3e} watch={Lh['watch']}")

    # ---- 7. NO-REFIT structural guarantee (gated) ------------------------
    # The frozen path must NEVER re-estimate phi / sigma_eps / the LIM / the
    # isotonic link / any threshold on live data. Patch every fitting entry
    # point to raise; re-run the frozen path; PASS iff nothing fires.
    log("\n[7] NO-REFIT structural check: frozen path must not call any "
        ".fit / estimator on live data")
    import stage3_lim as _L
    from sklearn.isotonic import IsotonicRegression as _Iso
    refit_ok = True
    refit_calls = []

    def _boom(name):
        def _f(*a, **k):
            refit_calls.append(name)
            raise AssertionError(f"frozen path re-estimated '{name}' on live data")
        return _f

    saved = {
        ("H", "DampedPersistence.fit"): H.DampedPersistence.fit,
        ("H", "Climatology.fit"): H.Climatology.fit,
        ("H", "ar1_phi"): H.ar1_phi,
        ("H", "quantile_threshold"): H.quantile_threshold,
        ("L", "build_many"): _L.build_many,
        ("L", "LIMFit.fit"): _L.LIMFit.fit,
        ("Iso", "fit"): _Iso.fit,
    }
    H.DampedPersistence.fit = _boom("DampedPersistence.fit")
    H.Climatology.fit = _boom("Climatology.fit")
    H.ar1_phi = _boom("ar1_phi")
    H.quantile_threshold = _boom("quantile_threshold")
    _L.build_many = _boom("build_many")
    _L.LIMFit.fit = _boom("LIMFit.fit")
    _Iso.fit = _boom("IsotonicRegression.fit")
    try:
        for zone in DEPLOY_MAP:
            dfz = pd.read_csv(SNAP028 / "outputs" / f"{zone}_monthly.csv")
            dfz["date"] = pd.to_datetime(dfz["date"])
            dfz = dfz.sort_values("date").reset_index(drop=True)
            forecast_frozen(dfz, zone, mani, leads=(1, 2, 3))
        sebs_onset_watch_frozen(dfs.iloc[:kidx + 1], live, mani, leads=onset_leads)
    except AssertionError as e:
        refit_ok = False
        log(f"  FAIL: {e}")
    finally:
        H.DampedPersistence.fit = saved[("H", "DampedPersistence.fit")]
        H.Climatology.fit = saved[("H", "Climatology.fit")]
        H.ar1_phi = saved[("H", "ar1_phi")]
        H.quantile_threshold = saved[("H", "quantile_threshold")]
        _L.build_many = saved[("L", "build_many")]
        _L.LIMFit.fit = saved[("L", "LIMFit.fit")]
        _Iso.fit = saved[("Iso", "fit")]
    log(f"  no-refit: {'OK — no estimator fired' if refit_ok else 'FAIL'} "
        f"({len(refit_calls)} refit call(s) intercepted)")

    # ---- verdict ---------------------------------------------------------
    log("\n" + "=" * 78)
    log("MAX ABS DIFF PER FIELD (gated):")
    ok = True
    for name, vals in diffs.items():
        mx = max(vals) if vals else float("nan")
        status = "OK" if mx <= TOL else "FAIL"
        ok &= (mx <= TOL)
        log(f"  {name:22s} n={len(vals):2d}  max_abs_diff={mx:.3e}  [{status}]")
    log(f"  {'frozen_no_refit':22s}          {'':13s} "
        f"[{'OK' if refit_ok else 'FAIL'}]")
    ok &= refit_ok
    log("")
    log("IDENTITY CHECK: " + ("PASS — re-fit AND frozen paths reproduce the "
                              "paper hindcast at the final/common origins "
                              "(machine precision), and the frozen path performs "
                              "no live re-estimation"
                              if ok else "FAIL — wrapper drift detected"))
    _flush()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
