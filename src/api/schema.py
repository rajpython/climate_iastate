"""Pydantic response models for the MHW State API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RegionInfo(BaseModel):
    region_id: str
    start_date: str
    end_date: str
    n_days: int


class DailyState(BaseModel):
    date: str
    area_frac: float
    Ibar: float
    Dbar: float
    Cbar: float
    Obar: float


class EventSummary(BaseModel):
    event_id: int
    start_date: str
    end_date: str
    duration_days: int
    peak_date: str
    peak_area_frac: float
    peak_Ibar: float
    mean_Cbar: float


class MapCell(BaseModel):
    lat: float
    lon: float
    value: float | None


class MapPayload(BaseModel):
    region: str
    date: str
    metric: str
    units: str
    cells: list[MapCell]


class IndexRecord(BaseModel):
    date: str
    value: float


class IndexPayload(BaseModel):
    index: str        # "ao" or "pdo"
    frequency: str    # "daily" or "monthly"
    records: list[IndexRecord]


class RiskRecord(BaseModel):
    date: str
    composite_risk: float
    risk_level: str
    pct_area_frac: float
    pct_Ibar: float
    pct_Dbar: float
    pct_Cbar: float


class RiskPayload(BaseModel):
    region: str
    records: list[RiskRecord]
