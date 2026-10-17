"""The board's heatwave record: vintage #7 (D1) — paths, identity and the display rule.

The board reads the sealed release ``mhw-hobday-consecutive-20261009-icegap-d1`` from a staged,
read-only folder (``data/record/mhw-d1/``, overridable with ``MHW_RECORD_DIR``) that the nightly job
never writes. Staging (``scripts/stage_d1_record.py``) copies the named release files there and
verifies every byte against the release manifest; nothing in this module writes into it.

The display rule (board plan 4bfbdf02 + addenda 01–03; ADDENDUM-02 8dfb518a for months):

* **Unknown share** U = absent input + missing SST + unknown ice + missing threshold (coverage
  sidecar). U, scorable and observed ice partition the retained weight.
* **Day:** U > 0.25 → missing and hatched; if also wholly unscorable (or absent) the area line has a
  gap, never 0. U ≤ 0.25 → area as computed; observed ice is a real zero, labelled ice-covered.
* **Month:** mean over eligible days (U ≤ 0.25) only; a month is MISSING with ≥ 11 rejected days or
  ≥ 5 consecutive rejected days. A rejected day is never counted as zero area.

Everything here is pure and network-free except the two small file loaders.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
RECORD_ID = "mhw-hobday-consecutive-20261009-icegap-d1"
VINTAGE_LABEL = "vintage #7 (D1)"
SEAL_PREFIX = "bf588433"
MANIFEST_PREFIX = "329c0d1b"
CERTIFIED_THROUGH = date(2026, 8, 31)
CERTIFIED_THROUGH_TEXT = "31 August 2026"

BANNER_TEXT = (
    f"Heatwave record: {VINTAGE_LABEL}, certified to {CERTIFIED_THROUGH_TEXT}. "
    "Daily updates are paused until a validated daily extension is adopted."
)

# ---------------------------------------------------------------------------
# Rule constants
# ---------------------------------------------------------------------------
HATCH_U = 0.25                # a day with unknown share above this is rejected (hatched)
MONTH_MAX_REJECTED = 11       # ≥ this many rejected days → month missing
MONTH_MAX_CONSECUTIVE = 5     # ≥ this many consecutive rejected days → month missing
ICE_COVERED_SHARE = 0.5       # observed-ice share at/above which a zero-area day reads "ice-covered"
FLOOR_TOL = 1e-9              # U above the zone floor by more than this = "coverage reduced"

UNKNOWN_PARTS = ("share_absent_input", "share_missing_sst", "share_unknown_ice",
                 "share_missing_threshold")

# Day labels (board wording; mini-boardpaz-1013 + addendum 02)
LABEL_NO_INPUT = "No input"
LABEL_INCOMPLETE = "Incomplete coverage"
LABEL_DETECTED = "Heatwave detected"
LABEL_ICE = "Ice-covered (zero heatwave area)"
LABEL_NONE_ASSESSED = "None detected in the assessed area"
LABEL_NONE = "No heatwave detected"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
def record_dir() -> Path:
    """Root of the staged record (``MHW_RECORD_DIR`` or ``data/record/mhw-d1``)."""
    env = os.environ.get("MHW_RECORD_DIR")
    return Path(env) if env else PROJECT_ROOT / "data" / "record" / "mhw-d1"


def agg_dir() -> Path:
    return record_dir() / "aggregates_region"


def states_dir() -> Path:
    return record_dir() / "states_grid"


def coverage_dir() -> Path:
    return record_dir() / "coverage_daily"


def risk_dir() -> Path:
    """Board-derived risk percentiles, recomputed from D1 (not a release file)."""
    return record_dir() / "risk"


def panel2016_dir() -> Path:
    return record_dir() / "panel2016"


def agg_path(zone: str) -> Path:
    return agg_dir() / f"region_daily_{zone}.parquet"


def coverage_path(zone: str) -> Path:
    return coverage_dir() / f"coverage_daily_{zone}.csv"


def list_zones() -> list[str]:
    d = agg_dir()
    return [p.stem.replace("region_daily_", "") for p in d.glob("region_daily_*.parquet")] if d.exists() else []


# ---------------------------------------------------------------------------
# Day rule
# ---------------------------------------------------------------------------
def unknown_share(cov: pd.DataFrame) -> pd.Series:
    """U = absent input + missing SST + unknown ice + missing threshold."""
    return sum(cov[c].astype(float) for c in UNKNOWN_PARTS)


def coverage_floor(cov: pd.DataFrame) -> float:
    """The zone's constant never-observed floor: the minimum missing-SST share."""
    return float(cov["share_missing_sst"].min())


def classify_days(agg: pd.DataFrame, cov: pd.DataFrame) -> pd.DataFrame:
    """Join the region aggregate to its coverage sidecar on ``date`` and apply the day rule.

    Returns the aggregate's columns plus: ``unknown_share``, the unknown-ice split, observed-ice
    share, ``status``, ``eligible`` (U ≤ 0.25 and input present), ``hatched`` (U > 0.25), ``gap``
    (hatched and wholly unscorable, or absent input), ``area_plot`` (area_frac, NaN on gap days),
    ``ice_covered``, ``coverage_reduced`` and ``label``.
    """
    a = agg.copy()
    a["date"] = pd.to_datetime(a["date"])
    c = cov.copy()
    c["date"] = pd.to_datetime(c["date"])
    keep = ["date", *UNKNOWN_PARTS, "share_observed_masked_ice", "share_scorable",
            "share_unknown_run_or_regional", "share_unknown_outage", "status"]
    df = a.merge(c[keep], on="date", how="left", validate="one_to_one")
    if df["status"].isna().any():
        missing = df.loc[df["status"].isna(), "date"].dt.date.tolist()[:5]
        raise ValueError(f"coverage sidecar lacks dates present in the aggregate, e.g. {missing}")

    floor = coverage_floor(c)
    U = unknown_share(df)
    absent = df["status"].eq("absent_input")
    df["unknown_share"] = U
    df["hatched"] = (U > HATCH_U) & ~absent
    df["eligible"] = ~df["hatched"] & ~absent
    df["gap"] = absent | (df["hatched"] & df["status"].eq("wholly_unscorable"))
    df["area_plot"] = df["area_frac"].astype(float).where(~df["gap"])
    area = df["area_frac"].astype(float).fillna(0.0)
    df["ice_covered"] = df["eligible"] & (area <= 0) & (df["share_observed_masked_ice"] >= ICE_COVERED_SHARE)
    df["coverage_reduced"] = df["eligible"] & (U > floor + FLOOR_TOL)

    label = np.full(len(df), LABEL_NONE, dtype=object)
    label[df["coverage_reduced"] & (area <= 0)] = LABEL_NONE_ASSESSED
    label[df["ice_covered"]] = LABEL_ICE
    label[df["eligible"] & (area > 0)] = LABEL_DETECTED
    label[df["hatched"]] = LABEL_INCOMPLETE
    label[absent] = LABEL_NO_INPUT
    df["label"] = label
    df.attrs["floor"] = floor
    return df.sort_values("date").reset_index(drop=True)


def load_zone(zone: str) -> pd.DataFrame | None:
    """Load a zone's aggregate + coverage sidecar from the staged record and classify every day."""
    ap, cp = agg_path(zone), coverage_path(zone)
    if not ap.exists() or not cp.exists():
        return None
    return classify_days(pd.read_parquet(ap), pd.read_csv(cp))


# ---------------------------------------------------------------------------
# Month / year rule (ADDENDUM-02)
# ---------------------------------------------------------------------------
def _max_run(flags: np.ndarray) -> int:
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return best


def monthly_summary(days: pd.DataFrame, area_thresh: float) -> pd.DataFrame:
    """Monthly values from classified days, eligible days only.

    Columns: ``month`` (period), ``n_days``, ``n_eligible``, ``n_rejected``, ``max_consec_rejected``,
    ``missing``, ``area_mean``, ``event_days``, ``max_area_frac``, ``max_Ibar``, ``max_Dbar``,
    ``has_reduced_zero`` (a kept zero month with an eligible day above the floor).
    Missing months carry NaN values (never 0).
    """
    d = days.copy()
    d["month"] = d["date"].dt.to_period("M")
    rows = []
    for m, g in d.groupby("month", sort=True):
        rej = ~g["eligible"].to_numpy()
        e = g[g["eligible"]]
        n_rej = int(rej.sum())
        run = _max_run(rej)
        missing = n_rej >= MONTH_MAX_REJECTED or run >= MONTH_MAX_CONSECUTIVE or e.empty
        nan = float("nan")
        area_mean = nan if missing else float(e["area_frac"].astype("float32").mean())
        rows.append({
            "month": m, "n_days": len(g), "n_eligible": len(e), "n_rejected": n_rej,
            "max_consec_rejected": run, "missing": missing,
            "area_mean": area_mean,
            "event_days": nan if missing else float((e["area_frac"] > area_thresh).sum()),
            "max_area_frac": nan if missing else float(e["area_frac"].max()),
            "max_Ibar": nan if missing else float(e["Ibar"].max()),
            "max_Dbar": nan if missing else float(e["Dbar"].max()),
            "has_reduced_zero": (not missing) and area_mean == 0 and bool(e["coverage_reduced"].any()),
        })
    return pd.DataFrame(rows)


def annual_summary(days: pd.DataFrame, area_thresh: float) -> pd.DataFrame:
    """Annual burden from classified days over eligible days only (rejected days never count as 0)."""
    d = days.copy()
    d["year"] = d["date"].dt.year
    e = d[d["eligible"]]
    out = e.groupby("year").agg(
        n_eligible=("date", "count"),
        max_af=("area_frac", "max"),
        mean_af=("area_frac", "mean"),
        event_days=("area_frac", lambda x: int((x > area_thresh).sum())),
        max_Ibar=("Ibar", "max"),
        max_Dbar=("Dbar", "max"),
        max_Cbar=("Cbar", "max"),
    )
    out["n_rejected"] = d.groupby("year")["eligible"].apply(lambda s: int((~s).sum()))
    out["rows"] = d.groupby("year")["date"].count()
    return out.reset_index()


# ---------------------------------------------------------------------------
# Map rule: detected area is A·V·R; unscorable cells grey; excluded cells never coloured
# ---------------------------------------------------------------------------
CELL_HIDDEN = 0      # R = 0 (outside the zone or one of the 142 excluded cells): not drawn
CELL_SCORED = 1      # retained and scorable (V = 1): metric drawn where non-zero
CELL_ICE = 2         # retained, observed masked ice (reason 2): drawn in the ice colour
CELL_UNKNOWN = 3     # retained, otherwise unscorable (absent / missing SST / unknown ice / no θ90): grey

REASON_OBSERVED_ICE = 2


def map_cells(metric: str, values: np.ndarray, A: np.ndarray, V: np.ndarray, R: np.ndarray,
              reason: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """One day's map: (metric values to colour, cell class) on the (lat, lon) grid.

    Detected-event metrics (A, I, D, C) are shown only where A·V·R = 1; exceedance ``x`` only where
    V·R = 1 and x > 0. Everything else is NaN. The class array says how undrawn cells are painted.
    """
    R1 = np.asarray(R).astype(bool)
    V1 = np.asarray(V).astype(bool) & R1
    det = np.asarray(A).astype(bool) & V1
    vals = np.asarray(values, dtype=float)
    if metric == "A":
        out = np.where(det, 1.0, np.nan)
    elif metric == "x":
        out = np.where(V1 & (vals > 0), vals, np.nan)
    else:
        out = np.where(det & (vals > 0), vals, np.nan)
    cls = np.full(R1.shape, CELL_HIDDEN, dtype=np.int8)
    cls[R1 & ~V1] = CELL_UNKNOWN
    cls[R1 & ~V1 & (np.asarray(reason) == REASON_OBSERVED_ICE)] = CELL_ICE
    cls[V1] = CELL_SCORED
    return out, cls
