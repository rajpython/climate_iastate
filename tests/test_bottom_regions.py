"""Tests for the BottomRegion registry — EBS must reproduce the old hardcoded constants."""
import numpy as np
import pytest

from mhw.bottom.regions import BOTTOM_REGIONS, EBS, get_region


def test_ebs_grid_matches_legacy_constants():
    # These are the exact module globals the engine used before region-parameterization:
    #   EBS_LATS = np.arange(54.0, 63.0, 0.25); EBS_LONS = np.arange(-179.0, -157.0, 0.25)
    np.testing.assert_array_equal(EBS.analysis_lats, np.arange(54.0, 63.0, 0.25))
    np.testing.assert_array_equal(EBS.analysis_lons, np.arange(-179.0, -157.0, 0.25))
    assert EBS.shelf_max_depth_m == 200.0
    assert EBS.grid_res == 0.25


def test_ebs_descriptor_fields():
    assert EBS.id == "ebs"
    assert EBS.product_kind == "cold_pool"
    assert EBS.has_survey_hauls is True
    assert set(EBS.valid_sources) == {"bering10k", "mom6_nep"}
    assert EBS.observed is not None
    assert EBS.observed.kind == "cold_pool_index"
    assert EBS.observed.r_object == "cold_pool_index"
    assert EBS.observed.rda_url.endswith("cold_pool_index.rda")
    # the column map must produce the schema the API/parquet expect
    assert EBS.observed.column_map["AREA_LTE2_KM2"] == "area_lte2_km2"
    assert EBS.observed.column_map["MEAN_GEAR_TEMPERATURE"] == "mean_bottom_temp"


def test_get_region_case_insensitive_and_unknown():
    assert get_region("EBS") is EBS
    assert get_region("ebs") is EBS
    with pytest.raises(KeyError):
        get_region("atlantis")


def test_registry_keys_are_lowercase():
    assert all(k == k.lower() for k in BOTTOM_REGIONS)
    assert "ebs" in BOTTOM_REGIONS
