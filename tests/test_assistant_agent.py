"""Agent-loop tests that don't need the network — graceful degradation via an injected stub client."""
from __future__ import annotations

from mhw.assistant.access import AccessSettings
from mhw.assistant.agent import stream_chat


class _ToolBlock:
    type = "tool_use"
    name = "list_datasets"   # a catalog tool that needs no data on disk
    input: dict = {}
    id = "t1"


class _FinalMsg:
    content = [_ToolBlock()]
    usage = None


class _StubStream:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    @property
    def text_stream(self):
        return iter(["working "])

    def get_final_message(self):
        return _FinalMsg()


class _StubMessages:
    def stream(self, **kwargs):
        return _StubStream()


class _StubClient:
    messages = _StubMessages()


def test_graceful_cap_yields_partial_progress_not_error():
    # max_tool_iterations=0 → the loop runs once, the stub always asks for a tool, so the cap is hit.
    events = list(stream_chat(
        [{"role": "user", "content": "do many things"}],
        settings=AccessSettings(max_tool_iterations=0),
        client=_StubClient()))
    types = [e["type"] for e in events]
    assert types[-1] == "done"
    assert "error" not in types
    assert any(e["type"] == "text" and "step limit" in e["text"] for e in events)
