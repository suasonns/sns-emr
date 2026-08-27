from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.services.document_storage import (
    DocumentStorageConfigurationError,
    max_upload_bytes_from_env,
)


class _RequestBodyTooLarge(Exception):
    pass


class DocumentUploadLimitMiddleware:
    """Reject oversized document multipart bodies while ASGI receives them."""

    MULTIPART_OVERHEAD_BYTES = 1024 * 1024

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope["path"].rstrip("/") == "/documents"
        ):
            await self.app(scope, receive, send)
            return

        try:
            limit = max_upload_bytes_from_env() + self.MULTIPART_OVERHEAD_BYTES
        except DocumentStorageConfigurationError:
            await JSONResponse(
                {"detail": "Document storage is misconfigured"},
                status_code=500,
            )(scope, receive, send)
            return

        content_length = _content_length(scope)
        if content_length is not None and content_length > limit:
            await JSONResponse(
                {"detail": "Document exceeds maximum allowed size"},
                status_code=413,
            )(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            await JSONResponse(
                {"detail": "Document exceeds maximum allowed size"},
                status_code=413,
            )(scope, receive, send)


def _content_length(scope: Scope) -> int | None:
    for name, value in scope.get("headers", []):
        if name.lower() == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None
