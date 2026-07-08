"""Assistant tools — thin, pure wrappers over the existing data layer.

No new data logic: each tool reads the same parquet the API/dashboard read, or calls an existing
pure helper (``cold_pool_summary``). Tools are network-free and unit-testable on small frames.
``dispatch`` returns ``(model_payload, client_event)`` — ``model_payload`` goes back to Claude as the
tool result; ``client_event`` (or ``None``) is streamed to the browser (chart specs, report tokens).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from mhw.fetch.foss_catch import cold_pool_summary

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"
_MAX_ROWS = 600  # cap records returned to the model to bound token spend


def _agg_dir(root: Path) -> Path:
    return root / "derived" / "aggregates_region"


def _raw_dir(root: Path) -> Path:
    return root / "raw"


def _records(df: pd.DataFrame) -> list[dict]:
    """Down-sample to <= _MAX_ROWS evenly and JSON-normalise."""
    if len(df) > _MAX_ROWS:
        step = len(df) // _MAX_ROWS + 1
        df = df.iloc[::step]
    out = df.where(pd.notna(df), None)
    return out.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Data tools (pure)
# ---------------------------------------------------------------------------

def list_regions(data_root: Path | None = None) -> dict:
    d = _agg_dir(data_root or DATA_ROOT)
    zones = sorted(p.stem.replace("region_daily_", "") for p in d.glob("region_daily_*.parquet"))
    return {"regions": zones}


def query_region_states(
    region: str,
    start: str | None = None,
    end: str | None = None,
    data_root: Path | None = None,
) -> dict:
    p = _agg_dir(data_root or DATA_ROOT) / f"region_daily_{region}.parquet"
    if not p.exists():
        return {"error": f"no data for region {region!r}"}
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    if start:
        df = df[df["date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["date"] <= pd.to_datetime(end)]
    df = df.copy()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return {"region": region, "columns": list(df.columns), "records": _records(df)}


def query_cold_pool(region: str = "sebs", data_root: Path | None = None) -> dict:
    p = _raw_dir(data_root or DATA_ROOT) / f"coldpool_index_observed_{region}.parquet"
    if not p.exists():
        return {"error": f"no observed cold-pool index for region {region!r}"}
    df = pd.read_parquet(p).sort_values("year")
    return {"region": region, "records": _records(df)}


def catch_thermal_summary(
    species_code: int,
    threshold: float = 2.0,
    data_root: Path | None = None,
) -> dict:
    p = _raw_dir(data_root or DATA_ROOT) / f"catch_bottom_state_{species_code}.parquet"
    if not p.exists():
        return {"error": f"no catch×bottom-state data for species_code {species_code}"}
    summary = cold_pool_summary(pd.read_parquet(p), threshold=threshold)
    return {"species_code": species_code, "threshold_c": threshold, "records": _records(summary)}


def query_index(index: str = "pdo", data_root: Path | None = None) -> dict:
    name = index.lower()
    fname = {"ao": "ao_daily.parquet", "pdo": "pdo_monthly.parquet"}.get(name)
    if fname is None:
        return {"error": f"unknown index {index!r}; known: ao, pdo"}
    p = _raw_dir(data_root or DATA_ROOT) / fname
    if not p.exists():
        return {"error": f"index {index!r} not available"}
    df = pd.read_parquet(p)
    if "date" in df.columns:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return {"index": name, "records": _records(df)}


def query_landings(
    species: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    data_root: Path | None = None,
) -> dict:
    p = _raw_dir(data_root or DATA_ROOT) / "landings_foss_ak.parquet"
    if not p.exists():
        return {"error": "landings not available"}
    df = pd.read_parquet(p)
    if species:
        df = df[df["species"].str.contains(species, case=False, na=False)]
    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    return {"records": _records(df)}


# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "name": "list_regions",
        "description": "List the region/zone ids that have daily MHW aggregate data.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "query_region_states",
        "description": (
            "Daily MHW aggregates for a region: area_frac (share of region in MHW), Ibar (mean "
            "intensity °C), Dbar (mean duration days), Cbar (cumulative °C·days), Obar (onset rate). "
            "Optional ISO date range."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string"},
                "start": {"type": "string", "description": "YYYY-MM-DD"},
                "end": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["region"],
        },
    },
    {
        "name": "query_cold_pool",
        "description": "AFSC observed cold-pool index (annual): area ≤2/1/0/−1 °C km², mean bottom/surface temp. Cold-pool regions sebs/nbs.",
        "input_schema": {
            "type": "object",
            "properties": {"region": {"type": "string", "default": "sebs"}},
        },
    },
    {
        "name": "catch_thermal_summary",
        "description": (
            "Per (region, year) share of a species' biomass/hauls inside the cold band (≤ threshold °C) "
            "with mean CPUE in/out and BT–CPUE correlation, from survey catch × bottom state. "
            "species_code e.g. 68580 snow crab, 21720 Pacific cod, 21740 walleye pollock."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "species_code": {"type": "integer"},
                "threshold": {"type": "number", "default": 2.0},
            },
            "required": ["species_code"],
        },
    },
    {
        "name": "query_index",
        "description": "Climate index time series: 'ao' (Arctic Oscillation, daily) or 'pdo' (Pacific Decadal Oscillation, monthly).",
        "input_schema": {
            "type": "object",
            "properties": {"index": {"type": "string", "enum": ["ao", "pdo"]}},
            "required": ["index"],
        },
    },
    {
        "name": "query_landings",
        "description": "Statewide Alaska commercial landings (annual): landings_t and ex-vessel value_usd, optional species substring + year range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "species": {"type": "string"},
                "start_year": {"type": "integer"},
                "end_year": {"type": "integer"},
            },
        },
    },
    {
        "name": "make_chart",
        "description": (
            "Render a chart for the user from data you already retrieved. chart_type ∈ line|scatter|bar. "
            "series is a list of {name, x, y}. Returns nothing to you except confirmation — the chart is "
            "shown to the user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "enum": ["line", "scatter", "bar"]},
                "title": {"type": "string"},
                "x_title": {"type": "string"},
                "y_title": {"type": "string"},
                "series": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "x": {"type": "array"},
                            "y": {"type": "array", "items": {"type": "number"}},
                        },
                        "required": ["x", "y"],
                    },
                },
            },
            "required": ["chart_type", "title", "series"],
        },
    },
    {
        "name": "build_report",
        "description": (
            "Build a downloadable PowerPoint (.pptx) deck for the user. slides is a list of "
            "{heading, bullets:[...], chart:<a chart spec exactly as passed to make_chart, or omit>}. "
            "Returns a download the user can click; do not expect the file back."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "bullets": {"type": "array", "items": {"type": "string"}},
                            "chart": {"type": "object"},
                        },
                        "required": ["heading"],
                    },
                },
            },
            "required": ["title", "slides"],
        },
    },
]

_DATA_TOOLS = {
    "list_regions": list_regions,
    "query_region_states": query_region_states,
    "query_cold_pool": query_cold_pool,
    "catch_thermal_summary": catch_thermal_summary,
    "query_index": query_index,
    "query_landings": query_landings,
}


def dispatch(name: str, tool_input: dict[str, Any], data_root: Path | None = None) -> tuple[dict, dict | None]:
    """Execute a tool. Returns ``(model_payload, client_event)``."""
    ti = dict(tool_input or {})

    if name in _DATA_TOOLS:
        return _DATA_TOOLS[name](**ti, data_root=data_root), None

    if name == "make_chart":
        from mhw.assistant.charts import build_chart

        spec = build_chart(
            ti.get("chart_type", "line"), ti.get("title", ""), ti.get("series", []),
            ti.get("x_title", ""), ti.get("y_title", ""),
        )
        return ({"ok": True, "note": "Chart rendered for the user."},
                {"type": "chart", "spec": spec})

    if name == "build_report":
        from mhw.assistant.report import build_report

        out = build_report(ti.get("title", ""), ti.get("slides", []), ti.get("subtitle", ""))
        return ({"ok": True, "filename": out["filename"]},
                {"type": "report", "token": out["token"], "filename": out["filename"]})

    return ({"error": f"unknown tool {name!r}"}, None)
