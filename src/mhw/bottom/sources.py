"""Bottom-ocean-state data-source descriptors (the only source-specific config).

Each :class:`BottomSource` captures everything :mod:`mhw.bottom.loader` needs to
open one source over OPeNDAP with a uniform return contract. All values for
Bering10K were confirmed live against the PMEL THREDDS server (2026-06-17).

Adding a source (e.g. MOM6 NEP10k) is a new descriptor here — not new code.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BottomSource:
    """Descriptor for one bottom-temperature data source."""

    id: str
    label: str                      # user-facing label (dashboard)
    opendap_url: str
    temp_var: str                   # bottom-temperature variable name
    lat_coord: str                  # 2-D curvilinear latitude coordinate
    lon_coord: str                  # 2-D curvilinear longitude coordinate
    time_coord: str
    drop_vars: tuple[str, ...] = ()  # vars to drop on open (decode conflicts)
    cadence: str = "weekly"
    period: str = ""
    lagged: bool = True             # recent-historical, NOT near-real-time
    notes: str = ""


# --- Bering10K ROMS / ACLIM — operational hindcast (validated, EBS/Bering) -------
# Confirmed live: variable `temp` (long_name "…potential temperature, bottom 5m
# mean", °C); temp(ocean_time, eta_rho=258, xi_rho=182); lat_rho/lon_rho 2-D;
# ocean_time weekly 1970-01-18 .. 2024-08-18. The scalar `s_rho` collides with the
# `s_rho` dimension on decode, so it (and siblings) must be dropped on open.
# Re-verified 2026-06-18: collection still resolves; ocean_time = 2837 weekly steps,
# consistent with a ~2024-08 end — no newer public release found (so CEFI MOM6's
# 2025-06 hindcast is currently the *fresher* of the two bottom-temp sources).
BERING10K_K20_CORECFS = BottomSource(
    id="bering10k",
    label="Bering10K ROMS (ACLIM)",
    opendap_url=(
        "https://data.pmel.noaa.gov/aclim/thredds/dodsC/"
        "B10K-K20_Level2_CORECFS_bottom5m_collection.nc"
    ),
    temp_var="temp",
    lat_coord="lat_rho",
    lon_coord="lon_rho",
    time_coord="ocean_time",
    drop_vars=("s_rho", "s_w", "Cs_r", "Cs_w"),
    cadence="weekly",
    period="1970-present (~3x/yr refresh; to 2024-08 as of check)",
    lagged=True,
    notes="Validated EBS/Bering domain. Bottom = mean over deepest 5 m.",
)


# --- MOM6 NEP10k (CEFI) — co-presented option ------------------------------------
# Verified live against the CEFI THREDDS server (2026-06-18). The regridded hindcast
# carries bottom temperature as `btm_temp` (long_name "Bottom Temperature", deg C) —
# NOT `tob` as earlier guessed. Latest release r20250912 covers 1993-01..2025-06 (390
# monthly steps), i.e. *fresher* than the Bering10K hindcast (~2024-08). The `regrid`
# product is on a REGULAR lat/lon grid (lat=815, lon=341), so — unlike Bering10K's
# curvilinear rho-grid — lat/lon here are 1-D. Domain spans Baja→Chukchi (lat 10.8..80.7°N,
# lon 156.9..255°E), i.e. GOA + EBS + Chukchi, verified live 2026-06-21. The forecast arm is
# NOT yet released: seasonal_forecast / seasonal_reforecast / decadal_forecast appear as
# directory names in the THREDDS catalog tree but hold ZERO .nc files (raw + regrid, every
# cadence), and the public S3 bucket has only hindcast/ under the NEP domain (checked
# 2026-06-21). So "coming soon" is literal — timeline is the open question (see
# docs/forecast_extension/outreach/holsman-data-availability.md).
#   NOTE: loader.load_bottom_temp assumes 2-D curvilinear lat/lon (it unpacks
#   lat.dims -> (y, x)); this rectilinear product needs a 1-D-coord branch in the
#   loader before it will open. A `latest/` alias folder also exists alongside the
#   dated releases if a rolling pointer is preferred over the pinned r20250912.
MOM6_NEP = BottomSource(
    id="mom6_nep",
    label="MOM6 NEP10k (CEFI)",
    opendap_url=(
        "https://psl.noaa.gov/thredds/dodsC/Projects/CEFI/regional_mom6/cefi_portal/"
        "northeast_pacific/full_domain/hindcast/monthly/regrid/r20250912/"
        "btm_temp.nep.full.hcast.monthly.regrid.r20250912.199301-202506.nc"
    ),
    temp_var="btm_temp",
    lat_coord="lat",
    lon_coord="lon",
    time_coord="time",
    drop_vars=(),
    cadence="monthly",
    period="1993-01..2025-06 hindcast (release r20250912); forecast arm not yet released",
    lagged=True,
    notes=(
        "Regular lat/lon grid (815x341), already rectilinear. btm_temp = Bottom "
        "Temperature (degC). Domain Baja->Chukchi (GOA+EBS+Chukchi). Hindcast also "
        "carries full COBALT set incl. bottom o2/aragonite/salinity/nutrients. "
        "Forecast/reforecast dirs exist but are EMPTY (no files, 2026-06-21); Bering "
        "validation underway."
    ),
)


SOURCES: dict[str, BottomSource] = {
    s.id: s for s in (BERING10K_K20_CORECFS, MOM6_NEP)
}
