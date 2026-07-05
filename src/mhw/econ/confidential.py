"""Confidentiality guard for the commercial-landings layer (NOAA "rule of three").

Vessel/processor-level and thin area×species×gear cells are suppressed under NOAA's rule of
three (a cell must aggregate ≥ 3 distinct vessels/processors to be public). The public exports
this board ingests are **already** suppressed, but we enforce it defensively so a thin cell can
never reach a page: every tidy frame carries a boolean ``confidential`` column, and any cell we
can identify as failing the rule is flagged (and dropped before display).

E1 (FOSS statewide) is a fully public, already-aggregated feed with no per-cell vessel count, so
``mark_confidential`` simply stamps ``confidential=False``. The count-aware guard is here for the
E2+ sources that expose a vessel/processor count.
"""
from __future__ import annotations

import pandas as pd

RULE_OF_THREE = 3


def mark_confidential(df: pd.DataFrame, count_col: str | None = None,
                      min_n: int = RULE_OF_THREE) -> pd.DataFrame:
    """Add a boolean ``confidential`` column (rule of three).

    If *count_col* is given, a cell is confidential when its distinct vessel/processor count is
    below *min_n*. If it is None (e.g. an already-aggregated public feed with no count), nothing
    is flagged. Does not mutate the input.
    """
    out = df.copy()
    if count_col and count_col in out.columns:
        out["confidential"] = pd.to_numeric(out[count_col], errors="coerce").fillna(0) < min_n
    else:
        out["confidential"] = False
    return out


def suppress_confidential(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows flagged ``confidential`` so a thin cell is never displayed.

    A no-op when nothing is flagged. Requires the ``confidential`` column (call
    :func:`mark_confidential` first).
    """
    if "confidential" not in df.columns:
        return df
    return df[~df["confidential"].astype(bool)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Economic SAFE suppression bands
# ---------------------------------------------------------------------------
# The Groundfish Economic SAFE reports do NOT null suppressed cells; the published (rounded /
# partially-imputed) value stays, alongside a companion band column telling you how much of the
# cell was confidential. So we ANNOTATE (band label + a midpoint % + a boolean), never drop —
# AKFIN already releases these as non-confidential aggregates. Bands are ordered least→most.
SUPPRESSION_BANDS = ("0%", "<1%", "1-5%", "5-10%", "10-25%", "25-50%", "50-75%", "100%")

# Band → representative midpoint percent (for optional numeric use / sorting).
_BAND_MIDPOINT: dict[str, float] = {
    "0%": 0.0, "<1%": 0.5, "1-5%": 3.0, "5-10%": 7.5,
    "10-25%": 17.5, "25-50%": 37.5, "50-75%": 62.5, "100%": 100.0,
}


def normalize_suppression(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Turn a raw ``PERCENT_*_SUPPRESSED`` band column into tidy annotation columns.

    Adds ``suppressed_band`` (cleaned band label, e.g. '1-5%'), ``suppressed_pct`` (band midpoint,
    float), and ``suppressed`` (bool: any suppression, i.e. band not '0%'/empty). The original
    *col* is dropped. A no-op (adds no columns) if *col* is absent. Does not mutate the input.
    """
    out = df.copy()
    if col not in out.columns:
        return out
    band = out[col].astype("string").str.strip()
    out["suppressed_band"] = band.where(band.isin(SUPPRESSION_BANDS), other=pd.NA)
    out["suppressed_pct"] = out["suppressed_band"].map(_BAND_MIDPOINT)
    out["suppressed"] = out["suppressed_pct"].fillna(0.0) > 0.0
    return out.drop(columns=[col])
