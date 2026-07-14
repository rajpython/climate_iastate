"""Tests for the climate-index parsers — pure text parsing, no network."""
import pandas as pd
import pytest

from mhw.fetch.indices import parse_npi

# A miniature of the PSL np.data payload: "<start> <end>" header, year + 12 columns,
# a -999 missing sentinel in the latest partial year, a trailing -999 line, then description text.
_NPI_SAMPLE = """ 2020 2022
2020  1009.123  1014.001  1016.664  1020.682  1016.016  1015.449  1017.244  1017.843  1015.484  1010.816  1010.593  1014.172
2021  1011.996  1010.893  1006.939  1013.548  1015.502  1016.559  1018.756  1017.023  1013.076  1012.413  1008.084  1010.479
2022  1003.891  1010.360  1011.667  1018.706  -999.000  -999.000  -999.000  -999.000  -999.000  -999.000  -999.000  -999.000
-999
Trenberth and Hurrell North Pacific Index (Monthly)
"""


def test_parse_npi_shapes_and_sentinel():
    df = parse_npi(_NPI_SAMPLE)
    # 12 + 12 + 4 real months (8 of 2022 are -999 → dropped)
    assert len(df) == 28
    assert list(df.columns) == ["date", "npi"]
    assert df["date"].iloc[0] == pd.Timestamp("2020-01-01")
    assert df["date"].iloc[-1] == pd.Timestamp("2022-04-01")   # last non-missing month
    assert (df["npi"] > 990).all() and (df["npi"] < 1030).all()
    assert not (df["npi"] <= -999).any()                        # sentinel fully removed


def test_parse_npi_is_sorted_by_date():
    df = parse_npi(_NPI_SAMPLE)
    assert df["date"].is_monotonic_increasing


def test_parse_npi_raises_on_empty_payload():
    with pytest.raises(ValueError, match="zero rows"):
        parse_npi("some header\nno data rows here\n-999\n")
