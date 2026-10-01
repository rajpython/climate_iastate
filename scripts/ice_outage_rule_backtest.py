"""Back-test ice-outage rules (2026-10-01): hide the ice field over outage-shaped windows in normal years and
score each candidate against the real field. Run from the repo root: python scripts/ice_outage_rule_backtest.py
The chosen rule (F: interpolated ice, open water above 2 degC) is in mhw.climatology.ice_outage."""
import numpy as np  # noqa: F401  (kept explicit for readers)
import numpy as np, pandas as pd, xarray as xr
TH = 0.15
def load(z, y0, y1):
    S, I, T = [], [], []
    for y in range(y0, y1 + 1):
        ds = xr.open_dataset(f"data/raw/oisst_{z}_{y}.nc"); S.append(ds.sst.values); I.append(ds.ice.values)
        T.append(pd.DatetimeIndex(ds.time.values).normalize()); ds.close()
    return np.concatenate(S), np.concatenate(I), T[0].append(T[1:])
def rules(s, before, after, frac):
    b = np.fmax(np.nan_to_num(before), np.nan_to_num(after))
    lin = (1 - frac) * np.nan_to_num(before) + frac * np.nan_to_num(after)
    return {"A_bracket": b > TH,
            "B_bracket_and_sst<=0": (b > TH) & (s <= 0.0),
            "B_bracket_and_sst<=-0.5": (b > TH) & (s <= -0.5),
            "C_linear_interp": lin > TH,
            "D_interp_or_(bracket&sst<=-1.0)": (lin > TH) | ((b > TH) & (s <= -1.0)),
            "F_interp&sst<=2": (lin > TH) & (s <= 2.0),
            "G_interp&sst<=1": (lin > TH) & (s <= 1.0),
            "H_interp&sst<=0.5": (lin > TH) & (s <= 0.5)}
windows = {"melt Apr18-Jun30": ("04-18", "06-30"), "winter Jan07-Feb28": ("01-07", "02-28"), "early-winter Dec06-Jan10": ("12-06", "01-10")}
years = [y for y in range(1992, 2025) if y not in (2016, 2017, 2020)]
tot = {}
for z in ["sebs", "nbs", "chukchi", "beaufort"]:
    Sx, Ix, Tx = load(z, 1991, 2025)
    for wname, (a, b) in windows.items():
        for y in years[::3]:
            y1 = y + 1 if wname.startswith("early") else y
            t0, t1 = pd.Timestamp(f"{y}-{a}"), pd.Timestamp(f"{y1}-{b}")
            i0, i1 = Tx.get_loc(t0), Tx.get_loc(t1)
            before, after = Ix[i0 - 1], Ix[i1 + 1]
            n = i1 - i0 + 1
            for k in range(n):
                s = Sx[i0 + k]; truth = np.nan_to_num(Ix[i0 + k]) > TH; f = np.isfinite(s)
                for r, m in rules(s, before, after, (k + 1) / (n + 1)).items():
                    key = (wname, r); c = tot.setdefault(key, [0, 0, 0, 0])
                    c[0] += int((m & truth & f).sum()); c[1] += int((truth & f).sum())
                    c[2] += int((m & ~truth & f).sum()); c[3] += int((~truth & f).sum())
for (w, r), (tp, p, fp, nn) in sorted(tot.items()):
    print(f"{w:26s} {r:32s} ice caught {tp/p:.3f}   open wrongly masked {fp/max(nn,1):.3f}")
