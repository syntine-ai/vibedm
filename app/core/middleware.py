from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import Settings
from app.core.errors import error_payload

request_logger = logging.getLogger("app.request")


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp, *, header_name: str) -> None:
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.lower().encode("latin-1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = headers.get(self.header_name) or str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != self.header_name_bytes
                ]
                raw_headers.append((self.header_name_bytes, request_id.encode("latin-1")))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self.max_bytes <= 0:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_length = headers.get("content-length")
        if content_length is not None and self._exceeds_limit(content_length):
            await self._send_too_large(scope, receive, send)
            return

        bytes_seen = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal bytes_seen
            message = await receive()
            if message["type"] == "http.request":
                bytes_seen += len(message.get("body", b""))
                if bytes_seen > self.max_bytes:
                    raise RequestBodyTooLarge
            return message

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, send_wrapper)
        except RequestBodyTooLarge:
            if response_started:
                raise
            await self._send_too_large(scope, receive, send)

    def _exceeds_limit(self, content_length: str) -> bool:
        try:
            return int(content_length) > self.max_bytes
        except ValueError:
            return False

    async def _send_too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content=error_payload(
                "request_too_large",
                "Request body too large",
                {"max_bytes": self.max_bytes},
            ),
        )
        await response(scope, receive, send)


class RequestBodyTooLarge(Exception):
    pass


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, log_json: bool, request_id_header: str) -> None:
        super().__init__(app)
        self.log_json = log_json
        self.request_id_header = request_id_header

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started_at = time.perf_counter()
        status_code = 500
        exc_info = False

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            exc_info = True
            raise
        finally:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            self._log_request(request, status_code, latency_ms, exc_info=exc_info)

    def _log_request(
        self,
        request: Request,
        status_code: int,
        latency_ms: float,
        *,
        exc_info: bool,
    ) -> None:
        client = request.client.host if request.client else ""
        request_id = getattr(request.state, "request_id", None) or request.headers.get(
            self.request_id_header, ""
        )
        event = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status": status_code,
            "latency_ms": latency_ms,
            "request_id": request_id,
            "client_ip": client,
            "user_agent": request.headers.get("user-agent", ""),
        }

        if self.log_json:
            request_logger.info(json.dumps(event, separators=(",", ":")), exc_info=exc_info)
        else:
            request_logger.info(
                "%s %s %s %.2fms request_id=%s client_ip=%s user_agent=%s",
                event["method"],
                event["path"],
                event["status"],
                event["latency_ms"],
                event["request_id"],
                event["client_ip"],
                event["user_agent"],
                exc_info=exc_info,
            )


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s" if settings.log_json else "%(levelname)s:%(name)s:%(message)s",
    )
    logging.getLogger("app").setLevel(level)
    request_logger.setLevel(level)


def configure_middlewares(app: FastAPI, settings: Settings) -> None:
    configure_logging(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Workspace-Id"],
    )

    if settings.enable_gzip:
        app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(
        RequestLoggingMiddleware,
        log_json=settings.log_json,
        request_id_header=settings.request_id_header,
    )

    if settings.enable_proxy_headers:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_proxy_ips)

    app.add_middleware(RequestIdMiddleware, header_name=settings.request_id_header)
