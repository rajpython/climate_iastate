"""AO and PDO index fetchers — climate regime conditioning indicators.

Sources
-------
AO daily  : NOAA CPC FTP — full history (1950–present)
            https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.ao.cdas.z1000.19500101_current.csv
            Format: year,month,day,ao_index_cdas

PDO monthly: NOAA PSL — full history (1870–present)
             https://psl.noaa.gov/pdo/data/pdo.timeseries.sstens.csv
             Format: header line, then YYYY-MM-DD,value (-9999 = missing)

CLI: mhw-fetch-indices --plot
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# ---------------------------------------------------------------------------
# Source URLs
# ---------------------------------------------------------------------------
AO_URL = (
    "https://ftp.cpc.ncep.noaa.gov/cwlinks/"
    "norm.daily.ao.cdas.z1000.19500101_current.csv"
)
PDO_URL = "https://psl.noaa.gov/pdo/data/pdo.timeseries.sstens.csv"

_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# AO — fetch & parse
# ---------------------------------------------------------------------------

def fetch_ao(years_back: int = 2) -> pd.DataFrame:
    """Fetch AO daily index from CPC FTP.

    Parameters
    ----------
    years_back : int
        How many years of history to retain in the returned DataFrame.
        Full history is downloaded; older rows are dropped.

    Returns
    -------
    pd.DataFrame with columns: date (datetime64), ao (float64)
    """
    print("Fetching AO daily index from CPC FTP …")
    resp = requests.get(AO_URL, timeout=_TIMEOUT)
    resp.raise_for_status()

    # Parse: year,month,day,ao_index_cdas
    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = df.columns.str.strip()

    # Build date column
    df["date"] = pd.to_datetime(
        df[["year", "month", "day"]].rename(
            columns={"year": "year", "month": "month", "day": "day"}
        )
    )
    df = df.rename(columns={"ao_index_cdas": "ao"})[["date", "ao"]]
    df = df.dropna(subset=["ao"]).sort_values("date").reset_index(drop=True)

    if years_back is not None:
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=years_back)
        df = df[df["date"] >= cutoff].reset_index(drop=True)

    print(f"  AO: {len(df):,} rows, {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ---------------------------------------------------------------------------
# PDO — fetch & parse
# ---------------------------------------------------------------------------

def fetch_pdo(years_back: int = 5) -> pd.DataFrame:
    """Fetch PDO monthly index from NOAA PSL.

    Parameters
    ----------
    years_back : int
        How many years of history to retain in the returned DataFrame.

    Returns
    -------
    pd.DataFrame with columns: date (datetime64, first-of-month), pdo (float64)
    """
    print("Fetching PDO monthly index from NOAA PSL …")
    resp = requests.get(PDO_URL, timeout=_TIMEOUT)
    resp.raise_for_status()

    lines = resp.text.splitlines()

    # First line is a header comment; skip it
    data_lines = [ln for ln in lines[1:] if ln.strip()]

    rows = []
    for ln in data_lines:
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        date_str = parts[0].strip()
        val_str = parts[1].strip()
        try:
            dt = pd.to_datetime(date_str)
            val = float(val_str)
        except (ValueError, TypeError):
            continue
        if val == -9999.0:  # missing sentinel
            continue
        rows.append({"date": dt, "pdo": val})

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    if years_back is not None:
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=years_back)
        df = df[df["date"] >= cutoff].reset_index(drop=True)

    print(f"  PDO: {len(df):,} rows, {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ---------------------------------------------------------------------------
# Save as parquet
# ---------------------------------------------------------------------------

def save_parquet(df: pd.DataFrame, fname: str) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / fname
    df.to_parquet(out, index=False)
    print(f"  Saved → {out}")
    return out


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_indices_plotly(
    ao: pd.DataFrame,
    pdo: pd.DataFrame,
    ao_years: int = 2,
    pdo_years: int = 5,
) -> Path:
    """Render AO daily + PDO monthly time series with Plotly and save as HTML."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            f"Arctic Oscillation (AO) — daily, last {ao_years} yr",
            f"Pacific Decadal Oscillation (PDO) — monthly, last {pdo_years} yr",
        ),
        vertical_spacing=0.14,
    )

    # ---- AO panel — daily line ----
    fig.add_trace(
        go.Scatter(
            x=ao["date"],
            y=ao["ao"],
            mode="lines",
            line=dict(color="steelblue", width=1),
            name="AO",
            showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_hline(y=0, line_width=0.8, line_color="black", row=1, col=1)

    # ---- PDO panel — monthly step ----
    fig.add_trace(
        go.Scatter(
            x=pdo["date"],
            y=pdo["pdo"],
            mode="lines",
            line=dict(color="darkorange", width=2, shape="hv"),
            name="PDO",
            showlegend=False,
        ),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_width=0.8, line_color="black", row=2, col=1)

    fig.update_yaxes(title_text="AO Index", row=1, col=1)
    fig.update_yaxes(title_text="PDO Index", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    fig.update_layout(
        height=700,
        width=1000,
        title_text="Climate Regime Indices — AO & PDO",
        title_x=0.5,
    )

    out_dir = PROJECT_ROOT / "outputs" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "ao_pdo_indices.html"
    fig.write_html(str(html_path))
    print(f"  Plot (HTML) → {html_path}")

    try:
        png_path = out_dir / "ao_pdo_indices.png"
        fig.write_image(str(png_path))
        print(f"  Plot (PNG)  → {png_path}")
    except Exception:
        print("  (PNG export skipped — install kaleido for static image export)")

    fig.show()
    return html_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch AO daily and PDO monthly climate indices.",
    )
    parser.add_argument(
        "--ao-years", type=int, default=2, metavar="N",
        help="Years of AO history to retain (default: 2)",
    )
    parser.add_argument(
        "--pdo-years", type=int, default=5, metavar="N",
        help="Years of PDO history to retain (default: 5)",
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Generate and display time series plots (Plotly)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    ao = fetch_ao(years_back=args.ao_years)
    pdo = fetch_pdo(years_back=args.pdo_years)

    print("\nSaving parquet files …")
    save_parquet(ao, "ao_daily.parquet")
    save_parquet(pdo, "pdo_monthly.parquet")

    # Summary
    print(f"\nAO  — range: {ao['ao'].min():.3f} to {ao['ao'].max():.3f}")
    print(f"PDO — range: {pdo['pdo'].min():.3f} to {pdo['pdo'].max():.3f}")
    print(f"AO latest date:  {ao['date'].max().date()}")
    print(f"PDO latest date: {pdo['date'].max().date()}")

    if args.plot:
        print("\nGenerating plots …")
        plot_indices_plotly(ao, pdo, ao_years=args.ao_years, pdo_years=args.pdo_years)


if __name__ == "__main__":
    main()
