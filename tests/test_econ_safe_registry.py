"""Registry integrity for the Groundfish Economic SAFE catalog (no IO)."""
from mhw.econ.safe_reports import (
    ALL_REPORTS,
    CRAB_FAMILIES,
    CRAB_REPORTS,
    FAMILIES,
    SAFE_REPORTS,
    all_families,
    get_report,
    reports_by_family,
)


def test_seventeen_reports():
    assert len(SAFE_REPORTS) == 17
    # 005/006 not issued
    assert "gfsafe005" not in SAFE_REPORTS
    assert "gfsafe019" in SAFE_REPORTS


def test_every_report_well_formed():
    for r in SAFE_REPORTS.values():
        assert r.id == r.code.lower()
        assert r.family in FAMILIES
        assert r.files, f"{r.code} has no source files"
        assert r.measures, f"{r.code} has no measures"
        assert r.parquet_name == f"{r.id}.parquet"


def test_gfsafe004_is_two_files():
    assert len(get_report("gfsafe004").files) == 2


def test_get_report_case_insensitive():
    assert get_report("GFSAFE002") is get_report("gfsafe002")
    assert get_report("nope") is None


def test_family_helpers():
    assert {r.id for r in reports_by_family("value")} == {"gfsafe002", "gfsafe007", "gfsafe008"}
    fam = all_families()
    assert sum(len(v) for v in fam.values()) == 17


def test_crab_reports():
    assert len(CRAB_REPORTS) == 5
    assert set(CRAB_REPORTS) == {"crsafeexec01", "crsafeexec02", "crsafeexec03",
                                 "crsafe004", "crsafe005"}
    for r in CRAB_REPORTS.values():
        assert r.id == r.code.lower()
        assert r.family in CRAB_FAMILIES
        assert r.files and r.measures
    # crab ids resolve through the shared lookup, and merge into ALL_REPORTS
    assert get_report("CRSAFEEXEC01") is CRAB_REPORTS["crsafeexec01"]
    assert len(ALL_REPORTS) == 22 and "gfsafe001" in ALL_REPORTS
