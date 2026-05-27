from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode
from uuid import UUID
import httpx

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

# Instagram Business Login scopes (shows Instagram login screen, not Facebook)
INSTAGRAM_SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments",
    "instagram_business_content_publish",
    "instagram_business_manage_insights",
]


class InstagramOAuthProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def exchange_code(self, code: str) -> InstagramProfile:
        if (
            not self.settings.instagram_app_id
            or self.settings.instagram_app_id == "dev"
            or not self.settings.instagram_app_secret
            or self.settings.instagram_app_secret == "dev"
        ):
            # Fallback to dev profile in mock mode
            return InstagramProfile(
                ig_user_id=f"dev-{code}",
                ig_username="connected.account",
                access_token=f"dev-token-{code}",
                scopes=INSTAGRAM_SCOPES,
            )

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Exchange code for short-lived token via Instagram Business Login
            token_res = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": self.settings.instagram_app_id,
                    "client_secret": self.settings.instagram_app_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.settings.instagram_redirect_uri,
                    "code": code,
                },
            )
            if token_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to exchange OAuth code: {token_res.text}",
                )
            token_data = token_res.json()
            short_lived_token = token_data.get("access_token")
            ig_user_id = str(token_data.get("user_id", ""))

            if not short_lived_token or not ig_user_id:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message="OAuth response did not return access_token or user_id",
                )

            # Step 2: Exchange for long-lived token (60-day)
            long_token_res = await client.get(
                "https://graph.instagram.com/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.settings.instagram_app_secret,
                    "access_token": short_lived_token,
                },
            )
            if long_token_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to get long-lived token: {long_token_res.text}",
                )
            long_lived_token = long_token_res.json().get("access_token", short_lived_token)

            # Step 3: Fetch Instagram Business profile (username, name)
            profile_res = await client.get(
                f"https://graph.instagram.com/v25.0/{ig_user_id}",
                params={
                    "fields": "id,username,name,profile_picture_url",
                    "access_token": long_lived_token,
                },
            )
            if profile_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to fetch Instagram profile: {profile_res.text}",
                )
            profile_data = profile_res.json()
            ig_username = profile_data.get("username") or profile_data.get("name", "ig_user")

            return InstagramProfile(
                ig_user_id=ig_user_id,
                ig_username=ig_username,
                access_token=long_lived_token,
                scopes=INSTAGRAM_SCOPES,
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
        self.provider = provider or InstagramOAuthProvider(settings)

    async def start_oauth(self, user: CurrentUser) -> OAuthStartResponse:
        state = sign_state({"user_id": str(user.id)}, self.settings.instagram_app_secret or "dev")
        params = urlencode(
            {
                "client_id": self.settings.instagram_app_id or "dev-instagram-app",
                "redirect_uri": self.settings.instagram_redirect_uri,
                "response_type": "code",
                "scope": ",".join(INSTAGRAM_SCOPES),
                "state": state,
                "force_reauth": "true",
            }
        )
        # Instagram Business Login endpoint — shows Instagram login screen (not Facebook)
        return OAuthStartResponse(
            url=f"https://www.instagram.com/oauth/authorize?{params}", state=state
        )

    async def complete_oauth(
        self, user: CurrentUser, code: str, state: str, workspace_id: UUID | None = None
    ) -> InstagramWorkspaceResponse:
        payload = verify_state(state, self.settings.instagram_app_secret or "dev")
        if payload.get("user_id") != str(user.id):
            raise ApiError(
                status_code=400, code="invalid_state", message="OAuth state user mismatch"
            )

        profile = await self.provider.exchange_code(code)

        if workspace_id is not None:
            workspace_detail = await self.repository.get_workspace_detail(workspace_id)
            if workspace_detail is None:
                raise ApiError(
                    status_code=404,
                    code="workspace_not_found",
                    message="Workspace not found",
                )

            # Clear any connection on the target workspace, and delete duplicate connection for this IG account elsewhere
            await self.repository.disconnect(workspace_id)
            await self.repository.delete_connection_by_ig_user(profile.ig_user_id)

            await self.repository.create_connection_for_workspace(
                workspace_id=workspace_id,
                ig_user_id=profile.ig_user_id,
                ig_username=profile.ig_username,
                access_token=profile.access_token,
                scopes=profile.scopes,
            )

            workspace = workspace_detail | {
                "ig_username": profile.ig_username,
                "ig_user_id": profile.ig_user_id,
                "plan": "free",
                "active": True,
            }
            return InstagramWorkspaceResponse(workspace=workspace)

        existing = await self.repository.find_connection_by_ig_user(profile.ig_user_id)
        if existing is not None:
            # Update connection in place and return existing workspace details
            await self.repository.update_connection(
                workspace_id=existing["workspace_id"],
                access_token=profile.access_token,
                scopes=profile.scopes,
                ig_username=profile.ig_username,
            )
            workspace_detail = await self.repository.get_workspace_detail(existing["workspace_id"])
            if workspace_detail is None:
                raise ApiError(
                    status_code=404,
                    code="workspace_not_found",
                    message="Workspace not found",
                )
            workspace = workspace_detail | {
                "ig_username": profile.ig_username,
                "ig_user_id": profile.ig_user_id,
                "plan": "free",
                "active": True,
            }
            return InstagramWorkspaceResponse(workspace=workspace)

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

    async def get_media(self, workspace_id: UUID, limit: int = 10, after: str | None = None) -> dict:
        connection = await self.repository.get_connection(workspace_id)
        if not connection:
            raise ApiError(status_code=400, code="not_connected", message="Instagram not connected to this workspace")

        ig_user_id = connection["ig_user_id"]
        token = connection["access_token_enc"].decode("utf-8")

        if not token or token.startswith("dev-token") or token == "dev":
            # Return premium mock media in development mode
            mock_data = [
                {
                    "id": f"mock-media-{i}",
                    "caption": f"This is a premium mock Reel #{i} talking about automations! 🚀 #vibedm #socialmedia",
                    "media_type": "VIDEO" if i % 3 == 0 else "IMAGE",
                    "media_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80" if i % 3 != 0 else "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400&q=80",
                    "thumbnail_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80" if i % 3 != 0 else "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400&q=80",
                    "permalink": "https://instagram.com",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                for i in range(1, limit + 1)
            ]
            return {
                "data": mock_data,
                "paging": {"cursors": {"after": "mock-cursor"} if after is None else None}
            }

        # Fetch from Instagram Graph API
        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
                "limit": limit,
                "access_token": token,
            }
            if after:
                params["after"] = after

            res = await client.get(
                f"https://graph.instagram.com/v25.0/{ig_user_id}/media",
                params=params
            )
            if res.status_code != 200:
                raise ApiError(status_code=400, code="meta_api_failed", message=f"Meta API failed: {res.text}")
            return res.json()

