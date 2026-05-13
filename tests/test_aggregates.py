"""Schema and invariant tests for regional aggregate parquet files.

Integration tests use on-disk parquet — no ERDDAP, no network calls.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parents[1]
AGG_DIR = PROJECT_ROOT / "data" / "derived" / "aggregates_region"

BACKFILL_START = pd.Timestamp("1982-01-01")
REQUIRED_COLS = {"date", "area_frac", "Ibar", "Dbar", "Cbar", "Obar"}
FLOAT_COLS = ["area_frac", "Ibar", "Dbar", "Cbar", "Obar"]


def _expected_row_count(df: pd.DataFrame) -> int:
    """One row per day from BACKFILL_START to the file's latest date (continuity check)."""
    end = pd.to_datetime(df["date"]).max()
    return (end - BACKFILL_START).days + 1


# ---------------------------------------------------------------------------
# Schema tests (GOA as canonical fixture)
# ---------------------------------------------------------------------------

class TestGoaSchema:
    def test_required_columns_present(self, goa_agg):
        assert REQUIRED_COLS.issubset(set(goa_agg.columns)), (
            f"Missing columns: {REQUIRED_COLS - set(goa_agg.columns)}"
        )

    def test_row_count(self, goa_agg):
        expected = _expected_row_count(goa_agg)
        assert len(goa_agg) == expected, (
            f"Expected {expected} rows ({BACKFILL_START.date()} → "
            f"{pd.to_datetime(goa_agg['date']).max().date()}), got {len(goa_agg)}"
        )

    def test_date_parseable(self, goa_agg):
        parsed = pd.to_datetime(goa_agg["date"], errors="coerce")
        assert parsed.notna().all(), "All dates must parse without errors"

    def test_float_columns_numeric(self, goa_agg):
        for col in FLOAT_COLS:
            assert pd.api.types.is_numeric_dtype(goa_agg[col]), (
                f"Column '{col}' must be numeric, got {goa_agg[col].dtype}"
            )


# ---------------------------------------------------------------------------
# Invariant tests (GOA)
# ---------------------------------------------------------------------------

class TestGoaInvariants:
    def test_area_frac_in_bounds(self, goa_agg):
        assert goa_agg["area_frac"].between(0.0, 1.0).all(), (
            "area_frac must be in [0, 1]"
        )

    def test_metric_columns_non_negative(self, goa_agg):
        for col in ["Ibar", "Dbar", "Cbar", "Obar"]:
            assert (goa_agg[col] >= 0).all(), f"{col} must be >= 0"

    def test_no_nulls(self, goa_agg):
        null_counts = goa_agg[list(REQUIRED_COLS)].isnull().sum()
        assert null_counts.sum() == 0, f"Unexpected NaN values:\n{null_counts[null_counts > 0]}"

    def test_ibar_zero_when_inactive(self, goa_agg):
        """When area_frac == 0 (no active cells), Ibar must be 0 (conditional mean)."""
        inactive = goa_agg[goa_agg["area_frac"] == 0.0]
        if len(inactive) > 0:
            assert (inactive["Ibar"] == 0.0).all(), (
                "Ibar must equal 0 when area_frac == 0"
            )


# ---------------------------------------------------------------------------
# Multi-region parametrize
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("region", ["goa", "ebs", "nbs", "chukchi", "beaufort"])
def test_all_regions_schema(region):
    """Every region parquet must be continuous from 1982-01-01, have required columns,
    and area_frac ∈ [0,1]."""
    path = AGG_DIR / f"region_daily_{region}.parquet"
    if not path.exists():
        pytest.skip(f"Parquet not found (run mhw-backfill first): {path}")

    df = pd.read_parquet(path)
    expected = _expected_row_count(df)
    assert len(df) == expected, (
        f"[{region}] Expected {expected} rows "
        f"({BACKFILL_START.date()} → {pd.to_datetime(df['date']).max().date()}), got {len(df)}"
    )
    assert REQUIRED_COLS.issubset(set(df.columns)), (
        f"[{region}] Missing columns: {REQUIRED_COLS - set(df.columns)}"
    )
    assert df["area_frac"].between(0.0, 1.0).all(), (
        f"[{region}] area_frac out of [0, 1]"
    )
