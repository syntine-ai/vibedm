from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.deps import CurrentUser
from app.main import create_app
from app.modules.auth.routers.auth import get_auth_service
from app.modules.auth.schemas.auth import AuthMeResponse, UserProfile, WorkspaceSummary

TEST_SECRET = "test-secret"


@pytest.fixture(autouse=True)
def reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/test")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:3000")
    get_settings.cache_clear()


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def auth_header(user_id: UUID) -> dict[str, str]:
    token = jwt.encode(
        {"sub": str(user_id), "email": "alex@example.com", "role": "authenticated"},
        TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


class FakeAuthService:
    async def get_me(self, user: CurrentUser) -> AuthMeResponse:
        return AuthMeResponse(
            user=UserProfile(
                id=user.id,
                email=user.email,
                first_name="Alex",
                last_name="Morgan",
                phone=None,
                avatar_url=None,
            ),
            workspaces=[
                WorkspaceSummary(
                    id=uuid4(),
                    name="alex.creates",
                    role="owner",
                    ig_username="alex.creates",
                    plan="free",
                    active=True,
                )
            ],
        )

    async def sync_user(self, user: CurrentUser) -> UserProfile:
        return UserProfile(
            id=user.id,
            email=user.email,
            first_name=None,
            last_name=None,
            phone=None,
            avatar_url=None,
        )

    async def logout(self, user: CurrentUser) -> dict[str, bool]:
        return {"revoked": False}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
