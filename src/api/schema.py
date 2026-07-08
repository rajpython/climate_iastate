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


# ---------------------------------------------------------------------------
# Cold pool — AFSC observed index (EBS bottom-trawl survey, validation target)
# ---------------------------------------------------------------------------

class ColdPoolRecord(BaseModel):
    year:                int
    area_lte2_km2:       float | None  # headline cold-pool index: area ≤ 2 °C
    area_lte1_km2:       float | None
    area_lte0_km2:       float | None
    area_lteminus1_km2:  float | None
    mean_bottom_temp:    float | None  # °C, survey gear (bottom) temperature
    mean_surface_temp:   float | None  # °C


class ColdPoolPayload(BaseModel):
    source:    str = "AFSC EBS bottom-trawl survey (observed)"
    region:    str = "sebs"
    units:     str = "km2 (areas); degC (temperatures)"
    note:      str = (
        "Observed survey-derived cold-pool index; annual, summer survey. "
        "Lagged (not near-real-time). Validation target for modelled bottom temperature."
    )
    records:   list[ColdPoolRecord]


# ---------------------------------------------------------------------------
# Survey-replicated model validation (model sampled at haul locations + dates)
# ---------------------------------------------------------------------------

class OceanHealthRecord(BaseModel):
    year:  int
    value: float | None   # annual shelf mean of the variable (units in the payload)


class OceanHealthPayload(BaseModel):
    variable: str = "salinity"
    region:   str = "sebs"
    kind:     str = "observed"       # "observed" | "modelled"
    source:   str
    units:    str = "psu"
    note:     str = ""
    records:  list[OceanHealthRecord]


class EconMeasureInfo(BaseModel):
    col:   str
    label: str
    units: str
    kind:  str = ""


class EconReportInfo(BaseModel):
    id:         str
    code:       str
    title:      str
    family:     str
    dimensions: list[str]
    measures:   list[EconMeasureInfo]
    year_span:  str


class EconReportListPayload(BaseModel):
    source:  str = "AKFIN Groundfish Economic SAFE (NOAA/AFSC)"
    note:    str = (
        "Fishery-dependent commercial groundfish economics at FMP-area resolution "
        "(BSAI / GOA / All Alaska) — distinct from the survey ecosystem regions. Annual, "
        "download-and-cache from AKFIN Apex reports."
    )
    reports: list[EconReportInfo]


class EconDataPayload(BaseModel):
    report_id: str
    code:      str
    title:     str
    family:    str
    columns:   list[str]
    note:      str = ""
    records:   list[dict]


class LandingsRecord(BaseModel):
    year:         int
    species:      str
    species_code: str | None = None
    landings_t:   float | None    # commercial landings, metric tons
    value_usd:    float | None    # ex-vessel value, current (nominal) US$


class LandingsPayload(BaseModel):
    source:     str = "NOAA FOSS Commercial Landings (statewide Alaska)"
    area_group: str = "statewide"
    resolution: str = "statewide"   # statewide Alaska — NOT sub-region
    units:      str = "metric tons (landings); current US$ (ex-vessel value)"
    note:       str = (
        "Fishery-DEPENDENT commercial harvest — distinct from the fishery-independent survey. "
        "Statewide Alaska only (not sub-region). Ex-vessel value is nominal (not inflation-"
        "adjusted). Annual, finalised with a lag. Aggregated/non-confidential (NOAA rule of three)."
    )
    records:    list[LandingsRecord]


class SurveyReplicateRecord(BaseModel):
    year:                    int
    n_hauls:                 int
    obs_mean_bottom_temp:    float | None  # °C, observed gear temp averaged over hauls
    model_mean_bottom_temp:  float | None  # °C, model sampled at the same hauls
    bias_c:                  float | None  # model − observed


class SurveyReplicatePayload(BaseModel):
    source: str
    method: str = (
        "Survey replication: model bottom temperature sampled at each AFSC haul's "
        "location and nearest date, then compared to observed gear temperature "
        "(after Kearney 2021; Seelanki et al. 2025). This is the literature-standard "
        "model-vs-survey comparison — distinct from the full-shelf model product."
    )
    bias_c:  float | None = None   # overall haul-level bias (model − obs)
    rmse_c:  float | None = None   # overall haul-level RMSE
    corr:    float | None = None   # overall haul-level correlation
    n_hauls: int = 0
    records: list[SurveyReplicateRecord]


# ---------------------------------------------------------------------------
# Short-term MHW forecast (LOFRA damped-persistence module, run on our area_frac)
# ---------------------------------------------------------------------------

class ForecastRole(str, Enum):
    PERSISTENCE = "persistence"   # point + AR(1) band + L1 occurrence probability
    CLIMATOLOGY = "climatology"   # magnitude/area shown as climatology only (ice-limited)


class OnsetState(str, Enum):
    ELEVATED = "elevated"
    NORMAL   = "normal"


class ForecastLeadRecord(BaseModel):
    lead:        str              # honesty-ladder id: L1 / L2 / L3
    lead_months: int
    confidence:  str              # headline / banded / watch
    method:      str              # damped_persistence / climatology
    point:       float | None     # forecast area_frac at this lead
    ar1_var:     float | None     # h-step AR(1) predictive variance (source of the band)
    band_lo:     float | None
    band_hi:     float | None
    l1_prob:     float | None     # occurrence probability — L1 only (None otherwise)


class ForecastPayload(BaseModel):
    zone:           str
    role:           ForecastRole
    ice_caveat:     bool = False  # NBS + Arctic: satellite SST ice-contaminated
    lim_reading:    bool = True   # False where the broad-field/LIM interpretation is unavailable
    module_version: str | None = None   # pinned, paper-validated module (null before v1 delivery)
    fit_vintage:    str | None = None    # coefficient-manifest fit-vintage (provenance)
    note:           str = ""
    records:        list[ForecastLeadRecord]


class OnsetRecord(BaseModel):
    date:      date_type
    state:     OnsetState
    threshold: float              # tunable decision threshold (paper operating point default)


class OnsetWatchPayload(BaseModel):
    zone:           str = "sebs"
    module_version: str | None = None
    fit_vintage:    str | None = None
    note:           str = (
        "Experimental two-state early-warning WATCH (elevated/normal) — a discrimination "
        "indicator, NOT a calibrated probability and NOT a triggered alarm. SEBS only."
    )
    records:        list[OnsetRecord]
