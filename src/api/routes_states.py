"""Routes for regional state aggregates and event detection."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

import yaml

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
                    # Close event at last active row
                    end_idx = i - gap_count
                    seg = df.loc[start_idx:end_idx]
                    if len(seg) >= 5:
                        peak = seg.loc[seg["area_frac"].idxmax()]
                        event_id += 1
                        events.append(EventSummary(
                            event_id=event_id,
                            start_date=str(seg["date"].iloc[0]),
                            end_date=str(seg["date"].iloc[-1]),
                            duration_days=len(seg),
                            peak_date=str(peak["date"]),
                            peak_area_frac=round(float(peak["area_frac"]), 4),
                            peak_Ibar=round(float(peak["Ibar"]), 3),
                            mean_Cbar=round(float(seg["Cbar"].mean()), 3),
                        ))
                    in_event = False
                    gap_count = 0

    # Close any open event at end of series
    if in_event:
        seg = df.loc[start_idx:]
        if len(seg) >= 5:
            peak = seg.loc[seg["area_frac"].idxmax()]
            event_id += 1
            events.append(EventSummary(
                event_id=event_id,
                start_date=str(seg["date"].iloc[0]),
                end_date=str(seg["date"].iloc[-1]),
                duration_days=len(seg),
                peak_date=str(peak["date"]),
                peak_area_frac=round(float(peak["area_frac"]), 4),
                peak_Ibar=round(float(peak["Ibar"]), 3),
                mean_Cbar=round(float(seg["Cbar"].mean()), 3),
            ))

    return events


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/regions", response_model=list[RegionInfo])
def list_regions():
    """List all regions that have aggregated daily data."""
    result = []
    for region in _list_regions():
        df = _load_agg(region)
        result.append(RegionInfo(
            region_id=region,
            start_date=str(df["date"].min()),
            end_date=str(df["date"].max()),
            n_days=len(df),
        ))
    return result


@router.get("/states/region/{region_id}", response_model=list[DailyState])
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
            date=str(r["date"]),
            area_frac=round(float(r["area_frac"]), 4),
            Ibar=round(float(r["Ibar"]), 3),
            Dbar=round(float(r["Dbar"]), 2),
            Cbar=round(float(r["Cbar"]), 3),
            Obar=round(float(r["Obar"]), 3),
        )
        for _, r in df.iterrows()
    ]


@router.get("/events/{region_id}", response_model=list[EventSummary])
def get_events(
    region_id: str,
    start: date | None = Query(None),
    end:   date | None = Query(None),
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
