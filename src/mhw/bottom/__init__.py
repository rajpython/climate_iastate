"""Bottom-ocean-state ingestion, regridding, and cold-pool products.

This package adds *bottom* temperature / cold-pool capability to the dashboard,
mirroring the surface (OISST) pipeline. Design (see
``docs/forecast_extension/forecast-implementation-document.md``):

* **Source-agnostic regrid.** Regional ocean models (Bering10K ROMS, MOM6 NEP10k)
  live on ~10 km **curvilinear** grids, incompatible with the regular 0.25° OISST
  grid the rest of the pipeline (masks, cos-lat weights, climatology zarr) assumes.
  :mod:`mhw.bottom.regrid` remaps a curvilinear field onto that 0.25° grid using
  only numpy + scipy (no conda / xesmf).
* **Per-source loaders.** :mod:`mhw.bottom.sources` holds one descriptor per data
  source (OPeNDAP URL, variable name, coordinate names); :mod:`mhw.bottom.loader`
  opens them with a single return contract. Adding MOM6 NEP10k is a new descriptor,
  not new machinery.

Decision (2026-06-17): present **both** Bering10K ROMS and MOM6 NEP10k as labelled
options. The bottom product is bottom temperature → EBS cold-pool extent
(area ≤ 2 °C), validated against the AFSC observed cold-pool index. Bottom state is
a **lagged / recent-historical** product, not near-real-time — label accordingly.
"""
from __future__ import annotations

from mhw.bottom.regrid import regrid_curvilinear_to_regular, alaska_target_grid
from mhw.bottom.sources import BottomSource, BERING10K_K20_CORECFS

__all__ = [
    "regrid_curvilinear_to_regular",
    "alaska_target_grid",
    "BottomSource",
    "BERING10K_K20_CORECFS",
]
