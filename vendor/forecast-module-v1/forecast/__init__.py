"""
forecast — forward-mode operational wrappers around the paper-validated
Stage-3 models (sst-forecast-method-review, paper v14).

Packaging build only: no new science, no new equations. See forecast/core.py
for provenance and forecast/selftest_identity_check.py for the acceptance
gate (wrapper == hindcast at the final origin, machine precision).

Entry points
------------
OPERATIONAL DEFAULT (frozen coefficients — the dashboard path):
  forecast_frozen(area_frac_df, zone, manifest, leads=(1, 2, 3))
      Applies the PINNED per-zone coefficients (phi, sigma_eps, seasonal
      climatology, q90, frozen residual set); re-estimates nothing. Point +
      predictive variance (+ L1 q90 occurrence for the damped zones).
  sebs_onset_watch_frozen(area_frac_df, field, manifest, leads=(1, 2))
      Applies the PINNED LIM (EOF basis + G1 + zone read-off), isotonic link
      and thresholds to the live field's origin state. SEBS only.
  load_manifest(path=None) / load_live_field(nc_path)
      Load the pinned manifest (+ companion npz) and ingest an arbitrary
      broad-basin OISST-anomaly NetCDF into a projectable field.

VALIDATION / REPLICATION ONLY (re-fits every call — do NOT deploy):
  run_latest_origin(area_frac_df, zone, leads=(1, 2, 3))
  sebs_onset_watch(area_frac_df, field=None, leads=(1, 2), threshold=None)
      Re-fit paths that reproduce the paper's per-origin rolling hindcast
      bit-for-bit (see forecast/selftest_identity_check.py). Kept for
      replication and for drift-checking the frozen path.

DEPLOY_MAP
    The LOFRA-verified zone -> product deployment contract (paper v14).

Owner: Metrica. Re-fit fit vintage: snap-obl028-predictand-20260701 (predictand),
snap-obl029-broadfield-20260701 (LIM field). Frozen coefficients pinned at the
last SCORED hindcast origin per deployed lead (persistence/clim 2026-04, SEBS
onset 2026-05).
"""
from .core import (  # noqa: F401
    DEPLOY_MAP,
    FIT_VINTAGE_FIELD,
    FIT_VINTAGE_PREDICTAND,
    ZONES,
    load_default_field,
    run_latest_origin,
    sebs_onset_watch,
)
from .frozen import (  # noqa: F401
    FrozenManifest,
    LiveField,
    forecast_frozen,
    load_live_field,
    load_manifest,
    sebs_onset_watch_frozen,
)

__version__ = "1.1.0"
