"""The Claude tool-use loop — the assistant's reasoning core.

`stream_chat` yields events (`text`, `chart`, `report`, `error`, `done`) so the API can stream them
to the browser. `anthropic` is imported lazily inside the function so this module — and the whole API
— imports cleanly even before the SDK is installed (the SDK only ships in the `assistant` extra).
Token usage is recorded against the monthly budget after every model turn.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator

from mhw.assistant.access import AccessSettings, budget_tracker
from mhw.assistant.tools import TOOLS, dispatch

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM = """\
You are **Deckhand**, the data assistant for the Alaska Marine Ecosystems Dashboard
(marine.iastate.ai), a NOAA-data board covering the Alaska shelf seas (Gulf of Alaska,
Eastern/Northern Bering, Aleutians, Chukchi, Beaufort). You combine the board's indicators into
charts, tables, slide decks, and CSV/Excel downloads.

WORKFLOW — always in this order:
1. DISCOVER: `list_datasets` to see what exists; `describe_dataset` for a dataset's dimensions,
   measures (with units), and join keys; `list_dimension_values` to get the exact valid values of a
   dimension (region ids, species NAMES, gears, fisheries, years).
2. QUERY: `query(dataset, filters, columns)` for tidy records. `aggregate`/`rank`/`summary_stats`
   for group-bys, top-N, and stats. `join_series`/`correlate` to compare two datasets on year(+region).
   `descriptive_indicators` for anomaly/percentile/analog-years.
3. PRESENT: `make_chart` (line|bar|scatter|histogram; trendline; dual_axis) for plots; `make_table`
   (columns + rows) for tabular answers (rankings, summaries). For a scatter with a correlation/
   regression line, call `correlate` first and plot its `points` (scatter) plus its `fit_line` (a
   line series) — do NOT compute correlations or fits yourself.
4. EXPORT: `build_report` for a PowerPoint (slides may hold a chart via `chart_ref`, a `table`, and
   bullets — pass each chart's `chart_id` as `chart_ref`, don't resend the spec). Use `export_data`
   to hand the user a CSV or Excel file (from a dataset+filters, or a table you assembled) — reach
   for this whenever they just want the raw numbers.

COMPOUND REQUESTS: when a request has several parts ("plot A and B, correlate them, and make a
deck"), FIRST restate it as an explicit checklist of deliverables, then complete EVERY item — drop
nothing. Issue INDEPENDENT tool calls together in one step (e.g. query two datasets, or make several
charts, in a single turn) rather than one per turn — faster, and it stays within the step budget.
Make each chart with make_chart and keep the chart_id it returns; assemble the deck with build_report
by passing each chart_id as the slide's chart_ref — NEVER paste a chart spec back.

GROUNDING — non-negotiable:
- Every number you state and every chart/deck you build MUST come from a tool result in THIS
  conversation. NEVER invent, estimate, or recall values from memory.
- Before querying a name you're unsure of (a species, region, gear, fishery), call
  `list_dimension_values` and use an EXACT returned value. Do not guess (e.g. it is `CRAB, SNOW`,
  not "snow crab").
- If a query returns 0 rows or a name is unknown, say so plainly and offer the valid values — do NOT
  fabricate to fill the gap, and do NOT chart empty data.

BOARD FACTS: region ids sebs, nbs, wgoa, egoa, ai_west, ai_central, ai_east, chukchi, beaufort (plus
roll-ups ebs, goa, ai). MHW columns (Hobday): area_frac, Ibar (°C), Dbar (days), Cbar (°C·days),
Obar (°C/day). Cold pool is an EBS/NBS product; `landings` are STATEWIDE (not per-region) with
comma-inverted species names; econ-SAFE is FMP-area (BSAI/GOA), not survey regions; ex-vessel value
is nominal. Forecast data (if present) is short-term damped persistence with an honest expiry — never
oversell skill. Always state units and caveats. Be concise."""


def _activity_label(tool_names: list[str]) -> str:
    """A human 'what I'm doing now' label for a batch of tool calls (shown as a status ticker)."""
    s = set(tool_names)
    if "build_report" in s:
        return "Assembling the PowerPoint…"
    if "make_chart" in s:
        return "Building the chart…"
    if s & {"correlate", "join_series", "aggregate", "rank", "summary_stats", "descriptive_indicators"}:
        return "Analyzing the data…"
    if s & {"list_datasets", "describe_dataset", "list_dimension_values"}:
        return "Looking up the data catalog…"
    if "query" in s:
        return "Querying the data…"
    return "Working…"


def _record_usage(usage) -> None:
    try:
        total = int(getattr(usage, "input_tokens", 0)) + int(getattr(usage, "output_tokens", 0))
        if total:
            budget_tracker().add(total)
    except Exception:  # noqa: BLE001 — usage accounting must never break a reply
        pass


def stream_chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    data_root: Path | None = None,
    settings: AccessSettings | None = None,
    max_tokens: int = 4096,
    client=None,
) -> Iterator[dict]:
    """Run the tool-use loop, yielding event dicts. ``messages`` is the running chat history.

    ``client`` may be injected for testing; otherwise the Anthropic SDK is imported lazily so the API
    stays importable without it.
    """
    if client is None:
        import anthropic  # lazy
        client = anthropic.Anthropic()

    settings = settings or AccessSettings.from_env()
    model = model or os.getenv("ASSISTANT_MODEL", DEFAULT_MODEL)
    convo: list[dict] = list(messages)
    chart_store: dict = {}      # per-turn: chart_id -> spec, so build_report can reuse charts
    produced: list[str] = []    # labels of artifacts produced, for the graceful-cap message

    for _ in range(settings.max_tool_iterations + 1):
        with client.messages.stream(
            model=model, system=SYSTEM, tools=TOOLS, messages=convo, max_tokens=max_tokens,
        ) as stream:
            for text in stream.text_stream:
                yield {"type": "text", "text": text}
            final = stream.get_final_message()

        _record_usage(getattr(final, "usage", None))

        tool_uses = [b for b in final.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses:
            yield {"type": "done"}
            return

        # Tell the client what's happening next — long tool loops otherwise look frozen.
        yield {"type": "status", "label": _activity_label([b.name for b in tool_uses])}
        convo.append({"role": "assistant", "content": final.content})
        results = []
        for block in tool_uses:
            payload, event = dispatch(block.name, block.input, data_root=data_root,
                                      chart_store=chart_store)
            if event is not None:
                yield event
                if event.get("type") == "chart":
                    produced.append("a chart")
                elif event.get("type") == "report":
                    produced.append(f"a deck ({event.get('filename')})")
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(payload, default=str),
            })
        convo.append({"role": "user", "content": results})

    # Cap reached mid-task: degrade gracefully with a partial-progress message (charts already
    # streamed to the browser are preserved). No extra model call — name what was produced and invite
    # continuation, instead of a bare error that drops the work.
    made = f" So far I produced {len(produced)} item(s): {', '.join(produced)}." if produced else ""
    yield {"type": "text",
           "text": f"\n\n_(I reached the step limit for one turn before finishing every part of your "
                   f"request.{made} Ask me to continue and I'll pick up the remaining items.)_"}
    yield {"type": "done"}
