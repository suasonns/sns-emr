from __future__ import annotations

import asyncio
import json

from app.core.recording_upload_limit import RecordingUploadLimitMiddleware


def test_recording_upload_middleware_rejects_oversized_stream(monkeypatch):
    monkeypatch.setenv("VISIT_RECORDING_MAX_UPLOAD_BYTES", "5")
    app_called = False

    async def app(scope, receive, send):
        nonlocal app_called
        app_called = True
        await receive()
        await receive()

    middleware = RecordingUploadLimitMiddleware(app)
    middleware.MULTIPART_OVERHEAD_BYTES = 0
    messages = iter(
        [
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": False},
        ]
    )
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    asyncio.run(
        middleware(
            {
                "type": "http",
                "method": "POST",
                "path": "/visit-recordings",
                "headers": [],
            },
            receive,
            send,
        )
    )

    assert app_called is True
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"]) == {
        "detail": "Recording exceeds maximum allowed size"
    }


def test_recording_upload_middleware_does_not_limit_other_routes(monkeypatch):
    monkeypatch.setenv("VISIT_RECORDING_MAX_UPLOAD_BYTES", "1")
    sent = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def receive():
        return {"type": "http.request", "body": b"large", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(
        RecordingUploadLimitMiddleware(app)(
            {"type": "http", "method": "POST", "path": "/other", "headers": []},
            receive,
            send,
        )
    )
    assert sent[0]["status"] == 204
