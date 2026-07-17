"""Pinned LOFRA forecast scorings (occurrence + onset) — read-only reference layer.

The research cell delivers fixed-per-vintage skill tables (verbatim from the certified corrected-
predictand v2 re-run) which we vendor at ``vendor/forecast-scorings-v2/`` and display under LOFRA's
honesty rails — never re-derived board-side. Provenance + display rules + verbatim captions live in
that dir's ``SCORINGS-MANIFEST.md``; the handoff is
``docs/handoffs/lofra-to-dashboard-20260716-05-forecast-scorings-guidance.md``.

Two deployed forecasts are scored here:
  * occurrence probability = the **damped-persistence** model read off as P(area_frac > train-q90);
    ``bss_clim`` is skill over climatology, NOT a model beating persistence.
  * SEBS onset watch = the **LIM k=12** path (experimental; discriminates onset but never shown as
    beating persistence). Used by the Phase-2 onset panel.

Pure readers only (network-free, unit-tested). Display ``stratum = 'all'``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCORINGS_DIR = PROJECT_ROOT / "vendor" / "forecast-scorings-v2"

# The deployed forecasts whose scorings we display (per LOFRA's SCORINGS-MANIFEST).
OCCURRENCE_FORECASTER = "damped_persistence"
ONSET_FORECASTER = "lim_k12"

# LOFRA's verbatim panel captions (SCORINGS-MANIFEST.md §A / §B) — render exactly.
OCCURRENCE_CAPTION = (
    "The estimated chance next month's marine-heatwave area exceeds the local 90th-percentile "
    "threshold, one month ahead, from the damped-persistence model. Skill is measured against "
    "seasonal climatology; it is resolvable at one month in the productive zones and decays toward "
    "climatology beyond, where it is shown as “watch” rather than a number."
)


@lru_cache(maxsize=None)
def _read(name: str) -> pd.DataFrame | None:
    """Load a pinned scorings CSV once, or None if the reference dir is absent."""
    path = SCORINGS_DIR / name
    if not path.exists():
        return None
    return pd.read_csv(path)


def occurrence_skill(zone: str, lead: int = 1, stratum: str = "all") -> dict | None:
    """One row of occurrence probabilistic skill for the deployed (damped-persistence) forecast.

    Returns a dict (``bss_clim``, ``auc``, ``n``, ``base_rate``, ``brier`` …) or ``None`` when the
    table or the requested zone×lead is absent.
    """
    df = _read("occurrence_probabilistic_skill_v2.csv")
    if df is None:
        return None
    m = df[(df["zone"] == zone) & (df["forecaster"] == OCCURRENCE_FORECASTER)
           & (df["lead"] == lead) & (df["stratum"] == stratum)]
    return None if m.empty else m.iloc[0].to_dict()


def occurrence_reliability(zone: str, lead: int = 1) -> pd.DataFrame:
    """Reliability-curve bins (``bin``, ``n``, ``p_mean``, ``o_freq``) for the occurrence forecast.

    Empty frame when the table/zone is absent (caller renders nothing).
    """
    df = _read("occurrence_reliability_bins_v2.csv")
    cols = ["bin", "n", "p_mean", "o_freq"]
    if df is None:
        return pd.DataFrame(columns=cols)
    m = df[(df["zone"] == zone) & (df["forecaster"] == OCCURRENCE_FORECASTER)
           & (df["lead"] == lead)].sort_values("bin")
    return m[cols].reset_index(drop=True)


def occurrence_resolvable(zone: str, lead: int = 1, stratum: str = "all") -> bool:
    """True when occurrence skill is resolvable (``bss_clim > 0``) — else display as 'watch'."""
    s = occurrence_skill(zone, lead, stratum)
    return bool(s is not None and s["bss_clim"] > 0)


def onset_discrimination(lead: int = 1, forecaster: str = ONSET_FORECASTER,
                         stratum: str = "all") -> dict | None:
    """SEBS onset discrimination row (``onset_auc``, ``sedi``, ``pod``, ``far``) for a forecaster.

    Defaults to the deployed LIM-k12 watch; pass ``forecaster='persistence'`` for the honesty
    anchor. ``None`` when absent. (Consumed by the Phase-2 onset panel.)
    """
    df = _read("onset_discrimination_v2.csv")
    if df is None:
        return None
    m = df[(df["zone"] == "sebs") & (df["forecaster"] == forecaster)
           & (df["lead"] == lead) & (df["stratum"] == stratum)]
    return None if m.empty else m.iloc[0].to_dict()
