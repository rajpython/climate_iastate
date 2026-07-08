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

Your job: help users explore the board's data, build charts, and export PowerPoint decks. Always \
ground answers in the tools — never invent numbers. Retrieve data with the query tools, then use \
make_chart to visualise and build_report to export a deck.

Region/zone ids: sebs (SE Bering), nbs (N Bering), wgoa/egoa (Gulf), ai_west/ai_central/ai_east \
(Aleutians), chukchi, beaufort. MHW aggregate columns follow Hobday notation: area_frac (share in \
MHW), Ibar (intensity °C), Dbar (duration days), Cbar (cumulative °C·days), Obar (onset rate).

Honesty rules: the cold pool is an EBS/NBS product; landings are statewide (not per-region); \
ex-vessel value is nominal. If forecast data comes up, be clear it is short-term damped-persistence \
with an honest expiry — never oversell skill. State units and caveats plainly. Be concise."""


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
    max_tokens: int = 2048,
) -> Iterator[dict]:
    """Run the tool-use loop, yielding event dicts. ``messages`` is the running chat history."""
    import anthropic  # lazy — keeps the API importable without the SDK installed

    settings = settings or AccessSettings.from_env()
    model = model or os.getenv("ASSISTANT_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    convo: list[dict] = list(messages)

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
            payload, event = dispatch(block.name, block.input, data_root=data_root)
            if event is not None:
                yield event
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(payload, default=str),
            })
        convo.append({"role": "user", "content": results})

    # Exhausted the tool-iteration cap without a final answer.
    yield {"type": "error", "detail": "Reached the tool-step limit for this turn."}
    yield {"type": "done"}
