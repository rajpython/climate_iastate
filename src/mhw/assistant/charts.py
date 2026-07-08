"""Chart building — returns a Plotly **figure spec** (dict), never a rendered image.

Returning a spec (not a PNG) keeps the chatbot frontend-portable: Streamlit renders it with
``st.plotly_chart`` today and a React frontend would render the same dict with ``react-plotly.js``.
Supports line / bar / scatter / histogram, an optional OLS **trendline** (for scatter/line), and a
**dual axis** (second series on a secondary y). Empty/non-numeric series are rejected — a mechanical
backstop against charting ungrounded or missing data.
"""
from __future__ import annotations

from typing import Any

import numpy as np

_FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"


class ChartError(ValueError):
    """Raised when a chart cannot be built from the given series (empty / non-numeric)."""


def _style(fig, title: str, x_title: str, y_title: str) -> None:
    fig.update_layout(
        title={"text": title, "font": {"size": 18, "family": _FONT}},
        font={"size": 15, "family": _FONT},
        template="plotly_white",
        margin={"l": 60, "r": 60, "t": 56, "b": 48},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    fig.update_xaxes(title_text=x_title, title_font={"size": 14}, tickfont={"size": 12})
    fig.update_yaxes(title_text=y_title, title_font={"size": 14}, tickfont={"size": 12})


def _numeric(vals) -> np.ndarray:
    arr = np.array([v for v in vals if v is not None], dtype="float64")
    return arr


def build_chart(
    chart_type: str,
    title: str,
    series: list[dict[str, Any]],
    x_title: str = "",
    y_title: str = "",
    trendline: bool = False,
    dual_axis: bool = False,
) -> dict:
    """Build a Plotly figure dict.

    ``chart_type`` ∈ {line, scatter, bar, histogram}. Each series is ``{"name","x","y"}``
    (histogram uses ``x`` as the values; ``y`` optional).
    """
    import plotly.graph_objects as go

    if not series:
        raise ChartError("no series supplied — retrieve data with a tool before charting")
    ctype = (chart_type or "line").lower()
    fig = go.Figure()

    for i, s in enumerate(series):
        name, x, y = s.get("name", f"series {i+1}"), s.get("x", []), s.get("y", [])
        secondary = dual_axis and i == 1
        axis = {"yaxis": "y2"} if secondary else {}
        if ctype == "histogram":
            vals = _numeric(x if x else y)
            if vals.size == 0:
                raise ChartError(f"series {name!r} has no numeric values")
            fig.add_histogram(x=vals, name=name)
            continue
        if len(x) == 0 or len(y) == 0:
            raise ChartError(f"series {name!r} is empty — nothing to plot")
        if _numeric(y).size == 0:
            raise ChartError(f"series {name!r} has no numeric y-values")
        if ctype == "bar":
            fig.add_bar(x=x, y=y, name=name, **axis)
        elif ctype == "scatter":
            fig.add_scatter(x=x, y=y, mode="markers", name=name, **axis)
        else:
            fig.add_scatter(x=x, y=y, mode="lines", name=name, **axis)
        if trendline and ctype in ("scatter", "line"):
            xf = _numeric(x)
            yf = _numeric(y)
            if xf.size >= 2 and xf.size == yf.size and np.unique(xf).size > 1:
                slope, intercept = np.polyfit(xf, yf, 1)
                xs = [float(xf.min()), float(xf.max())]
                fig.add_scatter(x=xs, y=[slope * xs[0] + intercept, slope * xs[1] + intercept],
                                mode="lines", name=f"{name} fit",
                                line={"dash": "dash"}, **axis)

    _style(fig, title, x_title, y_title)
    if dual_axis:
        fig.update_layout(yaxis2={"overlaying": "y", "side": "right",
                                  "title": series[1].get("name", "") if len(series) > 1 else ""})
    return fig.to_dict()
