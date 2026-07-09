"""Tool dispatch tests — catalog-driven routing, chart events, grounding backstops."""
from __future__ import annotations

import pandas as pd
import pytest

from mhw.assistant import tools


def _mhw(tmp):
    a = tmp / "derived" / "aggregates_region"
    a.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=5, freq="D"),
        "area_frac": [0.1, 0.2, 0.3, 0.4, 0.5],
        "Ibar": [1.0] * 5, "Dbar": [0.0] * 5, "Cbar": [0.0] * 5, "Obar": [0.0] * 5,
    }).to_parquet(a / "region_daily_sebs.parquet")
    return tmp


def test_dispatch_query(tmp_path):
    _mhw(tmp_path)
    payload, ev = tools.dispatch("query", {"dataset": "mhw_daily", "filters": {"region": "sebs"}},
                                 data_root=tmp_path)
    assert ev is None
    assert payload["n_total"] == 5


def test_dispatch_list_datasets():
    payload, ev = tools.dispatch("list_datasets", {})
    assert ev is None
    assert any(d["id"] == "mhw_daily" for d in payload["datasets"])


def test_dispatch_aggregate(tmp_path):
    _mhw(tmp_path)
    payload, ev = tools.dispatch(
        "aggregate", {"dataset": "mhw_daily", "group_by": "region", "measure": "area_frac", "agg": "mean"},
        data_root=tmp_path)
    assert ev is None and payload["n"] == 1


def test_dispatch_make_chart_event():
    pytest.importorskip("plotly")
    payload, ev = tools.dispatch(
        "make_chart",
        {"chart_type": "line", "title": "t", "series": [{"name": "a", "x": [1, 2], "y": [3, 4]}]})
    assert payload["ok"] is True
    assert ev["type"] == "chart" and "data" in ev["spec"]


def test_dispatch_make_chart_empty_rejected():
    pytest.importorskip("plotly")
    payload, ev = tools.dispatch("make_chart", {"chart_type": "line", "title": "t", "series": []})
    assert "error" in payload
    assert ev is None


def test_dispatch_scatter_trendline():
    pytest.importorskip("plotly")
    payload, ev = tools.dispatch("make_chart", {
        "chart_type": "scatter", "title": "t", "trendline": True,
        "series": [{"name": "a", "x": [1, 2, 3, 4], "y": [2, 4, 6, 8]}]})
    assert ev["type"] == "chart"
    # scatter + its OLS fit = 2 traces
    assert len(ev["spec"]["data"]) == 2


def test_dispatch_unknown_tool():
    payload, ev = tools.dispatch("bogus", {})
    assert "error" in payload
    assert ev is None


def test_make_chart_registers_chart_id():
    pytest.importorskip("plotly")
    store: dict = {}
    payload, ev = tools.dispatch(
        "make_chart",
        {"chart_type": "line", "title": "t", "series": [{"name": "a", "x": [1, 2], "y": [3, 4]}]},
        chart_store=store)
    assert payload["chart_id"] == "chart_1"
    assert ev["chart_id"] == "chart_1"
    assert "chart_1" in store


def test_build_report_resolves_two_chart_refs(tmp_path):
    pytest.importorskip("pptx")
    pytest.importorskip("plotly")
    pytest.importorskip("kaleido")
    store: dict = {}
    for _ in range(2):
        tools.dispatch("make_chart",
                       {"chart_type": "bar", "title": "t", "series": [{"name": "a", "x": ["x"], "y": [1.0]}]},
                       chart_store=store)
    payload, ev = tools.dispatch(
        "build_report",
        {"title": "Deck", "slides": [{"heading": "A", "chart_ref": "chart_1"},
                                     {"heading": "B", "chart_ref": "chart_2"}]},
        chart_store=store)
    assert payload["ok"] is True
    assert ev["type"] == "report"


def test_build_report_unknown_chart_ref_errors():
    payload, ev = tools.dispatch(
        "build_report",
        {"title": "Deck", "slides": [{"heading": "A", "chart_ref": "chart_99"}]},
        chart_store={})
    assert "error" in payload
    assert ev is None


def test_dispatch_catches_tool_exception_as_payload():
    # Missing required args (bad model input) must degrade to an error payload, not raise.
    payload, ev = tools.dispatch("aggregate", {"dataset": "landings"})
    assert "error" in payload
    assert ev is None


def test_make_table_event():
    payload, ev = tools.dispatch(
        "make_table", {"title": "Top", "columns": ["a", "b"], "rows": [[1, 2], [3, 4]]})
    assert payload["ok"] is True
    assert ev["type"] == "table"
    assert ev["spec"]["columns"] == ["a", "b"]


def test_export_data_from_table_csv():
    from mhw.assistant.report import report_path
    payload, ev = tools.dispatch(
        "export_data",
        {"format": "csv", "table": {"columns": ["x", "y"], "rows": [[1, 2]]}, "filename": "mine"})
    assert ev["type"] == "download"
    assert ev["filename"].endswith(".csv")
    assert report_path(ev["token"]) is not None


def test_export_data_from_dataset_xlsx(tmp_path):
    pytest.importorskip("xlsxwriter")
    d = tmp_path / "raw"
    d.mkdir(parents=True)
    pd.DataFrame({"year": [2000], "species": ["CRAB, SNOW"], "area_group": ["s"],
                  "landings_t": [1.0], "value_usd": [2.0]}).to_parquet(d / "landings_foss_ak.parquet")
    payload, ev = tools.dispatch("export_data", {"format": "xlsx", "dataset": "landings"},
                                 data_root=tmp_path)
    assert ev["type"] == "download"
    assert ev["filename"].endswith(".xlsx")


def test_build_report_table_slide(tmp_path):
    pytest.importorskip("pptx")
    from mhw.assistant.report import build_report
    out = build_report("Deck", [{"heading": "T", "table": {"columns": ["a", "b"],
                                                            "rows": [[1, 2], [3, 4]]}}],
                       out_dir=tmp_path)
    assert (tmp_path / out["token"]).exists()


def test_build_report_writes_pptx(tmp_path):
    pytest.importorskip("pptx")
    pytest.importorskip("plotly")
    pytest.importorskip("kaleido")
    from mhw.assistant.charts import build_chart
    from mhw.assistant.report import build_report

    spec = build_chart("bar", "T", [{"name": "a", "x": ["x"], "y": [1.0]}])
    out = build_report("Test Deck", [{"heading": "H", "bullets": ["b1"], "chart": spec}],
                       out_dir=tmp_path)
    assert (tmp_path / out["token"]).exists()
    assert out["filename"].endswith(".pptx")
