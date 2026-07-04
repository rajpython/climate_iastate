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
