"""Percentile-based risk score for regional MHW state.

For each day computes:
  - Percentile rank of area_frac, Ibar, Dbar, Cbar within reference distribution
  - Composite risk score = weighted average of percentile ranks (0–100)

Risk levels:
    0–33  : Normal   (green)
    33–66 : Elevated (orange)
    66–100: High Risk (red)

Reference distribution:
    mode=frozen   — built once from all available data (test year as proxy
                    until full backfill; rebuilt with mhw-compute-risk --rebuild)
    mode=incremental — grows daily (not implemented; future extension)

Coverage-aware (vintage #7 / D1): pass ``eligible`` and only eligible days (unknown share ≤ 0.25)
form the reference distribution; rejected days get no score (NaN, level "Incomplete coverage").

CLI:
    mhw-compute-risk --region goa [--ref-start YYYY-MM-DD --ref-end YYYY-MM-DD]
    mhw-compute-risk --region goa --record      # D1 record in, board risk folder out
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import percentileofscore

from mhw.climatology.build_mu_theta import PROJECT_ROOT, _load_config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AGG_DIR  = PROJECT_ROOT / "data" / "derived" / "aggregates_region"
RISK_DIR = PROJECT_ROOT / "data" / "derived" / "risk"

# Metric weights for composite score
RISK_WEIGHTS: dict[str, float] = {
    "area_frac": 0.40,
    "Ibar":      0.25,
    "Dbar":      0.25,
    "Cbar":      0.10,
}

RISK_THRESHOLDS = [(33.0, "Normal", "green"), (66.0, "Elevated", "orange"), (100.0, "High Risk", "red")]
LEVEL_INCOMPLETE = "Incomplete coverage"


def _pct_rank(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Percentile rank of each value in `values` against `reference` (0–100)."""
    return np.array([
        percentileofscore(reference, v, kind="rank")
        for v in values
    ], dtype=np.float32)


def compute_risk_table(
    df: pd.DataFrame,
    ref_df: pd.DataFrame | None = None,
    eligible: np.ndarray | None = None,
) -> pd.DataFrame:
    """Compute risk scores for every row in df.

    Parameters
    ----------
    df     : region_daily DataFrame (date, area_frac, Ibar, Dbar, Cbar, Obar)
    ref_df : reference distribution DataFrame; defaults to df itself (proxy mode)
    eligible : optional boolean mask aligned with df. Ineligible rows are dropped from the
               default reference and scored NaN with level "Incomplete coverage".

    Returns
    -------
    DataFrame with columns: date, area_frac_pct, Ibar_pct, Dbar_pct,
                            Cbar_pct, composite_risk, risk_level
    """
    ok = np.ones(len(df), dtype=bool) if eligible is None else np.asarray(eligible, dtype=bool)
    if ref_df is None:
        ref_df = df[ok]   # test-year proxy

    result = pd.DataFrame({"date": df["date"].values})

    # Percentile ranks
    pct_cols = {}
    for col in RISK_WEIGHTS:
        ref_vals = ref_df[col].values.astype(float)
        cur_vals = df[col].values.astype(float)
        pct = np.full(len(df), np.nan, dtype=np.float32)
        pct[ok] = _pct_rank(cur_vals[ok], ref_vals)
        pct_cols[f"{col}_pct"] = pct
        result[f"{col}_pct"] = pct_cols[f"{col}_pct"]

    # Composite score (weighted average)
    composite = np.zeros(len(df), dtype=np.float32)
    for col, w in RISK_WEIGHTS.items():
        composite += w * pct_cols[f"{col}_pct"]
    result["composite_risk"] = composite.astype(np.float32)

    # Risk level label
    def _level(score: float) -> str:
        if np.isnan(score):
            return LEVEL_INCOMPLETE
        for threshold, label, _ in RISK_THRESHOLDS:
            if score <= threshold:
                return label
        return "High Risk"

    result["risk_level"] = [_level(s) for s in result["composite_risk"]]
    return result


def save_risk_table(risk_df: pd.DataFrame, region_id: str, out_dir: Path | None = None) -> Path:
    """Save risk table to ``out_dir`` (default data/derived/risk/)/risk_{region}.parquet."""
    out_dir = RISK_DIR if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"risk_{region_id}.parquet"
    risk_df.to_parquet(out, index=False)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compute MHW risk scores from region_daily metrics.")
    p.add_argument("--region",    default="goa")
    p.add_argument("--ref-start", default=None, help="Reference period start YYYY-MM-DD")
    p.add_argument("--ref-end",   default=None, help="Reference period end YYYY-MM-DD")
    p.add_argument("--record", action="store_true",
                   help="Read the staged D1 record (aggregate + coverage) and write to its risk folder")
    args = p.parse_args(argv)

    eligible = None
    out_dir = None
    if args.record:
        from mhw import record
        days = record.load_zone(args.region)
        if days is None:
            print(f"ERROR: staged record for {args.region} not found under {record.record_dir()}")
            return 1
        df = days[["date", *RISK_WEIGHTS, "Obar"]].copy()
        eligible = days["eligible"].to_numpy()
        out_dir = record.risk_dir()
    else:
        agg_path = AGG_DIR / f"region_daily_{args.region}.parquet"
        if not agg_path.exists():
            print(f"ERROR: {agg_path} not found. Run mhw-aggregate first.")
            return 1
        df = pd.read_parquet(agg_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Reference window (eligible days only when coverage-aware)
    ref_df = df.copy() if eligible is None else df[eligible].copy()
    if args.ref_start:
        ref_df = ref_df[ref_df["date"] >= pd.to_datetime(args.ref_start).date()]
    if args.ref_end:
        ref_df = ref_df[ref_df["date"] <= pd.to_datetime(args.ref_end).date()]

    print(f"Computing risk scores for {args.region} ({len(df)} days, "
          f"reference: {len(ref_df)} days) …")

    risk_df = compute_risk_table(df, ref_df, eligible=eligible)
    out = save_risk_table(risk_df, args.region, out_dir)

    # Summary
    latest = risk_df.iloc[-1]
    peak   = risk_df.loc[risk_df["composite_risk"].idxmax()]
    print(f"  Latest ({df['date'].iloc[-1]}): "
          f"composite_risk={latest['composite_risk']:.1f} → {latest['risk_level']}")
    print(f"  Peak   ({peak['date']}):  "
          f"composite_risk={peak['composite_risk']:.1f} → {peak['risk_level']}")
    print(f"  Saved → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
