"""Region descriptors for the bottom-ocean-state engine (the only region-specific config).

The cold-pool / bottom-state engine started EBS-only with the analysis grid, shelf-depth
rule, and observed-product URLs hard-coded. This module lifts all of that into a single
:class:`BottomRegion` descriptor so the engine, fetchers, API, and dashboard can be driven
by ``region`` — adding a region (NBS, Bering slope, GOA…) becomes a new descriptor here, not
new code. Mirrors the source-descriptor pattern in :mod:`mhw.bottom.sources`.

Two product kinds (plan §3):
  * ``"cold_pool"`` — EBS/NBS shallow shelf: the ≤2 °C cold-pool *area* index is meaningful.
  * ``"bottom_temp"`` — GOA/AI/slope: no cold pool (deep / no winter ice), so the product is
    bottom-temperature *conditions* only (no area-by-threshold index).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

# Region ids are lowercase, consistent with config/regions.geojson and the dashboard's
# REGION_ORDER (components/ts_event_metrics.py). Bottom regions may extend beyond the SST
# regions (e.g. "slope"), but shared ids (ebs, nbs) must match.


@dataclass(frozen=True)
class ObservedProduct:
    """How to fetch a region's *observed* (survey-derived) validation target.

    ``kind`` selects the fetch/parse branch:
      * ``"cold_pool_index"`` — AFSC EBS R object ``cold_pool_index`` (carries the
        area-by-threshold index + mean gear temp).
      * ``"mean_temperature"`` — the ``{nbs,goa,ai}_mean_temperature`` products (NBS carries
        ``AREA_LTE2_KM2``; GOA/AI are temperature-only). [wired in Phase 1]
      * ``None`` — no packaged observed product (e.g. slope = raw survey hauls only).
    """

    kind: str
    rda_url: str = ""
    r_object: str = ""
    hauls_url: str = ""
    hauls_survey_id: int | None = None  # filter the haul file to one AFSC survey (98 EBS, 143 NBS)
    column_map: Mapping[str, str] = field(default_factory=dict)
    years: str = ""             # human label, e.g. "1982–present (no 2020)"


@dataclass(frozen=True)
class BottomRegion:
    """Everything region-specific the bottom-state engine needs for one region."""

    id: str
    label: str                          # user-facing (dashboard titles)
    product_kind: str                   # "cold_pool" | "bottom_temp"
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    shelf_max_depth_m: float            # ≤ this depth = "shelf" for the area index
    valid_sources: tuple[str, ...]      # model ids (mhw.bottom.sources) valid here
    has_survey_hauls: bool              # is per-haul survey replication possible?
    observed: ObservedProduct | None = None
    grid_res: float = 0.25              # analysis-grid resolution (°)

    @property
    def analysis_lats(self) -> np.ndarray:
        """Regular analysis-grid latitudes (matches the old EBS_LATS for EBS)."""
        return np.arange(self.lat_min, self.lat_max, self.grid_res)

    @property
    def analysis_lons(self) -> np.ndarray:
        """Regular analysis-grid longitudes (matches the old EBS_LONS for EBS)."""
        return np.arange(self.lon_min, self.lon_max, self.grid_res)


# --- Observed-product URLs (canonical source of truth; fetch/coldpool imports these) ------
_COLDPOOL_REPO = "https://raw.githubusercontent.com/afsc-gap-products/coldpool/main/data/"
EBS_RDA_URL = _COLDPOOL_REPO + "cold_pool_index.rda"
EBS_HAULS_URL = _COLDPOOL_REPO + "index_hauls_temperature_data.csv"
NBS_RDA_URL = _COLDPOOL_REPO + "nbs_mean_temperature.rda"
# NBS has no standalone index-haul file; it lives in the combined EBS+NBS full-area haul
# CSV, distinguished by survey_definition_id 143 (EBS = 98).
NBS_HAULS_URL = _COLDPOOL_REPO + "ebs_nbs_temperature_full_area.csv"

# R-object column -> snake_case schema (EBS cold_pool_index).
EBS_COLUMN_MAP: dict[str, str] = {
    "YEAR": "year",
    "AREA_LTE2_KM2": "area_lte2_km2",
    "AREA_LTE1_KM2": "area_lte1_km2",
    "AREA_LTE0_KM2": "area_lte0_km2",
    "AREA_LTEMINUS1_KM2": "area_lteminus1_km2",
    "MEAN_GEAR_TEMPERATURE": "mean_bottom_temp",
    "MEAN_BT_LT100M": "mean_bottom_temp_lt100m",
    "MEAN_SURFACE_TEMPERATURE": "mean_surface_temp",
    "MEAN_GEAR_SALINITY": "mean_bottom_salinity",
    "LAST_UPDATE": "last_update",
}


# --- Eastern Bering Sea — the original, fully-wired region --------------------------------
# Grid/depth values are exactly the old module globals in bottom/coldpool.py:
#   EBS_LATS = np.arange(54.0, 63.0, 0.25); EBS_LONS = np.arange(-179.0, -157.0, 0.25)
#   SHELF_MAX_DEPTH_M = 200.0
EBS = BottomRegion(
    id="ebs",
    label="Eastern Bering Sea",
    product_kind="cold_pool",
    lat_min=54.0, lat_max=63.0,
    lon_min=-179.0, lon_max=-157.0,
    shelf_max_depth_m=200.0,
    valid_sources=("bering10k", "mom6_nep"),
    has_survey_hauls=True,
    observed=ObservedProduct(
        kind="cold_pool_index",
        rda_url=EBS_RDA_URL,
        r_object="cold_pool_index",
        hauls_url=EBS_HAULS_URL,
        column_map=EBS_COLUMN_MAP,
        years="1982–present (no 2020 — survey cancelled)",
    ),
)


# --- Northern Bering Sea — cold-pool region (Phase 1) ------------------------------------
# Validated 2026-06-22: `nbs_mean_temperature` carries AREA_LTE{2,1,0,-1}_KM2 computed
# apples-to-apples with the EBS cold_pool_index (same coldpool package), so EBS replicates
# directly with the same column map. Observed index is SPORADIC (survey years 2010, 2017,
# 2019, 2021, 2022, 2023, 2025) — a *survey* limit; both models cover NBS continuously.
# Per-haul survey temps for replication come from the shared full-area CSV (sdid 143), years
# 2010–2023. Grid bounds from the NBS haul footprint (lat 60.6–65.3, lon -175.3–-161.5); the
# shelf is entirely shallow (≤80 m) so the ≤200 m rule captures all of it.
NBS = BottomRegion(
    id="nbs",
    label="Northern Bering Sea",
    product_kind="cold_pool",
    lat_min=60.0, lat_max=66.0,
    lon_min=-176.0, lon_max=-160.0,
    shelf_max_depth_m=200.0,
    valid_sources=("bering10k", "mom6_nep"),
    has_survey_hauls=True,
    observed=ObservedProduct(
        kind="cold_pool_index",
        rda_url=NBS_RDA_URL,
        r_object="nbs_mean_temperature",
        hauls_url=NBS_HAULS_URL,
        hauls_survey_id=143,
        column_map=EBS_COLUMN_MAP,   # identical schema (minus MEAN_BT_LT100M, absent in NBS)
        years="2010–2025 (sporadic; survey years only)",
    ),
)


# Bering slope, GOA, AI land here in later phases (see docs/alaska_shelf_expansion_plan.md).
BOTTOM_REGIONS: dict[str, BottomRegion] = {r.id: r for r in (EBS, NBS)}

DEFAULT_REGION_ID = "ebs"


def get_region(region_id: str) -> BottomRegion:
    """Look up a region by id (case-insensitive), raising a clear error if unknown."""
    key = region_id.lower()
    if key not in BOTTOM_REGIONS:
        raise KeyError(
            f"Unknown bottom region {region_id!r}; known: {sorted(BOTTOM_REGIONS)}"
        )
    return BOTTOM_REGIONS[key]
