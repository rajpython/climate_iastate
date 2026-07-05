"""Pure-transform tests for the Economic SAFE ingest (no IO)."""
import pandas as pd

from mhw.econ.areas import fmp_area_code, fmp_area_label
from mhw.econ.confidential import normalize_suppression
from mhw.econ.ingest_safe import tidy_report
from mhw.econ.safe_reports import get_report


def test_fmp_area_normalization():
    assert fmp_area_code("Bering Sea and Aleutian Islands") == "bsai"
    assert fmp_area_code("Gulf of Alaska") == "goa"
    assert fmp_area_code("All Alaska") == "ak"
    assert fmp_area_code("Narnia") is None
    assert fmp_area_label("goa") == "Gulf of Alaska"


def test_tidy_report_gfsafe002():
    raw = pd.DataFrame({
        "FMP_AREA": ["Bering Sea and Aleutian Islands", "Gulf of Alaska"],
        "HARVEST_SECTOR": ["All Sectors", "All Sectors"],
        "SPECIES_GROUP": ["Pollock", "Pacific Cod"],
        "YEAR": [2024, 2024],
        "RETAINED_CATCH_MT": ["1298586", "20000"],
        "EXVESSEL_VALUE": ["373983694", "50000000"],
    })
    out = tidy_report(raw, get_report("gfsafe002"))
    assert list(out["area_code"]) == ["bsai", "goa"]
    assert out["area_label"].iloc[0] == "Bering Sea & Aleutian Islands"
    assert out["year"].dtype == "Int64" and out["year"].iloc[0] == 2024
    # measures coerced to numeric
    assert out["retained_catch_mt"].iloc[0] == 1298586
    assert out["exvessel_value"].iloc[0] == 373983694
    assert (out["report_id"] == "gfsafe002").all()
    assert (out["family"] == "value").all()
    assert "fmp_area" not in out.columns


def test_suppression_bands():
    raw = pd.DataFrame({"PERCENT_VAL_SUPPRESSED": ["0%", "1-5%", "100%", "weird", None]})
    out = normalize_suppression(raw, "PERCENT_VAL_SUPPRESSED")
    assert list(out["suppressed"]) == [False, True, True, False, False]
    assert out["suppressed_pct"].iloc[1] == 3.0
    assert out["suppressed_band"].iloc[2] == "100%"
    assert pd.isna(out["suppressed_band"].iloc[3])          # 'weird' not a band
    assert "PERCENT_VAL_SUPPRESSED" not in out.columns


def test_tidy_report_with_suppression():
    raw = pd.DataFrame({
        "FMP_AREA": ["Bering Sea and Aleutian Islands"],
        "GEAR": ["Trawl"], "SECTOR": ["Catcher Vessels"], "SPECIES": ["Pollock"],
        "YEAR": [2024], "EXVES_VAL": [100], "PERCENT_VAL_SUPPRESSED": ["1-5%"],
    })
    out = tidy_report(raw, get_report("gfsafe007"))
    assert out["suppressed"].iloc[0] is True or bool(out["suppressed"].iloc[0])
    assert "percent_val_suppressed" not in out.columns
