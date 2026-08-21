from __future__ import annotations

from httpx import AsyncClient


async def test_health_endpoint_and_correlation_header(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


async def test_openapi_exposes_active_modules_only(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/workspaces" in paths
    assert "/api/v1/instagram/oauth/start" in paths
    assert "/api/v1/automations" in paths
    assert "/api/v1/contacts" in paths
    assert "/api/v1/dashboard/stats" in paths
    assert "/api/v1/billing/plans" in paths
    assert "/api/public/webhooks/stripe" in paths

    assert not any(path.startswith("/api/v1/products") for path in paths)
    assert not any(path.startswith("/api/v1/orders") for path in paths)
    assert not any(path.startswith("/api/v1/referrals") for path in paths)


async def test_error_envelope_for_unknown_route(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Not Found", "details": {}}
    }
