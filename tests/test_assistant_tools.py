"""Assistant tool wrappers — pure, network-free, exercised on small in-memory frames."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from mhw.assistant import tools


def _write_region(tmp_path: Path, zone: str = "sebs") -> Path:
    d = tmp_path / "derived" / "aggregates_region"
    d.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=5, freq="D"),
        "area_frac": [0.1, 0.2, 0.3, 0.4, 0.5],
        "Ibar": [1.0] * 5, "Dbar": [0.0] * 5, "Cbar": [0.0] * 5, "Obar": [0.0] * 5,
    })
    df.to_parquet(d / f"region_daily_{zone}.parquet")
    return tmp_path


def test_list_regions(tmp_path):
    _write_region(tmp_path)
    assert tools.list_regions(data_root=tmp_path)["regions"] == ["sebs"]


def test_query_region_states(tmp_path):
    _write_region(tmp_path)
    out = tools.query_region_states("sebs", data_root=tmp_path)
    assert len(out["records"]) == 5
    assert out["records"][0]["date"] == "2020-01-01"
    # date-range filter
    out2 = tools.query_region_states("sebs", start="2020-01-03", data_root=tmp_path)
    assert len(out2["records"]) == 3


def test_query_region_states_missing(tmp_path):
    out = tools.query_region_states("nope", data_root=tmp_path)
    assert "error" in out


def test_dispatch_make_chart_returns_spec():
    pytest.importorskip("plotly")
    payload, event = tools.dispatch(
        "make_chart",
        {"chart_type": "line", "title": "t", "series": [{"name": "a", "x": [1, 2], "y": [3, 4]}]},
    )
    assert payload["ok"] is True
    assert event["type"] == "chart"
    assert "data" in event["spec"] and "layout" in event["spec"]


def test_dispatch_unknown_tool():
    payload, event = tools.dispatch("bogus", {})
    assert "error" in payload
    assert event is None


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
