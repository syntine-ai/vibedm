from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi import Request
from fastapi.responses import PlainTextResponse
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app


@asynccontextmanager
async def middleware_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    base_url: str = "http://localhost",
    **env: str,
) -> AsyncIterator[AsyncClient]:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()

    app = create_app()

    @app.post("/_test/echo-size")
    async def echo_size(request: Request) -> dict[str, int]:
        body = await request.body()
        return {"size": len(body)}

    @app.get("/_test/large")
    async def large_response() -> PlainTextResponse:
        return PlainTextResponse("x" * 2_000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        yield client


async def test_request_id_is_generated_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(monkeypatch) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


async def test_incoming_request_id_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(monkeypatch) as client:
        response = await client.get("/health", headers={"X-Request-ID": "req-test-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"


async def test_request_log_includes_core_request_fields(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.request")

    async with middleware_client(
        monkeypatch,
        LOG_JSON="true",
        LOG_LEVEL="INFO",
    ) as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "req-log-123", "User-Agent": "pytest-agent"},
        )

    assert response.status_code == 200
    request_logs = [record for record in caplog.records if record.name == "app.request"]
    assert request_logs

    payload = json.loads(request_logs[-1].getMessage())
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status"] == 200
    assert payload["request_id"] == "req-log-123"
    assert payload["user_agent"] == "pytest-agent"
    assert payload["client_ip"] == "127.0.0.1"
    assert payload["latency_ms"] >= 0


async def test_oversized_request_returns_standard_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(monkeypatch, MAX_REQUEST_BODY_BYTES="8") as client:
        response = await client.post("/_test/echo-size", content=b"123456789")

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "request_too_large",
            "message": "Request body too large",
            "details": {"max_bytes": 8},
        }
    }


async def test_request_at_size_limit_reaches_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(monkeypatch, MAX_REQUEST_BODY_BYTES="8") as client:
        response = await client.post("/_test/echo-size", content=b"12345678")

    assert response.status_code == 200
    assert response.json() == {"size": 8}


async def test_disallowed_host_returns_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(
        monkeypatch,
        base_url="http://evil.example",
        ALLOWED_HOSTS="localhost",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 400


async def test_allowed_host_reaches_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(
        monkeypatch,
        base_url="http://localhost",
        ALLOWED_HOSTS="localhost",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_gzip_is_applied_for_large_compressible_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(
        monkeypatch,
        ENABLE_GZIP="true",
        GZIP_MINIMUM_SIZE="1000",
    ) as client:
        response = await client.get("/_test/large", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert response.text == "x" * 2_000


async def test_openapi_and_health_still_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with middleware_client(monkeypatch) as client:
        health_response = await client.get("/health")
        openapi_response = await client.get("/openapi.json")

    assert health_response.status_code == 200
    assert openapi_response.status_code == 200
