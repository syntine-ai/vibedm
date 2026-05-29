from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
import pytest
from httpx import Response

from app.config import Settings
from app.core.errors import ApiError
from app.modules.instagram.services.instagram import InstagramOAuthProvider, InstagramService
from app.modules.instagram.schemas.instagram import InstagramProfile
from app.deps import CurrentUser
from app.security import sign_state


class FakeInstagramRepository:
    def __init__(self) -> None:
        self.connection = None
        self.workspace = None
        self.updated_calls = []

    async def find_connection_by_ig_user(self, ig_user_id: str) -> dict | None:
        if self.connection and self.connection["ig_user_id"] == ig_user_id:
            return {
                "workspace_id": self.connection["workspace_id"],
                "ig_user_id": self.connection["ig_user_id"],
                "ig_username": self.connection["ig_username"],
            }
        return None

    async def create_workspace_with_connection(
        self, owner_id, name, ig_user_id, ig_username, access_token, scopes
    ) -> dict:
        self.workspace = {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "owner_id": owner_id,
            "name": name,
            "avatar_url": None,
        }
        self.connection = {
            "workspace_id": self.workspace["id"],
            "ig_user_id": ig_user_id,
            "ig_username": ig_username,
            "access_token": access_token,
            "scopes": scopes,
        }
        return self.workspace | {
            "ig_username": ig_username,
            "ig_user_id": ig_user_id,
            "plan": "free",
            "active": True,
        }

    async def update_connection(
        self, workspace_id: UUID, access_token: str, scopes: list[str], ig_username: str | None = None
    ) -> None:
        self.updated_calls.append({
            "workspace_id": workspace_id,
            "access_token": access_token,
            "scopes": scopes,
            "ig_username": ig_username,
        })
        if self.connection and self.connection["workspace_id"] == workspace_id:
            self.connection["access_token"] = access_token
            self.connection["scopes"] = scopes
            if ig_username:
                self.connection["ig_username"] = ig_username

    async def get_workspace_detail(self, workspace_id: UUID) -> dict | None:
        if self.workspace and self.workspace["id"] == workspace_id:
            return self.workspace
        return None

    async def disconnect(self, workspace_id: UUID) -> None:
        if self.connection and self.connection["workspace_id"] == workspace_id:
            self.connection = None

    async def delete_connection_by_ig_user(self, ig_user_id: str) -> None:
        if self.connection and self.connection["ig_user_id"] == ig_user_id:
            self.connection = None

    async def create_connection_for_workspace(
        self, workspace_id: UUID, ig_user_id: str, ig_username: str, access_token: str, scopes: list[str]
    ) -> None:
        self.connection = {
            "workspace_id": workspace_id,
            "ig_user_id": ig_user_id,
            "ig_username": ig_username,
            "access_token": access_token,
            "scopes": scopes,
        }


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


async def test_complete_oauth_new_connection_success() -> None:
    settings = Settings(
        instagram_app_id="my-app-id",
        instagram_app_secret="my-app-secret",
        instagram_redirect_uri="http://localhost/callback",
    )
    repo = FakeInstagramRepository()
    service = InstagramService(repository=repo, settings=settings)
    user = CurrentUser(id="22222222-2222-2222-2222-222222222222", email="user@test.com", claims={})

    state = sign_state({"user_id": str(user.id)}, settings.instagram_app_secret or "dev")

    fake_profile = InstagramProfile(
        ig_user_id="ig-12345",
        ig_username="new.instagram.user",
        access_token="token-abc",
        scopes=["scope1"],
    )
    service.provider.exchange_code = AsyncMock(return_value=fake_profile)

    res = await service.complete_oauth(user=user, code="auth-code-123", state=state)

    assert res.workspace["ig_user_id"] == "ig-12345"
    assert res.workspace["ig_username"] == "new.instagram.user"
    assert res.workspace["plan"] == "free"
    assert res.workspace["active"] is True
    assert repo.connection["access_token"] == "token-abc"


async def test_complete_oauth_reconnect_success() -> None:
    settings = Settings(
        instagram_app_id="my-app-id",
        instagram_app_secret="my-app-secret",
        instagram_redirect_uri="http://localhost/callback",
    )
    repo = FakeInstagramRepository()

    # Pre-populate connection in repository to simulate existing connection
    await repo.create_workspace_with_connection(
        owner_id=UUID("22222222-2222-2222-2222-222222222222"),
        name="old.username",
        ig_user_id="ig-12345",
        ig_username="old.username",
        access_token="old-token",
        scopes=["old-scope"],
    )

    service = InstagramService(repository=repo, settings=settings)
    user = CurrentUser(id="22222222-2222-2222-2222-222222222222", email="user@test.com", claims={})

    state = sign_state({"user_id": str(user.id)}, settings.instagram_app_secret or "dev")

    # Mock exchange_code to return updated profile (new token, scopes, username)
    fake_profile = InstagramProfile(
        ig_user_id="ig-12345",
        ig_username="new.username.refreshed",
        access_token="new-token-refreshed",
        scopes=["new-scope-1", "new-scope-2"],
    )
    service.provider.exchange_code = AsyncMock(return_value=fake_profile)

    res = await service.complete_oauth(user=user, code="auth-code-reconnect", state=state)

    assert len(repo.updated_calls) == 1
    assert repo.updated_calls[0]["workspace_id"] == UUID("11111111-1111-1111-1111-111111111111")
    assert repo.updated_calls[0]["access_token"] == "new-token-refreshed"
    assert repo.updated_calls[0]["scopes"] == ["new-scope-1", "new-scope-2"]
    assert repo.updated_calls[0]["ig_username"] == "new.username.refreshed"

    assert res.workspace["id"] == UUID("11111111-1111-1111-1111-111111111111")
    assert res.workspace["ig_username"] == "new.username.refreshed"
    assert res.workspace["ig_user_id"] == "ig-12345"
    assert res.workspace["plan"] == "free"
    assert res.workspace["active"] is True


async def test_complete_oauth_reconnect_to_existing_workspace_success() -> None:
    settings = Settings(
        instagram_app_id="my-app-id",
        instagram_app_secret="my-app-secret",
        instagram_redirect_uri="http://localhost/callback",
    )
    repo = FakeInstagramRepository()

    # Pre-populate workspace and a connection
    await repo.create_workspace_with_connection(
        owner_id=UUID("22222222-2222-2222-2222-222222222222"),
        name="my-workspace",
        ig_user_id="ig-old",
        ig_username="old.username",
        access_token="old-token",
        scopes=["old-scope"],
    )

    service = InstagramService(repository=repo, settings=settings)
    user = CurrentUser(id="22222222-2222-2222-2222-222222222222", email="user@test.com", claims={})

    state = sign_state({"user_id": str(user.id)}, settings.instagram_app_secret or "dev")

    # Mock exchange_code to return a new profile/token
    fake_profile = InstagramProfile(
        ig_user_id="ig-new-reconnect",
        ig_username="new.username.reconnected",
        access_token="new-token-reconnected",
        scopes=["new-scope"],
    )
    service.provider.exchange_code = AsyncMock(return_value=fake_profile)

    # Pass the existing workspace_id to complete_oauth
    existing_workspace_id = UUID("11111111-1111-1111-1111-111111111111")
    res = await service.complete_oauth(
        user=user, code="auth-code-reconnect", state=state, workspace_id=existing_workspace_id
    )

    # Assert returned workspace matches existing workspace details, not a newly created one
    assert res.workspace["id"] == existing_workspace_id
    assert res.workspace["ig_username"] == "new.username.reconnected"
    assert res.workspace["ig_user_id"] == "ig-new-reconnect"

    # Assert new connection is linked to the existing workspace in the repository
    assert repo.connection["workspace_id"] == existing_workspace_id
    assert repo.connection["ig_user_id"] == "ig-new-reconnect"
    assert repo.connection["access_token"] == "new-token-reconnected"


async def test_start_oauth_facebook_login_for_business() -> None:
    settings = Settings(
        instagram_app_id="my-app-id",
        instagram_app_secret="my-app-secret",
        instagram_redirect_uri="http://localhost/callback",
        instagram_config_id="3859738497654753",
    )
    service = InstagramService(repository=FakeInstagramRepository(), settings=settings)
    user = CurrentUser(id="22222222-2222-2222-2222-222222222222", email="user@test.com", claims={})

    res = await service.start_oauth(user)
    assert "https://www.facebook.com/v25.0/dialog/oauth" in res.url
    assert "client_id=my-app-id" in res.url
    assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in res.url
    assert "config_id=3859738497654753" in res.url
    assert "response_type=code" in res.url
    assert "force_reauth=true" in res.url


@patch("httpx.AsyncClient.get")
async def test_exchange_code_facebook_login_for_business_success(mock_get) -> None:
    settings = Settings(
        instagram_app_id="real-id",
        instagram_app_secret="real-secret",
        instagram_redirect_uri="http://localhost/callback",
        instagram_config_id="3859738497654753",
    )
    provider = InstagramOAuthProvider(settings)

    # Mock the HTTP calls:
    # 1. GET oauth/access_token
    # 2. GET me/accounts
    # 3. GET ig_user_id
    mock_get.side_effect = [
        Response(200, json={"access_token": "fb-user-access-token", "scopes": ["custom_scope"]}),
        Response(200, json={
            "data": [
                {
                    "name": "My Business Page",
                    "access_token": "fb-page-access-token",
                    "id": "page-id-999",
                    "instagram_business_account": {"id": "ig-business-888"}
                }
            ]
        }),
        Response(200, json={"id": "ig-business-888", "username": "thevijaymarathi", "name": "Vijay Marathi"}),
    ]

    profile = await provider.exchange_code("fb-code-123")
    assert profile.ig_user_id == "ig-business-888"
    assert profile.ig_username == "thevijaymarathi"
    assert profile.access_token == "fb-page-access-token"
    assert "custom_scope" in profile.scopes


