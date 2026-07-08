"""Unified dataset catalog — the single source of truth the assistant tools read.

Generalizes the ``mhw/econ/safe_reports.py`` descriptor pattern to *every* board layer: each dataset
is a declarative ``DatasetSpec`` (grain, dimensions, measures+units, join keys, how to load). Tools
never hard-code a dataset; they discover and query through this registry, so (a) adding a dataset is a
registry entry and (b) every dimension value is discoverable — the agent looks up ``CRAB, SNOW``
instead of guessing ``"snow crab"`` and silently getting nothing.

Dimensions come from two places, unified on load:
  * **file dimensions** — encoded in the filename (region, source, variable, species) via a regex;
  * **column dimensions** — already columns in the parquet (species in landings, gear/sector in econ).
Loading globs the files, adds the file dimensions as columns, and concatenates to one tidy frame.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mhw.econ.safe_reports import ALL_REPORTS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA = PROJECT_ROOT / "data"

# Catch species_code → common name (filenames carry the code; name lives in a column too).
SPECIES = {
    "10110": "arrowtooth flounder", "20510": "sablefish", "21720": "Pacific cod",
    "21740": "walleye pollock", "21921": "Atka mackerel", "30060": "Pacific ocean perch",
    "68580": "snow crab", "69322": "red king crab",
}


@dataclass(frozen=True)
class Measure:
    col: str
    label: str
    units: str
    kind: str = ""


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    title: str
    grain: str                                   # daily | monthly | annual | per-haul | annual-season
    glob: str                                    # under data/, e.g. "raw/coldpool_index_observed_*.parquet"
    measures: tuple[Measure, ...]
    join_keys: tuple[str, ...]                   # ("year",) | ("year","region") | ("date",) | ("season",)
    file_dims: tuple[tuple[str, str], ...] = ()  # (dim_name, regex-with-one-group) parsed from the filename
    col_dims: tuple[str, ...] = ()               # dimension columns already present in the parquet
    exclude: tuple[str, ...] = ()                # filename substrings to skip (e.g. "monthly")
    coverage: str = ""
    note: str = ""

    @property
    def dimensions(self) -> tuple[str, ...]:
        return tuple([d for d, _ in self.file_dims] + list(self.col_dims))

    @property
    def measure_cols(self) -> list[str]:
        return [m.col for m in self.measures]


def _m(col, label, units, kind=""):
    return Measure(col, label, units, kind)


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

_CORE: dict[str, DatasetSpec] = {}


def _reg(spec: DatasetSpec) -> None:
    _CORE[spec.id] = spec


_reg(DatasetSpec(
    "mhw_daily", "Marine-heatwave daily aggregates", "daily",
    "derived/aggregates_region/region_daily_*.parquet",
    (_m("area_frac", "MHW area fraction", "fraction 0–1", "share"),
     _m("Ibar", "Mean intensity", "°C", "temp"),
     _m("Dbar", "Mean duration", "days", "days"),
     _m("Cbar", "Cumulative intensity", "°C·days", "temp"),
     _m("Obar", "Onset rate", "°C/day", "temp")),
    ("date", "region"),
    file_dims=(("region", r"region_daily_(\w+)\.parquet"),),
    coverage="1982–present, 12 zones"))

_reg(DatasetSpec(
    "mhw_risk", "Marine-heatwave risk percentiles", "daily",
    "derived/risk/risk_*.parquet",
    (_m("area_frac_pct", "Area-fraction percentile", "%", "share"),
     _m("Ibar_pct", "Intensity percentile", "%", "share"),
     _m("Dbar_pct", "Duration percentile", "%", "share"),
     _m("Cbar_pct", "Cumulative percentile", "%", "share"),
     _m("composite_risk", "Composite risk", "0–100", "share"),
     _m("risk_level", "Risk level", "category", "category")),
    ("date", "region"),
    file_dims=(("region", r"risk_(\w+)\.parquet"),),
    coverage="1982–present, 12 zones"))

_reg(DatasetSpec(
    "index_ao", "Arctic Oscillation index", "daily", "raw/ao_daily.parquet",
    (_m("ao", "Arctic Oscillation", "index", "index"),), ("date",),
    coverage="daily"))

_reg(DatasetSpec(
    "index_pdo", "Pacific Decadal Oscillation index", "monthly", "raw/pdo_monthly.parquet",
    (_m("pdo", "Pacific Decadal Oscillation", "index", "index"),), ("date",),
    coverage="monthly"))

_reg(DatasetSpec(
    "coldpool_observed", "AFSC observed cold-pool / bottom-state index", "annual",
    "raw/coldpool_index_observed_*.parquet",
    (_m("area_lte2_km2", "Cold-pool area ≤2 °C", "km²", "area"),
     _m("area_lte1_km2", "Area ≤1 °C", "km²", "area"),
     _m("area_lte0_km2", "Area ≤0 °C", "km²", "area"),
     _m("area_lteminus1_km2", "Area ≤−1 °C", "km²", "area"),
     _m("mean_bottom_temp", "Mean bottom temperature", "°C", "temp"),
     _m("mean_bottom_temp_lt100m", "Mean bottom temp (<100 m)", "°C", "temp"),
     _m("mean_surface_temp", "Mean surface temperature", "°C", "temp"),
     _m("mean_bottom_salinity", "Mean bottom salinity", "psu", "salinity")),
    ("year", "region"),
    file_dims=(("region", r"coldpool_index_observed_(\w+)\.parquet"),),
    coverage="annual summer survey; cold-pool areas SEBS/NBS only, bottom temp elsewhere"))

_reg(DatasetSpec(
    "coldpool_modelled", "Modelled cold-pool / bottom temperature", "annual",
    "derived/cold_pool/coldpool_model_*.parquet",
    (_m("mean_bottom_temp", "Mean bottom temperature", "°C", "temp"),
     _m("area_lte2_km2", "Cold-pool area ≤2 °C", "km²", "area"),
     _m("area_lte1_km2", "Area ≤1 °C", "km²", "area"),
     _m("area_lte0_km2", "Area ≤0 °C", "km²", "area"),
     _m("area_lteminus1_km2", "Area ≤−1 °C", "km²", "area")),
    ("year", "source", "region"),
    file_dims=(("source", r"coldpool_model_(bering10k|mom6_nep)"),
               ("region", r"coldpool_model_(?:bering10k|mom6_nep)_(\w+?)(?:_monthly)?\.parquet")),
    exclude=("monthly", "depth_profile"),
    coverage="annual; Bering10K (EBS/NBS/slope) and MOM6 NEP (all)"))

_reg(DatasetSpec(
    "survey_replicate", "Survey-replicated model skill (bottom temp)", "annual",
    "derived/cold_pool/survey_replicate_annual_*.parquet",
    (_m("n_hauls", "Hauls", "count", "count"),
     _m("obs_mean_bottom_temp", "Observed mean bottom temp", "°C", "temp"),
     _m("model_mean_bottom_temp", "Model mean bottom temp", "°C", "temp"),
     _m("bias_c", "Model − observed bias", "°C", "temp")),
    ("year", "source", "region"),
    file_dims=(("source", r"survey_replicate_annual_(bering10k|mom6_nep)"),
               ("region", r"survey_replicate_annual_(?:bering10k|mom6_nep)_(\w+)\.parquet")),
    coverage="annual, co-located at survey hauls"))

_reg(DatasetSpec(
    "oceanhealth_modelled", "Modelled shelf ocean-health variables", "annual",
    "derived/ocean_health/oceanhealth_*.parquet",
    (_m("mean_bottom_oxygen", "Mean bottom oxygen", "ml/l", "oxygen"),
     _m("mean_bottom_ph", "Mean bottom pH", "pH", "ph"),
     _m("mean_bottom_salinity", "Mean bottom salinity", "psu", "salinity")),
    ("year", "variable", "region"),
    file_dims=(("variable", r"oceanhealth_(salinity|oxygen|ph)_"),
               ("region", r"oceanhealth_(?:salinity|oxygen|ph)_mom6_nep_(\w+)\.parquet")),
    coverage="annual, MOM6 NEP"))

_reg(DatasetSpec(
    "oceanhealth_observed", "Observed shelf ocean-health (survey CTD)", "annual",
    "raw/survey_ctd_observed_*.parquet",
    (_m("mean_bottom_oxygen", "Mean bottom oxygen", "ml/l", "oxygen"),
     _m("mean_bottom_ph", "Mean bottom pH", "pH", "ph"),
     _m("mean_bottom_salinity", "Mean bottom salinity", "psu", "salinity")),
    ("year", "region"),
    file_dims=(("region", r"survey_ctd_observed_(\w+)\.parquet"),),
    coverage="annual, sparse"))

_reg(DatasetSpec(
    "catch_thermal", "Survey catch × bottom thermal state (per haul)", "per-haul",
    "raw/catch_bottom_state_*.parquet",
    (_m("cpue_kgkm2", "CPUE (weight)", "kg/km²", "cpue"),
     _m("cpue_nokm2", "CPUE (number)", "n/km²", "cpue"),
     _m("bottom_temperature_c", "Bottom temperature", "°C", "temp"),
     _m("surface_temperature_c", "Surface temperature", "°C", "temp"),
     _m("depth_m", "Depth", "m", "depth")),
    ("year", "region", "species_code"),
    file_dims=(("species_code", r"catch_bottom_state_(\d+)\.parquet"),),
    col_dims=("common_name",),
    coverage="per-haul; 8 species (see SPECIES)"))

_reg(DatasetSpec(
    "hauls", "AFSC bottom-trawl haul temperatures (per haul)", "per-haul",
    "raw/coldpool_hauls_observed_*.parquet",
    (_m("gear_temperature", "Bottom (gear) temperature", "°C", "temp"),
     _m("surface_temperature", "Surface temperature", "°C", "temp"),
     _m("bottom_depth", "Bottom depth", "m", "depth")),
    ("year", "region"),
    file_dims=(("region", r"coldpool_hauls_observed_(\w+)\.parquet"),),
    coverage="per-haul"))

_reg(DatasetSpec(
    "landings", "Commercial landings (statewide Alaska, FOSS)", "annual",
    "raw/landings_foss_ak.parquet",
    (_m("landings_t", "Landings", "metric tons", "catch"),
     _m("value_usd", "Ex-vessel value", "US$ (nominal)", "value")),
    ("year",),
    col_dims=("species", "area_group"),
    coverage="1950–2024; statewide (not per-region); species named e.g. 'CRAB, SNOW'"))


def _build_econ() -> None:
    """One DatasetSpec per econ-SAFE report, reusing the safe_reports registry verbatim."""
    for rid, r in ALL_REPORTS.items():
        cols_lower = tuple(d.lower() for d in r.dimensions)
        key = "season" if rid in {"crsafe004", "crsafe005"} else "year"
        measures = tuple(_m(m.col.lower(), m.label, m.units, m.kind) for m in r.measures)
        _reg(DatasetSpec(
            f"econ_safe:{rid}", f"Econ SAFE — {r.title}", "annual",
            f"raw/econ_safe/{rid}.parquet",
            measures, (key,),
            col_dims=(key,) + cols_lower,
            coverage=r.year_span,
            note=f"AKFIN {r.code}; family {r.family}. {r.notes}"))


_build_econ()

CATALOG: dict[str, DatasetSpec] = dict(_CORE)


# ---------------------------------------------------------------------------
# Loading + discovery
# ---------------------------------------------------------------------------

def get_spec(dataset: str) -> DatasetSpec | None:
    return CATALOG.get(dataset)


def load_dataset(dataset: str, data_root: Path | None = None) -> pd.DataFrame:
    """Read + concatenate a dataset's parquet files, materialising file-dimension columns."""
    spec = CATALOG[dataset]
    root = data_root or DATA
    frames = []
    for fp in sorted(root.glob(spec.glob)):
        if any(x in fp.name for x in spec.exclude):
            continue
        dims = {}
        for dim, rx in spec.file_dims:
            mt = re.search(rx, fp.name)
            if mt is None:
                dims = None
                break
            dims[dim] = mt.group(1)
        if dims is None:
            continue  # filename didn't parse to this spec's dimensions — skip defensively
        df = pd.read_parquet(fp)
        for k, v in dims.items():
            df[k] = v
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if dataset == "catch_thermal" and "species_code" in out.columns:
        out["species_name"] = out["species_code"].map(SPECIES)
    return out


def list_datasets() -> dict:
    return {
        "datasets": [
            {"id": s.id, "title": s.title, "grain": s.grain,
             "dimensions": list(s.dimensions), "measures": s.measure_cols,
             "join_keys": list(s.join_keys), "coverage": s.coverage}
            for s in CATALOG.values()
        ]
    }


def describe_dataset(dataset: str) -> dict:
    s = CATALOG.get(dataset)
    if s is None:
        return {"error": f"unknown dataset {dataset!r}", "valid_datasets": sorted(CATALOG)}
    return {
        "id": s.id, "title": s.title, "grain": s.grain, "coverage": s.coverage, "note": s.note,
        "dimensions": list(s.dimensions), "join_keys": list(s.join_keys),
        "measures": [{"col": m.col, "label": m.label, "units": m.units, "kind": m.kind}
                     for m in s.measures],
    }


def list_dimension_values(dataset: str, dimension: str, data_root: Path | None = None) -> dict:
    s = CATALOG.get(dataset)
    if s is None:
        return {"error": f"unknown dataset {dataset!r}", "valid_datasets": sorted(CATALOG)}
    if dimension not in s.dimensions:
        return {"error": f"{dimension!r} is not a dimension of {dataset!r}",
                "valid_dimensions": list(s.dimensions)}
    df = load_dataset(dataset, data_root=data_root)
    if df.empty or dimension not in df.columns:
        return {"dataset": dataset, "dimension": dimension, "values": []}
    vals = sorted(v for v in df[dimension].dropna().unique().tolist())
    return {"dataset": dataset, "dimension": dimension, "n": len(vals), "values": vals}
