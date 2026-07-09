"""Analytics over the catalog — aggregation, cross-dataset joins, correlation/regression, ranking.

All functions read through :mod:`mhw.assistant.catalog` (grounded — the agent never passes raw data
for a calculation) and return JSON-able dicts. Cross-dataset work reduces each side to its join-key
grain (annual mean) before aligning, so "cold pool vs snow crab" joins on ``year`` even though the two
datasets key region differently.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mhw.assistant.catalog import CATALOG, load_dataset

_AGGS = {"sum", "mean", "median", "min", "max", "count", "std"}
_EMPTY_NOTE = "0 rows after filters — do NOT chart or state values; check names with list_dimension_values"


def _apply_filters(df: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    if df.empty or not filters:
        return df
    f = dict(filters)
    ymin, ymax = f.pop("year_min", None), f.pop("year_max", None)
    if "year" in df.columns:
        if ymin is not None:
            df = df[df["year"] >= int(ymin)]
        if ymax is not None:
            df = df[df["year"] <= int(ymax)]
    elif "date" in df.columns:
        d = pd.to_datetime(df["date"])
        if ymin is not None:
            df = df[d >= pd.Timestamp(int(ymin), 1, 1)]
        if ymax is not None:
            df = df[d <= pd.Timestamp(int(ymax), 12, 31)]
    for k, v in f.items():
        if k in df.columns:
            vals = v if isinstance(v, (list, tuple, set)) else [v]
            df = df[df[k].astype(str).isin([str(x) for x in vals])]
    return df


def _load_filtered(dataset: str, filters: dict | None, data_root: Path | None) -> pd.DataFrame:
    if dataset not in CATALOG:
        return pd.DataFrame()
    return _apply_filters(load_dataset(dataset, data_root=data_root), filters)


def aggregate(dataset, group_by, measure, agg="mean", filters=None, data_root=None):
    if agg not in _AGGS:
        return {"error": f"agg must be one of {sorted(_AGGS)}"}
    df = _load_filtered(dataset, filters, data_root)
    if df.empty:
        return {"records": [], "note": _EMPTY_NOTE}
    gb = group_by if isinstance(group_by, list) else [group_by]
    gb = [g for g in gb if g in df.columns]
    if not gb or (measure not in df.columns and agg != "count"):
        return {"error": f"bad group_by/measure for {dataset!r}",
                "valid_dimensions": list(CATALOG[dataset].dimensions),
                "valid_measures": CATALOG[dataset].measure_cols}
    series = df.groupby(gb)[measure] if measure in df.columns else df.groupby(gb).size()
    g = (series.size().reset_index(name=measure) if agg == "count"
         else getattr(series, agg)().reset_index())
    return {"dataset": dataset, "group_by": gb, "measure": measure, "agg": agg,
            "n": len(g), "records": g.to_dict("records")}


def _annual_side(dataset, measure, filters, on, data_root):
    df = _load_filtered(dataset, filters, data_root)
    if df.empty or measure not in df.columns:
        return None
    if "year" in on and "year" not in df.columns and "date" in df.columns:
        df = df.assign(year=pd.to_datetime(df["date"]).dt.year)
    keys = [k for k in on if k in df.columns]
    if not keys:
        return None
    return df.groupby(keys)[measure].mean().reset_index()


def join_series(dataset_a, measure_a, dataset_b, measure_b, on=("year",),
                filters_a=None, filters_b=None, data_root=None):
    on = list(on)
    a = _annual_side(dataset_a, measure_a, filters_a, on, data_root)
    b = _annual_side(dataset_b, measure_b, filters_b, on, data_root)
    if a is None or b is None:
        return {"error": "one side has no rows or lacks the measure", "records": []}
    keys = [k for k in on if k in a.columns and k in b.columns]
    if not keys:
        return {"error": f"no shared join key in {on}", "records": []}
    a = a.rename(columns={measure_a: "a"})
    b = b.rename(columns={measure_b: "b"})
    m = a.merge(b, on=keys, how="inner").dropna(subset=["a", "b"])
    recs = [{**{k: r[k] for k in keys}, "a": float(r["a"]), "b": float(r["b"])}
            for _, r in m.iterrows()]
    return {"on": keys, "measure_a": measure_a, "measure_b": measure_b, "n": len(recs),
            "records": recs}


def correlate(dataset_a, measure_a, dataset_b, measure_b, on=("year",),
              filters_a=None, filters_b=None, data_root=None):
    j = join_series(dataset_a, measure_a, dataset_b, measure_b, on, filters_a, filters_b, data_root)
    recs = j.get("records", [])
    if len(recs) < 3:
        return {"error": "need ≥3 aligned points to correlate", "n": len(recs), **({} if "error" not in j else {"detail": j["error"]})}
    x = np.array([r["a"] for r in recs], float)
    y = np.array([r["b"] for r in recs], float)
    r = float(np.corrcoef(x, y)[0, 1])
    slope, intercept = (float(v) for v in np.polyfit(x, y, 1))
    xs = [float(x.min()), float(x.max())]
    return {
        "n": len(recs), "pearson_r": round(r, 4), "r_squared": round(r * r, 4),
        "slope": slope, "intercept": intercept,
        "points": {"x": x.tolist(), "y": y.tolist()},
        "fit_line": {"x": xs, "y": [slope * xs[0] + intercept, slope * xs[1] + intercept]},
        "labels": {"x": f"{dataset_a}.{measure_a}", "y": f"{dataset_b}.{measure_b}"},
        "join_keys": j.get("on"),
    }


def rank(dataset, measure, by, top_n=10, agg="sum", filters=None, ascending=False, data_root=None):
    a = aggregate(dataset, by, measure, agg, filters, data_root)
    if not a.get("records"):
        return a
    recs = sorted(a["records"], key=lambda r: (r.get(measure) is None, r.get(measure)),
                  reverse=not ascending)[:int(top_n)]
    return {"dataset": dataset, "by": a["group_by"], "measure": measure, "agg": agg,
            "top_n": int(top_n), "ascending": ascending, "records": recs}


def summary_stats(dataset, measure, filters=None, data_root=None):
    df = _load_filtered(dataset, filters, data_root)
    if df.empty or measure not in df.columns:
        return {"error": "no rows or unknown measure", "records": []}
    s = pd.to_numeric(df[measure], errors="coerce").dropna()
    if s.empty:
        return {"error": "measure has no numeric values"}
    out = {"dataset": dataset, "measure": measure, "n": int(s.size),
           "mean": float(s.mean()), "std": float(s.std()), "min": float(s.min()),
           "max": float(s.max()), "median": float(s.median())}
    tcol = "year" if "year" in df.columns else ("date" if "date" in df.columns else None)
    if tcol:
        x = (pd.to_datetime(df["date"]).dt.year if tcol == "date" else df["year"]).astype(float)
        xv, yv = x.loc[s.index].values, s.values
        if len(np.unique(xv)) > 1:
            out["trend_per_year"] = round(float(np.polyfit(xv, yv, 1)[0]), 6)
    return out


def descriptive_indicators(dataset, measure, filters=None, year=None, data_root=None):
    """Anomaly / percentile / ordinal rank / analog years for a target year vs the annual series."""
    from mhw.bottom.indicators import (
        analog_years, anomaly, ordinal_rank, percentile_rank,
    )
    df = _load_filtered(dataset, filters, data_root)
    if df.empty or measure not in df.columns:
        return {"error": "no rows or unknown measure"}
    if "year" not in df.columns and "date" in df.columns:
        df = df.assign(year=pd.to_datetime(df["date"]).dt.year)
    if "year" not in df.columns:
        return {"error": "dataset has no annual axis"}
    ann = df.groupby("year")[measure].mean().dropna()
    if len(ann) < 3:
        return {"error": "need ≥3 years"}
    years = ann.index.astype(int).tolist()
    vals = ann.values.astype(float).tolist()
    tgt_year = int(year) if year is not None else years[-1]
    if tgt_year not in years:
        return {"error": f"year {tgt_year} not in series", "available_years": years}
    val = vals[years.index(tgt_year)]
    anom = anomaly(val, vals)
    return {
        "dataset": dataset, "measure": measure, "year": tgt_year, "value": round(val, 4),
        "anomaly": round(anom, 4),
        "direction": "above typical" if anom > 0 else ("below typical" if anom < 0 else "typical"),
        "percentile_rank": round(percentile_rank(val, vals), 1),
        "ordinal_rank_smallest": ordinal_rank(val, vals, smallest=True),
        "analog_years": analog_years(tgt_year, years, vals, k=3),
    }
