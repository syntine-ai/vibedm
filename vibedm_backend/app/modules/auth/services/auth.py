from __future__ import annotations

from app.core.errors import ApiError
from app.deps import CurrentUser
from app.modules.auth.repositories.auth import AuthRepository
from app.modules.auth.schemas.auth import AuthMeResponse, UserProfile, WorkspaceSummary


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    async def sync_user(self, user: CurrentUser) -> UserProfile:
        row = await self.repository.upsert_user(user)
        return UserProfile(**row)

    async def get_me(self, user: CurrentUser) -> AuthMeResponse:
        user_row = await self.repository.get_user(user.id)
        if user_row is None:
            user_profile = await self.sync_user(user)
        else:
            user_profile = UserProfile(**user_row)

        workspaces = [
            WorkspaceSummary(**row) for row in await self.repository.list_workspaces(user.id)
        ]
        return AuthMeResponse(user=user_profile, workspaces=workspaces)

    async def logout(self, user: CurrentUser) -> dict[str, bool]:
        if not user.id:
            raise ApiError(status_code=401, code="unauthorized", message="Missing user")
        return {"revoked": False}
