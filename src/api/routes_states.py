"""Routes for regional state aggregates and event detection (v1).

URL conventions (under /v1 router prefix added in main.py):
    GET /regions                       List all regions
    GET /regions/{id}                  Single region metadata
    GET /regions/{id}/states           Daily aggregate time series
    GET /regions/{id}/events           Regional MHW event summaries

Parquet columns (Ibar/Dbar/Cbar/Obar) follow Hobday-paper notation; the API
exposes them as mean_intensity / mean_duration / cumul_intensity / onset_rate
to keep the JSON contract snake_case.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import yaml
from fastapi import APIRouter, HTTPException, Query

from api.schema import DailyState, EventSummary, RegionInfo

router = APIRouter()

ROOT         = Path(__file__).parents[2]
AGG_DIR      = ROOT / "data" / "derived" / "aggregates_region"
_cfg         = yaml.safe_load((ROOT / "config" / "climatology.yml").read_text())
AREA_THRESH  = float(_cfg["regional_events"]["area_frac_threshold"])
GAP_DAYS     = int(_cfg["mhw_definition"]["gap_days"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_regions() -> list[str]:
    return sorted(
        p.stem.replace("region_daily_", "")
        for p in AGG_DIR.glob("region_daily_*.parquet")
    )


def _load_agg(region: str) -> pd.DataFrame:
    p = AGG_DIR / f"region_daily_{region}.parquet"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"No data for region '{region}'")
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values("date").reset_index(drop=True)


def _region_info(region: str) -> RegionInfo:
    df = _load_agg(region)
    return RegionInfo(
        region_id=region,
        start_date=df["date"].min(),
        end_date=df["date"].max(),
        n_days=len(df),
    )


def _detect_events(df: pd.DataFrame) -> list[EventSummary]:
    """Detect MHW events from aggregates using area_frac > AREA_THRESH."""
    events: list[EventSummary] = []
    in_event = False
    start_idx = 0
    event_id = 0
    gap_count = 0

    for i, row in df.iterrows():
        active = row["area_frac"] > AREA_THRESH
        if not in_event:
            if active:
                in_event = True
                start_idx = i
                gap_count = 0
        else:
            if active:
                gap_count = 0
            else:
                gap_count += 1
                if gap_count > GAP_DAYS:
                    end_idx = i - gap_count
                    seg = df.loc[start_idx:end_idx]
                    if len(seg) >= 5:
                        peak = seg.loc[seg["area_frac"].idxmax()]
                        event_id += 1
                        events.append(EventSummary(
                            event_id=event_id,
                            start_date=seg["date"].iloc[0],
                            end_date=seg["date"].iloc[-1],
                            duration_days=len(seg),
                            peak_date=peak["date"],
                            peak_area_frac=round(float(peak["area_frac"]), 4),
                            peak_intensity=round(float(peak["Ibar"]), 3),
                            mean_cumul_intensity=round(float(seg["Cbar"].mean()), 3),
                        ))
                    in_event = False
                    gap_count = 0

    if in_event:
        seg = df.loc[start_idx:]
        if len(seg) >= 5:
            peak = seg.loc[seg["area_frac"].idxmax()]
            event_id += 1
            events.append(EventSummary(
                event_id=event_id,
                start_date=seg["date"].iloc[0],
                end_date=seg["date"].iloc[-1],
                duration_days=len(seg),
                peak_date=peak["date"],
                peak_area_frac=round(float(peak["area_frac"]), 4),
                peak_intensity=round(float(peak["Ibar"]), 3),
                mean_cumul_intensity=round(float(seg["Cbar"].mean()), 3),
            ))

    return events


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/regions", response_model=list[RegionInfo])
def list_regions():
    """List all regions that have aggregated daily data."""
    return [_region_info(r) for r in _list_regions()]


@router.get("/regions/{region_id}", response_model=RegionInfo)
def get_region(region_id: str):
    """Return metadata for a single region (date range and row count)."""
    return _region_info(region_id)


@router.get("/regions/{region_id}/states", response_model=list[DailyState])
def get_daily_states(
    region_id: str,
    start: date | None = Query(None, description="Start date YYYY-MM-DD"),
    end:   date | None = Query(None, description="End date YYYY-MM-DD"),
):
    """Return daily aggregated MHW state metrics for a region."""
    df = _load_agg(region_id)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    if df.empty:
        raise HTTPException(status_code=404, detail="No data in requested date range")

    return [
        DailyState(
            date=r["date"],
            area_frac=round(float(r["area_frac"]), 4),
            mean_intensity=round(float(r["Ibar"]), 3),
            mean_duration=round(float(r["Dbar"]), 2),
            cumul_intensity=round(float(r["Cbar"]), 3),
            onset_rate=round(float(r["Obar"]), 3),
        )
        for _, r in df.iterrows()
    ]


@router.get("/regions/{region_id}/events", response_model=list[EventSummary])
def get_events(
    region_id: str,
    start: date | None = Query(None, description="Start date YYYY-MM-DD"),
    end:   date | None = Query(None, description="End date YYYY-MM-DD"),
    min_duration: int  = Query(5, ge=1, description="Minimum event duration in days"),
):
    """Detect and return MHW events for a region."""
    df = _load_agg(region_id)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    events = _detect_events(df)
    return [e for e in events if e.duration_days >= min_duration]
