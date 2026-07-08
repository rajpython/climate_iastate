"""Assistant tools — a small, generic, catalog-driven surface over every board dataset.

No per-dataset tools: discovery + query + analytics read the :mod:`mhw.assistant.catalog` registry, so
the set is exhaustive by construction and every dimension value is discoverable (the fix for the
"snow crab" → ``CRAB, SNOW`` naming trap). ``dispatch`` returns ``(model_payload, client_event)`` —
the payload goes back to Claude; the event (or ``None``) streams to the browser (chart specs, report
tokens). Every query result carries provenance and an explicit empty-result contract so the agent
self-corrects instead of fabricating.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from mhw.assistant import analytics, catalog

_MAX_ROWS = 500
_EMPTY_NOTE = ("0 rows for those filters — do NOT chart or state values. Use the valid_values below "
               "or call list_dimension_values, then retry.")


def _downsample(df: pd.DataFrame) -> list[dict]:
    if len(df) > _MAX_ROWS:
        df = df.iloc[:: len(df) // _MAX_ROWS + 1]
    return df.where(pd.notna(df), None).to_dict("records")


def query(dataset: str, filters: dict | None = None, columns: list | None = None,
          data_root: Path | None = None) -> dict:
    spec = catalog.get_spec(dataset)
    if spec is None:
        return {"error": f"unknown dataset {dataset!r}", "valid_datasets": sorted(catalog.CATALOG)}
    df = catalog.load_dataset(dataset, data_root=data_root)
    if df.empty:
        return {"records": [], "note": "dataset has no data on disk"}
    fdf = analytics._apply_filters(df, filters)
    if fdf.empty:
        vv = {}
        for k in (filters or {}):
            if k in df.columns and k not in ("year_min", "year_max"):
                vv[k] = sorted(df[k].dropna().astype(str).unique())[:60]
        return {"dataset": dataset, "records": [], "note": _EMPTY_NOTE, "valid_values": vv}
    if columns:
        keep = [c for c in columns if c in fdf.columns] or list(fdf.columns)
        fdf = fdf[keep]
    if "date" in fdf.columns:
        fdf = fdf.assign(date=pd.to_datetime(fdf["date"]).dt.strftime("%Y-%m-%d"))
    return {"dataset": dataset, "filters": filters or {}, "n_total": len(fdf),
            "n_returned": min(len(fdf), _MAX_ROWS), "records": _downsample(fdf)}


# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------

_DS = {"type": "string", "description": "catalog dataset id (see list_datasets)"}
_FILTERS = {"type": "object", "description": "dimension filters, e.g. {\"region\":\"sebs\",\"year_min\":2015}. "
            "Values may be scalars or lists; year_min/year_max bound the time axis."}

TOOLS: list[dict] = [
    {"name": "list_datasets",
     "description": "List every dataset the board exposes with its grain, dimensions, measures, and join keys. Start here.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "describe_dataset",
     "description": "Full detail for one dataset: dimensions, measures (with units), join keys, coverage.",
     "input_schema": {"type": "object", "properties": {"dataset": _DS}, "required": ["dataset"]}},
    {"name": "list_dimension_values",
     "description": "Valid values of a dimension (regions, species names, gears, fisheries, years). Use this to resolve a name BEFORE querying — never guess a value.",
     "input_schema": {"type": "object", "properties": {"dataset": _DS, "dimension": {"type": "string"}},
                      "required": ["dataset", "dimension"]}},
    {"name": "query",
     "description": "Return tidy records from a dataset with optional filters/columns. Empty results are explicit (with valid_values) — never fabricate when empty.",
     "input_schema": {"type": "object", "properties": {
         "dataset": _DS, "filters": _FILTERS,
         "columns": {"type": "array", "items": {"type": "string"}}}, "required": ["dataset"]}},
    {"name": "aggregate",
     "description": "Group-by aggregation: group_by dimension(s), a measure, and agg in sum|mean|median|min|max|count|std.",
     "input_schema": {"type": "object", "properties": {
         "dataset": _DS, "group_by": {"type": ["string", "array"]}, "measure": {"type": "string"},
         "agg": {"type": "string"}, "filters": _FILTERS},
         "required": ["dataset", "group_by", "measure"]}},
    {"name": "rank",
     "description": "Top-N by a measure: aggregate by a dimension then sort. ascending=true for smallest.",
     "input_schema": {"type": "object", "properties": {
         "dataset": _DS, "measure": {"type": "string"}, "by": {"type": "string"},
         "top_n": {"type": "integer"}, "agg": {"type": "string"},
         "ascending": {"type": "boolean"}, "filters": _FILTERS},
         "required": ["dataset", "measure", "by"]}},
    {"name": "summary_stats",
     "description": "Count/mean/std/min/max/median of a measure (+ per-year trend slope if time-indexed).",
     "input_schema": {"type": "object", "properties": {
         "dataset": _DS, "measure": {"type": "string"}, "filters": _FILTERS},
         "required": ["dataset", "measure"]}},
    {"name": "join_series",
     "description": "Align two datasets' measures on shared keys (year, optionally region), reducing each to that grain by annual mean. Use for cross-dataset comparisons.",
     "input_schema": {"type": "object", "properties": {
         "dataset_a": _DS, "measure_a": {"type": "string"}, "dataset_b": _DS, "measure_b": {"type": "string"},
         "on": {"type": "array", "items": {"type": "string"}},
         "filters_a": _FILTERS, "filters_b": _FILTERS},
         "required": ["dataset_a", "measure_a", "dataset_b", "measure_b"]}},
    {"name": "correlate",
     "description": "Pearson r + linear regression (slope/intercept/R²) between two datasets' measures aligned on year(+region). Returns the aligned points AND a fitted line — pass both to make_chart (scatter + the fit line).",
     "input_schema": {"type": "object", "properties": {
         "dataset_a": _DS, "measure_a": {"type": "string"}, "dataset_b": _DS, "measure_b": {"type": "string"},
         "on": {"type": "array", "items": {"type": "string"}},
         "filters_a": _FILTERS, "filters_b": _FILTERS},
         "required": ["dataset_a", "measure_a", "dataset_b", "measure_b"]}},
    {"name": "descriptive_indicators",
     "description": "For a target year vs the annual series: anomaly, direction, percentile rank, ordinal rank, and analog years.",
     "input_schema": {"type": "object", "properties": {
         "dataset": _DS, "measure": {"type": "string"}, "filters": _FILTERS, "year": {"type": "integer"}},
         "required": ["dataset", "measure"]}},
    {"name": "make_chart",
     "description": "Render a chart from data you retrieved. chart_type ∈ line|bar|scatter|histogram; series is a list of {name,x,y}. trendline adds an OLS fit; dual_axis puts the 2nd series on a right axis. Returns a chart_id you can pass to build_report as chart_ref (no need to resend the whole spec).",
     "input_schema": {"type": "object", "properties": {
         "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "histogram"]},
         "title": {"type": "string"}, "x_title": {"type": "string"}, "y_title": {"type": "string"},
         "trendline": {"type": "boolean"}, "dual_axis": {"type": "boolean"},
         "series": {"type": "array", "items": {"type": "object", "properties": {
             "name": {"type": "string"}, "x": {"type": "array"}, "y": {"type": "array"}}}}},
         "required": ["chart_type", "title", "series"]}},
    {"name": "build_report",
     "description": "Build a downloadable PowerPoint. slides is a list of {heading, bullets:[...], chart_ref:<a chart_id from make_chart> OR chart:<a full spec>}. Prefer chart_ref to reuse a chart you already made.",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"}, "subtitle": {"type": "string"},
         "slides": {"type": "array", "items": {"type": "object", "properties": {
             "heading": {"type": "string"}, "bullets": {"type": "array", "items": {"type": "string"}},
             "chart_ref": {"type": "string", "description": "id returned by a prior make_chart"},
             "chart": {"type": "object"}}, "required": ["heading"]}}},
         "required": ["title", "slides"]}},
]

_CATALOG_TOOLS = {
    "list_datasets": lambda **k: catalog.list_datasets(),
    "describe_dataset": lambda **k: catalog.describe_dataset(k["dataset"]),
    "list_dimension_values": lambda **k: catalog.list_dimension_values(
        k["dataset"], k["dimension"], data_root=k.get("data_root")),
    "query": lambda **k: query(**k),
}
_ANALYTICS_TOOLS = {
    "aggregate": analytics.aggregate, "rank": analytics.rank,
    "summary_stats": analytics.summary_stats, "join_series": analytics.join_series,
    "correlate": analytics.correlate, "descriptive_indicators": analytics.descriptive_indicators,
}


def dispatch(name: str, tool_input: dict[str, Any], data_root: Path | None = None,
             chart_registry: dict | None = None) -> tuple[dict, dict | None]:
    """Execute a tool. Returns ``(model_payload, client_event)``.

    ``chart_registry`` (per-turn) holds charts by ``chart_id`` so ``build_report`` can embed a chart
    made earlier in the same turn via ``chart_ref`` — the fix for compound "make charts then a deck"
    requests without resending large specs.
    """
    ti = dict(tool_input or {})
    if data_root is not None:
        ti.setdefault("data_root", data_root)

    if name in _CATALOG_TOOLS:
        return _CATALOG_TOOLS[name](**ti), None
    if name in _ANALYTICS_TOOLS:
        return _ANALYTICS_TOOLS[name](**ti), None

    if name == "make_chart":
        from mhw.assistant.charts import ChartError, build_chart
        try:
            spec = build_chart(
                ti.get("chart_type", "line"), ti.get("title", ""), ti.get("series", []),
                ti.get("x_title", ""), ti.get("y_title", ""),
                trendline=bool(ti.get("trendline", False)), dual_axis=bool(ti.get("dual_axis", False)))
        except ChartError as exc:
            return {"error": str(exc)}, None
        chart_id = None
        if chart_registry is not None:
            chart_id = f"chart_{len(chart_registry) + 1}"
            chart_registry[chart_id] = spec
        note = "Chart rendered for the user."
        if chart_id:
            note += f" Reference it in build_report as chart_ref={chart_id!r}."
        return ({"ok": True, "chart_id": chart_id, "note": note},
                {"type": "chart", "spec": spec, "chart_id": chart_id})

    if name == "build_report":
        from mhw.assistant.report import build_report
        slides = []
        for s in ti.get("slides", []):
            s = dict(s)
            ref = s.pop("chart_ref", None)
            if ref and chart_registry and ref in chart_registry:
                s["chart"] = chart_registry[ref]
            slides.append(s)
        out = build_report(ti.get("title", ""), slides, ti.get("subtitle", ""))
        return ({"ok": True, "filename": out["filename"]},
                {"type": "report", "token": out["token"], "filename": out["filename"]})

    return {"error": f"unknown tool {name!r}"}, None
