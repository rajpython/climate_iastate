"""Routes for the data assistant (v1) — the chatbot's HTTP surface.

The Streamlit page (and any future React frontend) talks only to these endpoints; all the
intelligence lives in ``mhw.assistant``. ``POST /assistant/chat`` streams newline-delimited JSON
events (text / chart / report / error / done). Access is enforced by the single
``mhw.assistant.access.enforce_access`` guard, whose ``AccessError`` maps straight to an HTTP status.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from mhw.assistant.access import AccessError, enforce_access
from mhw.assistant.agent import stream_chat
from mhw.assistant.report import report_path

router = APIRouter()

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class ChatRequest(BaseModel):
    messages: list[dict]
    client_id: str | None = None   # stable per-browser-session id from the client
    password: str | None = None    # only used when access mode is "gated"


@router.post("/assistant/chat", tags=["Assistant"])
def assistant_chat(req: ChatRequest, request: Request):
    """Stream a chat turn as newline-delimited JSON events."""
    client_id = req.client_id or (request.client.host if request.client else "anon")
    try:
        enforce_access(client_id, req.password)
    except AccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    def gen():
        try:
            for event in stream_chat(req.messages):
                yield json.dumps(event, default=str) + "\n"
        except Exception as exc:  # noqa: BLE001 — surface any agent error to the client, don't 500 mid-stream
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@router.get("/assistant/report/{token}", tags=["Assistant"])
def assistant_report(token: str):
    """Download a generated PowerPoint deck by token."""
    p = report_path(token)
    if p is None:
        raise HTTPException(status_code=404, detail="Report not found or expired.")
    return FileResponse(str(p), media_type=_PPTX_MIME, filename="alaska_marine_report.pptx")


_DL_MIME = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": _PPTX_MIME,
}


@router.get("/assistant/download/{token}", tags=["Assistant"])
def assistant_download(token: str):
    """Download a generated data file (CSV / Excel) by token."""
    p = report_path(token)   # same sandboxed downloads dir, token-validated
    if p is None:
        raise HTTPException(status_code=404, detail="File not found or expired.")
    return FileResponse(str(p), media_type=_DL_MIME.get(p.suffix.lower(), "application/octet-stream"),
                        filename=p.name)
