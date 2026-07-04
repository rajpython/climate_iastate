"""Tests for the FOSS commercial-landings adapter — pure tidy/summary (no network)."""
import pandas as pd

from mhw.econ.confidential import mark_confidential, suppress_confidential
from mhw.econ.sources import FOSS_LANDINGS, TONNE_PER_LB
from mhw.fetch.landings_foss import TIDY_COLS, landings_summary, tidy_landings


def _raw():
    # Mimic FOSS landings rows: trailing space in names, commercial + recreational, a null-pounds
    # row that must be dropped, and one recreational row that the commercial filter drops.
    return [
        {"year": 2023, "ts_afs_name": "POLLOCK, WALLEYE ", "tsn": "934083",
         "pounds": 2204.6226218, "dollars": 1000.0, "region_name": "Alaska",
         "collection": "Commercial", "source": "AKFINHIST"},
        {"year": 2023, "ts_afs_name": "COD, PACIFIC", "tsn": "164711",
         "pounds": 4409.2452436, "dollars": 3000.0, "region_name": "Alaska",
         "collection": "Commercial", "source": "AKFINHIST"},
        {"year": 2023, "ts_afs_name": "SALMON, COHO", "tsn": "161977",
         "pounds": 100.0, "dollars": 50.0, "region_name": "Alaska",
         "collection": "Recreational", "source": "MRIP"},   # dropped: recreational
        {"year": 2022, "ts_afs_name": "SABLEFISH", "tsn": "172001",
         "pounds": None, "dollars": None, "region_name": "Alaska",
         "collection": "Commercial", "source": "AKFINHIST"},  # dropped: null pounds
    ]


def test_tidy_schema_and_conversion():
    df = tidy_landings(_raw())
    assert list(df.columns) == TIDY_COLS
    # recreational + null-pounds rows dropped → 2 commercial rows
    assert len(df) == 2
    assert set(df["collection"]) == {"Commercial"}
    # 2204.62 lb == exactly 1 tonne
    pollock = df[df["species"] == "POLLOCK, WALLEYE"].iloc[0]
    assert abs(pollock["landings_t"] - 1.0) < 1e-6
    assert abs(2204.6226218 * TONNE_PER_LB - 1.0) < 1e-6
    # trailing whitespace stripped; statewide constants stamped
    assert pollock["species"] == "POLLOCK, WALLEYE"
    assert (df["area_group"] == "statewide").all()
    assert (df["catch_or_landings"] == "landings").all()
    assert (~df["confidential"]).all()


def test_tidy_empty_returns_schema():
    df = tidy_landings([])
    assert list(df.columns) == TIDY_COLS
    assert df.empty


def test_landings_summary_value_share_sums_to_one():
    df = tidy_landings(_raw())
    summ = landings_summary(df)
    # Pacific cod ($3000) outranks pollock ($1000)
    assert list(summ["species"])[0] == "COD, PACIFIC"
    assert abs(summ["value_share"].sum() - 1.0) < 1e-9


def test_confidential_rule_of_three():
    df = pd.DataFrame({"n_vessels": [2, 3, 10]})
    marked = mark_confidential(df, count_col="n_vessels")
    assert list(marked["confidential"]) == [True, False, False]
    assert len(suppress_confidential(marked)) == 2
    # no count column → nothing flagged
    assert (~mark_confidential(df)["confidential"]).all()


def test_source_descriptor_maps_expected_fields():
    fm = FOSS_LANDINGS.field_map
    assert fm["ts_afs_name"] == "species"
    assert fm["pounds"] == "pounds"
    assert FOSS_LANDINGS.region_resolution == "statewide"
