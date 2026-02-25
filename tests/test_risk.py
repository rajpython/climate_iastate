"""Unit and integration tests for risk scoring.

Unit tests use synthetic DataFrames; integration tests use on-disk parquet.
No ERDDAP, no network calls.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mhw.states.risk import RISK_THRESHOLDS, RISK_WEIGHTS, _pct_rank, compute_risk_table

EXPECTED_ROWS = 15_706
VALID_RISK_LEVELS = {"Normal", "Elevated", "High Risk"}


# ---------------------------------------------------------------------------
# Helpers — synthetic DataFrames
# ---------------------------------------------------------------------------

def _make_synthetic_df(n: int = 10, seed: int = 0) -> pd.DataFrame:
    """Return a plausible region_daily DataFrame with n rows."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "date": pd.date_range("2010-01-01", periods=n),
            "area_frac": rng.uniform(0.0, 1.0, n),
            "Ibar": rng.uniform(0.0, 3.0, n),
            "Dbar": rng.uniform(0.0, 60.0, n),
            "Cbar": rng.uniform(0.0, 200.0, n),
            "Obar": rng.uniform(0.0, 1.0, n),
        }
    )


def _make_reference_df(n: int = 100) -> pd.DataFrame:
    """Return a reference distribution spanning [0, max_val] for each metric."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2000-01-01", periods=n),
            "area_frac": np.linspace(0.0, 1.0, n),
            "Ibar": np.linspace(0.0, 5.0, n),
            "Dbar": np.linspace(0.0, 120.0, n),
            "Cbar": np.linspace(0.0, 600.0, n),
            "Obar": np.linspace(0.0, 2.0, n),
        }
    )


# ---------------------------------------------------------------------------
# _pct_rank unit tests (2)
# ---------------------------------------------------------------------------

class TestPctRank:
    def test_uniform_reference(self):
        """Value at the midpoint of [0..100] → rank ≈ 50; output in [0, 100]."""
        reference = np.arange(0.0, 101.0, dtype=np.float32)
        result = _pct_rank(np.array([50.0]), reference)
        assert 0.0 <= result[0] <= 100.0
        assert abs(result[0] - 50.0) <= 5.0  # within 5 percentile points

    def test_single_value_reference_no_crash(self):
        """Single-element reference matching query must not crash; rank in (0, 100]."""
        reference = np.array([42.0], dtype=np.float32)
        result = _pct_rank(np.array([42.0]), reference)
        assert result[0] > 0.0
        assert result[0] <= 100.0


# ---------------------------------------------------------------------------
# compute_risk_table unit tests (4)
# ---------------------------------------------------------------------------

class TestComputeRiskTable:
    def test_output_columns(self):
        """Output DataFrame must contain the expected set of columns."""
        df = _make_synthetic_df()
        risk_df = compute_risk_table(df)
        expected = {
            "date",
            "area_frac_pct",
            "Ibar_pct",
            "Dbar_pct",
            "Cbar_pct",
            "composite_risk",
            "risk_level",
        }
        assert set(risk_df.columns) == expected

    def test_composite_formula(self):
        """composite_risk must equal the weighted sum of percentile rank columns."""
        df = _make_synthetic_df(n=20)
        risk_df = compute_risk_table(df)

        expected = (
            RISK_WEIGHTS["area_frac"] * risk_df["area_frac_pct"]
            + RISK_WEIGHTS["Ibar"]     * risk_df["Ibar_pct"]
            + RISK_WEIGHTS["Dbar"]     * risk_df["Dbar_pct"]
            + RISK_WEIGHTS["Cbar"]     * risk_df["Cbar_pct"]
        )
        np.testing.assert_allclose(
            risk_df["composite_risk"].values,
            expected.values,
            rtol=1e-5,
            err_msg="composite_risk does not match weighted sum of percentile ranks",
        )

    def test_risk_level_normal(self):
        """Row with composite_risk ≤ 33 must be labelled 'Normal'."""
        ref = _make_reference_df()
        # A single row at the very bottom of the reference → all pct ranks ≈ 1 → composite ≈ 1
        low_row = pd.DataFrame(
            {
                "date": [pd.Timestamp("2000-01-01")],
                "area_frac": [0.0],
                "Ibar": [0.0],
                "Dbar": [0.0],
                "Cbar": [0.0],
                "Obar": [0.0],
            }
        )
        risk_df = compute_risk_table(low_row, ref_df=ref)
        assert risk_df["composite_risk"].iloc[0] <= 33.0
        assert risk_df["risk_level"].iloc[0] == "Normal"

    def test_risk_level_high(self):
        """Row with composite_risk > 66 must be labelled 'High Risk'."""
        ref = _make_reference_df()
        high_row = pd.DataFrame(
            {
                "date": [pd.Timestamp("2000-01-01")],
                "area_frac": [1.0],
                "Ibar": [5.0],
                "Dbar": [120.0],
                "Cbar": [600.0],
                "Obar": [2.0],
            }
        )
        risk_df = compute_risk_table(high_row, ref_df=ref)
        assert risk_df["composite_risk"].iloc[0] > 66.0
        assert risk_df["risk_level"].iloc[0] == "High Risk"


# ---------------------------------------------------------------------------
# Integration tests using goa_risk fixture (2)
# ---------------------------------------------------------------------------

class TestGoaRiskIntegration:
    def test_row_count_and_composite_range(self, goa_risk):
        """GOA risk table must have 15,706 rows and composite_risk ∈ [0, 100]."""
        assert len(goa_risk) == EXPECTED_ROWS, (
            f"Expected {EXPECTED_ROWS} rows, got {len(goa_risk)}"
        )
        assert goa_risk["composite_risk"].between(0.0, 100.0).all(), (
            "composite_risk must be in [0, 100]"
        )

    def test_risk_level_valid_and_consistent(self, goa_risk):
        """risk_level values must be in the valid set and match score boundaries."""
        assert set(goa_risk["risk_level"]).issubset(VALID_RISK_LEVELS), (
            f"Unexpected risk levels: {set(goa_risk['risk_level']) - VALID_RISK_LEVELS}"
        )

        # Verify consistency with thresholds
        for _, row in goa_risk[["composite_risk", "risk_level"]].iterrows():
            score = float(row["composite_risk"])
            level = row["risk_level"]
            if score <= 33.0:
                assert level == "Normal", f"score={score:.1f} should be Normal, got {level}"
            elif score <= 66.0:
                assert level == "Elevated", f"score={score:.1f} should be Elevated, got {level}"
            else:
                assert level == "High Risk", f"score={score:.1f} should be High Risk, got {level}"
