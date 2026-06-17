"""CLI entry point for the MHW forecast — mirrors the existing mhw-* commands.

    mhw-forecast --region ebs --as-of 2026-06-01 --leads 14,30 [--method ar1] [--plot]

Registered in pyproject as ``mhw-forecast = "mhw.forecast.cli:main"``.

Status: argument surface is defined; the compute path is stubbed pending the
`io` adapters (see io.py TODOs). Wiring order, once io is implemented:
    1. load_climatology(region)           -> theta90, mu
    2. load_anomaly_history(region, ...)  -> fit_ar1 -> phi, sigma_eps
    3. load_current_anomaly(region, as_of)
    4. for lead in leads: baseline -> exceedance_probability -> prob map
    5. regional_probability per lead; write map + regional series; optional plot
"""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mhw-forecast", description=__doc__)
    p.add_argument("--region", required=True,
                   help="region id (goa|ebs|nbs|chukchi|beaufort)")
    p.add_argument("--as-of", help="forecast origin date YYYY-MM-DD (default: latest)")
    p.add_argument("--leads", default="14,30",
                   help="comma-separated forecast leads in days (default: 14,30)")
    p.add_argument("--method", default="ar1",
                   choices=["persistence", "damped", "ar1"],
                   help="baseline forecast method (default: ar1)")
    p.add_argument("--plot", action="store_true", help="render the probability map")
    return p


def main() -> int:
    args = build_parser().parse_args()
    leads = [int(x) for x in args.leads.split(",") if x.strip()]
    print(f"[mhw-forecast] region={args.region} as_of={args.as_of} "
          f"method={args.method} leads={leads}")
    raise NotImplementedError(
        "Compute path pending io adapters — see src/mhw/forecast/io.py"
    )


if __name__ == "__main__":
    raise SystemExit(main())
