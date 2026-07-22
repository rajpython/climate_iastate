"""Cross-validate our MHW onset rate against Oliver's marineHeatWaves reference code.

Purpose (obl069 / onset decision-of-record SDL-030): empirically confirm that our
`consecutive_first` engine's event detection + onset rate reproduce Oliver Hobday-co-author
`marineHeatWaves` reference implementation EXACTLY — including the (rare, small) negative onset
values that arise under the Hobday-faithful signed mean-referenced intensity.

Method: feed Oliver's VERBATIM detection+onset code our sealed climatology (θ90/μ) and
`temp = I + μ` (which reproduces our exceedance `x` and `relSeas` exactly), so the test isolates
the DETECTION + ONSET ALGORITHM from climatology-building (θ90 is separately byte-verified against
LOFRA-mini's independently-held sealed θ90). heatwaveR (R) is not run here (source verified
line-for-line identical to Oliver's at named commits — mini/Cobra + dashboard).

Reference: ecjoliver/marineHeatWaves @ marineHeatWaves.py (rate_onset); robwschlegel/heatwaveR
@ R/detect_event.R. Hobday et al. (2016) Table 2 defines r_onset in prose only (silent on
sign/clamping/interpolation) — we follow the reference implementation, per SDL-030.

Result (2026-07-22, beaufort cell (0,57), 1982-01-01..2026-07-01):
  58 events; 0 onset mismatches (>1e-4) vs our engine; event-days 841 == 841;
  the beaufort 1995-10-15 negative onset reproduces at -0.0248 exactly.

Run: fetch Oliver's file first (network):
  curl -s https://raw.githubusercontent.com/ecjoliver/marineHeatWaves/master/marineHeatWaves.py -o /tmp/mhw_oliver.py
  .venv/bin/python scripts/validate_onset_vs_marineheatwaves.py --region beaufort --cell 0 57
"""
from __future__ import annotations
import argparse, glob, re, datetime
from pathlib import Path
import numpy as np
import zarr
from scipy import ndimage

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _region_stores(region: str) -> list[str]:
    p = PROJECT_ROOT / "data" / "derived" / "states_grid"
    return sorted(glob.glob(str(p / f"states_{region}_*.zarr")),
                  key=lambda q: int(re.search(r"_(\d{4})-", q).group(1)))


def oliver_events_onset(temp, seas, thresh, t, *, minDuration=5, maxGap=2):
    """Oliver marineHeatWaves detection + rate_onset, VERBATIM (marineHeatWaves.py:303-403),
    driven with an injected climatology (seas/thresh). Returns list of (date_start, index_start,
    rate_onset), and total event-days."""
    clim = {"seas": np.asarray(seas, float), "thresh": np.asarray(thresh, float)}
    temp = np.asarray(temp, float).copy()
    T = len(temp)
    mhw = {k: [] for k in ("time_start", "time_end", "index_start", "date_start",
                           "duration", "rate_onset")}
    temp[np.isnan(temp)] = clim["seas"][np.isnan(temp)]
    exceed_bool = temp - clim["thresh"]
    exceed_bool[exceed_bool <= 0] = False
    exceed_bool[exceed_bool > 0] = True
    exceed_bool[np.isnan(exceed_bool)] = False
    events, n_events = ndimage.label(exceed_bool)
    for ev in range(1, n_events + 1):
        if (events == ev).sum() < minDuration:
            continue
        mhw["time_start"].append(t[np.where(events == ev)[0][0]])
        mhw["time_end"].append(t[np.where(events == ev)[0][-1]])
    gaps = np.array(mhw["time_start"][1:]) - np.array(mhw["time_end"][0:-1]) - 1
    if len(gaps) > 0:
        while gaps.min() <= maxGap:
            ev = np.where(gaps <= maxGap)[0][0]
            mhw["time_end"][ev] = mhw["time_end"][ev + 1]
            del mhw["time_start"][ev + 1]
            del mhw["time_end"][ev + 1]
            gaps = np.array(mhw["time_start"][1:]) - np.array(mhw["time_end"][0:-1]) - 1
            if len(gaps) == 0:
                break
    out = []
    total_days = 0
    for ev in range(len(mhw["time_start"])):
        tt_start = np.where(t == mhw["time_start"][ev])[0][0]
        tt_end = np.where(t == mhw["time_end"][ev])[0][0]
        relSeas = (temp - clim["seas"])[tt_start:tt_end + 1]
        tt_peak = int(np.argmax(relSeas))
        total_days += len(relSeas)
        if tt_start > 0:
            rel_start = 0.5 * (relSeas[0] + temp[tt_start - 1] - clim["seas"][tt_start - 1])
            rate = (relSeas[tt_peak] - rel_start) / (tt_peak + 0.5)
        else:
            rate = (relSeas[tt_peak] - relSeas[0]) / (1.0 if tt_peak == 0 else tt_peak)
        out.append((datetime.date.fromordinal(int(mhw["time_start"][ev])), tt_start, float(rate)))
    return out, total_days


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="beaufort")
    ap.add_argument("--cell", nargs=2, type=int, default=[0, 57], metavar=("I", "J"))
    args = ap.parse_args(argv)
    i, j = args.cell
    ss = _region_stores(args.region)
    I = np.concatenate([zarr.open_group(s, mode="r")["I"][:, i, j] for s in ss]).astype(float)
    A = np.concatenate([zarr.open_group(s, mode="r")["A"][:, i, j] for s in ss]).astype(int)
    Oours = np.concatenate([zarr.open_group(s, mode="r")["O"][:, i, j] for s in ss]).astype(float)
    cdir = PROJECT_ROOT / "data" / "derived" / "climatology"
    th90 = zarr.open_group(str(cdir / f"theta90_{args.region}.zarr"), mode="r")["theta90"][:, i, j]
    mu = zarr.open_group(str(cdir / f"mu_{args.region}.zarr"), mode="r")["mu"][:, i, j]
    d0 = datetime.date(1982, 1, 1)
    dates = [d0 + datetime.timedelta(days=k) for k in range(len(I))]
    doy = np.array([d.timetuple().tm_yday for d in dates])
    t = np.array([d.toordinal() for d in dates])
    seas, thresh = mu[doy - 1], th90[doy - 1]
    temp = I + seas
    events, total_days = oliver_events_onset(temp, seas, thresh, t)
    mism = sum(1 for (_, ti, o) in events if abs(o - float(Oours[ti])) > 1e-4)
    print(f"{args.region} cell({i},{j}): Oliver events={len(events)}  onset mismatches>1e-4={mism}  "
          f"event-days Oliver={total_days} ours={int(A.sum())}")
    for ds, ti, o in events:
        if o < 0:
            print(f"  negative-onset event {ds}: Oliver={o:.4f}  ours={float(Oours[ti]):.4f}  "
                  f"match={abs(o-float(Oours[ti]))<1e-4}")
    return 0 if mism == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
