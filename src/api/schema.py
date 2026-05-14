"""Pydantic response models for the MHW State API (v1).

Field naming conventions:
- All field names are snake_case in the API JSON, regardless of how they
  appear in the underlying parquet columns. The internal columns use
  Hobday-paper notation (Ibar/Dbar/Cbar/Obar); the API exposes those as
  mean_intensity / mean_duration / cumul_intensity / onset_rate.
- All date fields use Python `date` type (Pydantic serializes to ISO strings
  in JSON automatically; client-visible representation is unchanged).
- Categorical fields use string-valued Enums so OpenAPI clients can codegen
  typed enumerations.
"""
from __future__ import annotations

from datetime import date as date_type
from enum import Enum

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums (exposed in OpenAPI as typed enumerations)
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    NORMAL    = "Normal"
    ELEVATED  = "Elevated"
    HIGH_RISK = "High Risk"


class MapMetric(str, Enum):
    INTENSITY            = "I"   # threshold exceedance, °C above θ₉₀
    DURATION             = "D"   # consecutive-day count, only nonzero when confirmed
    CUMULATIVE_INTENSITY = "C"   # running sum of intensity, °C·days
    ACTIVE_FLAG          = "A"   # 1 when cell is in a confirmed MHW
    THRESHOLD_EXCEEDANCE = "x"   # raw SST anomaly above θ₉₀ (precursor of I)


class IndexName(str, Enum):
    AO  = "ao"
    PDO = "pdo"


class IndexFrequency(str, Enum):
    DAILY   = "daily"
    MONTHLY = "monthly"


# ---------------------------------------------------------------------------
# Region metadata
# ---------------------------------------------------------------------------

class RegionInfo(BaseModel):
    region_id:  str
    start_date: date_type
    end_date:   date_type
    n_days:     int


# ---------------------------------------------------------------------------
# Daily regional aggregates
# ---------------------------------------------------------------------------

class DailyState(BaseModel):
    date:             date_type
    area_frac:        float    # cosine-weighted share of region's ocean in confirmed MHW
    mean_intensity:   float    # parquet column: Ibar (°C above 90th-pct threshold)
    mean_duration:    float    # parquet column: Dbar (days)
    cumul_intensity:  float    # parquet column: Cbar (°C·days)
    onset_rate:       float    # parquet column: Obar (°C/day, nonzero only on confirmation days)


# ---------------------------------------------------------------------------
# Discrete regional events
# ---------------------------------------------------------------------------

class EventSummary(BaseModel):
    event_id:             int
    start_date:           date_type
    end_date:             date_type
    duration_days:        int
    peak_date:            date_type
    peak_area_frac:       float
    peak_intensity:       float    # parquet column: peak_Ibar
    mean_cumul_intensity: float    # parquet column: mean_Cbar


# ---------------------------------------------------------------------------
# Per-cell spatial map snapshot
# ---------------------------------------------------------------------------

class MapCell(BaseModel):
    lat:   float
    lon:   float
    value: float | None


class MapPayload(BaseModel):
    region: str
    date:   date_type
    metric: MapMetric
    units:  str
    cells:  list[MapCell]


# ---------------------------------------------------------------------------
# Climate indices
# ---------------------------------------------------------------------------

class IndexRecord(BaseModel):
    date:  date_type
    value: float


class IndexPayload(BaseModel):
    index:     IndexName
    frequency: IndexFrequency
    records:   list[IndexRecord]
