from __future__ import annotations

from httpx import AsyncClient


async def test_missing_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_valid_token_returns_user_and_workspaces(
    client: AsyncClient, auth_header: dict[str, str]
) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "alex@example.com"
    assert payload["workspaces"][0]["role"] == "owner"
