"""Ocean-health engine + loader tests (network-free).

Exercises the pure/grid-agnostic pieces of the ocean-health layer with synthetic in-memory
datasets passed via ``ds=`` — no OPeNDAP. The area-weighted shelf mean itself is reused from
the cold-pool engine (already covered by test_bottom_coldpool).
"""
from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from mhw.bottom.loader import load_bottom_field, resolve_variable
from mhw.bottom.oceanhealth import (
    VARIABLES,
    build_model_variable_series,
    nearest_summer_field,
)
from mhw.bottom.regions import EBS_COLUMN_MAP
from mhw.bottom.sources import BERING10K_K20_CORECFS, MOM6_NEP


def _sob_ds(ny=5, nx=4, times=("2020-06-15", "2020-07-15", "2020-08-15")):
    """MOM6-shaped rectilinear dataset carrying bottom salinity `sob(time, lat, lon)`."""
    lat = np.linspace(54.0, 62.0, ny)
    lon = np.linspace(-179.0, -160.0, nx)
    t = np.array(times, dtype="datetime64[ns]")
    data = 31.0 + np.random.default_rng(3).random((len(t), ny, nx))
    ds = xr.Dataset({"sob": (("time", "lat", "lon"), data)},
                    coords={"time": t, "lat": lat, "lon": lon})
    ds["sob"].attrs["units"] = "psu"
    return ds


# --- resolve_variable -----------------------------------------------------------------------

def test_resolve_variable_temp_is_default():
    assert resolve_variable(MOM6_NEP, "temp") == (MOM6_NEP.temp_var, MOM6_NEP.opendap_url)


def test_resolve_variable_salinity_uses_own_file():
    var, url = resolve_variable(MOM6_NEP, "salinity")
    assert var == "sob"
    assert url.endswith("sob.nep.full.hcast.monthly.regrid.r20250912.199301-202506.nc")


def test_resolve_variable_unknown_raises():
    with pytest.raises(ValueError, match="salinity"):
        # Bering10K's bottom5m bundle carries no salinity variable.
        resolve_variable(BERING10K_K20_CORECFS, "salinity")


# --- load_bottom_field for a non-temp variable ----------------------------------------------

def test_load_bottom_field_salinity_normalises_and_tags():
    da = load_bottom_field(MOM6_NEP, "salinity", ds=_sob_ds())
    assert da.dims == ("time", "y", "x")
    assert da.lat.dims == ("y", "x") and da.lon.dims == ("y", "x")
    assert da.attrs["variable"] == "salinity"
    assert da.attrs["units"] == "psu"          # kept from the dataset, NOT forced to Celsius
    assert da.attrs["source_id"] == "mom6_nep"


# --- nearest_summer_field -------------------------------------------------------------------

def test_nearest_summer_field_picks_july_step():
    ds = _sob_ds()
    field = nearest_summer_field(MOM6_NEP, ds, 2020, "salinity")  # target 07-04
    assert field is not None
    assert str(field["time"].values)[:7] == "2020-07"


def test_nearest_summer_field_none_outside_window():
    ds = _sob_ds(times=("2019-06-15", "2019-07-15"))  # different year
    assert nearest_summer_field(MOM6_NEP, ds, 2020, "salinity") is None


# --- variable registry ----------------------------------------------------------------------

def test_variables_columns_align_with_observed_product():
    # Model output column must match the observed AFSC column so the two series line up.
    assert VARIABLES["salinity"]["col"] == "mean_bottom_salinity"
    assert VARIABLES["salinity"]["col"] in EBS_COLUMN_MAP.values()


def test_build_series_rejects_unknown_variable_without_network():
    # Validation happens before any dataset is opened, so this needs no connectivity.
    with pytest.raises(ValueError, match="Unknown ocean-health variable"):
        build_model_variable_series(MOM6_NEP, variable="unobtanium")


# --- O₂ / pH model transforms + registry ----------------------------------------------------

def test_oxygen_and_ph_resolve_to_own_mom6_files():
    assert resolve_variable(MOM6_NEP, "oxygen")[0] == "btm_o2"
    assert resolve_variable(MOM6_NEP, "ph")[0] == "btm_htotal"


def test_o2_molkg_to_mll_lands_in_observed_range():
    from mhw.bottom.oceanhealth import _o2_molkg_to_mll
    # ~0.00035 mol/kg is a typical EBS bottom O₂ → ~8 ml/l (observed range 4–10).
    assert _o2_molkg_to_mll(np.array([0.00035]))[0] == pytest.approx(8.03, abs=0.1)


def test_htotal_to_ph_inverts_log():
    from mhw.bottom.oceanhealth import _htotal_to_ph
    # [H+] = 1e-8 mol/kg → pH 8.0; non-positive → NaN (masked land/fill).
    out = _htotal_to_ph(np.array([1e-8, 0.0, -1.0]))
    assert out[0] == pytest.approx(8.0)
    assert np.isnan(out[1]) and np.isnan(out[2])


def test_survey_ctd_variables_carry_obs_products_and_units():
    assert VARIABLES["oxygen"]["obs_products"] == ("survey_ctd",)
    assert VARIABLES["oxygen"]["units"] == "ml/l"
    assert VARIABLES["ph"].get("provisional") is True
    # Salinity can come from either product (cold-pool for EBS/NBS, survey-CTD for GOA/AI).
    assert VARIABLES["salinity"]["obs_products"] == ("coldpool", "survey_ctd")
