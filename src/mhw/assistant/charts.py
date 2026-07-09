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
_INK = "#2b3a4a"
_TITLE_BLUE = "#16407a"
_GRID = "#eef1f5"
_FIT = "#d1495b"
# Dashboard-branded categorical palette (blue, green, amber, purple, slate, teal) so multi-series
# charts share the board's look instead of Plotly defaults. Fit/trend lines stay _FIT (red).
_PALETTE = ["#1565c0", "#2e8b57", "#b35900", "#6a4c93", "#5f6b7a", "#0f9d9d", "#c2185b"]


class ChartError(ValueError):
    """Raised when a chart cannot be built from the given series (empty / non-numeric)."""


def _is_fit(name: str) -> bool:
    n = (name or "").lower()
    return "fit" in n or "trend" in n or "ols" in n


def _style(fig, title: str, x_title: str, y_title: str) -> None:
    # Legend BELOW the plot (never over the title), generous margins, and larger fonts so the chart
    # stays legible when rasterised into a slide.
    fig.update_layout(
        title={"text": title, "font": {"size": 20, "family": _FONT, "color": _TITLE_BLUE},
               "x": 0.02, "xanchor": "left"},
        font={"size": 15, "family": _FONT, "color": _INK},
        template="plotly_white",
        colorway=_PALETTE,
        plot_bgcolor="white", paper_bgcolor="white",
        margin={"l": 82, "r": 34, "t": 78, "b": 92},
        legend={"orientation": "h", "yanchor": "top", "y": -0.24, "xanchor": "center", "x": 0.5,
                "font": {"size": 14}},
    )
    fig.update_xaxes(title_text=x_title, title_font={"size": 17}, tickfont={"size": 14},
                     showgrid=True, gridcolor=_GRID, zeroline=False, linecolor="#c7d0da")
    fig.update_yaxes(title_text=y_title, title_font={"size": 17}, tickfont={"size": 14},
                     showgrid=True, gridcolor=_GRID, zeroline=False, linecolor="#c7d0da")


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
            if _is_fit(name):   # a fit/trend series is a LINE even on a scatter (not stray markers)
                fig.add_scatter(x=x, y=y, mode="lines", name=name,
                                line={"dash": "dash", "color": _FIT, "width": 2}, **axis)
            else:
                fig.add_scatter(x=x, y=y, mode="markers", name=name,
                                marker={"size": 8, "opacity": 0.82}, **axis)
        else:
            fig.add_scatter(x=x, y=y, mode="lines", name=name, line={"width": 2}, **axis)
        if trendline and ctype in ("scatter", "line"):
            xf = _numeric(x)
            yf = _numeric(y)
            if xf.size >= 2 and xf.size == yf.size and np.unique(xf).size > 1:
                slope, intercept = np.polyfit(xf, yf, 1)
                xs = [float(xf.min()), float(xf.max())]
                fig.add_scatter(x=xs, y=[slope * xs[0] + intercept, slope * xs[1] + intercept],
                                mode="lines", name=f"{name} fit",
                                line={"dash": "dash", "color": _FIT, "width": 2}, **axis)

    _style(fig, title, x_title, y_title)
    if dual_axis:
        fig.update_layout(yaxis2={"overlaying": "y", "side": "right",
                                  "title": series[1].get("name", "") if len(series) > 1 else ""})
    return fig.to_dict()
