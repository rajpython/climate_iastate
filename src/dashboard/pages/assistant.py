"""Ask the Data — the chatbot page (a thin client over the assistant service).

This page holds **no data logic**: it POSTs the chat history to ``/v1/assistant/chat`` and renders the
streamed events (text, inline Plotly charts, a PowerPoint download). All intelligence lives in the
``mhw.assistant`` service, so a future React frontend would replace only this shell. Deck bytes are
fetched server-side (by this Streamlit process) so the internal API URL never reaches the browser.
"""
from __future__ import annotations

import json
import os
import uuid

import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.getenv("ASSISTANT_API_BASE", "http://localhost:8000").rstrip("/")
CHAT_URL = f"{API_BASE}/v1/assistant/chat"
REPORT_URL = f"{API_BASE}/v1/assistant/report"

_CSS = """<style>
.as-title { font-size:2.0rem; font-weight:800; color:#16407a; margin:0; }
.as-lead { font-size:0.98rem; color:#33414f; margin:0.3rem 0 0.6rem; max-width:82ch; }
.as-note { font-size:0.8rem; color:#7a8694; }
</style>"""


def _render():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div class='as-title'>💬 Ask the Data</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='as-lead'>Ask questions about the Alaska shelf data on this board — marine "
        "heatwaves, cold pool, survey catch, and fishery economics — and I can build charts and "
        "export a PowerPoint deck. Answers are grounded in the board's data.</div>",
        unsafe_allow_html=True,
    )

    if "as_messages" not in st.session_state:
        st.session_state.as_messages = []   # [{role, content}] plain-text turns for the model
    if "as_artifacts" not in st.session_state:
        st.session_state.as_artifacts = {}   # msg_index -> {"charts": [...], "reports": [...]}
    if "as_client_id" not in st.session_state:
        st.session_state.as_client_id = uuid.uuid4().hex

    # Replay history (text + any charts/decks produced on that turn).
    for i, msg in enumerate(st.session_state.as_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for art in st.session_state.as_artifacts.get(i, {}).get("charts", []):
                st.plotly_chart(go.Figure(art), use_container_width=True)
            for rep in st.session_state.as_artifacts.get(i, {}).get("reports", []):
                st.download_button(
                    f"⬇︎ {rep['filename']}", data=rep["bytes"], file_name=rep["filename"],
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key=f"dl_{i}_{rep['token']}",
                )

    prompt = st.chat_input("Ask about the data, or ask for a chart / a deck…")
    if not prompt:
        return

    st.session_state.as_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    charts: list[dict] = []
    reports: list[dict] = []

    def _stream_text():
        """Yield assistant text as it streams; stash chart/report artifacts as they arrive."""
        payload = {
            "messages": [{"role": m["role"], "content": m["content"]}
                         for m in st.session_state.as_messages],
            "client_id": st.session_state.as_client_id,
        }
        try:
            with requests.post(CHAT_URL, json=payload, stream=True, timeout=120) as resp:
                if resp.status_code != 200:
                    yield f"\n\n⚠️ {resp.status_code}: {resp.text[:300]}"
                    return
                for line in resp.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    etype = event.get("type")
                    if etype == "text":
                        yield event.get("text", "")
                    elif etype == "chart":
                        charts.append(event["spec"])
                    elif etype == "report":
                        try:
                            r = requests.get(f"{REPORT_URL}/{event['token']}", timeout=60)
                            if r.status_code == 200:
                                reports.append({"token": event["token"],
                                                "filename": event.get("filename", "report.pptx"),
                                                "bytes": r.content})
                        except requests.RequestException:
                            pass
                    elif etype == "error":
                        yield f"\n\n⚠️ {event.get('detail', 'error')}"
        except requests.RequestException as exc:
            yield f"\n\n⚠️ Could not reach the assistant service: {exc}"

    with st.chat_message("assistant"):
        text = st.write_stream(_stream_text())
        for spec in charts:
            st.plotly_chart(go.Figure(spec), use_container_width=True)
        for rep in reports:
            st.download_button(
                f"⬇︎ {rep['filename']}", data=rep["bytes"], file_name=rep["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key=f"dl_new_{rep['token']}",
            )

    st.session_state.as_messages.append({"role": "assistant", "content": text or ""})
    st.session_state.as_artifacts[len(st.session_state.as_messages) - 1] = {
        "charts": charts, "reports": reports,
    }


_render()
