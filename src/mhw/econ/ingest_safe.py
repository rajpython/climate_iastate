"""Ingest AKFIN Groundfish Economic SAFE exports (GFSAFE*) into tidy parquet — one per report.

Reads the CSV exports in ``data/raw/akfin_exports/`` (downloaded from AKFIN's public Apex reports),
normalizes each against its :class:`mhw.econ.safe_reports.EconReport` descriptor, and caches one
parquet per report under ``data/raw/econ_safe/``. Source-specific facts live in the registry, not
here — adding/adjusting a report is a registry edit.

Normalization (pure, per report): lower-case columns, FMP_AREA → ``area_code``/``area_label``
(BSAI/GOA/All-Alaska), numeric coercion of the report's measures, and the suppression band column →
``suppressed_band``/``suppressed_pct``/``suppressed`` annotations (values are kept, never dropped —
AKFIN publishes these as non-confidential aggregates). GFSAFE004's two-file export (a download
size-limit split) is concatenated into one report.

CLI: mhw-ingest-econ-safe [--report gfsafe002] [--family value]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from mhw.econ import areas
from mhw.econ.confidential import normalize_suppression
from mhw.econ.safe_reports import (
    ALL_REPORTS,
    CRAB_REPORTS,
    SAFE_REPORTS,
    EconReport,
    get_report,
    reports_by_family,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPORTS_DIR = PROJECT_ROOT / "data" / "raw" / "akfin_exports"
OUT_DIR = PROJECT_ROOT / "data" / "raw" / "econ_safe"

# AKFIN codes suppressed / not-available cells with negative sentinels (-9999, -8888, …). Every
# Economic SAFE measure (catch, value, price, counts, weeks, lengths, tonnage, shares) is
# non-negative, so any negative value is a sentinel to blank.


# ---------------------------------------------------------------------------
# Pure transform (network-free, unit-testable)
# ---------------------------------------------------------------------------

def tidy_report(df: pd.DataFrame, report: EconReport) -> pd.DataFrame:
    """Normalize one report's raw rows to the tidy schema (network-free).

    Lower-cases columns, maps FMP_AREA → ``area_code`` + ``area_label``, coerces YEAR and the
    report's measures to numbers, annotates the suppression band, and stamps ``report_id`` +
    ``family``. Rows with an unrecognised FMP area are kept with a null ``area_code``.
    """
    out = df.copy()
    out.columns = [c.strip().lower() for c in out.columns]

    if "fmp_area" in out.columns:
        out["area_code"] = out["fmp_area"].map(areas.fmp_area_code)
        out["area_label"] = out["area_code"].map(areas.fmp_area_label)
        out = out.drop(columns=["fmp_area"])

    if "year" in out.columns:
        out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")

    for m in report.measures:
        c = m.col.lower()
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    # Blank negative suppressed/missing sentinels (-9999, -8888, …) to NaN across every numeric
    # column (except year) so they are never plotted, summed, or returned by the API. All SAFE
    # measures are non-negative, so a negative value is always a sentinel.
    num_cols = [c for c in out.select_dtypes("number").columns if c != "year"]
    if num_cols:
        out[num_cols] = out[num_cols].where(out[num_cols] >= 0)

    if report.suppression_col:
        out = normalize_suppression(out, report.suppression_col.lower())

    out["report_id"] = report.id
    out["family"] = report.family
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# IO / orchestration
# ---------------------------------------------------------------------------

def read_report(report: EconReport, exports_dir: Path = EXPORTS_DIR) -> pd.DataFrame:
    """Read a report's CSV file(s) (concatenating multi-file exports) and tidy it."""
    frames = []
    for fname in report.files:
        p = exports_dir / fname
        if not p.exists():
            raise FileNotFoundError(f"Missing export for {report.code}: {p}")
        frames.append(pd.read_csv(p))
    raw = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    return tidy_report(raw, report)


def save_parquet(df: pd.DataFrame, report: EconReport, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / report.parquet_name
    df.to_parquet(out, index=False)
    return out


def build(reports: list[EconReport], exports_dir: Path = EXPORTS_DIR,
          out_dir: Path = OUT_DIR) -> list[Path]:
    """Ingest each report → parquet; returns the written paths."""
    written = []
    for r in reports:
        df = read_report(r, exports_dir)
        p = save_parquet(df, r, out_dir)
        yrs = f"{int(df['year'].min())}–{int(df['year'].max())}" if "year" in df else "?"
        print(f"  {r.code:10s} {len(df):>7,} rows  {yrs}  → {p.name}")
        written.append(p)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest AKFIN Groundfish Economic SAFE CSV exports into tidy parquet.")
    p.add_argument("--report", default=None, help="Single report id (e.g. gfsafe002)")
    p.add_argument("--family", default=None, help="Ingest a whole family (e.g. value)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.report:
        r = get_report(args.report)
        if r is None:
            print(f"Unknown report {args.report!r}; known: {sorted(SAFE_REPORTS)}")
            return
        reports = [r]
    elif args.family:
        reports = reports_by_family(args.family) or [
            r for r in CRAB_REPORTS.values() if r.family == args.family]
        if not reports:
            print(f"No reports in family {args.family!r}")
            return
    else:
        reports = list(ALL_REPORTS.values())

    print(f"Ingesting {len(reports)} Economic SAFE report(s) from {EXPORTS_DIR} …")
    paths = build(reports)
    print(f"Done — {len(paths)} parquet(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
