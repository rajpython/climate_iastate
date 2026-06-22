"""Tests for the BottomRegion registry — EBS must reproduce the old hardcoded constants."""
import numpy as np
import pytest

from mhw.bottom.regions import BOTTOM_REGIONS, EBS, NBS, SLOPE, get_region


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


def test_nbs_descriptor():
    assert get_region("nbs") is NBS
    assert NBS.product_kind == "cold_pool"          # NBS has the area index, like EBS
    assert set(NBS.valid_sources) == {"bering10k", "mom6_nep"}
    assert NBS.observed.kind == "cold_pool_index"
    assert NBS.observed.r_object == "nbs_mean_temperature"
    # NBS reuses the EBS column map (same AREA_LTE*_KM2 schema) and filters the shared
    # full-area haul CSV to the NBS survey id.
    assert NBS.observed.column_map is EBS.observed.column_map
    assert NBS.observed.hauls_survey_id == 143
    # grid covers the NBS haul footprint (lat 60.6–65.3) and sits north of EBS
    assert NBS.analysis_lats.min() <= 60.65 and NBS.analysis_lats.max() >= 65.3
    assert NBS.analysis_lats.min() >= EBS.analysis_lats.min()


def test_slope_is_bottom_temp_band():
    assert get_region("slope") is SLOPE
    # deep, non-cold-pool: a depth BAND (200–1200 m), not the ≤200 m shelf
    assert SLOPE.product_kind == "bottom_temp"
    assert SLOPE.shelf_min_depth_m == 200.0 and SLOPE.shelf_max_depth_m == 1200.0
    # observed comes from FOSS survey hauls (BSS), not a packaged coldpool index
    assert SLOPE.observed.kind == "foss_hauls"
    assert SLOPE.observed.foss_srvy == "BSS"
    assert SLOPE.observed.rda_url == "" and SLOPE.observed.hauls_url == ""


def test_shelf_regions_have_zero_min_depth():
    # the min-depth band must stay 0 for the cold-pool shelves (behaviour-preserving)
    assert EBS.shelf_min_depth_m == 0.0
    assert NBS.shelf_min_depth_m == 0.0
