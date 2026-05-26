from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import Response

from app.config import Settings
from app.core.errors import ApiError
from app.modules.instagram.services.instagram import InstagramOAuthProvider, InstagramService
from app.deps import CurrentUser


class FakeInstagramRepository:
    def __init__(self) -> None:
        self.connection = None

    async def find_connection_by_ig_user(self, ig_user_id: str) -> dict | None:
        if self.connection and self.connection["ig_user_id"] == ig_user_id:
            return self.connection
        return None

    async def create_workspace_with_connection(
        self, owner_id, name, ig_user_id, ig_username, access_token, scopes
    ) -> dict:
        self.connection = {
            "id": "11111111-1111-1111-1111-111111111111",
            "owner_id": owner_id,
            "name": name,
            "ig_user_id": ig_user_id,
            "ig_username": ig_username,
            "access_token": access_token,
            "scopes": scopes,
        }
        return self.connection


async def test_start_oauth_generates_instagram_url() -> None:
    settings = Settings(
        instagram_app_id="my-app-id",
        instagram_app_secret="my-app-secret",
        instagram_redirect_uri="http://localhost/callback",
    )
    service = InstagramService(repository=FakeInstagramRepository(), settings=settings)
    user = CurrentUser(id="22222222-2222-2222-2222-222222222222", email="user@test.com", claims={})

    res = await service.start_oauth(user)
    assert "https://www.instagram.com/oauth/authorize" in res.url
    assert "client_id=my-app-id" in res.url
    assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in res.url
    assert "scope=" in res.url
    assert "force_reauth=true" in res.url


async def test_exchange_code_dev_mode_fallback() -> None:
    settings = Settings(
        instagram_app_id="dev",
        instagram_app_secret="dev",
    )
    provider = InstagramOAuthProvider(settings)
    profile = await provider.exchange_code("my-code")

    assert profile.ig_user_id == "dev-my-code"
    assert profile.ig_username == "connected.account"
    assert profile.access_token == "dev-token-my-code"


@patch("httpx.AsyncClient.post")
@patch("httpx.AsyncClient.get")
async def test_exchange_code_real_integration_success(mock_get, mock_post) -> None:
    settings = Settings(
        instagram_app_id="real-id",
        instagram_app_secret="real-secret",
        instagram_redirect_uri="http://localhost/callback",
    )
    provider = InstagramOAuthProvider(settings)

    # 1. Mock short-lived token exchange post response (returns access_token and user_id)
    mock_post.return_value = Response(200, json={"access_token": "short-lived-user-token", "user_id": "ig-user-555"})

    # 2. Mock multiple gets for Instagram Graph API:
    # First GET: upgrade to long-lived token
    # Second GET: fetch profile info
    mock_get.side_effect = [
        Response(200, json={"access_token": "long-lived-user-token"}),
        Response(200, json={"id": "ig-user-555", "username": "real.ig.username"}),
    ]

    profile = await provider.exchange_code("code-123")
    assert profile.ig_user_id == "ig-user-555"
    assert profile.ig_username == "real.ig.username"
    assert profile.access_token == "long-lived-user-token"
    assert "instagram_business_basic" in profile.scopes
