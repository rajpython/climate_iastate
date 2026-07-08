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
You are the data assistant for the Alaska Marine Ecosystems Dashboard (marine.iastate.ai), a NOAA-\
data board covering the Alaska shelf seas (Gulf of Alaska, Eastern/Northern Bering, Aleutians, \
Chukchi, Beaufort).

WORKFLOW — always in this order:
1. DISCOVER: `list_datasets` to see what exists; `describe_dataset` for a dataset's dimensions,
   measures (with units), and join keys; `list_dimension_values` to get the exact valid values of a
   dimension (region ids, species NAMES, gears, fisheries, years).
2. QUERY: `query(dataset, filters, columns)` for tidy records. `aggregate`/`rank`/`summary_stats`
   for group-bys, top-N, and stats. `join_series`/`correlate` to compare two datasets on year(+region).
   `descriptive_indicators` for anomaly/percentile/analog-years.
3. VISUALIZE: `make_chart` (line|bar|scatter|histogram; trendline; dual_axis). For a scatter with a
   correlation/regression line, call `correlate` first and plot its `points` (scatter) plus its
   `fit_line` (a line series) — do NOT compute correlations or fits yourself.
4. EXPORT: `build_report` for a PowerPoint of the charts/findings. To put charts you already made
   into a deck, pass each chart's `chart_id` as the slide's `chart_ref` — do not resend the spec.

COMPOUND REQUESTS: when a request has several parts ("plot A and B, correlate them, and make a
deck"), decompose it into the discrete steps first, then work through them. Batch INDEPENDENT tool
calls into a SINGLE turn (emit multiple tool calls at once) — e.g. query two datasets together —
rather than one per turn; this is faster and stays within the step budget. Make each chart with
make_chart (keep its chart_id), then assemble the deck with build_report using chart_ref.

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
) -> Iterator[dict]:
    """Run the tool-use loop, yielding event dicts. ``messages`` is the running chat history."""
    import anthropic  # lazy — keeps the API importable without the SDK installed

    settings = settings or AccessSettings.from_env()
    model = model or os.getenv("ASSISTANT_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    convo: list[dict] = list(messages)
    chart_registry: dict = {}   # per-turn: chart_id -> spec, so build_report can reuse charts

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

        convo.append({"role": "assistant", "content": final.content})
        results = []
        for block in tool_uses:
            payload, event = dispatch(block.name, block.input, data_root=data_root,
                                      chart_registry=chart_registry)
            if event is not None:
                yield event
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(payload, default=str),
            })
        convo.append({"role": "user", "content": results})

    # Cap reached mid-task: degrade gracefully — one final NO-TOOLS turn so the model summarizes
    # what it gathered instead of the user getting a bare error. (convo ends on a user tool_result
    # turn, so a tool-less assistant turn is valid.)
    yield {"type": "text",
           "text": "\n\n_(Reached the step limit for one turn — summarizing what I found so far.)_\n\n"}
    try:
        with client.messages.stream(
            model=model, system=SYSTEM, messages=convo, max_tokens=max_tokens,
        ) as stream:
            for text in stream.text_stream:
                yield {"type": "text", "text": text}
            final = stream.get_final_message()
        _record_usage(getattr(final, "usage", None))
    except Exception as exc:  # noqa: BLE001 — never fail the whole turn on the wrap-up call
        yield {"type": "error", "detail": f"wrap-up failed: {exc}"}
    yield {"type": "done"}
