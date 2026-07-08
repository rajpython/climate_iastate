"""Chart building — returns a Plotly **figure spec** (dict), never a rendered image.

Returning a spec (not a PNG) is what keeps the chatbot frontend-portable: Streamlit renders it with
``st.plotly_chart`` today and a React frontend would render the same dict with ``react-plotly.js``.
The styling mirrors ``dashboard/components/ts_event_metrics.py::mhw_plot`` but is inlined here so the
service never imports Streamlit.
"""
from __future__ import annotations

from typing import Any

_FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"


def _style(fig, title: str, x_title: str, y_title: str) -> None:
    fig.update_layout(
        title={"text": title, "font": {"size": 18, "family": _FONT}},
        font={"size": 15, "family": _FONT},
        template="plotly_white",
        margin={"l": 60, "r": 24, "t": 56, "b": 48},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    fig.update_xaxes(title_text=x_title, title_font={"size": 14}, tickfont={"size": 12})
    fig.update_yaxes(title_text=y_title, title_font={"size": 14}, tickfont={"size": 12})


def build_chart(
    chart_type: str,
    title: str,
    series: list[dict[str, Any]],
    x_title: str = "",
    y_title: str = "",
) -> dict:
    """Build a Plotly figure dict.

    ``chart_type`` ∈ {line, scatter, bar}. Each series is ``{"name", "x", "y"}`` (x/y are lists).
    """
    import plotly.graph_objects as go

    ctype = (chart_type or "line").lower()
    fig = go.Figure()
    for s in series:
        name, x, y = s.get("name", ""), s.get("x", []), s.get("y", [])
        if ctype == "bar":
            fig.add_bar(x=x, y=y, name=name)
        elif ctype == "scatter":
            fig.add_scatter(x=x, y=y, mode="markers", name=name)
        else:  # line (default)
            fig.add_scatter(x=x, y=y, mode="lines", name=name)
    _style(fig, title, x_title, y_title)
    return fig.to_dict()
