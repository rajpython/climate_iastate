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


# --- MOM6 NEP10k (CEFI) — co-presented option; descriptor to be confirmed --------
# Placeholder: CEFI regional MOM6 carries bottom temperature (`tob`); NEP domain
# Baja->Chukchi; PSL THREDDS / AWS S3 / GCS. URL + exact var/coord names still to be
# confirmed against the live CEFI catalog (forecast-arm coverage of `tob` is open).
MOM6_NEP = BottomSource(
    id="mom6_nep",
    label="MOM6 NEP10k (CEFI)",
    opendap_url="",                 # TODO: confirm against psl.noaa.gov CEFI catalog
    temp_var="tob",
    lat_coord="lat",
    lon_coord="lon",
    time_coord="time",
    drop_vars=(),
    cadence="monthly",
    period="1993-2019 hindcast (+ public forecast arm)",
    lagged=True,
    notes="CEFI cold-pool product AFSC-validated; forecast-arm tob coverage TBD.",
)


SOURCES: dict[str, BottomSource] = {
    s.id: s for s in (BERING10K_K20_CORECFS, MOM6_NEP)
}
