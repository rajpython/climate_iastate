"""Ask Deckhand — the chatbot page (a thin client over the assistant service).

This page holds **no data logic**: it POSTs the chat history to ``/v1/assistant/chat`` and renders the
streamed events (text, inline Plotly charts, a PowerPoint download). All intelligence lives in the
``mhw.assistant`` service, so a future React frontend would replace only this shell. Deck bytes are
fetched server-side (by this Streamlit process) so the internal API URL never reaches the browser.
"""
from __future__ import annotations

import json
import os
import uuid

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.getenv("ASSISTANT_API_BASE", "http://localhost:8000").rstrip("/")
CHAT_URL = f"{API_BASE}/v1/assistant/chat"
REPORT_URL = f"{API_BASE}/v1/assistant/report"
DOWNLOAD_URL = f"{API_BASE}/v1/assistant/download"


def _table_df(spec: dict) -> pd.DataFrame:
    return pd.DataFrame(spec.get("rows", []), columns=spec.get("columns") or None)

_CSS = """<style>
.as-title { font-size:2.0rem; font-weight:800; color:#16407a; margin:0; }
.as-lead { font-size:0.98rem; color:#33414f; margin:0.3rem 0 0.6rem; max-width:82ch; }
.as-note { font-size:0.8rem; color:#7a8694; }
</style>"""


def _render():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div class='as-title'>💬 Ask Deckhand</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='as-lead'>Combine any indicators on this dashboard — marine heatwaves, cold "
        "pool, survey catch, and fishery economics — into charts, tables, or a slide deck. I can "
        "also hand you the underlying data as a CSV or Excel file. Answers are grounded in the "
        "board's data.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='as-note'>💡 Please ask about data you can see on this dashboard — the marine "
        "heatwave, cold-pool, survey-catch, and fishery-economics indicators in the sections above. "
        "If a request is outside what the board holds, Deckhand will say so and point you to the "
        "closest available data rather than guess.</div>",
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
            for tbl in st.session_state.as_artifacts.get(i, {}).get("tables", []):
                if tbl.get("title"):
                    st.caption(tbl["title"])
                st.dataframe(_table_df(tbl), use_container_width=True, hide_index=True)
            for dl in st.session_state.as_artifacts.get(i, {}).get("downloads", []):
                st.download_button(f"⬇︎ {dl['filename']}", data=dl["bytes"], file_name=dl["filename"],
                                   mime=dl["mime"], key=f"dl_{i}_{dl['token']}")

    prompt = st.chat_input("Ask about the data, or ask for a chart / a deck…")
    if not prompt:
        return

    st.session_state.as_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    charts: list[dict] = []
    reports: list[dict] = []
    tables: list[dict] = []
    downloads: list[dict] = []
    _PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def _events():
        """Yield parsed NDJSON events from the assistant service (or a single error event)."""
        payload = {
            "messages": [{"role": m["role"], "content": m["content"]}
                         for m in st.session_state.as_messages],
            "client_id": st.session_state.as_client_id,
        }
        try:
            with requests.post(CHAT_URL, json=payload, stream=True, timeout=300) as resp:
                if resp.status_code != 200:
                    yield {"type": "error", "detail": f"{resp.status_code}: {resp.text[:300]}"}
                    return
                for line in resp.iter_lines():
                    if line:
                        yield json.loads(line)
        except requests.RequestException as exc:
            yield {"type": "error", "detail": f"Could not reach the assistant service: {exc}"}

    with st.chat_message("assistant"):
        # A live status ticker so a long tool loop never looks frozen — it updates with the
        # agent's activity labels ("Querying…", "Building the chart…") and collapses when done.
        status = st.status("Thinking…", expanded=False)
        text_ph = st.empty()
        text = ""
        for event in _events():
            etype = event.get("type")
            if etype == "text":
                text += event.get("text", "")
                text_ph.markdown(text + " ▌")          # trailing cursor while streaming
            elif etype == "status":
                status.update(label=event.get("label", "Working…"))
            elif etype == "chart":
                charts.append(event["spec"])
                st.plotly_chart(go.Figure(event["spec"]), use_container_width=True)
            elif etype == "report":
                try:
                    r = requests.get(f"{REPORT_URL}/{event['token']}", timeout=60)
                    if r.status_code == 200:
                        rep = {"token": event["token"],
                               "filename": event.get("filename", "report.pptx"), "bytes": r.content}
                        reports.append(rep)
                        st.download_button(f"⬇︎ {rep['filename']}", data=rep["bytes"],
                                           file_name=rep["filename"], mime=_PPTX,
                                           key=f"dl_new_{rep['token']}")
                except requests.RequestException:
                    pass
            elif etype == "table":
                spec = event.get("spec", {})
                tables.append(spec)
                if spec.get("title"):
                    st.caption(spec["title"])
                st.dataframe(_table_df(spec), use_container_width=True, hide_index=True)
            elif etype == "download":
                try:
                    r = requests.get(f"{DOWNLOAD_URL}/{event['token']}", timeout=60)
                    if r.status_code == 200:
                        dl = {"token": event["token"], "filename": event.get("filename", "data.csv"),
                              "mime": event.get("mime", "application/octet-stream"), "bytes": r.content}
                        downloads.append(dl)
                        st.download_button(f"⬇︎ {dl['filename']}", data=dl["bytes"],
                                           file_name=dl["filename"], mime=dl["mime"],
                                           key=f"dldata_new_{dl['token']}")
                except requests.RequestException:
                    pass
            elif etype == "error":
                text += f"\n\n⚠️ {event.get('detail', 'error')}"
                text_ph.markdown(text)

        if text.strip():
            text_ph.markdown(text)                      # drop the cursor
        elif not (charts or reports or tables or downloads):
            text = "_(No response — please try rephrasing, or ask me to continue.)_"
            text_ph.markdown(text)
        else:
            text_ph.empty()
        status.update(label="Done", state="complete")

    st.session_state.as_messages.append({"role": "assistant", "content": text or ""})
    st.session_state.as_artifacts[len(st.session_state.as_messages) - 1] = {
        "charts": charts, "reports": reports, "tables": tables, "downloads": downloads,
    }


_render()
