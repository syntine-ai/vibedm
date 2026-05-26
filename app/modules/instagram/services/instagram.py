from __future__ import annotations

from urllib.parse import urlencode

from app.config import Settings
from app.core.errors import ApiError
from app.deps import CurrentUser, WorkspaceContext
from app.modules.instagram.repositories.instagram import InstagramRepository
from app.modules.instagram.schemas.instagram import (
    InstagramProfile,
    InstagramWorkspaceResponse,
    OAuthStartResponse,
)
from app.security import sign_state, verify_state


class InstagramOAuthProvider:
    async def exchange_code(self, code: str) -> InstagramProfile:
        return InstagramProfile(
            ig_user_id=f"dev-{code}",
            ig_username="connected.account",
            access_token=f"dev-token-{code}",
            scopes=["instagram_basic", "instagram_manage_messages"],
        )


class InstagramService:
    def __init__(
        self,
        repository: InstagramRepository,
        settings: Settings,
        provider: InstagramOAuthProvider | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.provider = provider or InstagramOAuthProvider()

    async def start_oauth(self, user: CurrentUser) -> OAuthStartResponse:
        state = sign_state({"user_id": str(user.id)}, self.settings.instagram_app_secret or "dev")
        params = urlencode(
            {
                "client_id": self.settings.instagram_app_id or "dev-instagram-app",
                "redirect_uri": self.settings.instagram_redirect_uri,
                "response_type": "code",
                "scope": "instagram_basic,instagram_manage_messages",
                "state": state,
            }
        )
        return OAuthStartResponse(
            url=f"https://api.instagram.com/oauth/authorize?{params}", state=state
        )

    async def complete_oauth(
        self, user: CurrentUser, code: str, state: str
    ) -> InstagramWorkspaceResponse:
        payload = verify_state(state, self.settings.instagram_app_secret or "dev")
        if payload.get("user_id") != str(user.id):
            raise ApiError(
                status_code=400, code="invalid_state", message="OAuth state user mismatch"
            )

        profile = await self.provider.exchange_code(code)
        existing = await self.repository.find_connection_by_ig_user(profile.ig_user_id)
        if existing is not None:
            raise ApiError(
                status_code=409,
                code="ig_already_connected",
                message="Instagram account is already connected",
            )
        workspace = await self.repository.create_workspace_with_connection(
            owner_id=user.id,
            name=profile.ig_username,
            ig_user_id=profile.ig_user_id,
            ig_username=profile.ig_username,
            access_token=profile.access_token,
            scopes=profile.scopes,
        )
        return InstagramWorkspaceResponse(workspace=workspace)

    async def disconnect(self, workspace: WorkspaceContext) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.disconnect(workspace.id)
        return {"disconnected": True}
