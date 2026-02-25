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

CLI:
    mhw-compute-risk --region goa [--ref-start YYYY-MM-DD --ref-end YYYY-MM-DD]
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


def _pct_rank(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Percentile rank of each value in `values` against `reference` (0–100)."""
    return np.array([
        percentileofscore(reference, v, kind="rank")
        for v in values
    ], dtype=np.float32)


def compute_risk_table(
    df: pd.DataFrame,
    ref_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute risk scores for every row in df.

    Parameters
    ----------
    df     : region_daily DataFrame (date, area_frac, Ibar, Dbar, Cbar, Obar)
    ref_df : reference distribution DataFrame; defaults to df itself (proxy mode)

    Returns
    -------
    DataFrame with columns: date, area_frac_pct, Ibar_pct, Dbar_pct,
                            Cbar_pct, composite_risk, risk_level
    """
    if ref_df is None:
        ref_df = df   # test-year proxy

    result = pd.DataFrame({"date": df["date"].values})

    # Percentile ranks
    pct_cols = {}
    for col in RISK_WEIGHTS:
        ref_vals = ref_df[col].values.astype(float)
        cur_vals = df[col].values.astype(float)
        pct_cols[f"{col}_pct"] = _pct_rank(cur_vals, ref_vals)
        result[f"{col}_pct"] = pct_cols[f"{col}_pct"]

    # Composite score (weighted average)
    composite = np.zeros(len(df), dtype=np.float32)
    for col, w in RISK_WEIGHTS.items():
        composite += w * pct_cols[f"{col}_pct"]
    result["composite_risk"] = composite.astype(np.float32)

    # Risk level label
    def _level(score: float) -> str:
        for threshold, label, _ in RISK_THRESHOLDS:
            if score <= threshold:
                return label
        return "High Risk"

    result["risk_level"] = [_level(s) for s in result["composite_risk"]]
    return result


def save_risk_table(risk_df: pd.DataFrame, region_id: str) -> Path:
    """Save risk table to data/derived/risk/risk_{region}.parquet."""
    RISK_DIR.mkdir(parents=True, exist_ok=True)
    out = RISK_DIR / f"risk_{region_id}.parquet"
    risk_df.to_parquet(out, index=False)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description="Compute MHW risk scores from region_daily metrics.")
    p.add_argument("--region",    default="goa")
    p.add_argument("--ref-start", default=None, help="Reference period start YYYY-MM-DD")
    p.add_argument("--ref-end",   default=None, help="Reference period end YYYY-MM-DD")
    args = p.parse_args()

    agg_path = AGG_DIR / f"region_daily_{args.region}.parquet"
    if not agg_path.exists():
        print(f"ERROR: {agg_path} not found. Run mhw-aggregate first.")
        return 1

    df = pd.read_parquet(agg_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Reference window
    ref_df = df.copy()
    if args.ref_start:
        ref_df = ref_df[ref_df["date"] >= pd.to_datetime(args.ref_start).date()]
    if args.ref_end:
        ref_df = ref_df[ref_df["date"] <= pd.to_datetime(args.ref_end).date()]

    print(f"Computing risk scores for {args.region} ({len(df)} days, "
          f"reference: {len(ref_df)} days) …")

    risk_df = compute_risk_table(df, ref_df)
    out = save_risk_table(risk_df, args.region)

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
